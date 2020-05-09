from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0006_require_contenttypes_0002"),
        ("oneevent", "0002_event_employees_exception_groups"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
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
                ("order", models.IntegerField()),
                ("name", models.CharField(max_length=64)),
                (
                    "price",
                    models.DecimalField(default=0, max_digits=6, decimal_places=2),
                ),
                (
                    "event",
                    models.ForeignKey(
                        related_name="categories",
                        to="oneevent.Event",
                        on_delete=models.deletion.CASCADE,
                    ),
                ),
                (
                    "groups1",
                    models.ManyToManyField(
                        related_name="groups1_for_category+",
                        verbose_name="First groups matched by the rule",
                        to="auth.Group",
                        blank=True,
                    ),
                ),
                (
                    "groups2",
                    models.ManyToManyField(
                        related_name="groups2_for_category+",
                        verbose_name="Second groups matched by the rule",
                        to="auth.Group",
                        blank=True,
                    ),
                ),
            ],
            options={"ordering": ["order"]},
        ),
        migrations.AlterUniqueTogether(
            name="category",
            unique_together=set([("event", "order"), ("event", "name")]),
        ),
    ]
