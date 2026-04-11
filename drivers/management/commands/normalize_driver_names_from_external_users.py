from django.core.management.base import BaseCommand

from drivers.models import DriverProfile
from drivers.name_utils import derive_driver_name_from_external_user_name, should_normalize_driver_name


class Command(BaseCommand):
    help = "Normalize driver names from external_user_name for previously auto-created records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persist the normalized names. Omit for dry-run.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        matched_drivers: list[DriverProfile] = []

        for driver in DriverProfile.objects.exclude(external_user_name="").order_by("route_no", "driver_id"):
            if not should_normalize_driver_name(driver.name, driver.external_user_name):
                continue

            next_name = derive_driver_name_from_external_user_name(driver.external_user_name)
            if next_name == driver.name:
                continue
            matched_drivers.append(driver)

        updated_count = 0
        if apply_changes:
            for driver in matched_drivers:
                driver.name = derive_driver_name_from_external_user_name(driver.external_user_name)
                driver.save(update_fields=["name"])
                updated_count += 1

        mode = "apply" if apply_changes else "dry-run"
        self.stdout.write(
            self.style.SUCCESS(
                f"normalize_driver_names_from_external_users mode={mode} matched={len(matched_drivers)} updated={updated_count}"
            )
        )
