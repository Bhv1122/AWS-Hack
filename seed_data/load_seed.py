"""
SwasthyaSetu & AWS Platform - Seed Data Loader
Phase 1 Deliverable: seed_data/load_seed.py
-----------------------------------------------------------------
Backs up backend_lambdas/local_state.json to backend_lambdas/local_state.backup.json,
then atomically writes the seed datasets into the unified state store.
Supports:
  --reset : Overwrites state completely from clean baseline + seed
  --aws   : Upserts into DynamoDB/S3 only if live AWS credentials exist
Idempotent.
"""

import os
import sys
import json
import shutil
import argparse
import copy
from pathlib import Path
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

SEED_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SEED_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend_lambdas"
STATE_FILE = BACKEND_DIR / "local_state.json"
BACKUP_FILE = BACKEND_DIR / "local_state.backup.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

DEMO_PASSWORD_HASH = generate_password_hash("Demo@123")


def load_json_file(filename: str):
    p = SEED_DIR / filename
    if not p.exists():
        raise FileNotFoundError(f"Missing required seed dataset: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def backup_local_state():
    if STATE_FILE.exists():
        shutil.copy2(STATE_FILE, BACKUP_FILE)
        print(f"Backed up {STATE_FILE.name} -> {BACKUP_FILE.name}")
    else:
        print(f"No existing {STATE_FILE.name} to backup; creating fresh state.")


def load_seed(reset: bool = False, to_aws: bool = False):
    backup_local_state()

    # Load all 15 datasets
    medical_councils = load_json_file("medical_councils.json")
    hospitals = load_json_file("hospitals.json")
    doctors_registry = load_json_file("doctors_registry.json")
    patients = load_json_file("patients.json")
    reports = load_json_file("reports.json")
    prescriptions_seed = load_json_file("prescriptions_seed.json")
    adherence_history = load_json_file("adherence_history.json")
    ocr_samples = load_json_file("ocr_samples.json")
    drug_interactions = load_json_file("drug_interactions.json")
    medicine_generics = load_json_file("medicine_generics.json")
    pharmacies = load_json_file("pharmacies.json")
    asha_workers = load_json_file("asha_workers.json")
    occupational_risk = load_json_file("occupational_risk.json")
    translation_phrasebook = load_json_file("translation_phrasebook.json")
    audit_seed = load_json_file("audit_seed.json")
    notifications_seed = load_json_file("notifications_seed.json")

    # Load existing state or init fresh
    state = {}
    if not reset and STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}

    state.setdefault("meta", {
        "version": "2.0.0",
        "platform": "SwasthyaSetu & AWS Medication Platform",
        "lastLoaded": datetime.now(timezone.utc).isoformat(),
        "kmsAlias": "alias/MedCoord-HIPAA-MasterKey",
        "demoMode": True
    })

    # Attach all custom datasets as first-class keys
    state["medical_councils"] = medical_councils
    state["hospitals"] = hospitals
    state["doctors_registry"] = doctors_registry
    state["patients_list"] = patients
    state["clinical_reports"] = reports
    state["prescriptions_seed"] = prescriptions_seed
    state["adherence_history"] = adherence_history
    state["ocr_presets"] = ocr_samples
    state["drug_interactions"] = drug_interactions
    state["medicine_generics"] = medicine_generics
    state["pharmacies"] = pharmacies
    state["asha_workers"] = asha_workers
    state["occupational_risk_matrix"] = occupational_risk
    state["translation_phrasebook"] = translation_phrasebook
    state["notifications_inbox"] = notifications_seed

    # Tables map
    tables = state.setdefault("tables", {})
    patients_table = tables.setdefault("PatientsTable", {})
    prescriptions_table = tables.setdefault("PrescriptionsTable", {})
    adherence_table = tables.setdefault("AdherenceScheduleTable", {})

    # Populate PatientsTable
    for p in patients:
        pid = p["patientId"]
        p_rx = prescriptions_seed.get(pid, [])
        p_reports = [r for r in reports if r["patientId"] == pid]
        
        patient_record = {
            "patientId": pid,
            "uniquePatientId": pid,
            "name": p["name"],
            "age": p["age"],
            "gender": p["gender"],
            "originState": p["originState"],
            "originDistrict": p.get("originDistrict", "Ganjam"),
            "currentLocation": p["currentLocation"],
            "preferredLanguage": p["preferredLanguage"],
            "occupation": p["occupation"],
            "exposureYears": p["exposureYears"],
            "allergies": p["allergies"],
            "comorbidities": p["comorbidities"],
            "abhaId": p["abhaId"],
            "contact": p["mobile"],
            "phoneNumber": p["mobile"],
            "caregiver": p.get("caregiver", {}),
            "linkedAshaWorker": p.get("linkedAshaWorker", "ASHA-OD-402"),
            "consentPin": p.get("consent", {}).get("pin", "482910"),
            "activePrescriptions": p_rx,
            "reports": p_reports,
            "qrPayload": {
                "patientId": pid,
                "abhaId": p["abhaId"],
                "patientName": p["name"],
                "age": p["age"],
                "originState": p["originState"],
                "currentLocation": p["currentLocation"],
                "preferredLanguage": p["preferredLanguage"],
                "kmsKeyAlias": "alias/MedCoord-HIPAA-MasterKey",
                "verifyUrl": f"/api/auth/qr-verify?patientId={pid}",
                "issuedAt": datetime.now(timezone.utc).isoformat()
            },
            "synthetic": True
        }
        patients_table[pid] = patient_record
        
        # Mirror PAT-SS-1001 to legacy PAT-1001 and PATIENT-001
        if pid == "PAT-SS-1001":
            legacy_p = dict(patient_record)
            legacy_p["patientId"] = "PAT-1001"
            patients_table["PAT-1001"] = legacy_p
            legacy_p2 = dict(patient_record)
            legacy_p2["patientId"] = "PATIENT-001"
            patients_table["PATIENT-001"] = legacy_p2

    # Populate PrescriptionsTable
    for pid, rx_list in prescriptions_seed.items():
        for rx in rx_list:
            rx_id = rx["prescriptionId"]
            prescriptions_table[rx_id] = rx
            prescriptions_table[f"{pid}#{rx_id}"] = rx
            if pid in ("PAT-SS-1001", "PAT-1001"):
                prescriptions_table[f"PAT-1001#{rx_id}"] = rx
                prescriptions_table[f"PAT-SS-1001#{rx_id}"] = rx

    # Populate AdherenceScheduleTable
    for pid, doses in adherence_history.items():
        for d in doses:
            dose_id = d["doseId"]
            adherence_table[dose_id] = d

    # Populate Cognito Users
    cognito_users = state.setdefault("cognito_users", {})
    
    # 1. Doctors from doctors_registry
    for d in doctors_registry:
        doc_id = d.get("doctorId")
        if d.get("registered") and doc_id:
            cognito_users[doc_id] = {
                "userId": doc_id,
                "username": doc_id.lower(),
                "name": d["fullName"],
                "role": "DOCTOR",
                "passwordHash": DEMO_PASSWORD_HASH,
                "licenseNumber": d["licenseNumber"],
                "hospitalAffiliation": d["hospitalCodes"][0] if d.get("hospitalCodes") else "HOSP-BLR-990",
                "hospitalCode": d["hospitalCodes"][0] if d.get("hospitalCodes") else "HOSP-BLR-990",
                "specialty": d["specialty"],
                "degree": d["degree"],
                "govIdLast4": d.get("govIdLast4", "4412"),
                "scopes": ["patient:read", "prescription:write", "prescription:modify", "clinical:override", "audit:read"],
                "synthetic": True
            }

    # Ensure DOC-201 and DOC-202 exist
    if "DOC-201" not in cognito_users:
        cognito_users["DOC-201"] = {
            "userId": "DOC-201",
            "username": "dr.jenkins",
            "name": "Dr. Sarah Jenkins, MD, FACC",
            "role": "DOCTOR",
            "passwordHash": DEMO_PASSWORD_HASH,
            "licenseNumber": "KMC-2015-20101",
            "hospitalAffiliation": "Manipal Hospital Heart Institute, Whitefield",
            "hospitalCode": "HOSP-BLR-990",
            "specialty": "Cardiology",
            "degree": "MBBS, MD, FACC",
            "scopes": ["patient:read", "prescription:write", "prescription:modify", "clinical:override", "audit:read"],
            "synthetic": True
        }
    if "DOC-202" not in cognito_users:
        cognito_users["DOC-202"] = {
            "userId": "DOC-202",
            "username": "dr.verma",
            "name": "Dr. Rajesh Verma, MD, DM",
            "role": "DOCTOR",
            "passwordHash": DEMO_PASSWORD_HASH,
            "licenseNumber": "KMC-2017-20202",
            "hospitalAffiliation": "Aster CMI Hospital, Hebbal",
            "hospitalCode": "HOSP-BLR-104",
            "specialty": "Diabetology",
            "degree": "MBBS, MD, DM",
            "scopes": ["patient:read", "prescription:write", "prescription:modify", "clinical:override", "audit:read"],
            "synthetic": True
        }

    # 2. Patients in cognito_users
    for p in patients:
        pid = p["patientId"]
        cognito_users[pid] = {
            "userId": pid,
            "username": pid.lower(),
            "name": p["name"],
            "role": "PATIENT",
            "passwordHash": DEMO_PASSWORD_HASH,
            "phoneNumber": p["mobile"],
            "abhaId": p["abhaId"],
            "scopes": ["patient:read", "adherence:log", "consent:manage", "pharmacy:reserve"],
            "synthetic": True
        }
    # Legacy aliases
    cognito_users["PAT-1001"] = dict(cognito_users.get("PAT-SS-1001", {}), userId="PAT-1001")
    cognito_users["PATIENT-001"] = dict(cognito_users.get("PAT-SS-1001", {}), userId="PATIENT-001")

    # 3. Caregivers
    cognito_users["CARE-301"] = {
        "userId": "CARE-301",
        "username": "sunita.care",
        "name": "Sunita Kumar",
        "role": "CAREGIVER",
        "passwordHash": DEMO_PASSWORD_HASH,
        "phoneNumber": "9000000002",
        "linkedPatientId": "PAT-SS-1001",
        "scopes": ["patient:read", "adherence:log"],
        "synthetic": True
    }

    # 4. Pharmacies in cognito_users & pharmacy_inventory
    pi = state.get("pharmacy_inventory")
    if not isinstance(pi, list):
        pi = []
        state["pharmacy_inventory"] = pi
    existing_pi_ids = {p.get("id") for p in pi if isinstance(p, dict)}
    for pharm in pharmacies:
        pharm_id = pharm["id"]
        if pharm_id not in existing_pi_ids:
            pi.append(copy.deepcopy(pharm))
            existing_pi_ids.add(pharm_id)
        cognito_users[pharm_id] = {
            "userId": pharm_id,
            "username": pharm_id.lower(),
            "name": pharm["name"],
            "role": "PHARMACY",
            "passwordHash": DEMO_PASSWORD_HASH,
            "phoneNumber": pharm["phone"],
            "scopes": ["pharmacy:dispense", "inventory:update"],
            "synthetic": True
        }

    # Audit Trail
    cloudtrail_audit_logs = state.setdefault("cloudtrail_audit_logs", [])
    existing_event_ids = {e.get("eventId") for e in cloudtrail_audit_logs}
    for a in audit_seed:
        if a.get("eventId") not in existing_event_ids:
            cloudtrail_audit_logs.append(a)
    state["audit_trail"] = cloudtrail_audit_logs

    # Atomic write to local_state.json
    temp_file = BACKEND_DIR / "local_state.tmp.json"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(temp_file, STATE_FILE)
    print(f"Atomically wrote seed data into {STATE_FILE} ({len(patients_table)} patients, {len(prescriptions_table)} prescriptions).")

    # If --aws flag passed and boto3 credentials work, sync to AWS
    if to_aws:
        print("Checking AWS credentials for optional DynamoDB/S3 seed upsert...")
        try:
            from backend_lambdas.setup_db import run_cloud_provisioning_and_seeding
            run_cloud_provisioning_and_seeding()
            print("Successfully synced seed to live AWS cloud resources.")
        except Exception as e:
            print(f"AWS synchronization skipped/failed (sandbox fallback active): {e}")

    print("Seed loading complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load SwasthyaSetu seed datasets into state")
    parser.add_argument("--reset", action="store_true", help="Reset local_state.json to fresh baseline before loading")
    parser.add_argument("--aws", action="store_true", help="Sync loaded state to live AWS DynamoDB/S3 if creds present")
    args = parser.parse_args()

    load_seed(reset=args.reset, to_aws=args.aws)
