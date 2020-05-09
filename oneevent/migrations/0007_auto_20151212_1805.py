from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("oneevent", "0006_remove_employee_contractor_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="booking",
            name="session",
            field=models.ForeignKey(
                related_name="bookings",
                on_delete=django.db.models.deletion.SET_NULL,
                blank=True,
                to="oneevent.Session",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="session",
            name="max_participant",
            field=models.PositiveSmallIntegerField(
                default=0, help_text="Maximum number of participants (0 = no limit)"
            ),
        ),
    ]
