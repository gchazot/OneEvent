from decimal import Decimal

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone as django_timezone
from django.core.mail.message import EmailMultiAlternatives
from django.db.models.aggregates import Count
from .tz_utils import add_to_zones_map
from timezone_field import TimeZoneField

import icalendar
from icalendar.prop import vCalAddress, vText
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import logging


# A default datetime format (too lazy to use the one in settings)
dt_format = "%a, %d %b %Y %H:%M"


def end_of_day(when, timezone):
    """
    Returns the end of the day after of the given datetime object
    @param when: the datetime to use
    @param timezone: the timezone in which to calculate the end of the day
    """
    local_dt = when.astimezone(timezone)
    return timezone.normalize(local_dt.replace(hour=23, minute=59, second=59))


class Event(models.Model):
    """
    An event being organised
    """

    PUB_STATUS_CHOICES = (
        ("PUB", "Public"),
        ("REST", "Restricted"),
        ("PRIV", "Private"),
        ("UNPUB", "Unpublished"),
        ("ARCH", "Archived"),
    )

    title = models.CharField(max_length=64, unique=True)
    start = models.DateTimeField(help_text="Local start date and time")
    end = models.DateTimeField(
        blank=True, null=True, help_text="Local end date and time"
    )
    timezone = TimeZoneField(
        default="Europe/London", help_text="Local timezone of your event"
    )

    description = models.TextField(blank=True)

    pub_status = models.CharField(
        max_length=8,
        choices=PUB_STATUS_CHOICES,
        default="UNPUB",
        verbose_name="Publication status",
        help_text=(
            "Public: Visible and bookable by all; "
            "Restricted: Visible and Bookable by invited groups; "
            "Private: Visible by participant, bookable by all; "
            "Unpublished: Visible by organisers, not bookable; "
            "Archived: Not visible, not bookable"
        ),
    )

    location_name = models.CharField(
        max_length=64, null=True, blank=True, help_text="Venue of your event"
    )
    location_address = models.TextField(null=True, blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="events_owned",
        on_delete=models.CASCADE,
        help_text="Main organiser",
    )
    organisers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="events_organised"
    )

    booking_close = models.DateTimeField(
        blank=True, null=True, help_text="Limit date and time for registering"
    )
    choices_close = models.DateTimeField(
        blank=True, null=True, help_text="Limit date and time for changing choices"
    )

    max_participant = models.PositiveSmallIntegerField(
        default=0,
        help_text="Maximum number of participants to this event (0 = no limit)",
    )

    price_currency = models.CharField(
        max_length=3, null=True, blank=True, verbose_name="Currency for prices"
    )

    def __unicode__(self):
        result = "{0} - {1:%x %H:%M}".format(self.title, self.start)
        if self.end is not None:
            result += " to {0:%x %H:%M}".format(self.end)
        return result

    def __init__(self, *args, **kwargs):
        """
        Constructor to initialise some instance-level variables
        """
        super(Event, self).__init__(*args, **kwargs)
        # Cache dictionnary to save DB queries
        self.users_values_cache = None

    def clean(self):
        """
        Validate this model
        """
        super(Event, self).clean()
        if self.booking_close and self.booking_close > self.start:
            raise ValidationError("Bookings must close before the event starts")
        if self.choices_close and self.choices_close > self.start:
            raise ValidationError("Choices must close before the event starts")
        if (
            self.booking_close
            and self.choices_close
            and self.booking_close > self.choices_close
        ):
            raise ValidationError("Bookings must close before choices")

    def _populate_users_cache(self):
        """
        Fill in the cache of info about users related to this event
        """
        if self.users_values_cache is not None:
            return

        self.users_values_cache = {}

        def add_cache(user, category):
            user_cache = self.users_values_cache.get(user, {})
            user_cache[category] = True
            self.users_values_cache[user] = user_cache

        for orga in self.organisers.all():
            add_cache(orga.id, "__orga_group_")

        users = get_user_model().objects.all().prefetch_related("groups")
        for cat in self.categories.all():
            for user_id in [u.id for u in users if cat.match(u.groups.all())]:
                add_cache(user_id, cat.name)

    def _get_from_users_cache(self, user_id, key, default=None):
        """
        @return: the value for a user_id/key pair from the cache.
        @param default: default value if user/key is not found
        """
        self._populate_users_cache()
        return self.users_values_cache.get(user_id, {}).get(key, default)

    def user_is_organiser(self, user):
        """
        Check if the given user is part of the organisers of the event
        """
        is_orga = self._get_from_users_cache(user.id, "__orga_group_", False)
        is_owner = user == self.owner
        return is_orga or is_owner

    def get_user_category(self, user):
        """
        Finds the Event's category for the given user.
        @returns the Category object or None if none matches
        """
        if not self.categories:
            return None

        for category in self.categories.all():
            if self._get_from_users_cache(user.id, category.name, False):
                return category
        logging.warning("User {0} is in no category for {1}".format(user, self))
        return None

    def user_price(self, user):
        """
        Gets the price for a given user based on his category
        """
        cat = self.get_user_category(user)
        if cat is not None:
            return cat.price
        else:
            return None

    def user_can_update(self, user):
        """
        Check that the given user can update the event
        """
        return user.is_superuser or self.user_is_organiser(user)

    def user_can_list(self, user, list_archived):
        """
        Check that the given user can view the event in the list
        @param user: The user signed in. If not specified, assume anonymous user
        @param list_archived: Boolean to indicated it archived events are visible
        """
        if self.pub_status == "PUB":
            return True
        elif user.is_anonymous:
            # All other statuses are invisible to anonymous
            return False
        elif self.pub_status == "REST":
            return (
                user.is_superuser
                or self.user_is_organiser(user)
                or self.get_user_category(user) is not None
            )
        elif self.pub_status == "PRIV" or self.pub_status == "UNPUB":
            user_has_booking = (
                self.bookings.filter(person=user, cancelledOn=None).count() > 0
            )
            return user.is_superuser or user_has_booking or self.user_is_organiser(user)
        elif self.pub_status == "ARCH":
            if list_archived:
                return user.is_superuser or self.user_is_organiser(user)
            else:
                return False
        else:
            raise Exception("Unknown publication status: {0}".format(self.pub_status))

    def user_can_book(self, user):
        """
        Check if the given user can book the event
        """
        if user.is_anonymous:
            # All statuses are non-bookable by anonymous
            return False

        if self.pub_status == "PUB":
            return True
        elif self.pub_status == "REST":
            return (
                self.user_is_organiser(user) or self.get_user_category(user) is not None
            )
        elif self.pub_status == "PRIV":
            return True
        elif self.pub_status == "UNPUB":
            return False
        elif self.pub_status == "ARCH":
            return False
        else:
            raise Exception("Unknown publication status: {0}".format(self.pub_status))

    def get_real_end(self):
        """
        Get the real datetime of the end of the event
        """
        if self.end is not None:
            return self.end
        else:
            return end_of_day(self.start, self.timezone)

    def is_ended(self):
        """
        Check if the event is ended
        """
        return self.get_real_end() < django_timezone.now()

    def is_booking_open(self):
        """
        Check if the event is still open for bookings
        """
        closed = (
            self.booking_close is not None
            and django_timezone.now() > self.booking_close
        )
        published = self.pub_status in ("PUB", "REST", "PRIV")
        return (
            self.is_choices_open() and not self.is_ended() and not closed and published
        )

    def is_choices_open(self):
        """
        Check if the event is still open for choices
        """
        closed = (
            self.choices_close is not None
            and django_timezone.now() > self.choices_close
        )
        published = self.pub_status in ("PUB", "REST", "PRIV")
        return not self.is_ended() and not closed and published

    def is_fully_booked(self):
        """
        Checks if it is still possible to add a booking regarding the maximum number
        of participants
        """
        return 0 < self.max_participant <= self.get_active_bookings().count()

    def get_active_bookings(self):
        """
        Return the active bookings
        """
        return self.bookings.filter(cancelledOn__isnull=True)

    def get_cancelled_bookings(self):
        """
        Return the cancelled bookings
        """
        return self.bookings.filter(cancelledOn__isnull=False)

    def get_participants_ids(self):
        """
        Return the IDs of users with active bookings
        """
        return self.get_active_bookings().values_list("person__id", flat=True)

    def get_options_counts(self):
        """
        Get a summary of the options chosen for this event
        @return: a map of the form {Choice: {Option: count}}
        """
        result = {}
        event_options = Option.objects.filter(choice__event=self)
        event_options = event_options.filter(bookingoption__booking__cancelledOn=None)
        event_options = event_options.annotate(total=Count("bookingoption"))
        event_options = event_options.select_related("choice")

        for option in event_options:
            choice_counts = result.get(option.choice) or {}
            choice_counts[option] = option.total
            result[option.choice] = choice_counts
        return result

    def get_collected_money_sums(self):
        """
        Calculate the total money collected by each organiser, for each class of
        participant
        @return: a list of the form [(orga, {participant_class: total collected}]. This
        also includes a special participant class "Total" and a special organiser
        "Total" for the sums of values per organiser and per participant class
        """

        class Collected_sums(dict):
            """
            Class to present the results of the calculation in a form easily usable in
            a template
            """

            def __init__(self, categories, organisers):
                self.categories = categories
                self.organisers = organisers
                self._organiser_totals = {}
                self._overall_totals = {}

            def add_payment(self, organiser, category, value):
                """
                Add a collected amount to the results
                @param organiser: the organiser who collected the money
                @param category: the category of the booking for which money was
                collected
                @param value: the amount of money collected
                """

                def add_decimal_in_dict(dic, key, val):
                    """Helper to do a decimal addition to a member of a dict"""
                    new_value = dic.get(key, Decimal(0))
                    new_value += val
                    dic[key] = new_value

                # Add the amount to the oraganiser's values
                org_totals = self._organiser_totals.get(organiser, {})
                add_decimal_in_dict(org_totals, category, value)
                self._organiser_totals[organiser] = org_totals

                add_decimal_in_dict(self._overall_totals, category, value)

            def _make_row(self, organiser_totals):
                """
                Construct the row of sums for a given organiser
                """
                table_row = []
                total_orga = Decimal(0)
                for cat in self.categories:
                    value = organiser_totals.get(cat, Decimal(0))
                    table_row.append(value)
                    total_orga += value
                table_row.append(total_orga)
                return table_row

            def table_rows(self):
                """
                Yields rows with the contents of a table with collected sums
                Each returned row corresponds to an organiser, plus a row for total sums
                Columns of the rows are, in order:
                * the full name of the organiser ("Total" for the last row)
                * sum per category for the organiser, in same order as self.categories
                * total sum for the organiser
                """
                for orga in self.organisers:
                    table_row = [orga.get_full_name()]
                    table_row += self._make_row(self._organiser_totals.get(orga, {}))
                    yield table_row

                total_row = ["Total"]
                total_row += self._make_row(self._overall_totals)
                yield total_row

        bookings = self.bookings.select_related("person", "paidTo").filter(
            paidTo__isnull=False, exempt_of_payment=False
        )

        result = Collected_sums(
            self.categories.values_list("name", flat=True), self.organisers.all()
        )

        for booking in bookings:
            organiser = booking.paidTo
            category = booking.get_category_name()
            price = booking.must_pay()
            result.add_payment(organiser, category, price)

        return result


