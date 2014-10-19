'''
Created on 9 Jun 2014

@author: germs
'''
from django.test import TestCase
from models import Event, EventChoice, EventChoiceOption, ParticipantBooking, ParticipantOption
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class EventTest(TestCase):
    def test_uniqueTitle(self):
        Event.objects.create(title='title 1',
                             start=timezone.now())
        self.assertRaises(IntegrityError,
                          Event.objects.create,
                          title='title 1',
                          start=timezone.now())


class EventChoiceTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(title='myEvent',
                                       start=timezone.now())

    def test_uniqueEventTitle(self):
        EventChoice.objects.create(event=self.ev, title='choice 1')
        self.assertRaises(IntegrityError,
                          EventChoice.objects.create,
                          event=self.ev,
                          title='choice 1')


class EventChoiceOptionTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(title='myEvent',
                                       start=timezone.now())
        self.choice = EventChoice.objects.create(event=self.ev,
                                                 title='choice 1')

    def test_uniqueChoiceTitle(self):
        EventChoiceOption.objects.create(choice=self.choice,
                                         title='option 1')
        self.assertRaises(IntegrityError,
                          EventChoiceOption.objects.create,
                          choice=self.choice,
                          title='option 1')


class ParticipantBookingTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(title='myEvent',
                                       start=timezone.now())
        self.user = User.objects.create(username='myUser')

    def test_uniqueEventPerson(self):
        ParticipantBooking.objects.create(event=self.ev,
                                          person=self.user)

    def test_clean(self):
        reg = ParticipantBooking(event=self.ev,
                                 person=self.user,
                                 paidTo=self.user,
                                 datePaid=None)
        reg.clean()
        self.assertEquals(reg.paidTo, self.user)
        diff_datePaid = timezone.now() - reg.datePaid
        self.assertLess(diff_datePaid, timedelta(seconds=1))
        self.assertGreaterEqual(diff_datePaid, timedelta(seconds=0))

        reg = ParticipantBooking(event=self.ev,
                                 person=self.user,
                                 paidTo=None,
                                 datePaid=timezone.now())
        reg.clean()
        self.assertEquals(reg.paidTo, None)
        self.assertEquals(reg.datePaid, None)


class ParticipantChoiceTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(title='myEvent',
                                       start=timezone.now())
        self.choice = EventChoice.objects.create(event=self.ev,
                                                 title='choice 1')
        self.option = EventChoiceOption.objects.create(choice=self.choice,
                                                       title='option 1')
        self.user = User.objects.create(username='myUser')
        self.booking = ParticipantBooking.objects.create(event=self.ev,
                                                         person=self.user)

    def test_uniqueParticipantOption(self):
        ParticipantOption.objects.create(booking=self.booking,
                                         option=self.option)
        self.assertRaises(IntegrityError,
                          ParticipantOption.objects.create,
                          booking=self.booking,
                          option=self.option)

    def test_clean(self):
        ParticipantOption.objects.create(booking=self.booking,
                                         option=self.option)
        opt2 = EventChoiceOption.objects.create(choice=self.choice,
                                                title='option 2')
        pchoice2 = ParticipantOption.objects.create(booking=self.booking,
                                                    option=opt2)
        self.assertRaises(ValidationError, pchoice2.clean)
