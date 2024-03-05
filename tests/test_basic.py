from django.test import TestCase
from .models import Event, Category, Choice, Option, Booking, BookingOption
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from decimal import Decimal


def default_user():
    return get_user_model().objects.get_or_create(username="default")[0]


class EventTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(
            title="My Awesome Event", start=timezone.now(), owner=default_user()
        )

    def test_uniqueTitle(self):
        self.assertRaises(
            IntegrityError,
            Event.objects.create,
            title="My Awesome Event",
            start=timezone.now(),
            owner=default_user(),
        )

    def test_isFullyBooked_NoMaxParticipants(self):
        self.assertFalse(self.ev.is_fully_booked())

        user1 = get_user_model().objects.create(username="myUser")
        Booking.objects.create(event=self.ev, person=user1)
        self.assertFalse(self.ev.is_fully_booked())

    def test_isFullyBooked_Max1Participant(self):
        self.ev.max_participant = 1

        self.assertFalse(self.ev.is_fully_booked())

        user1 = get_user_model().objects.create(username="myUser1")
        Booking.objects.create(event=self.ev, person=user1)
        self.assertTrue(self.ev.is_fully_booked())

        user2 = get_user_model().objects.create(username="myUser2")
        Booking.objects.create(event=self.ev, person=user2)
        self.assertTrue(self.ev.is_fully_booked())

    def test_isFullyBooked_Max2Participants(self):
        self.ev.max_participant = 2

        self.assertFalse(self.ev.is_fully_booked())

        user1 = get_user_model().objects.create(username="myUser1")
        Booking.objects.create(event=self.ev, person=user1)
        self.assertFalse(self.ev.is_fully_booked())

        user2 = get_user_model().objects.create(username="myUser2")
        Booking.objects.create(event=self.ev, person=user2)
        self.assertTrue(self.ev.is_fully_booked())

    def test_collected_money_sums_no_data_returns_empty(self):
        sums = self.ev.get_collected_money_sums()

        self.assertSequenceEqual(sums.categories, [])
        self.assertSequenceEqual(sums.organisers, [])

    def test_collected_money_sums_returns_1_category(self):
        self.ev.categories.create(order=1, name="category1")

        sums = self.ev.get_collected_money_sums()

        self.assertSequenceEqual(sums.categories, ["category1"])

    def test_collected_money_sums_returns_2_categories(self):
        self.ev.categories.create(order=1, name="category1")
        self.ev.categories.create(order=2, name="category2")

        sums = self.ev.get_collected_money_sums()

        self.assertSequenceEqual(sums.categories, ["category1", "category2"])

    def test_collected_money_sums_1_booking_1_category_returns_value(self):
        price = Decimal("42.33")

        user = default_user()
        g1 = Group.objects.create(name="group1")
        user.groups.add(g1)

        self.ev.organisers.add(user)
        cat1 = self.ev.categories.create(order=1, name="category1", price=price)
        cat1.groups1.add(g1)

        self.ev.bookings.create(person=user, paidTo=user, datePaid=timezone.now())

        sums = self.ev.get_collected_money_sums()

        self.assertSequenceEqual(sums.categories, ["category1"])
        self.assertSequenceEqual(sums.organisers, [user])
        result_table = list(sums.table_rows())
        self.assertEqual(result_table[0], [user.get_full_name(), price, price])
        self.assertEqual(result_table[1], ["Total", price, price])


class CategoryTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(
            title="myEvent", start=timezone.now(), owner=default_user()
        )
        self.g1a = Group.objects.create(name="group1A")
        self.g1b = Group.objects.create(name="group1B")
        self.g1c = Group.objects.create(name="group1C")
        self.g2a = Group.objects.create(name="group2A")
        self.g2b = Group.objects.create(name="group2B")
        self.g2c = Group.objects.create(name="group2C")

    def test_match_1GroupInGroup1(self):
        cat = Category.objects.create(event=self.ev, order=1, name="category1")
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
        cat = Category.objects.create(event=self.ev, order=1, name="category1")
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
        cat = Category.objects.create(event=self.ev, order=1, name="category1")
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

        groups = Group.objects.filter(name__endswith="A")
        self.assertTrue(cat.match(groups))

    def test_match_2GroupsInGroup2(self):
        cat = Category.objects.create(event=self.ev, order=1, name="category1")
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

        groups = Group.objects.filter(name__endswith="A")
        self.assertTrue(cat.match(groups))

        groups = Group.objects.filter(name__endswith="B")
        self.assertFalse(cat.match(groups))

        groups = Group.objects.filter(name__startswith="group1A")
        groups |= Group.objects.filter(name__startswith="group2")
        self.assertTrue(cat.match(groups))


class ChoiceTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(
            title="myEvent", start=timezone.now(), owner=default_user()
        )

    def test_uniqueEventTitle(self):
        Choice.objects.create(event=self.ev, title="choice 1")
        self.assertRaises(
            IntegrityError, Choice.objects.create, event=self.ev, title="choice 1"
        )


class OptionTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(
            title="myEvent", start=timezone.now(), owner=default_user()
        )
        self.choice = Choice.objects.create(event=self.ev, title="choice 1")

    def test_uniqueChoiceTitle(self):
        Option.objects.create(choice=self.choice, title="option 1")
        self.assertRaises(
            IntegrityError, Option.objects.create, choice=self.choice, title="option 1"
        )


class BookingTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(
            title="myEvent", start=timezone.now(), owner=default_user()
        )
        self.user = get_user_model().objects.create(username="myUser")

        self.g1a = Group.objects.create(name="group1A")
        self.g1b = Group.objects.create(name="group1B")
        self.g2a = Group.objects.create(name="group2A")
        self.g2b = Group.objects.create(name="group2B")

    def _add_categories(self):
        self.cat1 = self.ev.categories.create(order=1, name="category1", price=33)
        self.cat1.groups1.add(self.g1a)

        self.cat2 = self.ev.categories.create(order=2, name="category2", price=42)
        self.cat2.groups1.add(self.g1b)
        self.cat2.groups2.add(self.g2b)

    def test_uniqueEventPerson(self):
        Booking.objects.create(event=self.ev, person=self.user)

    def test_clean(self):
        self._add_categories()
        reg = Booking(event=self.ev, person=self.user, paidTo=self.user, datePaid=None)
        reg.clean()
        self.assertEqual(reg.paidTo, self.user)
        diff_datePaid = timezone.now() - reg.datePaid
        self.assertLess(diff_datePaid, timedelta(seconds=1))
        self.assertGreaterEqual(diff_datePaid, timedelta(seconds=0))

        reg = Booking(
            event=self.ev, person=self.user, paidTo=None, datePaid=timezone.now()
        )
        reg.clean()
        self.assertEqual(reg.paidTo, None)
        self.assertEqual(reg.datePaid, None)

    def test_get_category_with_no_category_returns_None(self):
        reg = Booking(event=self.ev, person=self.user, paidTo=None, datePaid=None)
        self.assertIsNone(reg.get_category())

    def test_get_category_with_no_matching_category_returns_None(self):
        self._add_categories()
        reg = Booking(event=self.ev, person=self.user, paidTo=None, datePaid=None)
        # User has no group
        self.assertIsNone(reg.get_category())

        # User has no matching group
        self.user.groups.add(self.g1b)
        self.assertIsNone(reg.get_category())

    def test_get_category_with_matching_first_category_returns_first_Category(self):
        self._add_categories()
        reg = Booking(event=self.ev, person=self.user, paidTo=None, datePaid=None)
        self.user.groups.add(self.g1a)

        self.assertEqual(reg.get_category(), self.cat1)

    def test_get_category_with_matching_second_category_returns_second_Category(self):
        self._add_categories()
        reg = Booking(event=self.ev, person=self.user, paidTo=None, datePaid=None)
        self.user.groups.add(self.g1b)
        self.user.groups.add(self.g2b)

        self.assertEqual(reg.get_category(), self.cat2)

    def test_get_category_with_1_matching_category_returns_first_Category(self):
        self._add_categories()
        reg = Booking(event=self.ev, person=self.user, paidTo=None, datePaid=None)
        self.user.groups.add(self.g1a)
        self.user.groups.add(self.g1b)
        self.user.groups.add(self.g2b)

        self.assertEqual(reg.get_category(), self.cat1)

    def test_get_category_name_with_no_category_returns_Unknown(self):
        reg = Booking(event=self.ev, person=self.user, paidTo=None, datePaid=None)
        self.assertEqual("Unknown", reg.get_category_name())

    def test_get_category_name_with_category_returns_name(self):
        self._add_categories()
        reg = Booking(event=self.ev, person=self.user, paidTo=None, datePaid=None)
        self.user.groups.add(self.g1a)

        self.assertEqual("category1", reg.get_category_name())

    def test_payment_for_exempt_is_zero(self):
        reg = Booking(
            event=self.ev,
            person=self.user,
            paidTo=None,
            datePaid=None,
            exempt_of_payment=True,
        )

        self.assertEqual(Decimal(0), reg.must_pay())

    def test_payment_no_category_is_zero(self):
        reg = Booking(event=self.ev, person=self.user, paidTo=None, datePaid=None)

        self.assertEqual(Decimal(0), reg.must_pay())

    def test_payment_no_matching_category_is_default(self):
        self._add_categories()
        reg = Booking(event=self.ev, person=self.user, paidTo=None, datePaid=None)

        self.assertEqual(Decimal("9999.99"), reg.must_pay())

    def test_payment_matching_category_is_category_price(self):
        self._add_categories()
        reg = Booking(event=self.ev, person=self.user, paidTo=None, datePaid=None)
        self.user.groups.add(self.g1a)

        self.assertEqual(33, reg.must_pay())


class ParticipantChoiceTest(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(
            title="myEvent", start=timezone.now(), owner=default_user()
        )
        self.choice = Choice.objects.create(event=self.ev, title="choice 1")
        self.option = Option.objects.create(choice=self.choice, title="option 1")
        self.user = get_user_model().objects.create(username="myUser")
        self.booking = Booking.objects.create(event=self.ev, person=self.user)

    def test_uniqueBookingOption(self):
        BookingOption.objects.create(booking=self.booking, option=self.option)
        self.assertRaises(
            IntegrityError,
            BookingOption.objects.create,
            booking=self.booking,
            option=self.option,
        )

    def test_clean(self):
        BookingOption.objects.create(booking=self.booking, option=self.option)
        opt2 = Option.objects.create(choice=self.choice, title="option 2")
        pchoice2 = BookingOption.objects.create(booking=self.booking, option=opt2)
        self.assertRaises(ValidationError, pchoice2.clean)
