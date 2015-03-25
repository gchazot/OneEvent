
'''
Created on 22 Jun 2014

@author: germs
'''
from django.shortcuts import render, redirect, get_object_or_404, render_to_response
from django.contrib.auth.decorators import login_required
from django.db.models.query_utils import Q
from django.template.context import RequestContext
from django.http.response import HttpResponse, Http404
from django.template.defaultfilters import slugify
from django.contrib import messages
from django.utils import timezone

import unicode_csv
from timezones import get_tzinfo
from datetime import timedelta


from OneEvent.models import Event, Booking, Message, Choice, BookingOption
from OneEvent.forms import (BookingForm, EventForm, ChoiceForm, OptionFormSet, OptionFormSetHelper,
                            CreateBookingOnBehalfForm, MessageForm, ReplyMessageForm)
from django.contrib.auth.models import User


# A default datetime format (too lazy to use the one in settings)
dt_format = '%a, %d %b %Y %H:%M'


def index(request):
    if request.user.is_authenticated():
        return redirect('events_list_mine')
    else:
        return redirect('events_list_all')


def events_list(request, events, context, show_archived=False):
    context['events'] = []
    for evt in events:
        event_info = {'event': evt, 'booking': None}
        # Hide events that the user can not list
        if not evt.user_can_list(request.user, show_archived):
            continue

        if request.user.is_authenticated():
            # Look for a possible booking by the user
            try:
                user_booking = evt.get_active_bookings().get(person=request.user)
                event_info['booking'] = user_booking
                event_info['user_can_cancel'] = user_booking.user_can_cancel(request.user)
            except Booking.DoesNotExist:
                pass
            event_info['user_can_book'] = evt.user_can_book(request.user)
            event_info['user_can_update'] = evt.user_can_update(request.user)

        context['events'].append(event_info)

    return render(request, 'events_list.html', context, context_instance=RequestContext(request))


def events_list_future(request):
    context = {'events_shown': 'fut'}
    now = timezone.now()
    query = Q(end__gt=now) | Q(end=None, start__gte=now)
    events = Event.objects.filter(query)
    return events_list(request, events, context)


def events_list_past(request):
    context = {'events_shown': 'past'}
    now = timezone.now()
    query = Q(end__lte=now) | Q(end=None, start__lte=now)
    events = Event.objects.filter(query)
    return events_list(request, events, context)


def events_list_all(request):
    context = {'events_shown': 'all'}
    return events_list(request, Event.objects.all(), context)


def events_list_archived(request):
    context = {'events_shown': 'arch'}
    events = Event.objects.filter(pub_status='ARCH')
    return events_list(request, events, context, True)


@login_required
def events_list_mine(request):
    context = {'events_shown': 'mine'}
    query = Q(bookings__person=request.user, bookings__cancelledBy=None)
    query = query | Q(organisers=request.user)
    query = query | Q(owner=request.user)
    events = Event.objects.filter(query).distinct()
    if events.count() > 0:
        return events_list(request, events, context)
    else:
        messages.debug(request, "You have no event yet")
        return redirect('events_list_all')


@login_required
def booking_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_book(request.user):
        messages.error(request, 'You are not allowed to register to this event')
        return redirect('index')

    if event.is_booking_open():
        booking, _ = Booking.objects.get_or_create(event=event,
                                                   person=request.user,
                                                   defaults={'cancelledBy': request.user,
                                                             'cancelledOn': timezone.now()})
        messages.warning(request, 'Please confirm your registration here!')
        return redirect('booking_update', booking_id=booking.id)
    else:
        messages.error(request, u'Bookings are closed for "{0}"!'.format(event.title))
        return redirect('index')