class Session(models.Model):
    """
    A session from an event being organised
    """

    event = models.ForeignKey(
        "Event", related_name="sessions", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=64, unique=True)
    start = models.DateTimeField(help_text="Local start date and time")
    end = models.DateTimeField(
        blank=True, null=True, help_text="Local end date and time"
    )
    max_participant = models.PositiveSmallIntegerField(
        default=0, help_text="Maximum number of participants (0 = no limit)"
    )

    class Meta:
        unique_together = ("event", "title")
        ordering = ["event", "title"]

    def __unicode__(self):
        return "{0}: Session {1}".format(self.event.title, self.title)

    def get_label(self):
        """
        Generate a label for display in the interface
        """
        label = "{0} ({1}".format(self.title, self.start.strftime(dt_format))
        if self.end:
            label += " - {0}".format(self.end.strftime(dt_format))
        label += ")"

        if self.is_fully_booked():
            label += " - Session FULL"

        return label

    def get_active_bookings(self):
        """
        Return the active bookings
        """
        return self.event.get_active_bookings().filter(session=self)

    def is_fully_booked(self):
        """
        Checks if it is still possible to add a booking regarding the maximum number
        of participants
        """
        return 0 < self.max_participant <= self.get_active_bookings().count()


class Category(models.Model):
    """
    Entry recording one category of people invited to an event.
    The entry allows to describe who is invited to an event through their belonging to
     groups.
    It associates each booking with a category name and a price.
    Entries are ordered: the first category that matches a participant is the one he/she
    belongs to.
    The rule matches if the participant belongs to any of "groups1" AND to any of
     "groups2".
    """

    event = models.ForeignKey(
        "Event", related_name="categories", on_delete=models.CASCADE
    )
    order = models.IntegerField()
    name = models.CharField(max_length=64)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    groups1 = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="groups1_for_category+",
        verbose_name="First groups matched by the rule",
    )
    groups2 = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="groups2_for_category+",
        verbose_name="Second groups matched by the rule",
    )

    class Meta:
        unique_together = (("event", "name"),)
        ordering = ["order"]

    def __unicode__(self):
        return "{0}: {1}) {2}".format(self.event.title, self.order, self.name)

    def match(self, groups):
        """
        Check whether the given groups match this category
        @param groups: a queryset of groups, typically a user.groups.all()
        @returns True iff the category is matched
        """
        if not self.groups1.exists():
            return True
        if not (groups.all() & self.groups1.all()).exists():
            return False
        if not self.groups2.exists():
            return True
        if not (groups.all() & self.groups2.all()).exists():
            return False
        return True


