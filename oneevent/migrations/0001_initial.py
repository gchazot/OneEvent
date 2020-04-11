from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('confirmedOn', models.DateTimeField(null=True, blank=True)),
                ('cancelledOn', models.DateTimeField(null=True, blank=True)),
                ('datePaid', models.DateTimeField(null=True, blank=True)),
                ('exempt_of_payment', models.BooleanField(default=False)),
                ('cancelledBy', models.ForeignKey(related_name='cancelled_bookings', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='BookingOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('booking', models.ForeignKey(related_name='options', to='oneevent.Booking')),
            ],
            options={
                'ordering': ['option__choice__id', 'option__id', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=64)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=64)),
                ('start', models.DateTimeField(help_text=b'Local start date and time')),
                ('end', models.DateTimeField(help_text=b'Local end date and time', null=True, blank=True)),
                ('city', models.CharField(help_text=b'Timezone of your event', max_length=32, choices=[(b'Boston', b'Boston'), (b'Erding', b'Erding'), (b'London', b'London'), (b'Miami', b'Miami'), (b'Munich', b'Munich'), (b'Nice', b'Nice'), (b'Sydney', b'Sydney'), (b'Toronto', b'Toronto'), (b'UTC', b'UTC')])),
                ('description', models.TextField(blank=True)),
                ('pub_status', models.CharField(default=b'UNPUB', help_text=b'Public: Visible and bookable by all; Restricted: Visible and Bookable by invited groups; Private: Visible by participant, bookable by all; Unpublished: Visible by organisers, not bookable; Archived: Not visible, not bookable', max_length=8, verbose_name=b'Publication status', choices=[(b'PUB', b'Public'), (b'REST', b'Restricted'), (b'PRIV', b'Private'), (b'UNPUB', b'Unpublished'), (b'ARCH', b'Archived')])),
                ('location_name', models.CharField(help_text=b'Venue of your event', max_length=64, null=True, blank=True)),
                ('location_address', models.TextField(null=True, blank=True)),
                ('booking_close', models.DateTimeField(help_text=b'Limit date and time for registering', null=True, blank=True)),
                ('choices_close', models.DateTimeField(help_text=b'Limit date and time for changing choices', null=True, blank=True)),
                ('max_participant', models.PositiveSmallIntegerField(default=0, help_text=b'Maximum number of participants to this event (0 = no limit)')),
                ('price_for_employees', models.DecimalField(default=0, max_digits=6, decimal_places=2)),
                ('price_for_contractors', models.DecimalField(default=0, max_digits=6, decimal_places=2)),
                ('price_currency', models.CharField(max_length=3, null=True, verbose_name=b'Currency for prices', blank=True)),
                ('contractors_groups', models.ManyToManyField(related_name='contractors_for_event+', verbose_name=b'Groups considered as Contractors', to='auth.Group', blank=True)),
                ('employees_groups', models.ManyToManyField(related_name='employees_for_event+', verbose_name=b'Groups considered as Employees', to='auth.Group', blank=True)),
                ('organisers', models.ManyToManyField(related_name='events_organised', to=settings.AUTH_USER_MODEL, blank=True)),
                ('owner', models.ForeignKey(related_name='events_owned', to=settings.AUTH_USER_MODEL, help_text=b'Main organiser')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(max_length=8, verbose_name=b'Reason', choices=[(b'QUERY', b'Question'), (b'COMMENT', b'Comment'), (b'BUG', b'Bug report'), (b'FEAT', b'Feature request'), (b'ADMIN', b'Administration Request')])),
                ('title', models.CharField(max_length=128)),
                ('text', models.TextField(max_length=2048)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('safe_content', models.BooleanField(default=False)),
                ('sender', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('thread_head', models.ForeignKey(related_name='thread', blank=True, to='oneevent.Message', null=True)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=256)),
                ('default', models.BooleanField(default=False)),
                ('choice', models.ForeignKey(related_name='options', to='oneevent.Choice')),
            ],
            options={
                'ordering': ['choice__id', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=64)),
                ('start', models.DateTimeField(help_text=b'Local start date and time')),
                ('end', models.DateTimeField(help_text=b'Local end date and time', null=True, blank=True)),
                ('max_participant', models.PositiveSmallIntegerField(default=0, help_text=b'Maximum number of participants to this session (0 = no limit)')),
                ('event', models.ForeignKey(related_name='sessions', to='oneevent.Event')),
            ],
            options={
                'ordering': ['event', 'title'],
            },
        ),
        migrations.AddField(
            model_name='choice',
            name='event',
            field=models.ForeignKey(related_name='choices', to='oneevent.Event'),
        ),
        migrations.AddField(
            model_name='bookingoption',
            name='option',
            field=models.ForeignKey(blank=True, to='oneevent.Option', null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='event',
            field=models.ForeignKey(related_name='bookings', to='oneevent.Event'),
        ),
        migrations.AddField(
            model_name='booking',
            name='paidTo',
            field=models.ForeignKey(related_name='received_payments', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='person',
            field=models.ForeignKey(related_name='bookings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='booking',
            name='session',
            field=models.ForeignKey(related_name='bookings', blank=True, to='oneevent.Session', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='session',
            unique_together=set([('event', 'title')]),
        ),
        migrations.AlterUniqueTogether(
            name='option',
            unique_together=set([('choice', 'title')]),
        ),
        migrations.AlterUniqueTogether(
            name='choice',
            unique_together=set([('event', 'title')]),
        ),
        migrations.AlterUniqueTogether(
            name='bookingoption',
            unique_together=set([('booking', 'option')]),
        ),
        migrations.AlterUniqueTogether(
            name='booking',
            unique_together=set([('event', 'person')]),
        ),
    ]
