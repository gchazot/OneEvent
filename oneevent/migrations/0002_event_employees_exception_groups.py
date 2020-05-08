from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0006_require_contenttypes_0002"),
        ("oneevent", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="employees_exception_groups",
            field=models.ManyToManyField(
                related_name="employees_exceptions_for_event+",
                verbose_name="Groups NOT considered as Employees (exceptions)",
                to="auth.Group",
                blank=True,
            ),
        ),
    ]
