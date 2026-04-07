from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DriverProfile",
            fields=[
                (
                    "driver_id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("account_id", models.UUIDField()),
                ("company_id", models.UUIDField()),
                ("fleet_id", models.UUIDField()),
                ("org_unit_id", models.UUIDField()),
                ("employment_status", models.CharField(max_length=32)),
                ("qualification_status", models.CharField(max_length=32)),
            ],
            options={"ordering": ("driver_id",)},
        )
    ]
