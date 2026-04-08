import json
from pathlib import Path
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from drivers.models import DriverProfile


class Command(BaseCommand):
    help = "Import the drivers section from an ops-derived local fixture."

    def add_arguments(self, parser):
        parser.add_argument("--fixture", required=True, help="Absolute path to the fixture JSON file.")

    def handle(self, *args, **options):
        payload = self._load_fixture(options["fixture"])
        drivers = payload.get("drivers", [])
        imported = 0

        with transaction.atomic():
            for driver_payload in drivers:
                DriverProfile.objects.update_or_create(
                    driver_id=UUID(driver_payload["driver_id"]),
                    defaults={
                        "company_id": UUID(driver_payload["company_id"]),
                        "fleet_id": UUID(driver_payload["fleet_id"]),
                        "name": driver_payload["name"],
                        "ev_id": driver_payload["ev_id"],
                        "phone_number": driver_payload["phone_number"],
                        "address": driver_payload["address"],
                        "employment_status": driver_payload["employment_status"],
                        "qualification_status": driver_payload["qualification_status"],
                    },
                )
                imported += 1

        self.stdout.write(
            self.style.SUCCESS(f"Imported ops-derived driver fixture ({imported} drivers).")
        )

    def _load_fixture(self, fixture_path: str) -> dict:
        path = Path(fixture_path)
        if not path.exists():
            raise CommandError(f"Fixture file does not exist: {path}")
        return json.loads(path.read_text())
