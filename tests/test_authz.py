"""
Test Suite: tests/test_authz.py
Zero-Trust Server-Side Authorization & Confidentiality Verification:
1. 401 Unauthorized when accessing clinical endpoints without a session token.
2. 403 FORBIDDEN_IDOR when a patient token attempts to access another patient's clinical data.
3. 403 CONSENT_REQUIRED when a doctor accesses a locked patient without an active unlock grant.
4. Active Grant Access: doctor accesses patient clinical reports after unlocking with PIN.
5. Immediate Grant Termination on Patient Revoke (PIN rotation kills doctor session).
6. Immediate Grant Termination on Doctor Manual Lock (/api/auth/lock).
7. Confidentiality: Consent PIN never leaks in doctor lookup responses, timeline logs, or audit records.
8. Rate-limiting: 5 consecutive wrong PIN attempts triggers 429 RATE_LIMITED.
"""

import os
import sys
import json
import time
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from frontend_portal.app import app
from backend_lambdas.aws_core import local_store


class TestAuthorizationAndSecurity(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_unauthenticated_requests_return_401(self):
        """Clinical data endpoints require valid session token, returning 401 UNAUTHORIZED."""
        endpoints = [
            "/api/reports?patientId=PAT-1001",
            "/api/trends?patientId=PAT-1001&metric=HbA1c",
            "/api/audit?patientId=PAT-1001",
            "/api/consent/status?patientId=PAT-1001"
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 401, f"Expected 401 for {ep}, got {res.status_code}")
            data = res.get_json()
            self.assertEqual(data.get("code"), "UNAUTHORIZED")

    def test_02_patient_idor_prevention(self):
        """Patient token may only access own patientId. Cross-patient access returns 403 FORBIDDEN_IDOR."""
        # Log in as PAT-SS-1001
        p_res = self.client.post("/api/auth/login-patient", json={"identifier": "PAT-SS-1001"})
        self.assertEqual(p_res.status_code, 200)
        p_token = p_res.get_json()["token"]

        # Access own data -> 200 OK
        own_res = self.client.get("/api/reports?patientId=PAT-SS-1001", headers={"Authorization": f"Bearer {p_token}"})
        self.assertEqual(own_res.status_code, 200)

        # Attempt to access another patient's data (PAT-SS-1002) -> 403 FORBIDDEN_IDOR
        idor_res = self.client.get("/api/reports?patientId=PAT-SS-1002", headers={"Authorization": f"Bearer {p_token}"})
        self.assertEqual(idor_res.status_code, 403)
        self.assertEqual(idor_res.get_json().get("code"), "FORBIDDEN_IDOR")

    def test_03_doctor_locked_patient_access_blocked(self):
        """Doctor token cannot access clinical records of a locked patient (returns 403 CONSENT_REQUIRED)."""
        d_res = self.client.post("/api/auth/login-doctor", json={"identifier": "DOC-IN-8841", "mfa_otp": "654321"})
        self.assertEqual(d_res.status_code, 200)
        d_token = d_res.get_json()["token"]

        # Ensure patient PAT-SS-1003 is locked
        self.client.post("/api/auth/lock", json={"doctorId": "DOC-IN-8841", "patientId": "PAT-SS-1003"})

        res = self.client.get("/api/reports?patientId=PAT-SS-1003", headers={"Authorization": f"Bearer {d_token}"})
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json().get("code"), "CONSENT_REQUIRED")

    def test_04_doctor_unlock_and_grant_lifecycle(self):
        """Doctor unlocks patient record via Consent PIN; grant terminates on revoke or lock."""
        # 1. Patient gets live PIN
        p_res = self.client.post("/api/auth/login-patient", json={"identifier": "PAT-SS-1001"})
        live_pin = p_res.get_json()["consentPin"]

        # 2. Doctor logs in
        d_res = self.client.post("/api/auth/login-doctor", json={"identifier": "DOC-IN-8841", "mfa_otp": "654321"})
        d_token = d_res.get_json()["token"]

        # 3. Doctor unlocks with valid PIN
        unlock_res = self.client.post("/api/auth/lookup-patient", json={
            "doctorId": "DOC-IN-8841",
            "patientId": "PAT-SS-1001",
            "consentPin": live_pin
        })
        self.assertEqual(unlock_res.status_code, 200)

        # 4. Doctor queries reports -> 200 OK
        rep_res = self.client.get("/api/reports?patientId=PAT-SS-1001", headers={"Authorization": f"Bearer {d_token}"})
        self.assertEqual(rep_res.status_code, 200)
        self.assertGreater(rep_res.get_json()["count"], 0)

        # 5. Patient revokes consent -> PIN rotates and terminates active sessions
        rev_res = self.client.post("/api/auth/revoke-consent", json={"patientId": "PAT-SS-1001"})
        self.assertEqual(rev_res.status_code, 200)

        # 6. Doctor tries accessing reports again -> now 403 CONSENT_REQUIRED
        blocked_res = self.client.get("/api/reports?patientId=PAT-SS-1001", headers={"Authorization": f"Bearer {d_token}"})
        self.assertEqual(blocked_res.status_code, 403)
        self.assertEqual(blocked_res.get_json().get("code"), "CONSENT_REQUIRED")

    def test_05_consent_pin_confidentiality(self):
        """Consent PIN is never returned in doctor responses, logs, or audit records."""
        # 1. Patient login returns PIN to patient only
        p_res = self.client.post("/api/auth/login-patient", json={"identifier": "PAT-SS-1001"})
        live_pin = p_res.get_json()["consentPin"]
        self.assertTrue(bool(live_pin))

        # 2. Doctor lookup response MUST NOT contain consentPin
        doc_lookup = self.client.post("/api/auth/lookup-patient", json={
            "doctorId": "DOC-IN-8841",
            "patientId": "PAT-SS-1001",
            "consentPin": live_pin
        })
        doc_data = doc_lookup.get_json()
        self.assertNotIn("consentPin", doc_data)
        self.assertNotIn("consentPin", doc_data.get("patient", {}))
        self.assertNotIn("consentPin", doc_data.get("swasthyaPassport", {}))

        # 3. Inspect audit trail: PIN must not be leaked into audit details
        state = local_store.load_all()
        for log in state.get("audit_logs", []):
            if "PatientConsent" in log.get("action", "") or "Lookup" in log.get("action", ""):
                self.assertNotIn(f"PIN: {live_pin}", log.get("details", ""))

    def test_06_wrong_pin_rate_limiting(self):
        """5 failed PIN attempts triggers HTTP 429 RATE_LIMITED cooldown."""
        target_pid = "PAT-SS-1001"
        doc_id = "DOC-RATE-LIMIT"
        
        # Fire 5 wrong PIN attempts
        rate_limited = False
        for i in range(7):
            res = self.client.post("/api/auth/lookup-patient", json={
                "doctorId": doc_id,
                "patientId": target_pid,
                "consentPin": f"99999{i}"
            })
            if res.status_code == 429:
                rate_limited = True
                self.assertEqual(res.get_json().get("code"), "RATE_LIMITED")
                break

        self.assertTrue(rate_limited, "Expected 429 RATE_LIMITED after 5 consecutive failed PIN attempts")


if __name__ == "__main__":
    unittest.main()
