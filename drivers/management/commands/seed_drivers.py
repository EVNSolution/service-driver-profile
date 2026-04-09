from uuid import UUID

from django.core.management.base import BaseCommand

from drivers.models import DriverProfile


SAMPLE_DRIVER_ID = UUID("10000000-0000-0000-0000-000000000001")
SAMPLE_COMPANY_ID = UUID("30000000-0000-0000-0000-000000000001")
SAMPLE_FLEET_ID = UUID("40000000-0000-0000-0000-000000000001")


class Command(BaseCommand):
    help = "Create or update seeded driver profiles."

    def handle(self, *args, **options):
        DriverProfile.objects.update_or_create(
            driver_id=SAMPLE_DRIVER_ID,
            defaults={
                "company_id": SAMPLE_COMPANY_ID,
                "fleet_id": SAMPLE_FLEET_ID,
                "name": "Seed Driver",
                "external_user_name": "seed-driver",
                "ev_id": "EV-001",
                "phone_number": "010-1234-5678",
                "address": "Seoul",
                "employment_status": DriverProfile.EmploymentStatus.ACTIVE,
                "qualification_status": DriverProfile.QualificationStatus.QUALIFIED,
            },
        )
        self.stdout.write(self.style.SUCCESS("Seeded driver profiles."))
