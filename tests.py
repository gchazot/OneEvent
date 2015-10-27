'''
@author: Germain CHAZOT

Copyright 2014-2015 Germain CHAZOT

This file is part of OneEvent.

OneEvent is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OneEvent is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OneEvent.  If not, see <http://www.gnu.org/licenses/>.
'''
from django.test import TestCase
from models import Event, Category, Choice, Option, Booking, BookingOption
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User, Group


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

    def test_isFullyBooked_NoMaxParticipants(self):
        ev = Event.objects.create(title='event no max participants',
                                  start=timezone.now(),
                                  owner=default_user())
        self.assertFalse(ev.is_fully_booked())

        user1 = User.objects.create(username='myUser')
        Booking.objects.create(event=ev, person=user1)
        self.assertFalse(ev.is_fully_booked())

    def test_isFullyBooked_Max1Participant(self):
        ev = Event.objects.create(title='event no max participants',
                                  start=timezone.now(),
                                  owner=default_user(),
                                  max_participant=1)
        self.assertFalse(ev.is_fully_booked())

        user1 = User.objects.create(username='myUser1')
        Booking.objects.create(event=ev, person=user1)
        self.assertTrue(ev.is_fully_booked())

        user2 = User.objects.create(username='myUser2')
        Booking.objects.create(event=ev, person=user2)
        self.assertTrue(ev.is_fully_booked())

    def test_isFullyBooked_Max2Participants(self):
        ev = Event.objects.create(title='event no max participants',
                                  start=timezone.now(),
                                  owner=default_user(),
                                  max_participant=2)
        self.assertFalse(ev.is_fully_booked())

        user1 = User.objects.create(username='myUser1')
        Booking.objects.create(event=ev, person=user1)
        self.assertFalse(ev.is_fully_booked())

        user2 = User.objects.create(username='myUser2')
        Booking.objects.create(event=ev, person=user2)
        self.assertTrue(ev.is_fully_booked())


class CategoryTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(title='myEvent',
                                       start=timezone.now(),
                                       owner=default_user())
        self.g1a = Group.objects.create(name="group1A")
        self.g1b = Group.objects.create(name="group1B")
        self.g1c = Group.objects.create(name="group1C")
        self.g2a = Group.objects.create(name="group2A")
        self.g2b = Group.objects.create(name="group2B")
        self.g2c = Group.objects.create(name="group2C")

    def test_match_1GroupInGroup1(self):
        cat = Category.objects.create(event=self.ev,
                                      order=1,
                                      name="category1")
        cat.groups1.add(self.g1a)

        groups = Group.objects.filter(name__startswith="group1A")
        self.assertTrue(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group1B")
        self.assertFalse(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group1")
        self.assertTrue(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group2")
        self.assertFalse(cat.match(groups))

    def test_match_2GroupsInGroup1(self):
        cat = Category.objects.create(event=self.ev,
                                      order=1,
                                      name="category1")
        cat.groups1.add(self.g1a)
        cat.groups1.add(self.g1b)

        groups = Group.objects.filter(name__startswith="group1A")
        self.assertTrue(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group1B")
        self.assertTrue(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group1C")
        self.assertFalse(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group1")
        self.assertTrue(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group2")
        self.assertFalse(cat.match(groups))

    def test_match_1GroupInGroup2(self):
        cat = Category.objects.create(event=self.ev,
                                      order=1,
                                      name="category1")
        cat.groups1.add(self.g1a)
        cat.groups2.add(self.g2a)

        groups = Group.objects.filter(name__startswith="group1A")
        self.assertFalse(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group2A")
        self.assertFalse(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group1")
        self.assertFalse(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group")
        self.assertTrue(cat.match(groups))

        groups = Group.objects.filter(name__endswith='A')
        self.assertTrue(cat.match(groups))

    def test_match_2GroupsInGroup2(self):
        cat = Category.objects.create(event=self.ev,
                                      order=1,
                                      name="category1")
        cat.groups1.add(self.g1a)
        cat.groups2.add(self.g2a)
        cat.groups2.add(self.g2b)

        groups = Group.objects.filter(name__startswith="group1A")
        self.assertFalse(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group2A")
        self.assertFalse(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group1")
        self.assertFalse(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group")
        self.assertTrue(cat.match(groups))

        groups = Group.objects.filter(name__endswith='A')
        self.assertTrue(cat.match(groups))

        groups = Group.objects.filter(name__endswith='B')
        self.assertFalse(cat.match(groups))

        groups = Group.objects.filter(name__startswith='group1A')
        groups |= Group.objects.filter(name__startswith='group2')
        self.assertTrue(cat.match(groups))


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
