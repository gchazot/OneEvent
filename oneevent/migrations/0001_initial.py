from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("auth", "0006_require_contenttypes_0002"),
    ]

    operations = [
        migrations.CreateModel(
            name="Booking",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("confirmedOn", models.DateTimeField(null=True, blank=True)),
                ("cancelledOn", models.DateTimeField(null=True, blank=True)),
                ("datePaid", models.DateTimeField(null=True, blank=True)),
                ("exempt_of_payment", models.BooleanField(default=False)),
                (
                    "cancelledBy",
                    models.ForeignKey(
                        related_name="cancelled_bookings",
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="BookingOption",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "booking",
                    models.ForeignKey(
                        related_name="options",
                        to="oneevent.Booking",
                        on_delete=models.deletion.CASCADE,
                    ),
                ),
            ],
            options={"ordering": ["option__choice__id", "option__id", "id"]},
        ),
        migrations.CreateModel(
            name="Choice",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("title", models.CharField(max_length=64)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("title", models.CharField(unique=True, max_length=64)),
                ("start", models.DateTimeField(help_text="Local start date and time")),
                (
                    "end",
                    models.DateTimeField(
                        help_text="Local end date and time", null=True, blank=True
                    ),
                ),
                (
                    "city",
                    models.CharField(
                        help_text="Timezone of your event",
                        max_length=32,
                        choices=[
                            ("Boston", "Boston"),
                            ("Erding", "Erding"),
                            ("London", "London"),
                            ("Miami", "Miami"),
                            ("Munich", "Munich"),
                            ("Nice", "Nice"),
                            ("Sydney", "Sydney"),
                            ("Toronto", "Toronto"),
                            ("UTC", "UTC"),
                        ],
                    ),
                ),
                ("description", models.TextField(blank=True)),
                (
                    "pub_status",
                    models.CharField(
                        default="UNPUB",
                        help_text="Public: Visible and bookable by all; Restricted: "
                        "Visible and Bookable by invited groups; Private: "
                        "Visible by participant, bookable by all; "
                        "Unpublished: Visible by organisers, not bookable; "
                        "Archived: Not visible, not bookable",
                        max_length=8,
                        verbose_name="Publication status",
                        choices=[
                            ("PUB", "Public"),
                            ("REST", "Restricted"),
                            ("PRIV", "Private"),
                            ("UNPUB", "Unpublished"),
                            ("ARCH", "Archived"),
                        ],
                    ),
                ),
                (
                    "location_name",
                    models.CharField(
                        help_text="Venue of your event",
                        max_length=64,
                        null=True,
                        blank=True,
                    ),
                ),
                ("location_address", models.TextField(null=True, blank=True)),
                (
                    "booking_close",
                    models.DateTimeField(
                        help_text="Limit date and time for registering",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "choices_close",
                    models.DateTimeField(
                        help_text="Limit date and time for changing choices",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "max_participant",
                    models.PositiveSmallIntegerField(
                        default=0,
                        help_text="Maximum number of participants to this event (0 = "
                        "no limit)",
                    ),
                ),
                (
                    "price_for_employees",
                    models.DecimalField(default=0, max_digits=6, decimal_places=2),
                ),
                (
                    "price_for_contractors",
                    models.DecimalField(default=0, max_digits=6, decimal_places=2),
                ),
                (
                    "price_currency",
                    models.CharField(
                        max_length=3,
                        null=True,
                        verbose_name="Currency for prices",
                        blank=True,
                    ),
                ),
                (
                    "contractors_groups",
                    models.ManyToManyField(
                        related_name="contractors_for_event+",
                        verbose_name="Groups considered as Contractors",
                        to="auth.Group",
                        blank=True,
                    ),
                ),
                (
                    "employees_groups",
                    models.ManyToManyField(
                        related_name="employees_for_event+",
                        verbose_name="Groups considered as Employees",
                        to="auth.Group",
                        blank=True,
                    ),
                ),
                (
                    "organisers",
                    models.ManyToManyField(
                        related_name="events_organised",
                        to=settings.AUTH_USER_MODEL,
                        blank=True,
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        related_name="events_owned",
                        to=settings.AUTH_USER_MODEL,
                        help_text="Main organiser",
                        on_delete=models.deletion.PROTECT,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        max_length=8,
                        verbose_name="Reason",
                        choices=[
                            ("QUERY", "Question"),
                            ("COMMENT", "Comment"),
                            ("BUG", "Bug report"),
                            ("FEAT", "Feature request"),
                            ("ADMIN", "Administration Request"),
                        ],
                    ),
                ),
                ("title", models.CharField(max_length=128)),
                ("text", models.TextField(max_length=2048)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("safe_content", models.BooleanField(default=False)),
                (
                    "sender",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE
                    ),
                ),
                (
                    "thread_head",
                    models.ForeignKey(
                        related_name="thread",
                        blank=True,
                        to="oneevent.Message",
                        null=True,
                        on_delete=models.deletion.CASCADE,
                    ),
                ),
            ],
            options={"ordering": ["-created"]},
        ),
        migrations.CreateModel(
            name="Option",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("title", models.CharField(max_length=256)),
                ("default", models.BooleanField(default=False)),
                (
                    "choice",
                    models.ForeignKey(
                        related_name="options",
                        to="oneevent.Choice",
                        on_delete=models.deletion.CASCADE,
                    ),
                ),
            ],
            options={"ordering": ["choice__id", "id"]},
        ),
        migrations.CreateModel(
            name="Session",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("title", models.CharField(unique=True, max_length=64)),
                ("start", models.DateTimeField(help_text="Local start date and time")),
                (
                    "end",
                    models.DateTimeField(
                        help_text="Local end date and time", null=True, blank=True
                    ),
                ),
                (
                    "max_participant",
                    models.PositiveSmallIntegerField(
                        default=0,
                        help_text="Maximum number of participants to this session (0 "
                        "= no limit)",
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        related_name="sessions",
                        to="oneevent.Event",
                        on_delete=models.deletion.CASCADE,
                    ),
                ),
            ],
            options={"ordering": ["event", "title"]},
        ),
        migrations.AddField(
            model_name="choice",
            name="event",
            field=models.ForeignKey(
                related_name="choices",
                to="oneevent.Event",
                on_delete=models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="bookingoption",
            name="option",
            field=models.ForeignKey(
                blank=True,
                to="oneevent.Option",
                null=True,
                on_delete=models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="event",
            field=models.ForeignKey(
                related_name="bookings",
                to="oneevent.Event",
                on_delete=models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="paidTo",
            field=models.ForeignKey(
                related_name="received_payments",
                blank=True,
                to=settings.AUTH_USER_MODEL,
                null=True,
                on_delete=models.deletion.SET_NULL,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="person",
            field=models.ForeignKey(
                related_name="bookings",
                to=settings.AUTH_USER_MODEL,
                on_delete=models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="session",
            field=models.ForeignKey(
                related_name="bookings",
                blank=True,
                to="oneevent.Session",
                null=True,
                on_delete=models.deletion.CASCADE,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="session", unique_together=set([("event", "title")]),
        ),
        migrations.AlterUniqueTogether(
            name="option", unique_together=set([("choice", "title")]),
        ),
        migrations.AlterUniqueTogether(
            name="choice", unique_together=set([("event", "title")]),
        ),
        migrations.AlterUniqueTogether(
            name="bookingoption", unique_together=set([("booking", "option")]),
        ),
        migrations.AlterUniqueTogether(
            name="booking", unique_together=set([("event", "person")]),
        ),
    ]
