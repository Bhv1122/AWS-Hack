import urllib.request
import urllib.error
import json
import sys

BASE = "http://127.0.0.1:5000"

def post_json(path, data, headers=None):
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as he:
        try:
            return he.code, json.loads(he.read().decode("utf-8"))
        except Exception:
            return he.code, {"raw": he.read().decode("utf-8")}
    except Exception as e:
        return 0, {"error": str(e)}

def get_json(path, headers=None):
    hdrs = {}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(f"{BASE}{path}", headers=hdrs, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as he:
        try:
            return he.code, json.loads(he.read().decode("utf-8"))
        except Exception:
            return he.code, {"raw": he.read().decode("utf-8")}
    except Exception as e:
        return 0, {"error": str(e)}

def main():
    print("================================================================")
    print("STEP 1: DEBUG UNLOCK SCRIPT (Without UI)")
    print("================================================================")

    # 1. Log in as patient (PAT-SS-1001) and capture live consentPin
    print("\n--- 1. Login as Patient (PAT-SS-1001) ---")
    status, p_body = post_json("/api/auth/login-patient", {
        "identifier": "PAT-SS-1001",
        "password": "Password@123"
    })
    print(f"Status: {status}")
    print(f"Body: {json.dumps(p_body, indent=2)}")
    live_pin = p_body.get("consentPin")
    print(f"Captured Live PIN: {live_pin}")

    # 2. Log in as doctor (DOC-IN-8841) with 4 verification fields + OTP 654321
    print("\n--- 2. Login as Doctor (DOC-IN-8841) ---")
    status, d_body = post_json("/api/auth/login-doctor", {
        "identifier": "DOC-IN-8841",
        "doctor_id": "DOC-IN-8841",
        "password": "Password@123",
        "license_number": "KMC-2019-88412",
        "hospital_code": "HOSP-BLR-990",
        "gov_id_last4": "8841",
        "mfa_otp": "654321"
    })
    print(f"Status: {status}")
    print(f"Body: {json.dumps(d_body, indent=2)}")
    doc_token = d_body.get("sessionToken") or d_body.get("token")
    print(f"Captured Doctor Session Token: {doc_token}")

    auth_headers = {
        "Authorization": f"Bearer {doc_token}",
        "x-doctor-id": "DOC-IN-8841",
        "x-user-role": "DOCTOR"
    }

    # 3. POST /api/auth/lookup-patient with consentPin
    print("\n--- 3. Lookup Patient with Consent PIN ---")
    lookup_payload = {
        "doctorId": "DOC-IN-8841",
        "patientId": "PAT-SS-1001",
        "consentPin": str(live_pin),
        "emergencyBreakGlass": False
    }
    status, l_body = post_json("/api/auth/lookup-patient", lookup_payload, headers=auth_headers)
    print(f"Status: {status}")
    print(f"Body: {json.dumps(l_body, indent=2)}")

    # 4. Call endpoints doctor screen uses after unlock
    print("\n--- 4. Calling Doctor Workstation Post-Unlock Endpoints ---")
    endpoints_to_test = [
        "/api/profile?patientId=PAT-SS-1001",
        "/api/profile?patient_id=PAT-SS-1001",
        "/api/doctor/patients/PAT-SS-1001",
        "/api/reports?patientId=PAT-SS-1001",
        "/api/trends?patientId=PAT-SS-1001&metric=HbA1c",
        "/api/consent/status?patientId=PAT-SS-1001",
        "/api/audit?patientId=PAT-SS-1001",
        "/api/patient/PAT-SS-1001/timeline?limit=30"
    ]

    for ep in endpoints_to_test:
        st, b = get_json(ep, headers=auth_headers)
        print(f"\n[ENDPOINT] GET {ep}")
        print(f"Status: {st}")
        # print truncated body
        b_str = json.dumps(b)
        if len(b_str) > 200:
            print(f"Body: {b_str[:200]}... (len: {len(b_str)})")
        else:
            print(f"Body: {b_str}")

    # 5. Log in as the patient 3 more times and print the PIN each time. Does it change?
    print("\n--- 5. Patient Login PIN Churn Test (3 consecutive logins) ---")
    for i in range(1, 4):
        st, pb = post_json("/api/auth/login-patient", {
            "identifier": "PAT-SS-1001",
            "password": "Password@123"
        })
        pin_i = pb.get("consentPin")
        print(f"Login #{i}: Status={st}, consentPin={pin_i}")

if __name__ == "__main__":
    main()
