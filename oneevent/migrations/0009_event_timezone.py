from django.db import migrations
import timezone_field.fields


TIMEZONE_CODES = {
    "Boston": "US/Eastern",
    "Erding": "Europe/Berlin",
    "London": "Europe/London",
    "Miami": "US/Eastern",
    "Munich": "Europe/Berlin",
    "Nice": "Europe/Paris",
    "Sydney": "Australia/Sydney",
    "Toronto": "America/Toronto",
    "UTC": "UTC",
}


def forwards(apps, _schema_editor):
    event_model = apps.get_model("oneevent", "Event")
    all_events = event_model.objects.all()
    for event in all_events:
        event.timezone = TIMEZONE_CODES[event.city]
        event.save()


class Migration(migrations.Migration):

    dependencies = [
        ("oneevent", "0008_delete_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="timezone",
            field=timezone_field.fields.TimeZoneField(
                default="Europe/London", help_text="Local timezone of your event"
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
