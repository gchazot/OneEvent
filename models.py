from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging
from django.utils import timezone
from timezones import CITY_CHOICES, get_tzinfo
from django.utils.safestring import mark_safe
from django.template import loader
from django.core.mail import mail_admins
from django.core.mail.message import EmailMultiAlternatives
from django.db.models.query_utils import Q

import icalendar
from icalendar.prop import vCalAddress, vText
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def end_of_day(when, timezone):
    '''
    Returns the end of the day after of the given datetime object
    @param when: the datetime to use
    @param timezone: the timezone in which to calculate the end of the day
    '''
    local_dt = when.astimezone(timezone)
    return timezone.normalize(local_dt.replace(hour=23, minute=59, second=59))


class Event(models.Model):
    '''
    An event being organised
    '''
    PUB_STATUS_CHOICES = (
        ('PUB', 'Public'),
        ('REST', 'Restricted'),
        ('PRIV', 'Private'),
        ('UNPUB', 'Unpublished'),
        ('ARCH', 'Archived')
    )

    title = models.CharField(max_length=64, unique=True)
    start = models.DateTimeField(help_text='Local start date and time')
    end = models.DateTimeField(blank=True, null=True,
                               help_text='Local end date and time (optional)')
    city = models.CharField(max_length=32, choices=CITY_CHOICES,
                            help_text='Timezone of your event')

    pub_status = models.CharField(max_length=8, choices=PUB_STATUS_CHOICES, default='UNPUB',
                                  verbose_name='Publication status')

    location_name = models.CharField(max_length=64, null=True, blank=True,
                                     help_text='Venue of your event')
    location_address = models.TextField(null=True, blank=True)

    owner = models.ForeignKey('auth.User', related_name='events_owned')
    organisers = models.ManyToManyField('auth.User', blank=True, related_name='events_organised')

    booking_close = models.DateTimeField(blank=True, null=True,
                                         help_text='Limit date and time for registering')
    choices_close = models.DateTimeField(blank=True, null=True,
                                         help_text='Limit date and time for changing choices')

    price_for_employees = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    price_for_contractors = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    price_currency = models.CharField(max_length=3, null=True, blank=True,
                                      verbose_name='Currency for prices')

    employees_groups = models.ManyToManyField('auth.Group', blank=True,
                                              related_name='employees_for_event+',
                                              verbose_name='Groups considered as Employees')
    contractors_groups = models.ManyToManyField('auth.Group', blank=True,
                                                related_name='contractors_for_event+',
                                                verbose_name='Groups considered as Contractors')

    def __unicode__(self):
        result = u'{0} - {1:%x %H:%M}'.format(self.title, self.start)
        if self.end is not None:
            result += u' to {0:%x %H:%M}'.format(self.end)
        return result

    def clean(self):
        '''
        Validate this model
        '''
        super(Event, self).clean()
        if self.booking_close and self.booking_close > self.start:
            raise ValidationError("Bookings must close before the event starts")
        if self.choices_close and self.choices_close > self.start:
            raise ValidationError("Choices must close before the event starts")
        if self.booking_close and self.choices_close and self.booking_close > self.choices_close:
            raise ValidationError("Bookings must close before choices")

    def user_is_organiser(self, user):
        '''
        Check if the given user is part of the organisers of the event
        '''
        return user in self.organisers.all()

    def user_is_employee(self, user):
        '''
        Check if the user is part of the employees groups of the event
        '''
        common_groups = user.groups.all() & self.employees_groups.all()
        logging.debug("is_employee:{0}:{1}".format(user, common_groups))
        return common_groups.count() > 0

    def user_is_contractor(self, user):
        '''
        Check if the user is part of the contractors groups of the event
        '''
        common_groups = user.groups.all() & self.contractors_groups.all()
        logging.debug("is_contractor:{0}:{1}".format(user, common_groups))
        return common_groups.count() > 0

    def user_can_update(self, user):
        '''
        Check that the given user can update the event
        '''
        return user.is_superuser or user in self.organisers.all()

    def user_can_list(self, user):
        '''
        Check that the given user can view the event in the list
        '''
        if self.pub_status == 'PUB':
            return True
        elif self.pub_status == 'REST':
            return (user.is_superuser
                    or self.user_is_organiser(user)
                    or self.user_is_employee(user)
                    or self.user_is_contractor(user))
        elif self.pub_status == 'PRIV' or self.pub_status == 'UNPUB':
            user_has_booking = self.bookings.filter(person=user, cancelledBy=None).count() > 0
            return (user.is_superuser
                    or user_has_booking
                    or self.user_is_organiser(user))
        elif self.pub_status == 'ARCH':
            return False
        else:
            raise Exception("Unknown publication status: {0}".format(self.pub_status))

    def user_can_book(self, user):
        '''
        Check if the given user can book the event
        '''
        if self.pub_status == 'PUB':
            return True
        elif self.pub_status == 'REST':
            return (self.user_is_organiser(user)
                    or self.user_is_employee(user)
                    or self.user_is_contractor(user))
        elif self.pub_status == 'PRIV':
            return True
        elif self.pub_status == 'UNPUB':
            return False
        elif self.pub_status == 'ARCH':
            return False
        else:
            raise Exception("Unknown publication status: {0}".format(self.pub_status))

    def get_tzinfo(self):
        '''
        Get the tzinfo object applicable to this event
        '''
        return get_tzinfo(self.city)

    def get_real_end(self):
        '''
        Get the real datetime of the end of the event
        '''
        if self.end is not None:
            return self.end
        else:
            return end_of_day(self.start, self.get_tzinfo())

    def is_ended(self):
        '''
        Check if the event is ended
        '''
        return self.get_real_end() < timezone.now()

    def is_booking_open(self):
        '''
        Check if the event is still open for bookings
        '''
        closed = (self.booking_close is not None
                  and timezone.now() > self.booking_close)
        published = self.pub_status in ('PUB', 'REST', 'PRIV')
        return self.is_choices_open() and not self.is_ended() and not closed and published

    def is_choices_open(self):
        '''
        Check if the event is still open for choices
        '''
        closed = (self.choices_close is not None
                  and timezone.now() > self.choices_close)
        published = self.pub_status in ('PUB', 'REST', 'PRIV')
        return not self.is_ended() and not closed and published

    def get_active_bookings(self):
        '''
        Return the active bookings
        '''
        return self.bookings.filter(cancelledBy=None)

    def get_participants_ids(self):
        '''
        Return the ids of users with active bookings
        '''
        return self.get_active_bookings().values_list('person__id', flat=True)

    def get_options_counts(self):
        '''
        Get a summary of the options chosen for this event
        @return: a map of the form {EventChoice: {EventChoiceOption: count}}
        '''
        result = {}
        event_options = EventChoiceOption.objects.filter(choice__event=self)
        part_options = ParticipantOption.objects.filter(booking__event=self,
                                                        booking__cancelledBy=None)
        for option in event_options:
            choice_counts = result.get(option.choice) or {}
            choice_counts[option] = part_options.filter(option=option).count()
            result[option.choice] = choice_counts
        return result

    def get_collected_money_sums(self):
        '''
        Calculate the total money collected by each organiser, for each class of participant
        @return: a list of the form [(orga, {participant_class: total collected}]. This also
        includes a special participant class "Total" and a special organiser "Total" for the
        sums of values per organiser and per participant class
        '''
        organisers_sums = {}
        bookings = self.bookings.filter(paidTo__isnull=False)
        for booking in bookings:
            if booking.is_employee():
                entry_name = "Employees"
                entry_price = self.price_for_employees
            elif booking.is_contractor():
                entry_name = "Contractors"
                entry_price = self.price_for_contractors
            else:
                entry_name = "Other"
                entry_price = 1

            orga_entries = organisers_sums.get(booking.paidTo) or {}
            total = orga_entries.get(entry_name) or Decimal(0)
            orga_entries[entry_name] = total + entry_price
            organisers_sums[booking.paidTo] = orga_entries

        result = []
        overall_totals = {}
        for orga, orga_entries in organisers_sums.iteritems():
            orga_entries["Total"] = sum(organisers_sums[orga].values())
            result.append((orga, orga_entries,))

            for entry_name, entry_value in orga_entries.iteritems():
                entry_total = overall_totals.get(entry_name) or Decimal(0)
                overall_totals[entry_name] = entry_total + entry_value
        result.append(("Total", overall_totals,))

        return result


