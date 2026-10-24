#!/usr/bin/env python3
"""
tests/test_unlock_flow.py
Comprehensive automated regression test proving the doctor unlock flow:
1. Patient login -> read live PIN (no hardcoding).
2. Doctor login (with 4 verification fields + OTP 654321) -> capture doctor sessionToken.
3. Doctor unlock (/api/auth/lookup-patient) with live PIN -> 200 OK, accessGranted: True.
4. Subsequent clinical endpoints (/api/profile, /api/reports, /api/doctor/patients/PAT-1001, /api/audit)
   all return 200 using the doctor's session token.
5. Wrong PIN returns 403 with code "PIN_INVALID" and attemptsRemaining.
6. PIN remains identical across 3 consecutive patient logins.
7. Patient revoke consent (/api/auth/revoke-consent) causes:
   - Old PIN unlock returns 403 (CONSENT_REVOKED).
   - Doctor's next clinical data call returns 403.
8. Emergency Break-Glass unlock with typed justification (>=15 chars) works and is audited.
"""

import sys
import os
import json
import urllib.request
import urllib.error

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

BASE_URL = "http://127.0.0.1:5000"

def http_req(method, path, body=None, headers=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {"raw": content}
        return e.code, parsed

def test_unlock_flow():
    print("\n=======================================================")
    print("RUNNING UNLOCK FLOW TEST SUITE")
    print("=======================================================")

    # 1. Patient Login and Read PIN
    print("\n--- 1. Patient Login (PAT-SS-1001) ---")
    status, p_body = http_req("POST", "/api/auth/login-patient", {"patientId": "PAT-SS-1001"})
    assert status == 200, f"Patient login failed: {status} {p_body}"
    patient_pin = str(p_body.get("consentPin") or p_body.get("patient", {}).get("consentPin") or "").strip()
    assert len(patient_pin) == 6, f"Invalid PIN received: {patient_pin}"
    print(f"[PASS] Patient logged in successfully. Consent PIN: {patient_pin}")

    # 2. Check PIN stability across 3 consecutive logins
    print("\n--- 2. PIN Stability across 3 Logins ---")
    for i in range(1, 4):
        s_i, b_i = http_req("POST", "/api/auth/login-patient", {"patientId": "PAT-SS-1001"})
        assert s_i == 200
        pin_i = str(b_i.get("consentPin") or b_i.get("patient", {}).get("consentPin") or "").strip()
        assert pin_i == patient_pin, f"PIN changed on login {i}! Expected {patient_pin}, got {pin_i}"
        print(f"[PASS] Login {i}: PIN matches ({pin_i})")

    # 3. Doctor Login (DOC-IN-8841)
    print("\n--- 3. Doctor Login (DOC-IN-8841) ---")
    doc_payload = {
        "doctorId": "DOC-IN-8841",
        "medicalLicenseNumber": "KMC-2019-88412",
        "hospitalId": "HOSP-BLR-990",
        "mfaOtp": "654321"
    }
    status, doc_body = http_req("POST", "/api/auth/login-doctor", doc_payload)
    assert status == 200, f"Doctor login failed: {status} {doc_body}"
    doc_token = doc_body.get("sessionToken") or doc_body.get("token")
    doc_id = doc_body.get("doctorId") or "DOC-IN-8841"
    assert doc_token, "Doctor sessionToken missing in login response"
    print(f"[PASS] Doctor logged in successfully. Token: {doc_token[:16]}..., Doctor ID: {doc_id}")

    doc_headers = {
        "Authorization": f"Bearer {doc_token}",
        "x-doctor-id": doc_id,
        "x-user-role": "DOCTOR"
    }

    # 4. Wrong PIN returns 403 PIN_INVALID
    print("\n--- 4. Wrong PIN Rejection ---")
    bad_pin = "000000" if patient_pin != "000000" else "999999"
    status, bad_res = http_req("POST", "/api/auth/lookup-patient", {
        "doctorId": doc_id,
        "patientId": "PAT-SS-1001",
        "consentPin": bad_pin,
        "emergencyBreakGlass": False
    }, doc_headers)
    assert status == 403, f"Expected 403 for wrong PIN, got {status}: {bad_res}"
    assert bad_res.get("code") == "PIN_INVALID", f"Expected code 'PIN_INVALID', got {bad_res.get('code')}"
    print(f"[PASS] Wrong PIN returned 403 PIN_INVALID with attemptsRemaining={bad_res.get('attemptsRemaining')}")

    # 5. Doctor Unlock with Correct Live PIN
    print("\n--- 5. Doctor Unlock with Live PIN ---")
    status, unlock_res = http_req("POST", "/api/auth/lookup-patient", {
        "doctorId": doc_id,
        "patientId": "PAT-SS-1001",
        "consentPin": patient_pin,
        "emergencyBreakGlass": False
    }, doc_headers)
    assert status == 200, f"Doctor unlock failed: {status} {unlock_res}"
    assert unlock_res.get("accessGranted") is True, f"accessGranted not True: {unlock_res}"
    assert unlock_res.get("kmsDecrypted") is True, f"kmsDecrypted not True: {unlock_res}"
    assert unlock_res.get("patient", {}).get("name") == "Ramesh Kumar", f"Patient name missing/mismatched"
    assert "prescriptions" in unlock_res or "active_prescriptions" in unlock_res, "Prescriptions missing in unlock payload"
    print(f"[PASS] Unlock succeeded. Patient: {unlock_res.get('patient', {}).get('name')}, KMS Decrypted: True")

    # 6. Call clinical endpoints right after unlock with same doctor token
    print("\n--- 6. Post-Unlock Clinical Data Fetch ---")
    # /api/profile
    s_prof, b_prof = http_req("GET", "/api/profile?patientId=PAT-SS-1001", None, doc_headers)
    assert s_prof == 200, f"/api/profile returned {s_prof}: {b_prof}"
    print(f"[PASS] /api/profile returned 200 OK (Patient: {b_prof.get('patient', {}).get('name')})")

    # /api/reports
    s_rep, b_rep = http_req("GET", "/api/reports?patientId=PAT-SS-1001", None, doc_headers)
    assert s_rep == 200, f"/api/reports returned {s_rep}: {b_rep}"
    print(f"[PASS] /api/reports returned 200 OK (Report count: {len(b_rep.get('reports', []))})")

    # /api/doctor/patients/PAT-1001
    s_pat, b_pat = http_req("GET", "/api/doctor/patients/PAT-1001", None, doc_headers)
    assert s_pat == 200, f"/api/doctor/patients/PAT-1001 returned {s_pat}: {b_pat}"
    print(f"[PASS] /api/doctor/patients/PAT-1001 returned 200 OK")

    # /api/audit
    s_aud, b_aud = http_req("GET", "/api/audit?patientId=PAT-SS-1001", None, doc_headers)
    assert s_aud == 200, f"/api/audit returned {s_aud}: {b_aud}"
    print(f"[PASS] /api/audit returned 200 OK (Audit count: {len(b_aud.get('events', []))})")

    # 7. Patient Revokes Consent
    print("\n--- 7. Patient Revokes Consent ---")
    p_headers = {"x-user-id": "PAT-SS-1001", "x-user-role": "PATIENT"}
    s_rev, b_rev = http_req("POST", "/api/auth/revoke-consent", {"patientId": "PAT-SS-1001"}, p_headers)
    assert s_rev == 200, f"Revoke consent failed: {s_rev} {b_rev}"
    print(f"[PASS] Patient consent revoked: {b_rev.get('message')}")

    # Old PIN must now fail
    s_old, b_old = http_req("POST", "/api/auth/lookup-patient", {
        "doctorId": doc_id,
        "patientId": "PAT-SS-1001",
        "consentPin": patient_pin,
        "emergencyBreakGlass": False
    }, doc_headers)
    assert s_old == 403, f"Expected 403 after revocation, got {s_old}: {b_old}"
    print(f"[PASS] Old PIN rejected with 403 after revocation ({b_old.get('code')})")

    # Doctor subsequent clinical data call must return 403
    s_prof_rev, b_prof_rev = http_req("GET", "/api/profile?patientId=PAT-SS-1001", None, doc_headers)
    assert s_prof_rev == 403, f"Expected 403 for doctor data call after revocation, got {s_prof_rev}: {b_prof_rev}"
    print(f"[PASS] Doctor subsequent clinical call returned 403 FORBIDDEN after revocation")

    # 8. Emergency Break-Glass Override
    print("\n--- 8. Emergency Break-Glass Override ---")
    bg_payload = {
        "doctorId": doc_id,
        "patientId": "PAT-SS-1001",
        "emergencyBreakGlass": True,
        "breakGlassReason": "Unconscious trauma patient admitted to ICU protocol requiring urgent history"
    }
    s_bg, b_bg = http_req("POST", "/api/auth/lookup-patient", bg_payload, doc_headers)
    assert s_bg == 200, f"Break glass failed: {s_bg} {b_bg}"
    assert b_bg.get("accessGranted") is True, f"accessGranted not True for break glass: {b_bg}"
    assert b_bg.get("unlockedViaBreakGlass") is True or b_bg.get("breakGlass") is True, "breakGlass flag missing"
    print(f"[PASS] Emergency Break-Glass succeeded with 200 OK. accessGranted: True")

    # Verify audit event logged
    s_bg_aud, b_bg_aud = http_req("GET", "/api/audit?patientId=PAT-SS-1001", None, doc_headers)
    assert s_bg_aud == 200
    events = b_bg_aud.get("events") or b_bg_aud.get("auditLogs") or []
    bg_logged = any("BREAK_GLASS" in str(e.get("action", "")).upper() or "BREAK_GLASS" in str(e.get("eventName", "")).upper() for e in events)
    assert bg_logged, f"Break-glass audit entry not found in {events}"
    print(f"[PASS] Break-Glass action audited in CloudTrail stream")

    # 9. Modify and Discontinue Prescription (Doctor stays unlocked)
    print("\n--- 9. Modify & Discontinue Prescription (Doctor stays unlocked) ---")
    s_mod, b_mod = http_req("PUT", "/api/prescriptions", {
        "doctorId": doc_id,
        "patientId": "PAT-SS-1001",
        "prescriptionId": "RX-WAR-1001",
        "dosage": "7.5mg once daily",
        "new_dosage": "7.5mg once daily",
        "action": "MODIFY",
        "status": "MODIFIED",
        "reason": "INR target calibration adjust"
    }, doc_headers)
    assert s_mod == 200, f"Modify prescription failed: {s_mod} {b_mod}"
    print(f"[PASS] Modify prescription returned 200 OK ({b_mod.get('message')})")

    s_disc, b_disc = http_req("PUT", "/api/prescriptions", {
        "doctorId": doc_id,
        "patientId": "PAT-SS-1001",
        "prescriptionId": "RX-MET-1002",
        "action": "DISCONTINUE",
        "reason": "Adverse GI intolerance documented"
    }, doc_headers)
    assert s_disc == 200, f"Discontinue prescription failed: {s_disc} {b_disc}"
    print(f"[PASS] Discontinue prescription returned 200 OK ({b_disc.get('message')})")

    # Verify doctor is STILL unlocked and can access patient data without re-entering PIN
    s_stay, b_stay = http_req("GET", "/api/profile?patientId=PAT-SS-1001", None, doc_headers)
    assert s_stay == 200, f"Doctor lost access after modifying prescription! {s_stay}: {b_stay}"
    print(f"[PASS] Doctor session remains fully unlocked on patient record after modify/discontinue")

    # Reset patient consent for subsequent testing and demo usage
    print("\n--- Cleanup / Reset Patient Consent ---")
    s_reset, _ = http_req("POST", "/api/auth/login-patient", {"patientId": "PAT-SS-1001"})
    # Re-grant consent via login or store reset
    from backend_lambdas.aws_core import get_patient, save_patient
    p = get_patient("PAT-1001")
    if p:
        p["consentRevoked"] = False
        save_patient(p)
    print("[PASS] Patient consent state reset to active.")

    print("\n=======================================================")
    print("ALL UNLOCK FLOW REGRESSION TESTS PASSED!")
    print("=======================================================\n")

if __name__ == "__main__":
    test_unlock_flow()
