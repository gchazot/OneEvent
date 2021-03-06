# Generated by Django 3.0.6 on 2020-05-10 12:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('oneevent', '0010_remove_event_city'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(help_text='Main organiser', on_delete=django.db.models.deletion.CASCADE, related_name='events_owned', to=settings.AUTH_USER_MODEL),
        ),
    ]
