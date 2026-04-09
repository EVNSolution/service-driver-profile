from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("drivers", "0005_remove_driverprofile_account_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="driverprofile",
            name="external_user_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
    ]
