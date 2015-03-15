'''
Created on 9 Jun 2014

@author: germs
'''
from django.test import TestCase
from models import Event, Choice, Option, Booking, BookingOption
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User


def default_user():
    return User.objects.get_or_create(username='default')[0]


class EventTest(TestCase):
    def test_uniqueTitle(self):
        Event.objects.create(title='title 1',
                             start=timezone.now(),
                             owner=default_user())
        self.assertRaises(IntegrityError,
                          Event.objects.create,
                          title='title 1',
                          start=timezone.now(),
                          owner=default_user())


class ChoiceTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(title='myEvent',
                                       start=timezone.now(),
                                       owner=default_user())

    def test_uniqueEventTitle(self):
        Choice.objects.create(event=self.ev, title='choice 1')
        self.assertRaises(IntegrityError,
                          Choice.objects.create,
                          event=self.ev,
                          title='choice 1')


class OptionTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(title='myEvent',
                                       start=timezone.now(),
                                       owner=default_user())
        self.choice = Choice.objects.create(event=self.ev,
                                            title='choice 1')

    def test_uniqueChoiceTitle(self):
        Option.objects.create(choice=self.choice,
                              title='option 1')
        self.assertRaises(IntegrityError,
                          Option.objects.create,
                          choice=self.choice,
                          title='option 1')


class BookingTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(title='myEvent',
                                       start=timezone.now(),
                                       owner=default_user())
        self.user = User.objects.create(username='myUser')

    def test_uniqueEventPerson(self):
        Booking.objects.create(event=self.ev,
                               person=self.user)

    def test_clean(self):
        reg = Booking(event=self.ev,
                      person=self.user,
                      paidTo=self.user,
                      datePaid=None)
        reg.clean()
        self.assertEquals(reg.paidTo, self.user)
        diff_datePaid = timezone.now() - reg.datePaid
        self.assertLess(diff_datePaid, timedelta(seconds=1))
        self.assertGreaterEqual(diff_datePaid, timedelta(seconds=0))

        reg = Booking(event=self.ev,
                      person=self.user,
                      paidTo=None,
                      datePaid=timezone.now())
        reg.clean()
        self.assertEquals(reg.paidTo, None)
        self.assertEquals(reg.datePaid, None)


class ParticipantChoiceTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(title='myEvent',
                                       start=timezone.now(),
                                       owner=default_user())
        self.choice = Choice.objects.create(event=self.ev,
                                            title='choice 1')
        self.option = Option.objects.create(choice=self.choice,
                                            title='option 1')
        self.user = User.objects.create(username='myUser')
        self.booking = Booking.objects.create(event=self.ev,
                                              person=self.user)

    def test_uniqueBookingOption(self):
        BookingOption.objects.create(booking=self.booking,
                                     option=self.option)
        self.assertRaises(IntegrityError,
                          BookingOption.objects.create,
                          booking=self.booking,
                          option=self.option)

    def test_clean(self):
        BookingOption.objects.create(booking=self.booking,
                                     option=self.option)
        opt2 = Option.objects.create(choice=self.choice,
                                     title='option 2')
        pchoice2 = BookingOption.objects.create(booking=self.booking,
                                                option=opt2)
        self.assertRaises(ValidationError, pchoice2.clean)
