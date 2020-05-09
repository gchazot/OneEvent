from django.db import migrations


def create_categoories(apps, _schema_editor):
    Event = apps.get_model("oneevent", "Event")

    for event in Event.objects.all():
        employees = event.employees_groups.all()
        contractors = event.contractors_groups.all()
        exceptions = event.employees_exception_groups.all()

        order = 0
        if exceptions.exists():
            order += 1
            exc_category = event.categories.create(
                order=order, name="Exceptions", price=event.price_for_contractors
            )
            for exc_group in exceptions:
                exc_category.groups1.add(exc_group)

        if employees.exists():
            order += 1
            emp_category = event.categories.create(
                order=order, name="Employees", price=event.price_for_employees
            )
            for emp_group in employees:
                emp_category.groups1.add(emp_group)

        if contractors.exists():
            order += 1
            cnt_category = event.categories.create(
                order=order, name="Contractors", price=event.price_for_contractors
            )
            for cnt_group in contractors:
                if cnt_group not in exceptions:
                    cnt_category.groups1.add(cnt_group)


def delete_categories(apps, _schema_editor):
    Category = apps.get_model("oneevent", "Category")

    Category.objects.filter(
        name__in=["Exceptions", "Employees", "Contractors"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("oneevent", "0004_fix_unique_category"),
    ]

    operations = [
        migrations.RunPython(create_categoories, delete_categories),
    ]
