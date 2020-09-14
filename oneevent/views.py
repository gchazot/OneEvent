from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models.query_utils import Q
from django.http.response import HttpResponse, Http404
from django.template.defaultfilters import slugify
from django.contrib import messages
from django.utils import timezone

from . import unicode_csv

from .models import Event, Booking, Choice, BookingOption
from .forms import (
    EventForm,
    CategoryFormSet,
    CategoryFormSetHelper,
    SessionFormSet,
    SessionFormSetHelper,
    ChoiceForm,
    OptionFormSet,
    OptionFormSetHelper,
    CreateBookingOnBehalfForm,
    BookingChoicesForm,
    BookingSessionForm,
)
from django.contrib.auth import get_user_model
from django.urls import reverse


# A default datetime format (too lazy to use the one in settings)
dt_format = "%a, %d %b %Y %H:%M"


def index(request):
    if request.user.is_authenticated:
        return redirect("events_list_mine")
    else:
        return redirect("events_list_all")


def events_list(request, events, context, show_archived=False):
    context["events"] = []
    for evt in events:
        event_info = {"event": evt, "booking": None}
        # Hide events that the user can not list
        if not evt.user_can_list(request.user, show_archived):
            continue

        if request.user.is_authenticated:
            # Look for a possible booking by the user
            try:
                user_booking = evt.get_active_bookings().get(person=request.user)
                event_info["booking"] = user_booking
                event_info["user_can_cancel"] = user_booking.user_can_cancel(
                    request.user
                )
            except Booking.DoesNotExist:
                pass
            event_info["user_can_book"] = evt.user_can_book(request.user)
            event_info["user_can_update"] = evt.user_can_update(request.user)
            event_info["price_for_user"] = evt.user_price(request.user)

        context["events"].append(event_info)

    return render(request, "oneevent/events_list.html", context)


def events_list_future(request):
    context = {"events_shown": "fut"}
    now = timezone.now()
    query = Q(end__gt=now) | Q(end=None, start__gte=now)
    events = Event.objects.filter(query)
    return events_list(request, events, context)


def events_list_past(request):
    context = {"events_shown": "past"}
    now = timezone.now()
    query = Q(end__lte=now) | Q(end=None, start__lte=now)
    events = Event.objects.filter(query)
    return events_list(request, events, context)


def events_list_all(request):
    context = {"events_shown": "all"}
    return events_list(request, Event.objects.all(), context)


def events_list_archived(request):
    context = {"events_shown": "arch"}
    events = Event.objects.filter(pub_status="ARCH")
    return events_list(request, events, context, True)


@login_required
def events_list_mine(request):
    context = {"events_shown": "mine"}
    query = Q(bookings__person=request.user, bookings__cancelledOn=None)
    query = query | Q(organisers=request.user)
    query = query | Q(owner=request.user)
    events = Event.objects.filter(query).distinct()
    if events.count() > 0:
        return events_list(request, events, context)
    else:
        messages.debug(request, "You have no event yet")
        return redirect("events_list_all")


@login_required
def booking_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_book(request.user):
        messages.error(request, "You are not allowed to register to this event")
        return redirect("index")

    if event.is_booking_open():
        booking, _ = Booking.objects.get_or_create(
            event=event,
            person=request.user,
            defaults={"cancelledBy": request.user, "cancelledOn": timezone.now()},
        )
        if booking.is_cancelled() and event.is_fully_booked():
            messages.error(request, "Sorry the event is fully booked already")
            return redirect("index")
        messages.warning(request, "Please confirm your registration here!")
        return redirect("booking_update", booking_id=booking.id)
    else:
        messages.error(request, 'Bookings are closed for "{0}"!'.format(event.title))
        return redirect("index")


