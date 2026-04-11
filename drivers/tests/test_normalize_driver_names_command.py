from io import StringIO
from uuid import uuid4

from django.core.management import call_command
from django.test import TestCase

from drivers.models import DriverProfile


class NormalizeDriverNamesCommandTests(TestCase):
    def _create_driver(self, *, name: str, external_user_name: str):
        return DriverProfile.objects.create(
            company_id=uuid4(),
            fleet_id=uuid4(),
            name=name,
            external_user_name=external_user_name,
            ev_id=f"EV-{uuid4().hex[:8]}",
            phone_number="010-1234-5678",
            address="Seoul",
        )

    def test_command_dry_runs_without_updating_names(self):
        driver = self._create_driver(name="ZD홍길동", external_user_name="ZD홍길동")
        stdout = StringIO()

        call_command("normalize_driver_names_from_external_users", stdout=stdout)

        driver.refresh_from_db()
        self.assertEqual(driver.name, "ZD홍길동")
        self.assertIn("dry-run", stdout.getvalue())
        self.assertIn("matched=1", stdout.getvalue())
        self.assertIn("updated=0", stdout.getvalue())

    def test_command_updates_auto_created_names_when_apply_flag_is_set(self):
        driver = self._create_driver(name="ZD홍길동", external_user_name="ZD홍길동")
        stdout = StringIO()

        call_command("normalize_driver_names_from_external_users", "--apply", stdout=stdout)

        driver.refresh_from_db()
        self.assertEqual(driver.name, "홍길동")
        self.assertIn("updated=1", stdout.getvalue())

    def test_command_skips_manually_edited_names(self):
        driver = self._create_driver(name="홍길동 기사장", external_user_name="ZD홍길동")
        stdout = StringIO()

        call_command("normalize_driver_names_from_external_users", "--apply", stdout=stdout)

        driver.refresh_from_db()
        self.assertEqual(driver.name, "홍길동 기사장")
        self.assertIn("matched=0", stdout.getvalue())
