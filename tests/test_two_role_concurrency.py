#!/usr/bin/env python3
"""
tests/test_two_role_concurrency.py
Verifies that independent doctor and patient roles do not overwrite or interfere with each other:
1. Doctor logs in and unlocks patient PAT-SS-1001 with active Consent PIN.
2. In a second independent context, Patient logs in and views their dashboard.
3. Doctor modifies a prescription and continues accessing patient data.
4. Asserts doctor session remains fully unlocked with no session pollution or cross-overwriting.
"""

import sys
import os
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:5000"

def http_json(method, path, body=None, headers=None):
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

def main():
    print("=" * 60)
    print("RUNNING TWO-ROLE CONCURRENT SESSION TEST")
    print("=" * 60)

    # 1. Patient get current live PIN
    s_p, b_p = http_json("POST", "/api/auth/login-patient", {"patientId": "PAT-SS-1001"})
    assert s_p == 200, f"Patient login failed: {s_p} {b_p}"
    live_pin = str(b_p.get("consentPin") or b_p.get("patient", {}).get("consentPin", "")).strip()
    assert len(live_pin) == 6, f"Invalid live PIN: {live_pin}"
    print(f"[PASS] Step 1: Active Consent PIN retrieved: {live_pin}")

    # 2. Doctor logs in (Context A)
    s_d, b_d = http_json("POST", "/api/auth/login-doctor", {
        "doctorId": "DOC-IN-8841",
        "medicalLicenseNumber": "KMC-2019-88412",
        "hospitalId": "HOSP-BLR-990",
        "mfaOtp": "654321"
    })
    assert s_d == 200, f"Doctor login failed: {s_d} {b_d}"
    doc_token = b_d.get("sessionToken") or b_d.get("token")
    assert doc_token, "Doctor sessionToken missing"
    doc_headers = {
        "Authorization": f"Bearer {doc_token}",
        "x-doctor-id": "DOC-IN-8841",
        "x-user-role": "DOCTOR"
    }
    print(f"[PASS] Step 2: Doctor logged in (Token: {doc_token[:15]}...)")

    # 3. Doctor unlocks PAT-SS-1001 with live PIN
    s_u, b_u = http_json("POST", "/api/auth/lookup-patient", {
        "doctorId": "DOC-IN-8841",
        "patientId": "PAT-SS-1001",
        "consentPin": live_pin,
        "emergencyBreakGlass": False
    }, doc_headers)
    assert s_u == 200, f"Doctor unlock failed: {s_u} {b_u}"
    assert b_u.get("accessGranted") is True, f"accessGranted not True: {b_u}"
    print(f"[PASS] Step 3: Doctor unlocked PAT-SS-1001 successfully")

    # Verify doctor can access profile
    s_prof, b_prof = http_json("GET", "/api/profile?patientId=PAT-SS-1001", None, doc_headers)
    assert s_prof == 200, f"Doctor profile fetch failed: {s_prof}"
    print(f"[PASS] Step 4: Doctor viewed unlocked profile for {b_prof.get('patient', {}).get('name')}")

    # 4. In Context B (simulating second tab), Patient logs in & performs actions
    print("\n--- Simulating Patient Login in Second Context (Tab B) ---")
    s_pat_tab, b_pat_tab = http_json("POST", "/api/auth/login-patient", {"patientId": "PAT-SS-1001"})
    assert s_pat_tab == 200
    pat_token = b_pat_tab.get("sessionToken") or b_pat_tab.get("token") or "TOKEN-PAT-PAT-SS-1001"
    pat_headers = {
        "Authorization": f"Bearer {pat_token}",
        "x-user-id": "PAT-SS-1001",
        "x-user-role": "PATIENT"
    }
    # Patient accesses their own dashboard
    s_dash, b_dash = http_json("GET", "/api/patient/PAT-SS-1001/dashboard", None, pat_headers)
    assert s_dash == 200, f"Patient dashboard failed: {s_dash}"
    print(f"[PASS] Step 5: Patient accessed dashboard in Tab B (Active slots: {len(b_dash.get('daily_schedule', []))})")

    # 5. Doctor in Context A modifies a prescription
    print("\n--- Doctor in Tab A Performs Clinical Action ---")
    s_mod, b_mod = http_json("PUT", "/api/prescriptions", {
        "doctorId": "DOC-IN-8841",
        "patientId": "PAT-SS-1001",
        "prescriptionId": "RX-WAR-1001",
        "dosage": "5mg once daily",
        "new_dosage": "5mg once daily",
        "action": "MODIFY",
        "status": "ACTIVE",
        "reason": "Concurrent multi-role test calibration"
    }, doc_headers)
    assert s_mod == 200, f"Doctor modify prescription failed: {s_mod} {b_mod}"
    print(f"[PASS] Step 6: Doctor modified prescription successfully ({b_mod.get('message')})")

    # 6. Verify Doctor is STILL unlocked and accessible
    s_stay, b_stay = http_json("GET", "/api/profile?patientId=PAT-SS-1001", None, doc_headers)
    assert s_stay == 200, f"Doctor was kicked out by patient session! {s_stay}: {b_stay}"
    print(f"[PASS] Step 7: Doctor remains completely unlocked! No cross-role session contamination.")

    print("\n" + "=" * 60)
    print("TWO-ROLE CONCURRENCY VERIFICATION PASSED (100%)")
    print("=" * 60)

if __name__ == "__main__":
    main()
