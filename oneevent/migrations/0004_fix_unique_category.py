

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oneevent', '0003_auto_category'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='category',
            unique_together=set([('event', 'name')]),
        ),
    ]
