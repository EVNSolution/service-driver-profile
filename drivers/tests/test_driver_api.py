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
        self.company_id = uuid4()
        self.fleet_id = uuid4()

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

    def _payload(self, **overrides):
        payload = {
            "company_id": str(self.company_id),
            "fleet_id": str(self.fleet_id),
            "name": "Kim Driver",
            "ev_id": "EV-001",
            "phone_number": "010-1234-5678",
            "address": "Seoul",
            "employment_status": "active",
            "qualification_status": "qualified",
        }
        payload.update(overrides)
        return payload

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

    def test_driver_create_accepts_external_user_name(self):
        self._authenticate(self.user_token)

        response = self.client.post(
            "/",
            self._payload(external_user_name="ZD홍길동"),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["external_user_name"], "ZD홍길동")

    def test_driver_list_filters_by_external_user_name(self):
        self._authenticate(self.user_token)
        self.assertEqual(
            self.client.post(
                "/",
                self._payload(name="Kim Driver", ev_id="EV-001", external_user_name="ZD홍길동"),
                format="json",
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.post(
                "/",
                self._payload(name="Lee Driver", ev_id="EV-002", external_user_name="ZD이순신"),
                format="json",
            ).status_code,
            201,
        )

        response = self.client.get("/", {"external_user_name": "ZD홍길동"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["external_user_name"], "ZD홍길동")

    def test_driver_list_filters_by_external_user_name_and_scope(self):
        self._authenticate(self.user_token)
        other_company_id = uuid4()
        other_fleet_id = uuid4()
        self.assertEqual(
            self.client.post(
                "/",
                self._payload(external_user_name="ZD홍길동"),
                format="json",
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.post(
                "/",
                self._payload(
                    company_id=str(self.company_id),
                    fleet_id=str(other_fleet_id),
                    ev_id="EV-002",
                    name="Kim Driver 2",
                    external_user_name="ZD홍길동",
                ),
                format="json",
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.post(
                "/",
                self._payload(
                    company_id=str(other_company_id),
                    fleet_id=str(other_fleet_id),
                    ev_id="EV-003",
                    name="Kim Driver 3",
                    external_user_name="ZD홍길동",
                ),
                format="json",
            ).status_code,
            201,
        )

        response = self.client.get(
            "/",
            {
                "external_user_name": "ZD홍길동",
                "company_id": str(self.company_id),
                "fleet_id": str(self.fleet_id),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["fleet_id"], str(self.fleet_id))

    def test_driver_list_returns_paginated_shape_when_page_params_are_present(self):
        self._authenticate(self.user_token)
        for index in range(12):
            response = self.client.post(
                "/",
                self._payload(
                    name=f"Driver {index + 1}",
                    ev_id=f"EV-{index + 1:03d}",
                    external_user_name=f"ZD기사{index + 1}",
                ),
                format="json",
            )
            self.assertEqual(response.status_code, 201)

        response = self.client.get("/", {"page": 2, "page_size": 10})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(response.data["page"], 2)
        self.assertEqual(response.data["page_size"], 10)
        self.assertEqual(len(response.data["results"]), 2)

    def test_ensure_external_users_creates_missing_profiles_for_scope(self):
        self._authenticate(self.user_token)
        existing_response = self.client.post(
            "/",
            self._payload(external_user_name="ZD기존기사"),
            format="json",
        )
        self.assertEqual(existing_response.status_code, 201)

        response = self.client.post(
            "/ensure-external-users/",
            {
                "company_id": str(self.company_id),
                "fleet_id": str(self.fleet_id),
                "external_user_names": ["ZD기존기사", "ZD신규기사"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["created_external_user_names"], ["ZD신규기사"])
        self.assertEqual(response.data["existing_external_user_names"], ["ZD기존기사"])
        self.assertEqual(len(response.data["drivers"]), 2)
        created_driver = next(
            driver for driver in response.data["drivers"] if driver["external_user_name"] == "ZD신규기사"
        )
        self.assertEqual(created_driver["name"], "신규기사")
        self.assertEqual(created_driver["ev_id"], "")
        self.assertEqual(created_driver["phone_number"], "")
        self.assertEqual(created_driver["address"], "")

    def test_ensure_external_users_falls_back_to_original_name_when_hangul_is_missing(self):
        self._authenticate(self.user_token)

        response = self.client.post(
            "/ensure-external-users/",
            {
                "company_id": str(self.company_id),
                "fleet_id": str(self.fleet_id),
                "external_user_names": ["KOKUSHIBO"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        created_driver = next(
            driver for driver in response.data["drivers"] if driver["external_user_name"] == "KOKUSHIBO"
        )
        self.assertEqual(created_driver["name"], "KOKUSHIBO")

    def test_ensure_external_users_returns_contextual_invalid_request_message(self):
        self._authenticate(self.user_token)

        response = self.client.post(
            "/ensure-external-users/",
            {
                "company_id": str(self.company_id),
                "fleet_id": str(self.fleet_id),
                "external_user_names": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "invalid_request")
        self.assertEqual(
            response.data["message"],
            "Driver auto-create requires company_id, fleet_id, and at least one external_user_name.",
        )
        self.assertIn("external_user_names", response.data["details"])

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