class Choice(models.Model):
    """
    A choice that participants have to make for an event
    """

    event = models.ForeignKey("Event", related_name="choices", on_delete=models.CASCADE)
    title = models.CharField(max_length=64)

    class Meta:
        unique_together = ("event", "title")
        ordering = ["id"]

    def __unicode__(self):
        return "{0}: {1} choice".format(self.event.title, self.title)


class Option(models.Model):
    """
    An option available for a choice of an event
    """

    choice = models.ForeignKey(
        "Choice", related_name="options", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=256)
    default = models.BooleanField(default=False)

    class Meta:
        unique_together = ("choice", "title")
        ordering = ["choice__id", "id"]

    def __unicode__(self):
        if self.default:
            return "{0} : option {1} (default)".format(self.choice, self.title)
        else:
            return "{0} : option {1}".format(self.choice, self.title)


class Booking(models.Model):
    """
    Entry recording a user registration to an event
    """

    event = models.ForeignKey(
        "Event", related_name="bookings", on_delete=models.CASCADE
    )
    person = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="bookings", on_delete=models.CASCADE
    )
    session = models.ForeignKey(
        "Session",
        related_name="bookings",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    confirmedOn = models.DateTimeField(blank=True, null=True)
    cancelledBy = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="cancelled_bookings",
        on_delete=models.SET_NULL,
    )
    cancelledOn = models.DateTimeField(blank=True, null=True)

    paidTo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="received_payments",
        on_delete=models.SET_NULL,
    )
    datePaid = models.DateTimeField(blank=True, null=True)
    exempt_of_payment = models.BooleanField(default=False)

    class Meta:
        unique_together = ("event", "person")
        ordering = ["id"]

    def __unicode__(self):
        return "{0} : {1}".format(self.event.title, self.person)

    def clean(self):
        """
        Validate the contents of this Model
        """
        super(Booking, self).clean()
        if (
            self.paidTo is not None
            and self.must_pay() == 0
            and not self.exempt_of_payment
        ):
            raise ValidationError(
                "{0} does not have to pay for {1}".format(self.person, self.event)
            )
        # Reset the date paid against paid To
        if self.paidTo is not None and self.datePaid is None:
            self.datePaid = django_timezone.now()
        if self.paidTo is None and self.datePaid is not None:
            self.datePaid = None

        # Reset the cancel date against cancelledBy
        if self.cancelledBy is not None and self.cancelledOn is None:
            self.cancelledOn = django_timezone.now()
        if self.cancelledBy is None and self.cancelledOn is not None:
            self.cancelledOn = None

        # Checked that the booking is not cancelled and confirmed
        if self.is_cancelled() and self.confirmedOn is not None:
            raise ValidationError("Booking can not be both cancelled and confirmed")

    def user_can_update(self, user):
        """
        Check that the user can update the booking
        """
        if self.event.user_is_organiser(user):
            # Organisers can always update
            return True
        elif user == self.person:
            # updating a cancelled booking is like re-booking
            if self.cancelledOn is not None:
                return self.event.user_can_book(user)
            else:
                return self.event.is_choices_open()
        return False

    def user_can_cancel(self, user):
        """
        Check that the user can cancel the booking
        """
        is_own_open = user == self.person and self.event.is_booking_open()
        is_organiser = self.event.user_is_organiser(user)
        return is_own_open or is_organiser

    def user_can_update_payment(self, user):
        """
        Check that the user can update payment informations
        """
        return self.event.user_is_organiser(user)

    def is_cancelled(self):
        """
        Indicate if the booking is currently cancelled
        """
        return self.cancelledOn is not None

    def get_category(self):
        """
        Finds the Event's category for this booking.
        @returns the Category object or None if none matches
        """
        return self.event.get_user_category(self.person)

    def get_category_name(self):
        """
        @returns the name of the category or "Unknown"
        """
        cat = self.get_category()
        if cat is None:
            return "Unknown"
        return cat.name

    def must_pay(self):
        """
        Returns the amount that the person has to pay for the booking
        @return the amount to be paid as a Decimal value, 0 if no payment is needed. If
        the amount can not be determined, returns 9999.99
        """
        NOTHING = Decimal(0)
        DEFAULT = (
            Decimal(999999) / 100
        )  # To make sure there is no floating point rounding

        if self.exempt_of_payment or not self.event.categories.exists():
            return NOTHING

        price = self.event.user_price(self.person)
        if price is None:
            return DEFAULT
        return price

    def get_payment_status_class(self):
        """
        Return the status of payment (as a Bootstrap context CSS class)
        """
        if self.paidTo is not None:
            if self.is_cancelled():
                return "danger"
            else:
                return "success"
        else:
            if self.is_cancelled():
                return "default"
            elif self.must_pay() == Decimal(0):
                return "success"
            else:
                return "warning"
        return ""

    def get_invite_texts(self):
        """
        Get the text contents for an invite to the event
        @return: a tuple (title, description_plain, description_html)
        """
        event = self.event
        event_tz = event.timezone

        title_text = "Invitation to {0}".format(event.title)

        plain_lines = [
            "You have registered to an event",
            "Add it to your calendar!",
            "",
            "Event: {0}",
            "Start: {1}",
            "End: {2}",
            "Location: {3}",
            "Address: {4}",
            "Description: {5}",
        ]
        plain_text = "\n".join(plain_lines).format(
            event.title,
            event.start.astimezone(event_tz),
            event.get_real_end().astimezone(event_tz),
            event.location_name,
            event.location_address,
            event.description,
        )

        html_lines = [
            "<h2>You have registered to an event</h2>",
            "<h4>Add it to your calendar!</h4>",
            "<ul>",
            "<li><label>Event: </label>{0}</li>",
            "<li><label>Start: </label>{1}</li>",
            "<li><label>End: </label>{2}</li>",
            "<li><label>Location: </label>{3}</li>",
            "<li><label>Address: </label>{4}</li>",
            "</ul>",
            "<hr />",
            "<p>{5}</p>",
        ]
        html_text = "\n".join(html_lines).format(
            event.title,
            event.start.astimezone(event_tz),
            event.get_real_end().astimezone(event_tz),
            event.location_name,
            event.location_address,
            event.description,
        )

        if self.options.count() > 0:
            plain_lines = ["", "Your Choices:"]
            html_lines = ["<hr />", "<h4>Your Choices</h4>", "<ul>"]
            for part_opt in self.options.all():
                plain_lines.append(
                    "* {0} : {1}".format(
                        part_opt.option.choice.title, part_opt.option.title,
                    )
                )
                html_lines.append(
                    "<li><label>{0} : </label>{1}</li>".format(
                        part_opt.option.choice.title, part_opt.option.title,
                    )
                )
            plain_text = plain_text + "\n".join(plain_lines)
            html_lines.append("</ul>")
            html_text = html_text + "\n".join(html_lines)

        return (title_text, plain_text, html_text)

    def get_calendar_entry(self):
        """
        Build the iCalendar string for the event
        iCal validator, useful for debugging: http://icalvalid.cloudapp.net/
        """
        event = self.event
        event_tz = event.timezone
        creation_time = django_timezone.now()

        # Generate some description strings
        title, desc_plain, _desc_html = self.get_invite_texts()

        # Generate the Calendar event
        cal = icalendar.Calendar()
        cal.add("prodid", "-//OneEvent event entry//onevent//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "REQUEST")

        # Generate timezone infos relevant to the event
        tzmap = {}
        tzmap = add_to_zones_map(tzmap, event_tz.zone, event.start)
        tzmap = add_to_zones_map(tzmap, event_tz.zone, event.get_real_end())
        tzmap = add_to_zones_map(
            tzmap, django_timezone.get_default_timezone_name(), creation_time
        )

        for tzid, transitions in tzmap.items():
            cal_tz = icalendar.Timezone()
            cal_tz.add("tzid", tzid)
            cal_tz.add("x-lic-location", tzid)

            for transition, tzinfo in transitions.items():

                if tzinfo["dst"]:
                    cal_tz_sub = icalendar.TimezoneDaylight()
                else:
                    cal_tz_sub = icalendar.TimezoneStandard()

                cal_tz_sub.add("tzname", tzinfo["name"])
                cal_tz_sub.add("dtstart", transition)
                cal_tz_sub.add("tzoffsetfrom", tzinfo["tzoffsetfrom"])
                cal_tz_sub.add("tzoffsetto", tzinfo["tzoffsetto"])
                cal_tz.add_component(cal_tz_sub)
            cal.add_component(cal_tz)

        cal_evt = icalendar.Event()

        cal_evt.add("uid", "event{0}-booking{1}@oneevent".format(event.id, self.id))
        cal_evt.add("dtstamp", creation_time)
        cal_evt.add("dtstart", event.start.astimezone(event_tz))
        cal_evt.add("dtend", event.get_real_end().astimezone(event_tz))
        cal_evt.add("created", creation_time)
        cal_evt.add("sequence", "1")

        cal_evt.add("summary", title)
        cal_evt.add("description", desc_plain)
        cal_evt.add("location", vText(event.location_name))

        cal_evt.add("category", "Event")
        cal_evt.add("status", "CONFIRMED")
        cal_evt.add("transp", "OPAQUE")
        cal_evt.add("priority", "5")
        cal_evt.add("class", "PUBLIC")

        organiser = vCalAddress("mailto:{0}".format(event.owner.email))
        organiser.params["cn"] = vText(event.owner.get_full_name())
        organiser.params["role"] = vText("CHAIR")
        cal_evt.add("organizer", organiser, encode=0)

        attendee = vCalAddress("mailto:{0}".format(self.person.email))
        attendee.params["cutype"] = vText("INDIVIDUAL")
        attendee.params["role"] = vText("REQ-PARTICIPANT")
        attendee.params["partstat"] = vText("NEEDS-ACTION")
        attendee.params["rsvp"] = vText("FALSE")
        attendee.params["cn"] = vText(self.person.get_full_name())
        cal_evt.add("attendee", attendee, encode=0)

        cal.add_component(cal_evt)

        return cal.to_ical()

    def send_calendar_invite(self):
        """
        Send a calendar entry to the participant
        """
        title, _desc_plain, desc_html = self.get_invite_texts()
        cal_text = self.get_calendar_entry()

        # "Parts" used in various formats
        #         part_plain = MIMEText(desc_plain, "plain", 'utf-8')
        #         del(part_plain['MIME-Version'])

        part_html = MIMEText(desc_html, "html", "utf-8")
        del part_html["MIME-Version"]

        #         part_cal = MIMEText(cal_text, 'calendar; method=REQUEST', 'utf-8')
        #         del(part_cal['MIME-Version'])

        #         ical_atch = MIMEApplication(
        #             cal_text,
        #             'ics; charset="UTF-8"; name="%s"' % ("invite.ics"),
        #         )
        #         del(ical_atch['MIME-Version'])
        #         ical_atch.add_header(
        #             'Content-Disposition',
        #             'attachment',
        #             filename='invite.ics',
        #         )

        # The "Lotus Notes" fomat
        #         msgAlternative = MIMEMultipart('alternative')
        #         del(msgAlternative['MIME-Version'])
        #         msgAlternative.attach(part_html)
        #         msgAlternative.attach(part_cal)
        #
        #         msgRelated = MIMEMultipart('related')
        #         del(msgRelated['MIME-Version'])
        #         msgRelated.attach(msgAlternative)
        #         msgAlternative.attach(part_html)
        #
        #         msgMixed = MIMEMultipart('mixed')
        #         del(msgMixed['MIME-Version'])
        #         msgMixed.attach(msgRelated)
        #         msgMixed.attach(ical_atch)
        #
        #         msg = EmailMultiAlternatives(subject='test invite',
        #                                      body=None,
        #                                      to=['g.chazot@gmail.com'])
        #         msg.attach(msgMixed)

        #         # The "Google Calendar" format
        #         msgAlternative = MIMEMultipart('alternative')
        #         del(msgAlternative['MIME-Version'])
        #         msgAlternative.add_header(
        #             'Content-class',
        #             'urn:content-classes:calendarmessage',
        #         )
        #         msgAlternative.attach(part_plain)
        #         msgAlternative.attach(part_html)
        #         msgAlternative.attach(part_cal)
        #
        #         # Create the message object
        #         msg = EmailMultiAlternatives(subject=title,
        #                                      body=None,
        #                                      to=[self.person.email])
        #         msg.attach(msgAlternative)
        #         msg.attach(ical_atch)

        # The "Outlook" format

        from_full = "{0} on behalf of {1} <{2}>".format(
            settings.ONEEVENT_SITE_BRAND,
            self.event.owner.get_full_name(),
            settings.ONEEVENT_CALENDAR_INVITE_FROM,
        )

        reply_to_full = "{0} <{1}>".format(
            self.event.owner.get_full_name(),
            self.event.owner.email,
        )

        # Create the message object
        msg = EmailMultiAlternatives(
            subject=title,
            body=None,
            to=[self.person.email],
            from_email=from_full,
            reply_to=[reply_to_full],
        )
        msg.extra_headers["Content-class"] = "urn:content-classes:calendarmessage"
        msg.attach(part_html)

        filename = "invite.ics"
        part = MIMEBase("text", "calendar", method="REQUEST", name=filename)
        part.set_payload(cal_text)
        encoders.encode_base64(part)
        part.add_header("Content-Description", filename)
        part.add_header("Content-class", "urn:content-classes:calendarmessage")
        part.add_header("Filename", filename)
        part.add_header("Path", filename)
        msg.attach(part)

        print(cal_text)

        # Send the message
        return msg.send(fail_silently=False) == 1


class BookingOption(models.Model):
    """
    A choice made by a booking for an event
    """

    booking = models.ForeignKey(
        "Booking", related_name="options", on_delete=models.CASCADE
    )
    option = models.ForeignKey(
        "Option", null=True, blank=True, on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("booking", "option")
        ordering = ["option__choice__id", "option__id", "id"]

    def __unicode__(self):
        return "{0} -> {1}".format(self.booking, self.option)

    def clean(self):
        """
        Validate the contents of this Model
        """
        super(BookingOption, self).clean()
        dupes = BookingOption.objects.filter(
            booking=self.booking, option__choice=self.option.choice
        )
        if dupes.count() > 0:
            if dupes.count() != 1 or dupes[0].option != self.option:
                error = "Participant {0} already has a choice for {1}".format(
                    self.booking, self.option.choice
                )
                raise ValidationError(error)
