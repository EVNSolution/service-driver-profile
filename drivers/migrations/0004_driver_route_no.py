from django.db import migrations, models


def populate_driver_route_no(apps, schema_editor):
    DriverProfile = apps.get_model("drivers", "DriverProfile")
    for index, driver in enumerate(DriverProfile.objects.order_by("driver_id"), start=1):
        driver.route_no = index
        driver.save(update_fields=["route_no"])


class Migration(migrations.Migration):
    dependencies = [
        ("drivers", "0003_restore_driver_profile_hr_statuses"),
    ]

    operations = [
        migrations.AddField(
            model_name="driverprofile",
            name="route_no",
            field=models.PositiveIntegerField(editable=False, null=True, unique=True),
        ),
        migrations.RunPython(populate_driver_route_no, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="driverprofile",
            name="route_no",
            field=models.PositiveIntegerField(editable=False, unique=True),
        ),
    ]
