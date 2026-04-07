from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("drivers", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="driverprofile",
            name="address",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="ev_id",
            field=models.CharField(default="", max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="name",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="phone_number",
            field=models.CharField(default="", max_length=32),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="driverprofile",
            name="account_id",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.RemoveField(
            model_name="driverprofile",
            name="employment_status",
        ),
        migrations.RemoveField(
            model_name="driverprofile",
            name="org_unit_id",
        ),
        migrations.RemoveField(
            model_name="driverprofile",
            name="qualification_status",
        ),
    ]
