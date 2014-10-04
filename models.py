from django.db import models
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from datetime import date, datetime
from django.utils.timezone import utc
from decimal import Decimal
import logging


def end_of_day(when):
    '''
    Returns the end of the day after of the given datetime object
    '''
    return when.replace(hour=23, minute=59, second=59)


class Event(models.Model):
    '''
    An event being organised
    '''
    title = models.CharField(max_length=64, unique=True)
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)

    organisers = models.ManyToManyField(User, blank=True)

    booking_close = models.DateTimeField(blank=True, null=True, help_text='(UTC !)')
    choices_close = models.DateTimeField(blank=True, null=True, help_text='(UTC !)')

    price_for_employees = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    price_for_contractors = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    price_currency = models.CharField(max_length=3, null=True, blank=True)

    employees_groups = models.ManyToManyField(Group, related_name='employees_for_event+')
    contractors_groups = models.ManyToManyField(Group, related_name='contractors_for_event+')

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
#         if self.price_for_employees > 0 and self.employees_groups.count() == 0:
#             raise ValidationError("You must provide at least one employees group to set an empolyees price")
#         if self.price_for_contractors > 0 and self.contractors_groups.count() == 0:
#             raise ValidationError("You must provide at least one contractors group to set an contractors price")

    def user_can_update(self, user):
        '''
        Check that the given user can update the event
        '''
        return user in self.organisers.all()

    def get_real_end(self):
        '''
        Get the real datetime of the end of the event
        '''
        if self.end is not None:
            return self.end
        else:
            return end_of_day(self.start)

    def is_ended(self):
        '''
        Check if the event is ended
        '''
        return self.get_real_end() < datetime.now(utc)

    def is_booking_open(self):
        '''
        Check if the event is still open for bookings
        '''
        closed = self.booking_close is not None and datetime.now(utc) > self.booking_close
        return self.is_choices_open() and not self.is_ended() and not closed

    def is_choices_open(self):
        '''
        Check if the event is still open for choices
        '''
        closed = self.choices_close is not None and datetime.now(utc) > self.choices_close
        return not self.is_ended() and not closed

    def get_active_bookings(self):
        '''
        Return the active bookings
        '''
        return self.bookings.filter(cancelled=False)

    def get_participants_ids(self):
        '''
        Return the ids of users with active bookings
        '''
        return self.get_active_bookings().values_list('person__id', flat=True)

    def get_options_counts(self):
        '''
        Get a summary of the options chosen for this event
        output format is {EventChoice: {EventChoiceOption: count}}
        '''
        result = {}
        event_options = EventChoiceOption.objects.filter(choice__event=self)
        part_options = ParticipantOption.objects.filter(booking__event=self,
                                                        booking__cancelled=False)
        for option in event_options:
            choice_counts = result.get(option.choice) or {}
            choice_counts[option] = part_options.filter(option=option).count()
            result[option.choice] = choice_counts
        return result


class EventChoice(models.Model):
    '''
    A choice that participants have to make for an event
    '''
    event = models.ForeignKey(Event, related_name='choices')
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
    choice = models.ForeignKey(EventChoice, related_name='options')
    title = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    default = models.BooleanField(default=False)

    class Meta:
        unique_together = ('choice', 'title')

    def __unicode__(self):
        if self.default:
            return u'{0} : option {1} (default)'.format(self.choice, self.title)
        else:
            return u'{0} : option {1}'.format(self.choice, self.title)

    def clean(self):
        '''
        Validate the contents of this Model
        '''
        super(EventChoiceOption, self).clean()
        other = EventChoiceOption.objects.filter(choice=self.choice).exclude(id=self.id)
        if self.default:
            # reset other defaults
            other.update(default=False)
        elif other.filter(default=True).count() == 0:
            # Force at least one default
            self.default = True


class ParticipantBooking(models.Model):
    '''
    Entry recording a user registration to an event
    '''
    event = models.ForeignKey(Event, related_name='bookings')
    person = models.ForeignKey(User)
    cancelled = models.BooleanField(default=True)
    paidTo = models.ForeignKey(User, blank=True, null=True, related_name='received_payments')
    datePaid = models.DateField(blank=True, null=True)

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
            self.datePaid = date.today()
        if self.paidTo is None and self.datePaid is not None:
            self.datePaid = None

    def user_can_update(self, user):
        '''
        Check that the user can update the booking
        '''
        return (self.event.is_booking_open() and self.event.is_choices_open()
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
        common_groups = self.person.groups.all() & self.event.employees_groups.all()
        logging.debug("is_employee:{0}:{1}".format(self.person, common_groups))
        return common_groups.count() > 0

    def is_contractor(self):
        '''
        Check if the user is part of the contractors groups of the event
        '''
        common_groups = self.person.groups.all() & self.event.contractors_groups.all()
        logging.debug("is_contractor:{0}:{1}".format(self.person, common_groups))
        return common_groups.count() > 0

    def must_pay(self):
        '''
        Returns the amount that the person has to pay for the booking
        '''
        if self.is_employee():
            if self.event.price_for_employees is not None:
                return self.event.price_for_employees
            else:
                return Decimal(0.00)
        elif self.is_contractor():
            if self.event.price_for_contractors is not None:
                return self.event.price_for_contractors
            else:
                return Decimal(0.00)
        else:
            logging.error("User {0} is neither employee not contractor for {1}".format(self.person,
                                                                                       self.event))
            return Decimal(999.99)

    def get_payment_status_class(self):
        '''
        Return the status of payment (as a CSS class)
        '''
        if self.cancelled:
            if self.paidTo is None:
                return ''
            else:
                return 'danger'
        else:
            if self.must_pay() == 0:
                return 'success'
            elif self.paidTo is None:
                return 'warning'
        return ''


class ParticipantOption(models.Model):
    '''
    A choice made by a booking for an event
    '''
    booking = models.ForeignKey(ParticipantBooking, related_name='options')
    option = models.ForeignKey(EventChoiceOption, null=True, blank=True)

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
