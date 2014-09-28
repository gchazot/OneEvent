from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date


class Event(models.Model):
    '''
    An event being organised
    '''
    title = models.CharField(max_length=64, unique=True)
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)

    organisers = models.ManyToManyField(User, blank=True)

    def __unicode__(self):
        result = u'{0} - {1:%x %H:%M}'.format(self.title, self.start)
        if self.end is not None:
            result += u' to {0:%x %H:%M}'.format(self.end)
        return result

    def get_bookings(self):
        '''
        Return the active bookings
        '''
        return self.bookings.filter(cancelled=False)

    def user_can_update(self, user):
        '''
        Cherck that the given user can update the event
        '''
        return user in self.organisers.all()

    def get_participants_ids(self):
        '''
        Return the ids of users with active bookings
        '''
        return self.get_bookings().values_list('person__id', flat=True)

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
        return u'{0} : option {1} {2}'.format(self.choice, self.title, self.default)

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
    mustPay = models.BooleanField(default=False)
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
        if self.paidTo is not None and not self.mustPay:
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
        return user == self.person

    def user_can_update_payment(self, user):
        '''
        Check that the user can update payment informations
        '''
        return user in self.event.organisers.all()

    def get_payment_status_class(self):
        '''
        Return the CSS class for the status of payment
        '''
        if self.cancelled:
            if self.paidTo is None:
                return ''
            else:
                return 'danger'
        elif not self.mustPay:
            return 'success'
        elif self.paidTo is None:
            return 'warning'
        else:
            return 'success'


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
