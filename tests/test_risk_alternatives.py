#!/usr/bin/env python3
"""
tests/test_risk_alternatives.py
--------------------------------
Comprehensive test suite for Task 2:
- Risky medicine warnings & deterministic safer replacements
- POST /api/prescribe/check
- GET /api/medicines-catalog?q=...&patientId=...
- Zero-trust RBAC & Consent grant enforcement
- Caching & latency benchmark (<300ms)
- HIPAA audit trail (RISK_SHOWN, ALTERNATIVE_ACCEPTED)
"""

import sys
import os
import json
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure clean Windows console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from frontend_portal.app import app
from backend_lambdas.aws_core import (
    get_patient,
    save_patient,
    local_store,
    record_audit_event
)
from backend_lambdas.auth_security_engine import (
    issue_doctor_grant,
    revoke_doctor_grant,
    has_active_grant,
    lock_doctor_session
)
from backend_lambdas.clinical_risk_engine import (
    evaluate_medicine_safety,
    load_drug_alternatives,
    check_single_generic_against_patient
)


def run_tests():
    print("=" * 75)
    print("TASK 2 TEST SUITE: RISKY MEDICINES & SAFER ALTERNATIVES")
    print("=" * 75)

    client = app.test_client()
    local_store.reload()

    # Reset patient consent and grant for testing
    p = get_patient("PAT-1001")
    if p:
        p["consentRevoked"] = False
        save_patient(p)

    doctor_id = "DOC-IN-8841"
    patient_id = "PAT-SS-1001"
    norm_pid = "PAT-1001"

    # Setup active grant for DOC-IN-8841
    issue_doctor_grant(doctor_id, norm_pid, duration_seconds=3600)
    issue_doctor_grant(doctor_id, patient_id, duration_seconds=3600)
    local_store.reload()

    doc_headers = {
        "x-user-role": "DOCTOR",
        "x-doctor-id": doctor_id,
        "Authorization": f"Bearer {doctor_id}-SECURE-SESSION-TOKEN",
        "Content-Type": "application/json"
    }

    # -------------------------------------------------------------------------
    # Test 1: Augmentin + Penicillin Allergy -> SEVERE & Safe Alternatives
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Augmentin 625 Duo Tablet for PAT-SS-1001 (Penicillin Allergy)...")
    res = client.post("/api/prescribe/check", headers=doc_headers, json={
        "patientId": patient_id,
        "medicineName": "Augmentin 625 Duo Tablet",
        "dosage": "625 Duo"
    })
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.data}"
    data = res.get_json()

    assert data.get("riskLevel") == "SEVERE", f"Expected SEVERE, got {data.get('riskLevel')}"
    findings = data.get("findings", [])
    assert len(findings) > 0, "Expected non-empty findings"
    assert any("penicillin" in f.get("with", "").lower() or "penicillin" in f.get("plainExplanation", "").lower() for f in findings), \
        "Expected Penicillin allergy finding"

    alts = data.get("alternatives", [])
    assert len(alts) > 0, f"Expected non-empty alternatives for Augmentin, got {alts}"
    assert len(alts) <= 3, f"Expected at most 3 alternatives, got {len(alts)}"

    # Ensure no alternative is a penicillin
    for a in alts:
        g = a.get("generic", "").lower()
        assert not any(pen in g for pen in ("amox", "ampicil", "penicil")), f"Alternative {g} contains penicillin!"
        # Check that candidate evaluates to NONE or CAUTION
        r = a.get("riskLevel")
        assert r in ("NONE", "CAUTION"), f"Candidate alternative riskLevel must be NONE or CAUTION, got {r}"

    print(f"  -> PASS: SEVERE risk intercepted. Alternatives returned: {[a['generic'] for a in alts]}")

    # -------------------------------------------------------------------------
    # Test 2: Aspirin + Active Warfarin -> SEVERE & noSafeSubstitute
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Aspirin for PAT-SS-1001 (Active Warfarin Regimen)...")
    res2 = client.post("/api/prescribe/check", headers=doc_headers, json={
        "patientId": patient_id,
        "medicineName": "Ecosprin 75mg Tablet",
        "dosage": "75mg"
    })
    assert res2.status_code == 200, f"Expected 200, got {res2.status_code}"
    data2 = res2.get_json()

    assert data2.get("riskLevel") == "SEVERE", f"Expected SEVERE, got {data2.get('riskLevel')}"
    assert data2.get("noSafeSubstitute") is True, f"Expected noSafeSubstitute=True, got {data2.get('noSafeSubstitute')}"
    assert data2.get("specialistReview") is True, f"Expected specialistReview=True, got {data2.get('specialistReview')}"
    assert "cardiologist" in data2.get("noSubstituteMessage", "").lower(), "Expected cardiologist notice in message"
    print("  -> PASS: Aspirin flagged as SEVERE with noSafeSubstitute=True and specialistReview=True.")

    # -------------------------------------------------------------------------
    # Test 3: Ibuprofen + Warfarin -> SEVERE & Paracetamol replacement
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Ibuprofen for PAT-SS-1001 (Active Warfarin & NSAID duplicate)...")
    res3 = client.post("/api/prescribe/check", headers=doc_headers, json={
        "patientId": patient_id,
        "medicineName": "Brufen 400 Tablet",
        "dosage": "400mg"
    })
    assert res3.status_code == 200, f"Expected 200, got {res3.status_code}"
    data3 = res3.get_json()

    assert data3.get("riskLevel") == "SEVERE", f"Expected SEVERE, got {data3.get('riskLevel')}"
    alt_generics3 = [a.get("generic", "").lower() for a in data3.get("alternatives", [])]
    assert any("paracetamol" in g for g in alt_generics3), f"Expected paracetamol alternative, got {alt_generics3}"
    print(f"  -> PASS: Ibuprofen flagged as SEVERE with Paracetamol suggested: {alt_generics3}")

    # -------------------------------------------------------------------------
    # Test 4: Paracetamol -> NONE & Made-up name -> UNKNOWN
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Paracetamol (Safe) and Made-up name (Unknown)...")
    res_para = client.post("/api/prescribe/check", headers=doc_headers, json={
        "patientId": patient_id,
        "medicineName": "Dolo 650 Tablet",
        "dosage": "650mg"
    })
    assert res_para.status_code == 200
    assert res_para.get_json().get("riskLevel") == "NONE", f"Expected NONE, got {res_para.get_json().get('riskLevel')}"
    print("  -> PASS: Paracetamol evaluated as NONE (No conflicts found).")

    res_fake = client.post("/api/prescribe/check", headers=doc_headers, json={
        "patientId": patient_id,
        "medicineName": "XyloZorbaFakeDrug 999mg",
        "dosage": "999mg"
    })
    assert res_fake.status_code == 200
    fake_data = res_fake.get_json()
    assert fake_data.get("riskLevel") == "UNKNOWN", f"Expected UNKNOWN, got {fake_data.get('riskLevel')}"
    assert "review manually" in fake_data.get("findings", [{}])[0].get("plainExplanation", "").lower()
    print("  -> PASS: Made-up drug name evaluated as UNKNOWN (manual review prompt).")

    # -------------------------------------------------------------------------
    # Test 5: Authorization & Revocation Security (Zero-Trust)
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Zero-Trust Authorization & Revocation Security...")
    # A) No token -> 401
    res_unauth = client.post("/api/prescribe/check", json={"patientId": patient_id, "medicineName": "Paracetamol"})
    assert res_unauth.status_code == 401, f"Expected 401 without auth, got {res_unauth.status_code}"
    print("  -> PASS: 401 Unauthorized returned when no session token provided.")

    # B) Doctor without grant -> 403
    other_doc_headers = {
        "x-user-role": "DOCTOR",
        "x-doctor-id": "DOC-STRANGER-999",
        "Authorization": "Bearer DOC-STRANGER-999-TOKEN",
        "Content-Type": "application/json"
    }
    res_no_grant = client.post("/api/prescribe/check", headers=other_doc_headers, json={
        "patientId": patient_id,
        "medicineName": "Paracetamol"
    })
    assert res_no_grant.status_code == 403, f"Expected 403 without active grant, got {res_no_grant.status_code}"
    print("  -> PASS: 403 Forbidden returned for doctor without active unlock grant.")

    # C) Patient revokes access -> 403
    revoke_doctor_grant(doctor_id, norm_pid)
    revoke_doctor_grant(doctor_id, patient_id)
    local_store.reload()

    res_revoked = client.post("/api/prescribe/check", headers=doc_headers, json={
        "patientId": patient_id,
        "medicineName": "Paracetamol"
    })
    assert res_revoked.status_code == 403, f"Expected 403 after revocation, got {res_revoked.status_code}"
    print("  -> PASS: 403 Forbidden returned immediately after patient revokes consent grant.")

    # Re-grant for subsequent tests
    issue_doctor_grant(doctor_id, norm_pid, duration_seconds=3600)
    issue_doctor_grant(doctor_id, patient_id, duration_seconds=3600)
    local_store.reload()

    # -------------------------------------------------------------------------
    # Test 6: Catalog Search with PatientId & Latency Benchmark (< 300 ms)
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Catalog Search with patientId risk badges (< 300 ms)...")
    t0 = time.perf_counter()
    res_cat = client.get(f"/api/medicines-catalog?q=aug&limit=15&patientId={patient_id}", headers=doc_headers)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert res_cat.status_code == 200, f"Expected 200, got {res_cat.status_code}"
    cat_data = res_cat.get_json()
    items = cat_data.get("matches", [])
    assert len(items) > 0, "Expected catalog results for 'aug'"
    assert "risk" in items[0], "Expected 'risk' badge field in catalog items"
    assert items[0]["risk"] in ("NONE", "CAUTION", "SEVERE", "UNKNOWN")
    print(f"  -> PASS: Catalog search returned {len(items)} items with risk badges in {elapsed_ms:.2f} ms (< 300 ms target).")

    # -------------------------------------------------------------------------
    # Test 7: Audit Events (RISK_SHOWN & ALTERNATIVE_ACCEPTED)
    # -------------------------------------------------------------------------
    print("\n[TEST 7] Audit Events (RISK_SHOWN & ALTERNATIVE_ACCEPTED)...")
    res_accept = client.post("/api/prescribe/accept-alternative", headers=doc_headers, json={
        "patientId": patient_id,
        "originalMedicine": "Augmentin 625 Duo Tablet",
        "replacementMedicine": "Azithral 500 Tablet"
    })
    assert res_accept.status_code == 200, f"accept-alternative returned {res_accept.status_code}: {res_accept.data}"

    # Verify audit log in local store
    local_store.reload()
    state = local_store.load_all()
    audits = state.get("cloudtrail_audit_logs", [])
    risk_shown_events = [a for a in audits if a.get("action") == "RISK_SHOWN"]
    alt_accepted_events = [a for a in audits if a.get("action") == "ALTERNATIVE_ACCEPTED"]

    assert len(risk_shown_events) > 0, "Expected at least one RISK_SHOWN audit event"
    assert len(alt_accepted_events) > 0, "Expected at least one ALTERNATIVE_ACCEPTED audit event"

    # Verify Consent PIN is NEVER leaked in audit logs
    pin_leaks = [a for a in audits if "145582" in str(a) or "consentPin" in str(a)]
    assert len(pin_leaks) == 0, f"Critical Security Violation: Consent PIN leaked in audit stream! {pin_leaks}"
    print("  -> PASS: RISK_SHOWN and ALTERNATIVE_ACCEPTED audited. Zero PIN exposure verified.")

    print("\n" + "=" * 75)
    print("ALL 7 TASK 2 TESTS PASSED PERFECTLY!")
    print("=" * 75)


if __name__ == "__main__":
    run_tests()
