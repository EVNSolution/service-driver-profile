from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient


class DriverApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user_token = self._issue_token("user", allowed_nav_keys=["drivers"])
        self.admin_token = self._issue_token("admin", allowed_nav_keys=["drivers"])

    def _issue_token(self, role: str, *, allowed_nav_keys: list[str] | None = None) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(uuid4()),
            "email": f"{role}@example.com",
            "role": role,
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "jti": str(uuid4()),
            "type": "access",
        }
        if allowed_nav_keys is not None:
            payload["allowed_nav_keys"] = allowed_nav_keys
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def _authenticate(self, token: str) -> None:
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _payload(self):
        return {
            "company_id": str(uuid4()),
            "fleet_id": str(uuid4()),
            "name": "Kim Driver",
            "ev_id": "EV-001",
            "phone_number": "010-1234-5678",
            "address": "Seoul",
            "employment_status": "active",
            "qualification_status": "qualified",
        }

    def test_health_endpoint_responds(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")

    def test_unauthenticated_requests_return_401_shape(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(set(response.data.keys()), {"code", "message", "details"})

    def test_user_can_crud_driver_profile(self):
        self._authenticate(self.user_token)

        create_response = self.client.post("/", self._payload(), format="json")
        self.assertEqual(create_response.status_code, 201)
        self.assertNotIn("account_id", create_response.data)
        driver_id = create_response.data["driver_id"]
        driver_ref = create_response.data["route_no"]

        self.assertEqual(self.client.get(f"/{driver_ref}/").status_code, 200)
        self.assertEqual(self.client.get(f"/{driver_id}/").status_code, 200)
        self.assertEqual(
            self.client.patch(
                f"/{driver_ref}/",
                {"phone_number": "010-9999-9999"},
                format="json",
            ).status_code,
            200,
        )
        self.assertEqual(self.client.delete(f"/{driver_id}/").status_code, 204)

    def test_admin_can_crud_driver_profile(self):
        self._authenticate(self.admin_token)

        create_response = self.client.post("/", self._payload(), format="json")
        self.assertEqual(create_response.status_code, 201)
        self.assertNotIn("account_id", create_response.data)
        driver_id = create_response.data["driver_id"]
        driver_ref = create_response.data["route_no"]

        self.assertEqual(self.client.get(f"/{driver_ref}/").status_code, 200)
        self.assertEqual(self.client.get(f"/{driver_id}/").status_code, 200)
        self.assertEqual(
            self.client.patch(
                f"/{driver_ref}/",
                {"address": "Busan"},
                format="json",
            ).status_code,
            200,
        )
        self.assertEqual(self.client.delete(f"/{driver_id}/").status_code, 204)

    def test_check_ev_id_reports_duplicate_state(self):
        self._authenticate(self.user_token)

        payload = self._payload()
        self.assertEqual(self.client.post("/", payload, format="json").status_code, 201)

        duplicate_response = self.client.get(
            "/check-ev-id/",
            {"company_id": payload["company_id"], "ev_id": payload["ev_id"]},
        )
        available_response = self.client.get(
            "/check-ev-id/",
            {"company_id": payload["company_id"], "ev_id": "EV-NEW"},
        )

        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(duplicate_response.data, {"is_duplicate": True})
        self.assertEqual(available_response.status_code, 200)
        self.assertEqual(available_response.data, {"is_duplicate": False})

    def test_create_defaults_hr_statuses_when_not_provided(self):
        self._authenticate(self.admin_token)
        payload = self._payload()
        payload.pop("employment_status")
        payload.pop("qualification_status")

        response = self.client.post("/", payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertIn("route_no", response.data)
        self.assertEqual(response.data["employment_status"], "active")
        self.assertEqual(response.data["qualification_status"], "qualified")

    def test_missing_driver_returns_404_shape(self):
        self._authenticate(self.user_token)
        response = self.client.get("/999999/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(set(response.data.keys()), {"code", "message", "details"})

    def test_user_without_drivers_nav_key_cannot_list_driver_profiles(self):
        self._authenticate(self._issue_token("user", allowed_nav_keys=[]))

        response = self.client.get("/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(set(response.data.keys()), {"code", "message", "details"})

    def test_user_without_drivers_nav_key_cannot_check_ev_id(self):
        self._authenticate(self._issue_token("user", allowed_nav_keys=[]))

        response = self.client.get(
            "/check-ev-id/",
            {"company_id": str(uuid4()), "ev_id": "EV-001"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(set(response.data.keys()), {"code", "message", "details"})