@login_required
def booking_create_on_behalf(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_is_organiser(request.user):
        messages.error(request, "You can not create a booking on behalf for this event")
        return redirect("index")

    form = CreateBookingOnBehalfForm(event.id, request.POST or None)
    if form.is_valid():
        target_user = get_user_model().objects.get(username=form.cleaned_data["username"])
        booking, created = Booking.objects.get_or_create(
            event=event,
            person=target_user,
            defaults={"cancelledBy": request.user, "cancelledOn": timezone.now()},
        )

        if booking.is_cancelled() and event.is_fully_booked():
            messages.error(request, "Sorry the event is fully booked already")
            return redirect("event_manage", event_id=event_id)

        if created:
            messages.success(
                request,
                "Booking created for {0}. Please confirm it.".format(
                    target_user.get_full_name()
                ),
            )
        else:
            messages.warning(
                request,
                "Booking exists for {0}. You may edit it.".format(
                    target_user.get_full_name()
                ),
            )

        return redirect("booking_update", booking_id=booking.id)
    else:
        timezone.activate(event.timezone)
        context = {"form": form, "event": event}
        return render(request, "oneevent/booking_create_on_behalf.html", context)


# TODO: I deeply apologise to my future self about all the mess below that handles
#  booking updates
def _booking_update_finished_redirect(request, booking, updated_field):
    """
    Redirects the user to the appropriate page after the booking update process
    """
    message_text = "{0} updated".format(updated_field)
    if request.user == booking.person:
        messages.success(request, message_text)
        return redirect("events_list_mine")
    else:
        message_text += " for {0}".format(booking.person.get_full_name())
        messages.success(request, message_text)
        return redirect("event_manage", event_id=booking.event.id)


def _booking_update_session(request, booking, form_target_url):
    """
    Handle the form to select the session for a booking
    """
    session_form = BookingSessionForm(
        form_target_url, request.POST or None, instance=booking
    )
    if session_form.is_valid():
        if booking.is_cancelled() and booking.event.is_fully_booked():
            messages.error(request, "Sorry the event is fully booked already")
            return redirect("index")
        # Check for a fully booked session
        session = session_form.cleaned_data["session"]
        if session.is_fully_booked() and (
            booking.is_cancelled or booking.session.id != session.id
        ):
            messages.error(
                request, 'Sorry, session "{0}" is fully booked'.format(session.title)
            )
            return redirect(form_target_url, booking_id=booking.id)

        session_form.save()

        booking.confirmedOn = timezone.now()
        booking.cancelledBy = None
        booking.cancelledOn = None
        booking.save()

        if booking.event.choices.count() > 0:
            messages.warning(
                request, "Session confirmed, please validate your choices."
            )
            return redirect("booking_update", booking_id=booking.id)
        else:
            return _booking_update_finished_redirect(request, booking, "Session")
    else:
        context = {"booking": booking, "session_form": session_form}
        return render(request, "oneevent/booking_update_with_sessions.html", context)


def _booking_update_with_sessions(request, booking):
    """
    View to handle the modification of bookings on events with sessions
    """
    if any(
        (
            booking.is_cancelled(),
            request.GET.get("session_change"),
            booking.session is None,
            not booking.event.choices.exists(),
        )
    ):
        # Step 1: Handling Session selection
        return _booking_update_session(request, booking, "booking_update")
    elif booking.event.choices.count() > 0:
        # Step 2: Handling Choices
        choices_form = BookingChoicesForm(booking, request.POST or None)
        if choices_form.is_valid():
            choices_form.save()

            return _booking_update_finished_redirect(request, booking, "Choices")
        else:
            context = {"booking": booking, "choices_form": choices_form}
            return render(
                request, "oneevent/booking_update_with_sessions.html", context
            )
    else:
        # No Choice to handle
        return _booking_update_finished_redirect(request, booking, "Session")


def _booking_update_no_session(request, booking):
    """
    View to handle the modification of bookings on events without session
    """
    choices_form = BookingChoicesForm(booking, request.POST or None)

    if choices_form.is_valid():
        if booking.is_cancelled() and booking.event.is_fully_booked():
            messages.error(request, "Sorry the event is fully booked already")
            return redirect("index")

        choices_form.save()
        if booking.is_cancelled():
            booking.confirmedOn = timezone.now()
            booking.cancelledBy = None
            booking.cancelledOn = None
        booking.save()

        return _booking_update_finished_redirect(request, booking, "Registration")

    context = {"booking": booking, "choices_form": choices_form}
    return render(request, "oneevent/booking_update.html", context)


@login_required
def booking_update(request, booking_id):
    """
    Main view for updates to bookings: session and choices selection, or confirmation
    """
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.user_can_update(request.user):
        messages.error(request, "You are not authorised to update this booking !")
        return redirect("index")

    timezone.activate(booking.event.timezone)

    if booking.event.sessions.count() > 0:
        return _booking_update_with_sessions(request, booking)
    else:
        return _booking_update_no_session(request, booking)


@login_required
def booking_session_update(request, booking_id):
    """
    View to change the session on a booking
    """
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.user_can_update(request.user):
        messages.error(request, "You are not authorised to update this booking !")
        return redirect("index")

    timezone.activate(booking.event.timezone)

    return _booking_update_session(request, booking, "booking_session_update")


@login_required
def booking_cancel(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.user_can_cancel(request.user):
        messages.error(request, "You are not authorised to cancel this booking !")
        return redirect("index")

    timezone.activate(booking.event.timezone)

    if request.method == "POST":
        booking.confirmedOn = None
        booking.cancelledBy = request.user
        booking.cancelledOn = timezone.now()
        booking.save()
        messages.warning(request, "Registration cancelled")
        if request.user == booking.person:
            return redirect("events_list_mine")
        else:
            return redirect("event_manage", event_id=booking.event.id)
    else:
        return render(request, "oneevent/booking_cancel.html", {"booking": booking})


def get_registration_url(request, event_id):
    """
    Compute the absolute URL to create a booking on a given event
    @param request: An HttpRequest used to discover the FQDN and path
    @param event_id: the ID of the event to register to
    """
    registration_url_rel = reverse(booking_create, kwargs={"event_id": event_id})
    return request.build_absolute_uri(registration_url_rel)


@login_required
def event_manage(request, event_id):
    try:
        event = Event.objects.prefetch_related(
            "bookings__person", "bookings__options__option"
        ).get(id=event_id)
    except Event.DoesNotExist:
        return Http404

    if not event.user_can_update(request.user):
        messages.error(request, "You are not authorised to manage this event !")
        return redirect("index")

    # Activate the timezone from the event
    timezone.activate(event.timezone)

    context = {
        "event": event,
        "registration_url": get_registration_url(request, event_id),
    }
    return render(request, "oneevent/event_manage.html", context)


def _event_edit_form(request, event):
    """
    Handle the edition of an event from the form page
    Not to be used directly as a view
    """
    is_new_event = not bool(event.pk)

    # Activate the timezone from form data before processing the form
    # Use a separate form! otherwise the data is already processed
    tz_form = EventForm(request.POST or None, instance=event)
    if tz_form.is_valid():
        tz = tz_form.cleaned_data["timezone"]
        timezone.activate(tz)

    event_form = EventForm(request.POST or None, instance=event)
    if event_form.is_valid():
        event_form.save()
        if is_new_event:
            messages.success(request, "Event created")
            return redirect("event_update", event_id=event.id)
        elif event.user_is_organiser(request.user):
            messages.success(request, "Event details updated")
            return redirect("event_update", event_id=event.id)
        else:
            messages.warning(
                request,
                "You removed yourself from the organisers of {0}".format(event.title),
            )
            return redirect("index")
    else:
        if event_form.is_bound:
            messages.error(
                request, "Unable to update event details, see below for errors!"
            )
        # Not saving a form. Activate the timezone from the event
        timezone.activate(event.timezone)

    # Build FormSet for Categories
    category_formset = None
    category_helper = None
    if not is_new_event:
        category_formset = CategoryFormSet(instance=event)
        category_helper = CategoryFormSetHelper(event)

    # Build formset for Sessions
    session_formset = None
    session_helper = None
    if not is_new_event:
        session_formset = SessionFormSet(instance=event)
        session_helper = SessionFormSetHelper(event)

    template_context = {
        "event": event,
        "event_form": event_form,
        "category_formset": category_formset,
        "category_helper": category_helper,
        "session_formset": session_formset,
        "session_helper": session_helper,
    }

    if not is_new_event:
        template_context["registration_url"] = get_registration_url(request, event.id)

    return render(request, "oneevent/event_update.html", template_context)


@login_required
def event_update(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_update(request.user):
        messages.error(request, "You are not authorised to edit this event !")
        return redirect("index")

    return _event_edit_form(request, event)


@login_required
def event_update_categories(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_update(request.user):
        messages.error(request, "You are not authorised to edit this event !")
        return redirect("index")

    category_formset = CategoryFormSet(request.POST or None, instance=event)
    category_helper = CategoryFormSetHelper(event)

    if category_formset.is_valid():
        category_formset.save()
        messages.success(request, "Categories updated")
        return redirect("event_update", event_id=event.id)
    elif category_formset.is_bound:
        messages.error(request, "Unable to update categories, see below for errors!")

    # Build formset for sessions
    session_formset = SessionFormSet(instance=event)
    session_helper = SessionFormSetHelper(event)

    template_context = {
        "event": event,
        "event_form": EventForm(instance=event),
        "category_formset": category_formset,
        "category_helper": category_helper,
        "session_formset": session_formset,
        "session_helper": session_helper,
        "registration_url": get_registration_url(request, event_id),
    }

    timezone.activate(event.timezone)

    return render(request, "oneevent/event_update.html", template_context)


@login_required
def event_update_sessions(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_update(request.user):
        messages.error(request, "You are not authorised to edit this event !")
        return redirect("index")

    session_formset = SessionFormSet(request.POST or None, instance=event)
    session_helper = SessionFormSetHelper(event)

    if session_formset.is_valid():
        session_formset.save()
        messages.success(request, "Sessions updated")
        return redirect("event_update", event_id=event.id)
    elif session_formset.is_bound:
        messages.error(request, "Unable to update sessions, see below for errors!")

    # Build formset for categories
    category_formset = CategoryFormSet(instance=event)
    category_helper = CategoryFormSetHelper(event)

    template_context = (
        {
            "event": event,
            "event_form": EventForm(instance=event),
            "category_formset": category_formset,
            "category_helper": category_helper,
            "session_formset": session_formset,
            "session_helper": session_helper,
            "registration_url": get_registration_url(request, event_id),
        },
    )

    timezone.activate(event.timezone)

    return render(request, "oneevent/event_update.html", template_context)


@login_required
def event_create(request):
    new_event = Event(owner=request.user)
    return _event_edit_form(request, new_event)


@login_required
def _choice_edit_form(request, choice):
    """
    Handle the edition of a choice from the form page
    Not to be used directly as a view
    """
    if not choice.event.user_can_update(request.user):
        messages.error(request, "You are not authorised to edit this event !")
        return redirect("index")

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
            bookings = Booking.objects.filter(
                event=choice.event, cancelledOn__isnull=True
            )
            for bkg in bookings:
                print(
                    "Adding option to booking {0} : {1}".format(
                        bkg, options_formset.new_default
                    )
                )
                bkg.options.create(option=options_formset.new_default)

        messages.success(request, "Choice updated")
        return redirect("event_update", event_id=choice.event.id)
    else:
        if choice_form.is_bound or options_formset.is_bound:
            if is_new_choice:
                messages.error(request, "Unable to create choice, see errors below!")
            else:
                messages.error(request, "Unable to update choice, see errors below!")

    timezone.activate(choice.event.timezone)
    context = {
        "choice": choice,
        "choice_form": choice_form,
        "options_formset": options_formset,
        "options_helper": options_helper,
    }
    return render(request, "oneevent/choice_edit.html", context)


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
        messages.error(request, "You are not authorised to edit this event !")
        return redirect("index")

    if request.method == "POST":
        choice.delete()
        messages.success(request, "Choice deleted: {0}".format(choice.title))

        return redirect("event_update", event_id=choice.event.id)
    else:
        timezone.activate(choice.event.timezone)
        return render(request, "oneevent/choice_delete.html", {"choice": choice})


@login_required
def booking_payment_confirm(request, booking_id, cancel=False):
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.user_can_update_payment(request.user):
        messages.error(
            request, "You are not authorised to manage payment for this event !"
        )
        return redirect("index")

    if request.method == "POST":
        if not cancel:
            booking.paidTo = request.user
            booking.datePaid = timezone.now()
        else:
            booking.paidTo = None
            booking.datePaid = None
        booking.save()

        if not cancel:
            messages.success(
                request,
                "Payment confirmed for {0}".format(booking.person.get_full_name()),
            )
        else:
            messages.success(
                request,
                "Refund confirmed for {0}".format(booking.person.get_full_name()),
            )

        return redirect("event_manage", event_id=booking.event.id)
    else:
        timezone.activate(booking.event.timezone)
        context = {"booking": booking, "cancel": cancel}
        return render(request, "oneevent/booking_payment_confirm.html", context)


@login_required
def booking_payment_exempt(request, booking_id, cancel=False):
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.user_can_update_payment(request.user):
        messages.error(
            request, "You are not authorised to manage payment for this event !"
        )
        return redirect("index")

    if cancel and not booking.exempt_of_payment:
        messages.error(request, "This booking is not exempt of payment")
        return redirect("event_manage", event_id=booking.event.id)
    elif not cancel and booking.exempt_of_payment:
        messages.error(request, "This booking is already exempt of payment")
        return redirect("event_manage", event_id=booking.event.id)

    if request.method == "POST":
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
            messages.success(
                request,
                "Exemption confirmed for {0}".format(booking.person.get_full_name()),
            )
        else:
            messages.success(
                request,
                "Exemption cancelled for {0}".format(booking.person.get_full_name()),
            )
        return redirect("event_manage", event_id=booking.event.id)
    else:
        timezone.activate(booking.event.timezone)
        context = {"booking": booking, "cancel": cancel}
        return render(request, "oneevent/booking_payment_exempt.html", context)


@login_required
def event_download_options_summary(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_update(request.user):
        messages.error(
            request, "You are not authorised to download options for this event !"
        )
        return redirect("index")

    filename = "{0}_options_{1}.csv".format(
        slugify(event.title), timezone.now().strftime("%Y%m%d%H%M%S")
    )

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="{0}"'.format(filename)
    writer = unicode_csv.UnicodeWriter(response)

    summary_values = event.get_options_counts()
    writer.writerow(["Choice", "Options"])
    for choice, options in summary_values.items():
        row = [choice.title]
        for option, total in options.items():
            row.append(option.title)
            row.append(str(total))
        writer.writerow(row)

    return response


@login_required
def event_download_participants_list(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not event.user_can_update(request.user):
        messages.error(
            request, "You are not authorised to download participants for this event !"
        )
        return redirect("index")

    filename = "{0}_participants_{1}.csv".format(
        slugify(event.title), timezone.now().strftime("%Y%m%d%H%M%S")
    )

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="{0}"'.format(filename)
    writer = unicode_csv.UnicodeWriter(response)

    bookings = event.bookings.order_by("person__last_name", "person__first_name")

    header_row = [
        "Last name",
        "First name",
        "email",
        "Category",
        "Cancelled",
        "Cancelled By",
        "Confirmed On",
        "Payment status",
        "Paid to",
    ]

    if event.sessions.exists():
        header_row.append("Session")

    if event.choices.exists():
        header_row.append("Choices")

    writer.writerow(header_row)

    for booking in bookings:
        if booking.paidTo is not None:
            local_datePaid = booking.datePaid.astimezone(booking.event.timezone)
            payment = "Paid"
            paid_to = "{0} on {1}".format(
                booking.paidTo.get_full_name(), local_datePaid.strftime(dt_format),
            )
        else:
            paid_to = ""
            if booking.must_pay() > 0:
                payment = "Must pay {0} ({1})".format(
                    booking.must_pay(), event.price_currency
                )
            else:
                payment = "Not needed"

        if booking.is_cancelled():
            cancelled = "Yes"
            local_dateCancelled = booking.cancelledOn.astimezone(booking.event.timezone)
            cancelled_by = "{0} on {1}".format(
                booking.cancelledBy.get_full_name()
                if booking.cancelledBy
                else "Deleted User",
                local_dateCancelled.strftime(dt_format),
            )
            if booking.paidTo is None:
                payment = "N/A"
        else:
            cancelled = "No"
            cancelled_by = ""

        if booking.confirmedOn is not None:
            local_date_confirmed = booking.confirmedOn.astimezone(
                booking.event.timezone
            )
            confirmed_on = local_date_confirmed.strftime(dt_format)
        else:
            confirmed_on = "N/A"

        category = booking.get_category_name()

        row = [
            booking.person.last_name,
            booking.person.first_name,
            booking.person.email,
            category,
            cancelled,
            cancelled_by,
            confirmed_on,
            payment,
            paid_to,
        ]

        if event.sessions.exists():
            if booking.session:
                row.append(booking.session.title)
            else:
                row.append("")

        for option in booking.options.all():
            row.append(option.option.title)
        writer.writerow(row)

    return response


@login_required
def booking_send_invite(request, booking_id):
    if settings.ONEEVENT_CALENDAR_INVITE_FROM is not None:
        booking = get_object_or_404(Booking, id=booking_id)
        if booking.send_calendar_invite():
            messages.success(request, "Invitation sent to your email")
        else:
            messages.error(request, "Failure sending the invitation")
    else:
        messages.warning(request, "This site is not configured to send emails.")

    return redirect("booking_update", booking_id=booking_id)


@login_required
def user_delete(request):
    if request.method == "POST":
        user = request.user
        user.delete()
        messages.success(request, "Account deleted")

        return redirect("index")
    else:
        return render(request, "oneevent/user_delete.html")