@login_required
def booking_create_on_behalf(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_is_organiser(request.user):
        messages.error(request, 'You can not create a booking on behalf for this event')
        return redirect('index')

    form = CreateBookingOnBehalfForm(event.id, request.POST or None)
    if form.is_valid():
        target_user = User.objects.get(username=form.cleaned_data['username'])
        booking, created = Booking.objects.get_or_create(
            event=event,
            person=target_user,
            defaults={'cancelledBy': request.user,
                      'cancelledOn': timezone.now()})

        if created:
            messages.success(request,
                             u'Booking created for {0}. Please confirm it.'.format(
                                 target_user.get_full_name()))
        else:
            messages.warning(request,
                             u'Booking exists for {0}. You may edit it.'.format(
                                 target_user.get_full_name()))

        return redirect('booking_update', booking_id=booking.id)
    else:
        timezone.activate(event.get_tzinfo())
        return render_to_response('booking_create_on_behalf.html',
                                  {'form': form, 'event': event},
                                  context_instance=RequestContext(request))


@login_required
def booking_update(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.user_can_update(request.user):
        messages.error(request, 'You are not authorised to update this booking !')
        return redirect('index')

    timezone.activate(booking.event.get_tzinfo())

    booking_was_cancelled = (booking.cancelledBy is not None)

    form = BookingForm(booking, request.POST or None)

    if booking_was_cancelled and booking.event.is_fully_booked():
        messages.error(request, 'Sorry the event is fully booked already')
    elif form.is_valid():
        form.save()
        if booking_was_cancelled:
            booking.confirmedOn = timezone.now()
            booking.cancelledBy = None
            booking.cancelledOn = None
        booking.save()
        messages.success(request, 'Registration updated')
        return redirect('events_list_mine')

    return render_to_response('booking_update.html',
                              {'booking': booking,
                               'form': form},
                              context_instance=RequestContext(request))


@login_required
def booking_cancel(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.user_can_cancel(request.user):
        messages.error(request, 'You are not authorised to cancel this booking !')
        return redirect('index')

    timezone.activate(booking.event.get_tzinfo())

    if request.method == 'POST':
        booking.confirmedOn = None
        booking.cancelledBy = request.user
        booking.cancelledOn = timezone.now()
        booking.save()
        messages.warning(request, 'Registration cancelled')
        if request.user == booking.person:
            return redirect('events_list_mine')
        else:
            return redirect('event_manage', event_id=booking.event.id)
    else:
        return render_to_response('booking_cancel.html',
                                  {'booking': booking},
                                  context_instance=RequestContext(request))


@login_required
def event_manage(request, event_id):
    try:
        event = Event.objects.prefetch_related(
            'bookings__person',
            'bookings__options__option'
        ).get(id=event_id)
    except Event.DoesNotExist:
        return Http404

    if not event.user_can_update(request.user):
        messages.error(request, 'You are not authorised to manage this event !')
        return redirect('index')

    # Activate the timezone from the event
    timezone.activate(event.get_tzinfo())

    return render_to_response('event_manage.html',
                              {'event': event},
                              context_instance=RequestContext(request))


def _event_edit_form(request, event):
    '''
    Handle the edition of an event from the form page
    Not to be used directly as a view
    '''
    is_new_event = not bool(event.pk)

    # Activate the timezone from form data before processing the form
    # Use a separate form! otherwise the data is already processed
    tz_form = EventForm(request.POST or None, instance=event)
    if tz_form.is_valid():
        tz = get_tzinfo(tz_form.cleaned_data['city'])
        timezone.activate(tz)

    event_form = EventForm(request.POST or None, instance=event)
    if event_form.is_valid():
        event_form.save()
        if is_new_event:
            messages.success(request, 'Event created')
            return redirect('event_update', event_id=event.id)
        elif event.user_is_organiser(request.user):
            messages.success(request, 'Event details updated')
            return redirect('event_update', event_id=event.id)
        else:
            messages.warning(request,
                             u'You removed yourself from the organisers of {0}'.format(event.title))
            return redirect('index')
    else:
        if event_form.is_bound:
            messages.error(request, 'Unable to update event details, see below for errors!')
        # Not saving a form. Activate the timezone from the event
        timezone.activate(event.get_tzinfo())

    return render_to_response('event_update.html',
                              {'event': event, 'event_form': event_form},
                              context_instance=RequestContext(request))


@login_required
def event_update(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_update(request.user):
        messages.error(request, 'You are not authorised to edit this event !')
        return redirect('index')

    return _event_edit_form(request, event)


@login_required
def event_create(request):
    new_event = Event(owner=request.user,
                      city='London')
    return _event_edit_form(request, new_event)


@login_required
def _choice_edit_form(request, choice):
    '''
    Handle the edition of a choice from the form page
    Not to be used directly as a view
    '''
    if not choice.event.user_can_update(request.user):
        messages.error(request, 'You are not authorised to edit this event !')
        return redirect('index')

    is_new_choice = not bool(choice.pk)

    choice_form = ChoiceForm(request.POST or None, instance=choice)
    options_formset = OptionFormSet(request.POST or None, instance=choice)
    options_helper = OptionFormSetHelper()

    if choice_form.is_valid() and options_formset.is_valid():
        # Update existing bookings with a deleted option to the new default
        for deleted_option in options_formset.deleted_options:
            part_options = BookingOption.objects.filter(option=deleted_option)
            part_options.update(option=options_formset.new_default)

        # Save choice changes
        choice_form.save()
        options_formset.save()

        # If a new choice, choose default option for all bookings
        if is_new_choice:
            bookings = Booking.objects.filter(event=choice.event,
                                                         cancelledBy__exact=None)
            for bkg in bookings:
                print u"Adding option to booking {0} : {1}".format(bkg, options_formset.new_default)
                bkg.options.create(option=options_formset.new_default)

        messages.success(request, 'Choice updated')
        return redirect('event_update', event_id=choice.event.id)
    else:
        if choice_form.is_bound or options_formset.is_bound:
            if is_new_choice:
                messages.error(request, 'Unable to create choice, see errors below!')
            else:
                messages.error(request, 'Unable to update choice, see errors below!')

    timezone.activate(choice.event.get_tzinfo())
    return render_to_response('choice_edit.html',
                              {'choice': choice,
                               'choice_form': choice_form,
                               'options_formset': options_formset,
                               'options_helper': options_helper},
                              context_instance=RequestContext(request))


def choice_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    new_choice = Choice(event=event)
    return _choice_edit_form(request, new_choice)


def choice_update(request, choice_id):
    choice = get_object_or_404(Choice, id=choice_id)
    return _choice_edit_form(request, choice)


@login_required
def choice_delete(request, choice_id):
    choice = get_object_or_404(Choice, id=choice_id)

    if not choice.event.user_can_update(request.user):
        messages.error(request, 'You are not authorised to edit this event !')
        return redirect('index')

    if request.method == 'POST':
        choice.delete()
        messages.success(request, u'Choice deleted: {0}'.format(choice.title))

        return redirect('event_update', event_id=choice.event.id)
    else:
        timezone.activate(choice.event.get_tzinfo())
        return render_to_response('choice_delete.html',
                                  {'choice': choice},
                                  context_instance=RequestContext(request))


@login_required
def booking_payment_confirm(request, booking_id, cancel=False):
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.user_can_update_payment(request.user):
        messages.error(request, 'You are not authorised to manage payment for this event !')
        return redirect('index')

    if request.method == 'POST':
        if not cancel:
            booking.paidTo = request.user
            booking.datePaid = timezone.now()
        else:
            booking.paidTo = None
            booking.datePaid = None
        booking.save()

        if not cancel:
            messages.success(request,
                             u'Payment confirmed for {0}'.format(booking.person.get_full_name()))
        else:
            messages.success(request,
                             u'Refund confirmed for {0}'.format(booking.person.get_full_name()))

        return redirect('event_manage', event_id=booking.event.id)
    else:
        timezone.activate(booking.event.get_tzinfo())
        return render_to_response('booking_payment_confirm.html',
                                  {'booking': booking, 'cancel': cancel},
                                  context_instance=RequestContext(request))


@login_required
def booking_payment_exempt(request, booking_id, cancel=False):
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.user_can_update_payment(request.user):
        messages.error(request, 'You are not authorised to manage payment for this event !')
        return redirect('index')

    if cancel and not booking.exempt_of_payment:
        messages.error(request, 'This booking is not exempt of payment')
        return redirect('event_manage', event_id=booking.event.id)
    elif not cancel and booking.exempt_of_payment:
        messages.error(request, 'This booking is already exempt of payment')
        return redirect('event_manage', event_id=booking.event.id)

    if request.method == 'POST':
        if not cancel:
            booking.paidTo = request.user
            booking.datePaid = timezone.now()
            booking.exempt_of_payment = True
        else:
            booking.paidTo = None
            booking.datePaid = None
            booking.exempt_of_payment = False
        booking.save()

        if not cancel:
            messages.success(request,
                             u'Exemption confirmed for {0}'.format(booking.person.get_full_name()))
        else:
            messages.success(request,
                             u'Exemption cancelled for {0}'.format(booking.person.get_full_name()))
        return redirect('event_manage', event_id=booking.event.id)
    else:
        timezone.activate(booking.event.get_tzinfo())
        return render_to_response('booking_payment_exempt.html',
                                  {'booking': booking, 'cancel': cancel},
                                  context_instance=RequestContext(request))


@login_required
def event_download_options_summary(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_update(request.user):
        messages.error(request, 'You are not authorised to download options for this event !')
        return redirect('index')

    filename = "{0}_options_{1}.csv".format(slugify(event.title),
                                            timezone.now().strftime('%Y%m%d%H%M%S'))

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
    writer = unicode_csv.UnicodeWriter(response)

    summary_values = event.get_options_counts()
    writer.writerow([u"Choice", u"Options"])
    for choice, options in summary_values.iteritems():
        row = [choice.title]
        for option, total in options.iteritems():
            row.append(option.title)
            row.append(str(total))
        writer.writerow(row)

    return response


@login_required
def event_download_participants_list(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_update(request.user):
        messages.error(request, 'You are not authorised to download participants for this event !')
        return redirect('index')

    filename = "{0}_participants_{1}.csv".format(slugify(event.title),
                                                 timezone.now().strftime('%Y%m%d%H%M%S'))

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
    writer = unicode_csv.UnicodeWriter(response)

    bookings = event.bookings.order_by('person__last_name', 'person__first_name')

    writer.writerow([u'Last name', u'First name', u'email', u'Employment',
                     u'Cancelled', u'Cancelled By', u'Confirmed On',
                     u'Payment status', u'Paid to',
                     u'Choices'])
    for booking in bookings:
        if booking.paidTo is not None:
            local_datePaid = booking.datePaid.astimezone(booking.event.get_tzinfo())
            payment = u'Paid'
            paid_to = u'{0} on {1}'.format(booking.paidTo.get_full_name(),
                                           local_datePaid.strftime(dt_format))
        else:
            paid_to = u''
            if booking.must_pay() > 0:
                payment = u'Must pay {0} ({1})'.format(booking.must_pay(), event.price_currency)
            else:
                payment = u'Not needed'

        if booking.cancelledBy is not None:
            cancelled = u'Yes'
            local_dateCancelled = booking.cancelledOn.astimezone(booking.event.get_tzinfo())
            cancelled_by = u"{0} on {1}".format(booking.cancelledBy.get_full_name(),
                                                local_dateCancelled.strftime(dt_format))
            if booking.paidTo is None:
                payment = u"N/A"
        else:
            cancelled = u"No"
            cancelled_by = u''

        if booking.confirmedOn is not None:
            local_date_confirmed = booking.confirmedOn.astimezone(booking.event.get_tzinfo())
            confirmed_on = local_date_confirmed.strftime(dt_format)
        else:
            confirmed_on = 'N/A'

        if booking.is_employee():
            employment = u'Employee'
        elif booking.is_contractor():
            employment = u'Contractor'
        else:
            employment = u'Unknown'

        row = [booking.person.last_name, booking.person.first_name,
               booking.person.email, employment,
               cancelled, cancelled_by, confirmed_on,
               payment, paid_to]
        for option in booking.options.all():
            row.append(option.option.title)
        writer.writerow(row)

    return response


@login_required
def messages_list(request):
    threads = Message.objects.filter(thread_head=None)
    if not request.user.is_superuser:
        threads = threads.filter(sender=request.user)

    user_threads = []
    for thread_head in threads:
        messages = thread_head.full_thread()
        user_threads.append((thread_head, messages,))

    return render_to_response('messages_list.html',
                              {'threads': user_threads},
                              context_instance=RequestContext(request))


@login_required
def message_create(request, thread_id=None):
    # Pre-populate some fields of the message
    new_msg = Message(sender=request.user)
    if thread_id is None:
        thread_head = None
        form = MessageForm(request.POST or None, instance=new_msg)
    else:
        thread_head = get_object_or_404(Message, id=thread_id)
        new_msg.thread_head = thread_head
        new_msg.title = thread_head.title
        new_msg.category = thread_head.category
        form = ReplyMessageForm(request.POST or None, instance=new_msg)

    # Check a quota of messages
    limit = timezone.now() - timedelta(days=1)
    user_msgs = Message.objects.filter(created__gte=limit, sender=request.user)
    if user_msgs.count() >= 10:
        messages.error(request, 'Sorry you have used your message quota')
        return redirect('messages_list')

    if form.is_valid():
        new_message = form.save()
        new_message.send_message_notification()
        messages.success(request, 'Your message has been sent')
        return redirect('messages_list')

    return render_to_response('message_create.html',
                              {'form': form, 'thread_id': thread_id},
                              context_instance=RequestContext(request))


@login_required
def booking_send_invite(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.send_calendar_invite():
        messages.success(request, 'Invitation sent to your email')
    else:
        messages.error(request, 'Failure sending the invitation')
    return redirect('booking_update', booking_id=booking_id)
