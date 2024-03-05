import string
import random
from functools import partial
from datetime import date

from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth.models import Group, User


alphabet = string.ascii_lowercase + string.digits


def random_choice(length=8):
    return ''.join(random.choices(alphabet, k=length))


class Event(models.Model):
    code = models.TextField(unique=True, default=random_choice)
    title = models.TextField(unique=True)
    description = models.TextField(blank=True)
    registration_open = models.DateField(auto_now=True, help_text="Date registration opens")
    registration_close = models.DateField(blank=True, null=True, help_text="Date registration closes")
    max_participants = models.PositiveIntegerField(
        default=0,
        help_text="Maximum number of participants to this event (0 = no limit)",
    )
    currency = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    def clean(self):
        super(Event, self).clean()
        if self.registration_close and self.registration_open >= self.registration_close:
            raise ValidationError("Registration must open before it closes")

    def in_registration_window(self):
        today = date.today()
        return (today >= self.registration_open) and (not self.registration_close or today <= self.registration_close)

    def url(self):
        reverse("event_view", args=(self.unique_code,))


class RegistrationOption(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    item = models.TextField()
    price = models.FloatField(default=0, null=False)
    add_on = models.BooleanField(default=False)


class Registration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    options = models.ManyToManyField(RegistrationOption)
    paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'user'], name='Single registration')
        ]


class Message(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    message = models.TextField()
    emailed = models.BooleanField(default=False)


class DiscountCode(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    code = models.TextField(default=partial(random_choice, length=4))
    only_registration = models.BooleanField(default=True)
    percentage = models.IntegerField(help_text="Value as a percentage, like 10", blank=True, null=True)
    absolute = models.FloatField(help_text="Absolute amount of discount", blank=True, null=True)


class GroupDiscount(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    only_registration = models.BooleanField(default=True)
    percentage = models.IntegerField(help_text="Value as a percentage, like 10", blank=True, null=True)
    absolute = models.FloatField(help_text="Absolute amount of discount", blank=True, null=True)