class EventChoice(models.Model):
    '''
    A choice that participants have to make for an event
    '''
    event = models.ForeignKey('Event', related_name='choices')
    title = models.CharField(max_length=64)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('event', 'title')

    def __unicode__(self):
        return u'{0}: {1} choice'.format(self.event.title, self.title)


class EventChoiceOption(models.Model):
    '''
    An option available for a choice of an event
    '''
    choice = models.ForeignKey('EventChoice', related_name='options')
    title = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    default = models.BooleanField(default=False)

    class Meta:
        unique_together = ('choice', 'title')

    def __unicode__(self):
        if self.default:
            return u'{0} : option {1} (default)'.format(self.choice, self.title)
        else:
            return u'{0} : option {1}'.format(self.choice, self.title)


class ParticipantBooking(models.Model):
    '''
    Entry recording a user registration to an event
    '''
    event = models.ForeignKey('Event', related_name='bookings')
    person = models.ForeignKey('auth.User', related_name='bookings')

    cancelledBy = models.ForeignKey('auth.User', blank=True, null=True, related_name='cancelled_bookings')
    cancelledOn = models.DateTimeField(blank=True, null=True)

    paidTo = models.ForeignKey('auth.User', blank=True, null=True, related_name='received_payments')
    datePaid = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('event', 'person')

    def __unicode__(self):
        return u'{0} : {1}'.format(self.event.title, self.person)

    def clean(self):
        '''
        Validate the contents of this Model
        '''
        super(ParticipantBooking, self).clean()
        if self.paidTo is not None and self.must_pay() == 0:
            raise ValidationError("{0} does not have to pay for {1}".format(self.person,
                                                                            self.event))
        # Reset the date paid against paid To
        if self.paidTo is not None and self.datePaid is None:
            self.datePaid = timezone.now()
        if self.paidTo is None and self.datePaid is not None:
            self.datePaid = None

        # Reset the cancel date against cancelledBy
        if self.cancelledBy is not None and self.cancelledOn is None:
            self.cancelledOn = timezone.now()
        if self.cancelledBy is None and self.cancelledOn is not None:
            self.cancelledOn = None

    def user_can_update(self, user):
        '''
        Check that the user can update the booking
        '''
        return (self.event.is_booking_open()
                and self.event.is_choices_open()
                and user == self.person)

    def user_can_update_payment(self, user):
        '''
        Check that the user can update payment informations
        '''
        return user in self.event.organisers.all()

    def is_employee(self):
        '''
        Check if the user is part of the employees groups of the event
        '''
        return self.event.user_is_employee(self.person)

    def is_contractor(self):
        '''
        Check if the user is part of the contractors groups of the event
        '''
        return self.event.user_is_contractor(self.person)

    def must_pay(self):
        '''
        Returns the amount that the person has to pay for the booking
        '''
        if self.is_employee():
            if self.event.price_for_employees is not None:
                return self.event.price_for_employees
            else:
                return Decimal(0)
        elif self.is_contractor():
            if self.event.price_for_contractors is not None:
                return self.event.price_for_contractors
            else:
                return Decimal(0)
        else:
            logging.error("User {0} is neither employee not contractor for {1}".format(self.person,
                                                                                       self.event))
            return Decimal(999.99)

    def get_payment_status_class(self):
        '''
        Return the status of payment (as a CSS class)
        '''
        if self.cancelledBy is not None:
            if self.paidTo is None:
                return ''
            else:
                return 'danger'
        else:
            if self.must_pay() == Decimal(0) or self.paidTo is not None:
                return 'success'
            elif self.paidTo is None:
                return 'warning'
        return ''

    def get_invite_texts(self):
        '''
        Get the text contents for an invite to the event
        @return: a tuple (title, description_plain, description_html)
        '''
        event = self.event
        event_tz = event.get_tzinfo()

        title_text = 'Invitation to {0}'.format(event.title)

        plain_text = 'You have registered to an event\n\
                      Add it to your calendar!\n\
                      Event: {0}\n\
                      Start: {1}\n\
                      End: {2}\n\
                      Location: {3}\n\
                      Address: {4}\n'.format(event.title,
                                             event.start.astimezone(event_tz),
                                             event.get_real_end().astimezone(event_tz),
                                             event.location_name,
                                             event.location_address)

        html_text = '<h2>You have registered to an event</h2>\n\
                     <h4>Add it to your calendar!</h4>\n\
                     <ul>\n\
                     <li><label>Event: </label>{0}</li>\n\
                     <li><label>Start: </label>{1}</li>\n\
                     <li><label>End: </label>{2}</li>\n\
                     <li><label>Location: </label>{3}</li>\n\
                     <li><label>Address: </label>{4}</li>\n\
                     </ul>\n'.format(event.title,
                                     event.start.astimezone(event_tz),
                                     event.get_real_end().astimezone(event_tz),
                                     event.location_name,
                                     event.location_address)

        return (title_text, plain_text, html_text)

    def get_calendar_entry(self):
        '''
        Build the iCalendar string for the event
        '''
        event = self.event
        event_tz = event.get_tzinfo()

        # Generate some description strings
        title, desc_plain, _desc_html = self.get_invite_texts()

        # Generate the Calendar event
        cal = icalendar.Calendar()
        cal.add('prodid', '-//OneEvent event entry//onevent//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal_evt = icalendar.Event()
        cal_evt.add('summary', title)
        cal_evt.add('uid', 'event{0}-booking{1}@oneevent'.format(event.id, self.id))
        cal_evt.add('dtstamp', timezone.now())
        cal_evt.add('dtstart', event.start.astimezone(event_tz))
        cal_evt.add('dtend', event.get_real_end().astimezone(event_tz))
        cal_evt.add('description', desc_plain)
        cal_evt.add('status', 'CONFIRMED')
        cal_evt.add('transp', 'OPAQUE')
        cal_evt.add('priority', '5')
        cal_evt.add('class', 'PUBLIC')
        cal_evt['location'] = vText('{0} - {1}'.format(event.city, event.location_name))

        organiser = vCalAddress('mailto:{0}'.format(event.owner.email))
        organiser.params['cn'] = vText(event.owner.get_full_name())
        organiser.params['role'] = vText('CHAIR')
        cal_evt['organizer'] = organiser

        attendee = vCalAddress('mailto:{0}'.format(self.person.email))
        attendee.params['cutype'] = vText('INDIVIDUAL')
        attendee.params['x-num-guests'] = vText('0')
        attendee.params['role'] = vText('REQ-PARTICIPANT')
        attendee.params['partstat'] = vText('NEEDS-ACTION')
        attendee.params['rsvp'] = vText('FALSE')
        attendee.params['cn'] = vText(self.person.get_full_name())
        cal_evt.add('attendee', attendee, encode=0)

        cal.add_component(cal_evt)

        return cal.to_ical()

    def send_calendar_invite(self):
        '''
        Send a calendar entry to the participant
        '''
        title, desc_plain, desc_html = self.get_invite_texts()
        cal_text = self.get_calendar_entry()

        part_plain = MIMEText(desc_plain, "plain", 'utf-8')
        del(part_plain['MIME-Version'])

        part_html = MIMEText(desc_html, 'html', 'utf-8')
        del(part_html['MIME-Version'])

        part_cal = MIMEText(cal_text, 'calendar; method=REQUEST', 'utf-8')
        del(part_cal['MIME-Version'])

        ical_atch = MIMEApplication(cal_text,
                                    'ics; charset="UTF-8"; name="%s"' % ("invite.ics"))
        del(ical_atch['MIME-Version'])
        ical_atch.add_header('Content-Disposition', 'attachment', filename='invite.ics')

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

        # The "Google Calendar" format
        msgAlternative = MIMEMultipart('alternative')
        del(msgAlternative['MIME-Version'])
        msgAlternative.add_header('Content-class', 'urn:content-classes:calendarmessage')
        msgAlternative.attach(part_plain)
        msgAlternative.attach(part_html)
        msgAlternative.attach(part_cal)

        # Create the message object
        msg = EmailMultiAlternatives(subject=title,
                                     body=None,
                                     to=[self.person.email])
        msg.attach(msgAlternative)
        msg.attach(ical_atch)

        # Send the message
        return msg.send(fail_silently=False) == 1


class ParticipantOption(models.Model):
    '''
    A choice made by a booking for an event
    '''
    booking = models.ForeignKey('ParticipantBooking', related_name='options')
    option = models.ForeignKey('EventChoiceOption', null=True, blank=True)

    class Meta:
        unique_together = ('booking', 'option')

    def __unicode__(self):
        return u'{0} -> {1}'.format(self.booking, self.option)

    def clean(self):
        '''
        Validate the contents of this Model
        '''
        super(ParticipantOption, self).clean()
        dupes = ParticipantOption.objects.filter(booking=self.booking,
                                                 option__choice=self.option.choice)
        if dupes.count() > 0:
            error = 'Participant {0} already has a choice for {1}'.format(self.booking,
                                                                          self.option.choice)
            raise ValidationError(error)


class Message(models.Model):
    MSG_CAT_CHOICES = (
        ('QUERY', 'Question'),
        ('COMMENT', 'Comment'),
        ('BUG', 'Bug report'),
        ('FEAT', 'Feature request'),
        ('ADMIN', 'Administration Request'),
    )
    sender = models.ForeignKey('auth.User')
    category = models.CharField(max_length=8, choices=MSG_CAT_CHOICES,
                                verbose_name='Reason')
    title = models.CharField(max_length=128)
    text = models.TextField(max_length=2048)
    thread_head = models.ForeignKey('Message', related_name='thread',
                                    null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    safe_content = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return u'Message: From {0}, On {1}, Title "{2}"'.format(self.sender,
                                                                self.created,
                                                                self.title)

    def safe_title(self):
        '''
        Returns the title marked safe or not depending on safe_content
        '''
        if self.safe_content:
            return mark_safe(self.title)
        else:
            return self.title

    def safe_text(self):
        '''
        Returns the title marked safe or not depending on safe_content
        '''
        if self.safe_content:
            return mark_safe(self.text)
        else:
            return self.text

    def full_thread(self):
        '''
        Get the full thread of messages related to this one
        '''
        query = Q(id=self.id)
        if self.thread_head:
            query = query | Q(thread_head=self.thread_head)
        else:
            query = query | Q(thread_head=self)
        return Message.objects.filter(query)

    def send_message_notification(self):
        '''
        Send a notification email to the relevant person(s)
        '''
        if self.thread_head:
            prefix = "reply"
        else:
            prefix = "message"
        subject = '[OneEvent] [{1}] New {2}: {0}'.format(self.title,
                                                         self.get_category_display(),
                                                         prefix)
        message_html = loader.render_to_string('message_notification.html',
                                               {'message': self})
        message_text = self.safe_text()

        # Send to the user only the replies that do not come from himself
        if self.thread_head and self.sender != self.thread_head.sender:
            msg = EmailMultiAlternatives(subject, message_text,
                                         to=[self.thread_head.sender.email])
            msg.attach_alternative(message_html, "text/html")
            msg.send(fail_silently=True)
            print "Sent message to {0}".format(self.thread_head.sender.email)
        else:
            mail_admins(subject, message_text, html_message=message_html, fail_silently=True)
