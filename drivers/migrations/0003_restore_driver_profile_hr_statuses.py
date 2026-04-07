from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("drivers", "0002_trim_driver_profile_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="driverprofile",
            name="employment_status",
            field=models.CharField(
                choices=[
                    ("onboarding", "onboarding"),
                    ("active", "active"),
                    ("leave", "leave"),
                    ("resigned", "resigned"),
                    ("retired", "retired"),
                ],
                default="active",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="qualification_status",
            field=models.CharField(
                choices=[
                    ("pending_review", "pending_review"),
                    ("qualified", "qualified"),
                    ("restricted", "restricted"),
                    ("expired", "expired"),
                    ("revoked", "revoked"),
                ],
                default="qualified",
                max_length=32,
            ),
        ),
    ]
