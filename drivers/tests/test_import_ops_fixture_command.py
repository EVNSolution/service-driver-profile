import json
import tempfile
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

from django.core.management import call_command
from django.test import TestCase

from drivers.models import DriverProfile


class ImportOpsFixtureCommandTests(TestCase):
    def test_command_imports_drivers_idempotently(self):
        payload = {
            "drivers": [
                {
                    "driver_id": str(uuid4()),
                    "company_id": str(uuid4()),
                    "fleet_id": str(uuid4()),
                    "name": "Ops Driver A1-01",
                    "ev_id": "OPS-11-001",
                    "phone_number": "010-9000-1101",
                    "address": "Ops District 1-1",
                    "employment_status": "active",
                    "qualification_status": "qualified",
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            Path(tmp.name).write_text(json.dumps(payload))
            fixture_path = tmp.name
        self.addCleanup(Path(fixture_path).unlink, missing_ok=True)

        call_command("import_ops_fixture", "--fixture", fixture_path, stdout=Mock())
        call_command("import_ops_fixture", "--fixture", fixture_path, stdout=Mock())

        self.assertEqual(DriverProfile.objects.count(), 1)
