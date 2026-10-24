"""
measure_baseline_flow.py - Part A1 Baseline Measurement
Executes: Doctor Login -> Patient Lookup -> Profile -> Modify Prescription
Records round-trip and server timing in milliseconds per step.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.error

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend_lambdas.aws_core import get_patient, local_store

BASE_URL = "http://127.0.0.1:5000"

def http_json(endpoint, method="GET", body=None, headers=None):
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(body).encode("utf-8") if body else None
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            server_time = resp.headers.get("X-Response-Time-Ms")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = {"raw": raw}
            return {
                "status": resp.status,
                "elapsed_ms": elapsed_ms,
                "server_time_ms": float(server_time) if server_time else elapsed_ms,
                "data": parsed
            }
    except urllib.error.HTTPError as e:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        raw = e.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}
        return {
            "status": e.code,
            "elapsed_ms": elapsed_ms,
            "server_time_ms": elapsed_ms,
            "data": parsed
        }

def get_current_pin(pid="PAT-SS-1001"):
    local_store.reload()
    norm_id = "PAT-1001" if pid in ("PAT-1001", "PAT-SS-1001") else pid
    p = get_patient(norm_id) or get_patient(pid)
    if p:
        return p.get("consentPin") or p.get("activeConsentPin") or "482910"
    return "482910"

def main():
    print("=" * 60)
    print("PART A1: MEASURING BASELINE FLOW (WITHOUT OPTIMIZATIONS)")
    print("=" * 60)

    results = {}

    # 1. Doctor Login
    print("\n[Step 1] Doctor Login (DOC-IN-8841)...")
    res_login = http_json("/api/auth/login-doctor", method="POST", body={
        "identifier": "DOC-IN-8841",
        "password": "Doctor@123",
        "mfa_otp": "654321"
    })
    token = res_login["data"].get("sessionToken") or res_login["data"].get("token") or "TOKEN-DOC-DOC-IN-8841-default"
    print(f"  -> HTTP {res_login['status']} in {res_login['elapsed_ms']} ms (server: {res_login['server_time_ms']} ms)")
    results["1_doctor_login"] = res_login

    # 2. Patient Lookup (with PIN)
    current_pin = get_current_pin("PAT-SS-1001")
    print(f"\n[Step 2] Patient Lookup (PAT-SS-1001 with PIN {current_pin})...")
    res_lookup = http_json("/api/auth/lookup-patient", method="POST", body={
        "doctorId": "DOC-IN-8841",
        "patientId": "PAT-SS-1001",
        "consentPin": current_pin,
        "emergencyBreakGlass": False
    }, headers={"Authorization": f"Bearer {token}", "x-doctor-id": "DOC-IN-8841", "x-user-role": "DOCTOR"})
    print(f"  -> HTTP {res_lookup['status']} in {res_lookup['elapsed_ms']} ms (server: {res_lookup['server_time_ms']} ms)")
    results["2_lookup_patient"] = res_lookup

    # 3. Patient Profile
    print("\n[Step 3] Patient Profile (PAT-SS-1001)...")
    res_prof = http_json("/api/profile?patientId=PAT-SS-1001", method="GET", headers={
        "Authorization": f"Bearer {token}",
        "x-doctor-id": "DOC-IN-8841",
        "x-user-role": "DOCTOR"
    })
    print(f"  -> HTTP {res_prof['status']} in {res_prof['elapsed_ms']} ms (server: {res_prof['server_time_ms']} ms)")
    results["3_patient_profile"] = res_prof

    # Get an existing prescription ID
    rx_list = res_prof["data"].get("prescriptions") or res_prof["data"].get("active_prescriptions") or []
    rx_id = rx_list[0].get("prescriptionId") if rx_list else "RX-101"

    # 4. Modify Prescription Dosage
    print(f"\n[Step 4] Modify Prescription ({rx_id} -> 100mg)...")
    res_mod = http_json("/api/prescriptions", method="PUT", body={
        "doctorId": "DOC-IN-8841",
        "patientId": "PAT-SS-1001",
        "prescriptionId": rx_id,
        "dosage": "100mg once daily",
        "new_dosage": "100mg once daily",
        "action": "MODIFY",
        "status": "MODIFIED",
        "reason": "Baseline profiling test dose adjust"
    }, headers={"Authorization": f"Bearer {token}", "x-doctor-id": "DOC-IN-8841", "x-user-role": "DOCTOR"})
    print(f"  -> HTTP {res_mod['status']} in {res_mod['elapsed_ms']} ms (server: {res_mod['server_time_ms']} ms)")
    results["4_modify_prescription"] = res_mod

    # 5. Fetch Server-Side Slowest Steps
    print("\n[Step 5] Querying Server-Side Slowest Steps...")
    res_perf = http_json("/api/perf/report", method="GET")
    slowest_steps = res_perf["data"].get("slowest_steps", [])
    print(f"  -> Collected {len(slowest_steps)} recorded substeps.")

    print("\n" + "=" * 60)
    print("BASELINE FLOW TIMING SUMMARY (ROUND TRIP):")
    print(f"  1. Doctor Login:        {results['1_doctor_login']['elapsed_ms']:>8.2f} ms (HTTP {results['1_doctor_login']['status']})")
    print(f"  2. Lookup Patient (PIN):{results['2_lookup_patient']['elapsed_ms']:>8.2f} ms (HTTP {results['2_lookup_patient']['status']})")
    print(f"  3. Patient Profile:     {results['3_patient_profile']['elapsed_ms']:>8.2f} ms (HTTP {results['3_patient_profile']['status']})")
    print(f"  4. Modify Prescription: {results['4_modify_prescription']['elapsed_ms']:>8.2f} ms (HTTP {results['4_modify_prescription']['status']})")
    total_flow_ms = sum(r['elapsed_ms'] for r in results.values())
    print(f"  TOTAL FLOW TIME:        {total_flow_ms:>8.2f} ms")
    print("=" * 60)

    print("\nTOP 10 SLOWEST SUBSTEPS RECORDED:")
    for i, s in enumerate(slowest_steps[:10], 1):
        print(f"  {i:>2}. {s.get('step', 'unknown'):<35} : {s.get('elapsed_ms', 0):>8.2f} ms")
    print("=" * 60)

    # Save to a temporary JSON for report generator
    with open("tests/baseline_perf.json", "w", encoding="utf-8") as f:
        json.dump({
            "results": {k: {"status": v["status"], "elapsed_ms": v["elapsed_ms"]} for k, v in results.items()},
            "slowest_steps": slowest_steps[:10],
            "total_flow_ms": total_flow_ms
        }, f, indent=2)

if __name__ == "__main__":
    main()
