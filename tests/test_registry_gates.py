"""
Test Suite: tests/test_registry_gates.py
Validates every verification scenario in the Doctor Multi-Gate Verification Table:
1. Public Gate 1 live feedback (lookup_license)
2. Public hospital lookup (lookup_hospital)
3. Gate 1: LICENSE_NOT_FOUND (KMC-2024-00000)
4. Gate 1: LICENSE_SUSPENDED (KMC-2016-10233)
5. Gate 1: LICENSE_EXPIRED (TNMC-2011-45110)
6. Gate 1: ALREADY_REGISTERED (KMC-2019-88412 -> 409 with hint)
7. Gate 2: HOSPITAL_NOT_AFFILIATED (KMC-2018-55120 + HOSP-BLR-990)
8. Gate 3: GOVID_MISMATCH (KMC-2020-77341 + wrong govId)
9. Gate 4: MFA_INVALID (KMC-2021-66219 + wrong OTP)
10. VALID: Successful registration across all 4 gates (NMC-IND-55201, Odisha)
"""

import os
import sys
import json
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from frontend_portal.app import app
from backend_lambdas.registry_engine import lookup_license, lookup_hospital, verify_doctor_registration_4gates


class TestRegistryGates(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_public_license_lookup(self):
        """Live Gate 1 feedback returns maskedName and status without leaking full PII."""
        res = self.client.get("/api/registry/license/KMC-2019-88412")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("found"))
        self.assertEqual(data.get("status"), "ACTIVE")
        self.assertIn("A.", data.get("maskedName", ""))
        self.assertIn("*", data.get("maskedName", ""))

    def test_02_public_hospital_lookup(self):
        """Public hospital lookup confirms recognized hospital facilities."""
        res = self.client.get("/api/registry/hospital/HOSP-BLR-990")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("valid"))
        self.assertIn("Manipal", data.get("name", ""))

        res_bad = self.client.get("/api/registry/hospital/HOSP-UNKNOWN-999")
        self.assertEqual(res_bad.status_code, 404)

    def test_03_gate1_license_not_found(self):
        """Gate 1 fails with LICENSE_NOT_FOUND when license not in medical council registry."""
        res = self.client.post("/api/auth/register-doctor", json={
            "name": "Dr. Unknown",
            "licenseNumber": "KMC-2024-00000",
            "hospitalCode": "HOSP-BLR-990",
            "degree": "MBBS",
            "govIdProof": "0000",
            "mfaOtp": "654321"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data.get("code"), "LICENSE_NOT_FOUND")
        self.assertEqual(data.get("gate"), 1)

    def test_04_gate1_license_suspended(self):
        """Gate 1 fails with LICENSE_SUSPENDED for suspended medical licenses."""
        res = self.client.post("/api/auth/register-doctor", json={
            "name": "Dr. Vikram Rao",
            "licenseNumber": "KMC-2016-10233",
            "hospitalCode": "HOSP-BLR-102",
            "degree": "MBBS, MD",
            "govIdProof": "1023",
            "mfaOtp": "654321"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data.get("code"), "LICENSE_SUSPENDED")
        self.assertEqual(data.get("gate"), 1)

    def test_05_gate1_license_expired(self):
        """Gate 1 fails with LICENSE_EXPIRED for expired medical licenses."""
        res = self.client.post("/api/auth/register-doctor", json={
            "name": "Dr. Karthik Sundaram",
            "licenseNumber": "TNMC-2011-45110",
            "hospitalCode": "HOSP-CHN-501",
            "degree": "MBBS, MS",
            "govIdProof": "4511",
            "mfaOtp": "654321"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data.get("code"), "LICENSE_EXPIRED")
        self.assertEqual(data.get("gate"), 1)

    def test_06_gate1_already_registered(self):
        """Gate 1 returns 409 ALREADY_REGISTERED with a hint to sign in instead."""
        res = self.client.post("/api/auth/register-doctor", json={
            "name": "Dr. Ananya Sharma",
            "licenseNumber": "KMC-2019-88412",
            "hospitalCode": "HOSP-BLR-990",
            "degree": "MBBS, MD",
            "govIdProof": "4412",
            "mfaOtp": "654321"
        })
        self.assertEqual(res.status_code, 409)
        data = res.get_json()
        self.assertEqual(data.get("code"), "ALREADY_REGISTERED")
        self.assertEqual(data.get("gate"), 1)
        self.assertIn("Sign in instead", data.get("hint", ""))

    def test_07_gate2_hospital_not_affiliated(self):
        """Gate 2 fails with HOSPITAL_NOT_AFFILIATED when license is valid but not attached to hospital."""
        res = self.client.post("/api/auth/register-doctor", json={
            "name": "Dr. Sunita Patil",
            "licenseNumber": "KMC-2018-55120",
            "hospitalCode": "HOSP-BLR-990",  # Affiliated with HOSP-MYS-201, not BLR-990
            "degree": "MBBS, MD",
            "govIdProof": "5512",
            "mfaOtp": "654321"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data.get("code"), "HOSPITAL_NOT_AFFILIATED")
        self.assertEqual(data.get("gate"), 2)

    def test_08_gate3_govid_mismatch(self):
        """Gate 3 fails with GOVID_MISMATCH when govt ID last 4 do not match council record."""
        res = self.client.post("/api/auth/register-doctor", json={
            "name": "Dr. Arvind Bhat",
            "licenseNumber": "KMC-2020-77341",
            "hospitalCode": "HOSP-BLR-990",
            "degree": "MBBS, MD",
            "govIdProof": "9999",  # Council on file is 7734
            "mfaOtp": "654321"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data.get("code"), "GOVID_MISMATCH")
        self.assertEqual(data.get("gate"), 3)

    def test_09_gate4_mfa_invalid(self):
        """Gate 4 fails with MFA_INVALID (401) when OTP is invalid."""
        res = self.client.post("/api/auth/register-doctor", json={
            "name": "Dr. Priya Hegde",
            "licenseNumber": "KMC-2021-66219",
            "hospitalCode": "HOSP-BLR-990",
            "degree": "MBBS, DNB",
            "govIdProof": "6621",
            "mfaOtp": "000000"  # Valid demo OTP is 654321
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertEqual(data.get("code"), "MFA_INVALID")
        self.assertEqual(data.get("gate"), 4)

    def test_10_valid_registration_odisha(self):
        """All 4 gates pass: registers valid doctor (NMC-IND-55201, AIIMS Bhubaneswar)."""
        res = self.client.post("/api/auth/register-doctor", json={
            "name": "Dr. Debabrata Nayak",
            "licenseNumber": "NMC-IND-55201",
            "hospitalCode": "AIIMS-BBSR-101",
            "specialty": "Pulmonology",
            "degree": "MBBS, MD (Pulmonary Medicine)",
            "govIdProof": "5201",
            "mfaOtp": "654321"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("doctorId", "").startswith("DOC-IN-"))
        self.assertIn("Nayak", data.get("name", ""))


if __name__ == "__main__":
    unittest.main()
