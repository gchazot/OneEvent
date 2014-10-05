'''
Created on 22 Jun 2014

@author: germs
'''
from django.shortcuts import render, redirect, get_object_or_404, render_to_response
from django.contrib.auth.decorators import login_required
from django.db.models.query_utils import Q

from datetime import datetime, date

from OneEvent.models import Event, ParticipantBooking
from OneEvent.forms import BookingForm, EventForm
from django.template.context import RequestContext
from django.http.response import HttpResponse
from django.template.defaultfilters import slugify
from django.contrib import messages
import unicode_csv


def index(request):
    if request.user.is_authenticated():
        return redirect('my_events')
    else:
        return redirect('all_events')


def events_list(request, events, context={}):
    context['events'] = []
    for evt in events:
        event_info = {'event': evt, 'booking': None}
        if request.user.is_authenticated():
            try:
                event_info['booking'] = evt.get_active_bookings().get(person=request.user)
            except ParticipantBooking.DoesNotExist:
                pass
        context['events'].append(event_info)

    return render(request, 'events_list.html', context)


def future_events(request):
    context = {'events_shown': 'fut'}
    events = Event.objects.filter(end__gte=datetime.now())
    return events_list(request, events, context)


def past_events(request):
    context = {'events_shown': 'past'}
    now = datetime.now()
    query = Q(end__lte=now) | Q(end=None, start__lte=now)
    events = Event.objects.filter(query)
    return events_list(request, events, context)


def all_events(request):
    context = {'events_shown': 'all'}
    return events_list(request, Event.objects.all(), context)


@login_required
def my_events(request):
    context = {'events_shown': 'mine'}
    query = Q(bookings__person=request.user, bookings__cancelled=False)
    query = query | Q(organisers=request.user)
    events = Event.objects.filter(query).distinct()
    if events.count() > 0:
        return events_list(request, events, context)
    else:
        messages.debug(request, "You have no event yet")
        return redirect('all_events')


@login_required
def create_booking(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    if event.is_booking_open():
        booking, _ = ParticipantBooking.objects.get_or_create(event=event,
                                                              person=user)
        messages.warning(request, 'Please confirm your registration here!')
        return redirect('update_booking', booking_id=booking.id)
    else:
        messages.error(request, 'Bookings are closed for "{0}"!'.format(event.title))
        return redirect('index')


@login_required
def update_booking(request, booking_id):
    booking = get_object_or_404(ParticipantBooking, id=booking_id)

    if not booking.user_can_update(request.user):
        messages.error(request, 'You are not authorised to update this booking !')
        return redirect('index')

    form = BookingForm(booking, request.POST or None)
    if form.is_valid():
        form.save()
        booking.cancelled = False
        booking.save()
        messages.success(request, 'Registration updated')
        return redirect('my_events')

    return render_to_response('update_booking.html',
                              {'booking': booking,
                               'form': form},
                              context_instance=RequestContext(request))


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(ParticipantBooking, id=booking_id)

    if not booking.user_can_update(request.user):
        messages.error(request, 'You are not authorised to cancel this booking !')
        return redirect('index')

    if request.method == 'POST':
        booking.cancelled = True
        booking.save()
        messages.warning(request, 'Registration cancelled')
        return redirect('my_events')
    else:
        return render_to_response('cancel_booking.html',
                                  {'booking': booking},
                                  context_instance=RequestContext(request))


@login_required
def manage_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_update(request.user):
        messages.error(request, 'You are not authorised to manage this event !')
        return redirect('index')

    form = EventForm(request.POST or None, instance=event)
    if form.is_valid():
        form.save()
        if request.user in event.organisers.all():
            messages.success(request, 'Event details updated'.format(event.title))
            return redirect('manage_event', event_id=event_id)
        else:
            messages.success(request, 'You removed yourself from the organisers of {0}'.format(event.title))
            return redirect('index')
    return render_to_response('manage_event.html',
                              {'event': event, 'form': form},
                              context_instance=RequestContext(request))


@login_required
def confirm_payment(request, booking_id, cancel=False):
    booking = get_object_or_404(ParticipantBooking, id=booking_id)

    if not booking.user_can_update_payment(request.user):
        messages.error(request, 'You are not authorised to manage payment for this event !')
        return redirect('index')

    if request.method == 'POST':
        if not cancel:
            booking.paidTo = request.user
            booking.datePaid = date.today()
        else:
            booking.paidTo = None
            booking.datePaid = None
        booking.save()

        if not cancel:
            messages.success(request,
                             'Payment confirmed for {0}'.format(booking.person.get_full_name()))
        else:
            messages.success(request,
                             'Refund confirmed for {0}'.format(booking.person.get_full_name()))

        return redirect('manage_event', event_id=booking.event.id)
    else:
        return render_to_response('confirm_payment.html',
                                  {'booking': booking, 'cancel': cancel},
                                  context_instance=RequestContext(request))


@login_required
def dl_event_options_summary(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_update(request.user):
        messages.error(request, 'You are not authorised to download options for this event !')
        return redirect('index')

    filename = "{0}_options_{1}.csv".format(slugify(event.title),
                                            datetime.now().strftime('%Y%m%d%H%M%S'))

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
def dl_participants_list(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_update(request.user):
        messages.error(request, 'You are not authorised to download participants for this event !')
        return redirect('index')

    filename = "{0}_participants_{1}.csv".format(slugify(event.title),
                                                 datetime.now().strftime('%Y%m%d%H%M%S'))

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
    writer = unicode_csv.UnicodeWriter(response)

    bookings = event.bookings.order_by('person__last_name', 'person__first_name')

    writer.writerow(["Last name", "First name", 'Cancelled', 'Payment status', 'Choices'])
    for booking in bookings:
        if booking.paidTo is not None:
            payment = "{0} on {1}".format(booking.paidTo.get_full_name(), booking.datePaid)
        else:
            payment = "NOT PAID"

        if booking.cancelled:
            cancelled = "Yes"
        else:
            cancelled = "No"

        row = [booking.person.last_name, booking.person.first_name, cancelled, payment]
        for option in booking.options.all():
            row.append(option.option.title)
        writer.writerow(row)

    return response
