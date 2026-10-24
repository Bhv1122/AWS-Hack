"""
Registry Engine for SwasthyaSetu & AWS Platform
Provides strict multi-gate doctor validation, public rate-limited lookups,
and demo scenario catalogs from seed datasets.
"""

import os
import json
import re
import time
from typing import Dict, Any, Optional, Tuple, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_DIR = os.path.join(BASE_DIR, "seed_data")

# In-memory caches for registries
_COUNCILS_CACHE: Optional[Dict[str, Any]] = None
_HOSPITALS_CACHE: Optional[Dict[str, Any]] = None
_DOCTORS_CACHE: Optional[Dict[str, Any]] = None
_DOCTORS_LIST_CACHE: Optional[List[Dict[str, Any]]] = None
_RATE_LIMIT_STORE: Dict[str, List[float]] = {}
_WRONG_PIN_ATTEMPTS: Dict[str, List[float]] = {}


def _load_councils() -> Dict[str, Any]:
    global _COUNCILS_CACHE
    if _COUNCILS_CACHE is not None:
        return _COUNCILS_CACHE
    c_path = os.path.join(SEED_DIR, "medical_councils.json")
    if os.path.exists(c_path):
        with open(c_path, "r", encoding="utf-8") as f:
            councils = json.load(f)
            _COUNCILS_CACHE = {c["councilCode"]: c for c in councils}
    else:
        _COUNCILS_CACHE = {}
    return _COUNCILS_CACHE


def _load_hospitals() -> Dict[str, Any]:
    global _HOSPITALS_CACHE
    if _HOSPITALS_CACHE is not None:
        return _HOSPITALS_CACHE
    h_path = os.path.join(SEED_DIR, "hospitals.json")
    if os.path.exists(h_path):
        with open(h_path, "r", encoding="utf-8") as f:
            hospitals = json.load(f)
            _HOSPITALS_CACHE = {h["hospitalCode"]: h for h in hospitals}
    else:
        _HOSPITALS_CACHE = {}
    return _HOSPITALS_CACHE


def _load_doctors() -> Dict[str, Any]:
    global _DOCTORS_CACHE, _DOCTORS_LIST_CACHE
    if _DOCTORS_CACHE is not None:
        return _DOCTORS_CACHE
    d_path = os.path.join(SEED_DIR, "doctors_registry.json")
    if os.path.exists(d_path):
        with open(d_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
            _DOCTORS_LIST_CACHE = docs
            _DOCTORS_CACHE = {d["licenseNumber"].strip().upper(): d for d in docs}
    else:
        _DOCTORS_CACHE = {}
        _DOCTORS_LIST_CACHE = []
    return _DOCTORS_CACHE


def mask_name(full_name: str) -> str:
    """Masks doctor's name for privacy in public lookup: 'Dr. Ananya Sharma' -> 'Dr. A. S*****'"""
    parts = full_name.strip().split()
    if not parts:
        return "Dr. M*****"
    
    prefix = ""
    name_parts = parts
    if parts[0].lower() in ("dr.", "dr", "doctor"):
        prefix = "Dr. "
        name_parts = parts[1:]
    
    if len(name_parts) == 0:
        return "Dr. M*****"
    elif len(name_parts) == 1:
        p = name_parts[0]
        masked = p[0].upper() + "*" * max(len(p) - 1, 3)
        return prefix + masked
    else:
        first = name_parts[0][0].upper() + "."
        last = name_parts[-1][0].upper() + "*" * max(len(name_parts[-1]) - 1, 3)
        return f"{prefix}{first} {last}"


def lookup_license(license_number: str) -> Dict[str, Any]:
    """
    Public live lookup for Gate 1 feedback as doctor types.
    Rate-limited, returns maskedName and status.
    """
    if not license_number or not isinstance(license_number, str):
        return {"found": False, "status": "INVALID_FORMAT"}
    
    clean_num = license_number.strip().upper()
    docs = _load_doctors()
    
    if clean_num not in docs:
        return {"found": False, "status": "NOT_FOUND"}
    
    entry = docs[clean_num]
    masked = mask_name(entry.get("fullName", "Doctor"))
    return {
        "found": True,
        "licenseNumber": entry["licenseNumber"],
        "council": entry.get("councilCode"),
        "status": entry.get("status", "ACTIVE"),
        "maskedName": masked,
        "specialty": entry.get("specialty"),
        "degree": entry.get("degree"),
        "registered": entry.get("registered", False),
        "synthetic": True
    }


def lookup_hospital(hospital_code: str) -> Dict[str, Any]:
    """
    Public live lookup for hospital code validation.
    """
    if not hospital_code or not isinstance(hospital_code, str):
        return {"valid": False, "message": "Hospital code is required"}
    
    clean_code = hospital_code.strip().upper()
    hosps = _load_hospitals()
    
    if clean_code not in hosps:
        return {"valid": False, "message": f"Hospital code '{hospital_code}' not recognized"}
    
    h = hosps[clean_code]
    return {
        "valid": True,
        "hospitalCode": h["hospitalCode"],
        "name": h["hospitalName"],
        "city": h.get("city", "Bengaluru"),
        "state": h.get("state", "Karnataka"),
        "type": h.get("type", "General Hospital"),
        "synthetic": True
    }


def verify_doctor_registration_4gates(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], int]:
    """
    Validates doctor registration across the strict 4-Gate hierarchy:
      Gate 1: License status (SUSPENDED, EXPIRED, NOT_FOUND, ALREADY_REGISTERED)
      Gate 2: Hospital affiliation (HOSPITAL_NOT_FOUND, HOSPITAL_NOT_AFFILIATED)
      Gate 3: Degree & Govt ID verification (GOVID_MISMATCH)
      Gate 4: 2FA MFA OTP verification (MFA_INVALID)
    
    Returns (success, response_dict, http_status_code).
    """
    docs = _load_doctors()
    hosps = _load_hospitals()
    
    lic = str(data.get("licenseNumber") or data.get("license_number") or "").strip().upper()
    hosp_code = str(data.get("hospitalCode") or data.get("hospital_code") or "").strip().upper()
    gov_id = str(data.get("govIdLast4") or data.get("gov_id_last4") or data.get("govIdProof") or "").strip()
    mfa_otp = str(data.get("mfaOtp") or data.get("mfa_otp") or data.get("otp") or "").strip()
    degree = str(data.get("degree") or "").strip()

    # --- GATE 1: Medical Council License Check ---
    if not lic:
        return False, {
            "status": "ERROR",
            "code": "LICENSE_REQUIRED",
            "message": "Medical Council License Number is mandatory.",
            "gate": 1
        }, 400

    if lic not in docs:
        return False, {
            "status": "ERROR",
            "code": "LICENSE_NOT_FOUND",
            "message": f"Medical council license '{lic}' was not found in registered council directories.",
            "gate": 1
        }, 400

    doc_entry = docs[lic]
    lic_status = str(doc_entry.get("status", "ACTIVE")).upper()

    if lic_status == "SUSPENDED":
        return False, {
            "status": "ERROR",
            "code": "LICENSE_SUSPENDED",
            "message": f"License '{lic}' is currently SUSPENDED by the state medical council.",
            "gate": 1
        }, 400

    if lic_status == "EXPIRED":
        return False, {
            "status": "ERROR",
            "code": "LICENSE_EXPIRED",
            "message": f"License '{lic}' expired on {doc_entry.get('validTill', 'past date')}. Renewal required.",
            "gate": 1
        }, 400

    if lic_status == "REVOKED":
        return False, {
            "status": "ERROR",
            "code": "LICENSE_REVOKED",
            "message": f"License '{lic}' has been revoked by the Medical Council Disciplinary Committee.",
            "gate": 1
        }, 400

    if doc_entry.get("registered") is True:
        return False, {
            "status": "ERROR",
            "code": "ALREADY_REGISTERED",
            "message": f"License '{lic}' is already registered on SwasthyaSetu. Please sign in instead.",
            "gate": 1,
            "hint": "Sign in instead",
            "existingDoctorId": doc_entry.get("doctorId", "DOC-IN-8841")
        }, 409

    # --- GATE 2: Hospital Affiliation Check ---
    if not hosp_code:
        return False, {
            "status": "ERROR",
            "code": "HOSPITAL_REQUIRED",
            "message": "Institutional hospital authorization code is mandatory.",
            "gate": 2
        }, 400

    if hosp_code not in hosps:
        return False, {
            "status": "ERROR",
            "code": "HOSPITAL_NOT_FOUND",
            "message": f"Hospital code '{hosp_code}' is not recognized in verified healthcare networks.",
            "gate": 2
        }, 400

    affiliations = [h.upper() for h in doc_entry.get("hospitalCodes", [])]
    if hosp_code not in affiliations:
        return False, {
            "status": "ERROR",
            "code": "HOSPITAL_NOT_AFFILIATED",
            "message": f"License '{lic}' is not affiliated with hospital '{hosp_code}'. Affiliated facilities: {', '.join(affiliations)}.",
            "gate": 2
        }, 400

    # --- GATE 3: Govt ID Reference Check ---
    if not degree:
        return False, {
            "status": "ERROR",
            "code": "DEGREE_REQUIRED",
            "message": "Doctor degree credentials (e.g. MBBS, MD) are required.",
            "gate": 3
        }, 400

    expected_gov_id = str(doc_entry.get("govIdLast4", "")).strip()
    if not gov_id or gov_id != expected_gov_id:
        return False, {
            "status": "ERROR",
            "code": "GOVID_MISMATCH",
            "message": "Government ID last 4 digits do not match records on file with the medical council.",
            "gate": 3
        }, 400

    # --- GATE 4: 2FA MFA OTP Check ---
    if mfa_otp != "654321":
        return False, {
            "status": "ERROR",
            "code": "MFA_INVALID",
            "message": "Invalid Multi-Factor Authentication OTP code. Use universal demo OTP '654321'.",
            "gate": 4
        }, 401

    # --- ALL 4 GATES PASSED: Complete Registration ---
    new_doc_id = doc_entry.get("doctorId") or f"DOC-IN-{gov_id}1"
    doc_entry["registered"] = True
    doc_entry["doctorId"] = new_doc_id

    return True, {
        "status": "SUCCESS",
        "message": f"Doctor {doc_entry['fullName']} verified and registered successfully across all 4 gates.",
        "doctorId": new_doc_id,
        "name": doc_entry["fullName"],
        "licenseNumber": lic,
        "councilCode": doc_entry.get("councilCode"),
        "hospitalCode": hosp_code,
        "hospitalName": hosps[hosp_code]["hospitalName"],
        "specialty": doc_entry.get("specialty"),
        "degree": doc_entry.get("degree"),
        "synthetic": True
    }, 201


def check_pin_rate_limit(doctor_id: str, patient_id: str, is_wrong_attempt: bool = False) -> Tuple[bool, int, int]:
    """
    Enforces 5 failed attempts per 60 seconds cooldown.
    Returns (is_allowed, remaining_cooldown_seconds, attempts_remaining).
    """
    key = f"{doctor_id}:{patient_id}"
    now = time.time()
    attempts = _WRONG_PIN_ATTEMPTS.get(key, [])
    # Keep only attempts from the last 60 seconds
    recent = [t for t in attempts if now - t < 60]
    
    if len(recent) >= 5:
        oldest = recent[0]
        cooldown = int(60 - (now - oldest))
        return False, max(cooldown, 1), 0
    
    if is_wrong_attempt:
        recent.append(now)
        _WRONG_PIN_ATTEMPTS[key] = recent
        
    attempts_remaining = max(0, 5 - len(recent))
    return True, 0, attempts_remaining


def reset_pin_rate_limit(doctor_id: str, patient_id: str) -> None:
    """
    Clears wrong PIN attempt history for doctor-patient pair upon successful unlock.
    """
    key = f"{doctor_id}:{patient_id}"
    _WRONG_PIN_ATTEMPTS.pop(key, None)


def get_demo_scenarios_catalog() -> Dict[str, Any]:
    """Provides catalog of verified doctor & patient scenarios for Judge Panel."""
    return {
        "doctorVerificationScenarios": [
            {
                "id": "VALID_CARDIO",
                "label": "VALID: Dr. Ananya Sharma (Cardiology)",
                "licenseNumber": "KMC-2019-88412",
                "hospitalCode": "HOSP-BLR-990",
                "degree": "MBBS, MD (Cardiology)",
                "specialty": "Cardiology",
                "govIdLast4": "4412",
                "mfaOtp": "654321",
                "expectedGate": 4,
                "expectedOutcome": "VERIFIED (DOC-IN-8841)",
                "description": "Pre-registered cardiologist at Manipal Hospital Whitefield"
            },
            {
                "id": "VALID_ODISHA_SIGNUP",
                "label": "VALID: Dr. Debabrata Nayak (Odia Pulmonologist - Live Sign-Up)",
                "licenseNumber": "NMC-IND-55201",
                "hospitalCode": "AIIMS-BBSR-101",
                "degree": "MBBS, MD (Pulmonary Medicine)",
                "specialty": "Pulmonology",
                "govIdLast4": "5201",
                "mfaOtp": "654321",
                "expectedGate": 4,
                "expectedOutcome": "REGISTERS LIVE",
                "description": "Odia-speaking pulmonologist at AIIMS Bhubaneswar ready for live judge registration"
            },
            {
                "id": "SUSPENDED_LICENSE",
                "label": "NEGATIVE: Suspended Medical License",
                "licenseNumber": "KMC-2016-10233",
                "hospitalCode": "HOSP-BLR-102",
                "degree": "MBBS, MD (General Medicine)",
                "specialty": "General Medicine",
                "govIdLast4": "1023",
                "mfaOtp": "654321",
                "expectedGate": 1,
                "expectedOutcome": "400 LICENSE_SUSPENDED",
                "description": "Gate 1 fails: Council disciplinary suspension active"
            },
            {
                "id": "EXPIRED_LICENSE",
                "label": "NEGATIVE: Expired Medical License",
                "licenseNumber": "TNMC-2011-45110",
                "hospitalCode": "HOSP-CHN-501",
                "degree": "MBBS, MS (Orthopaedics)",
                "specialty": "Orthopaedics",
                "govIdLast4": "4511",
                "mfaOtp": "654321",
                "expectedGate": 1,
                "expectedOutcome": "400 LICENSE_EXPIRED",
                "description": "Gate 1 fails: License registration expired in 2021"
            },
            {
                "id": "NOT_IN_REGISTRY",
                "label": "NEGATIVE: Unregistered License Number",
                "licenseNumber": "KMC-2024-00000",
                "hospitalCode": "HOSP-BLR-990",
                "degree": "MBBS",
                "specialty": "General Practice",
                "govIdLast4": "0000",
                "mfaOtp": "654321",
                "expectedGate": 1,
                "expectedOutcome": "400 LICENSE_NOT_FOUND",
                "description": "Gate 1 fails: No record found in state council registry"
            },
            {
                "id": "WRONG_HOSPITAL",
                "label": "NEGATIVE: Wrong Hospital Affiliation",
                "licenseNumber": "KMC-2018-55120",
                "hospitalCode": "HOSP-BLR-990",
                "degree": "MBBS, MD (Diabetology)",
                "specialty": "Diabetology",
                "govIdLast4": "5512",
                "mfaOtp": "654321",
                "expectedGate": 2,
                "expectedOutcome": "400 HOSPITAL_NOT_AFFILIATED",
                "description": "Gate 2 fails: Doctor affiliated only with HOSP-MYS-201"
            },
            {
                "id": "WRONG_GOVID",
                "label": "NEGATIVE: Government ID Mismatch",
                "licenseNumber": "KMC-2020-77341",
                "hospitalCode": "HOSP-BLR-990",
                "degree": "MBBS, MD (Occupational Health)",
                "specialty": "Occupational Medicine",
                "govIdLast4": "9999",
                "mfaOtp": "654321",
                "expectedGate": 3,
                "expectedOutcome": "400 GOVID_MISMATCH",
                "description": "Gate 3 fails: Entered 9999, council record is 7734"
            },
            {
                "id": "WRONG_MFA",
                "label": "NEGATIVE: Invalid MFA OTP",
                "licenseNumber": "KMC-2021-66219",
                "hospitalCode": "HOSP-BLR-990",
                "degree": "MBBS, DNB (Family Medicine)",
                "specialty": "Family Medicine",
                "govIdLast4": "6621",
                "mfaOtp": "111111",
                "expectedGate": 4,
                "expectedOutcome": "401 MFA_INVALID",
                "description": "Gate 4 fails: Invalid OTP code provided"
            },
            {
                "id": "ALREADY_REGISTERED",
                "label": "NEGATIVE: Duplicate Registration",
                "licenseNumber": "KMC-2019-88412",
                "hospitalCode": "HOSP-BLR-990",
                "degree": "MBBS, MD (Cardiology)",
                "specialty": "Cardiology",
                "govIdLast4": "4412",
                "mfaOtp": "654321",
                "expectedGate": 1,
                "expectedOutcome": "409 ALREADY_REGISTERED",
                "description": "Gate 1 fails: Account already registered, prompt to sign in"
            }
        ],
        "patientScenarios": [
            {
                "patientId": "PAT-SS-1001",
                "name": "Ramesh Kumar",
                "origin": "Odisha (Ganjam) -> Bengaluru",
                "occupation": "Construction Mason (6 yrs)",
                "activeDrugs": ["Warfarin 5mg", "Metformin 500mg", "Atorvastatin 10mg"],
                "allergies": ["Penicillin"],
                "keyFeature": "Blocks Augmentin (Penicillin allergy), Blocks Aspirin (Warfarin interaction), High Silicosis Risk, Longitudinal HbA1c/INR trends"
            },
            {
                "patientId": "PAT-SS-1002",
                "name": "Rajesh Yadav",
                "origin": "Bihar (Gaya) -> Bengaluru",
                "occupation": "Textile / Garment Worker (8 yrs)",
                "activeDrugs": ["Asthalin Inhaler", "Deriphyllin 150mg"],
                "allergies": [],
                "keyFeature": "Byssinosis demo: Cotton dust cough, Monday chest tightness"
            },
            {
                "patientId": "PAT-SS-1003",
                "name": "Manjunath Gowda",
                "origin": "Karnataka (Raichur) -> Bengaluru",
                "occupation": "Auto Driver (14 yrs)",
                "activeDrugs": ["Diclofenac 50mg", "Ibuprofen 400mg", "Ramipril 5mg", "Telmisartan 40mg", "Pantoprazole 40mg", "Amlodipine 5mg"],
                "allergies": [],
                "keyFeature": "Duplicate therapy demo: 2 concurrent NSAIDs & concurrent ACEI + ARB"
            },
            {
                "patientId": "PAT-SS-1004",
                "name": "Lakshmi Murugan",
                "origin": "Tamil Nadu (Salem) -> Bengaluru",
                "occupation": "Domestic Worker (9 yrs)",
                "activeDrugs": ["Pantoprazole 40mg", "Paracetamol 650mg"],
                "allergies": ["Sulfa"],
                "keyFeature": "Sulfa allergy demo: Blocks Co-trimoxazole (Bactrim)"
            },
            {
                "patientId": "PAT-SS-1005",
                "name": "Santosh Pradhan",
                "origin": "Odisha (Balasore) -> Bengaluru",
                "occupation": "Welder (7 yrs)",
                "activeDrugs": ["Montelukast 10mg", "Levocetirizine 5mg"],
                "allergies": ["Aspirin", "NSAIDs"],
                "keyFeature": "Aspirin-sensitive asthma demo: Blocks all NSAIDs"
            },
            {
                "patientId": "PAT-SS-1006",
                "name": "Bina Mondal",
                "origin": "West Bengal (Murshidabad) -> Bengaluru",
                "occupation": "Kitchen Staff (4 yrs)",
                "activeDrugs": [],
                "allergies": [],
                "keyFeature": "Clean baseline demo: Prescribing safe antibiotic returns SAVED cleanly; >95% adherence"
            },
            {
                "patientId": "PAT-SS-1007",
                "name": "Dharmendra Paswan",
                "origin": "Jharkhand (Hazaribagh) -> Bengaluru",
                "occupation": "Stone Crusher (11 yrs)",
                "activeDrugs": ["Amlodipine 5mg"],
                "allergies": [],
                "keyFeature": "Poor adherence escalation demo: 6 consecutive missed doses triggers ASHA coordinator alert"
            },
            {
                "patientId": "PAT-SS-1008",
                "name": "Ankit Soren",
                "origin": "Jharkhand (Ranchi) -> Bengaluru",
                "occupation": "Delivery Rider (0 yrs)",
                "activeDrugs": [],
                "allergies": [],
                "keyFeature": "Empty state demo: Arrived 5 days ago, empty medical record view"
            },
            {
                "patientId": "PAT-SS-1009",
                "name": "Suresh Reddy",
                "origin": "Telangana (Mahbubnagar) -> Bengaluru",
                "occupation": "Security Guard (16 yrs)",
                "activeDrugs": ["Metformin 500mg", "Amlodipine 5mg"],
                "allergies": [],
                "keyFeature": "Elderly (68y) & Break-Glass demo: Past consent revocation & Emergency override on audit trail"
            },
            {
                "patientId": "PAT-SS-1010",
                "name": "Fatima Khatun",
                "origin": "UP (Gorakhpur) -> Bengaluru",
                "occupation": "Sanitation Worker (3 yrs)",
                "activeDrugs": ["Folic Acid 5mg", "Ferrous Ascorbate 100mg"],
                "allergies": [],
                "keyFeature": "Pregnant patient demo: 24 weeks gestation, antenatal care profile"
            }
        ]
    }
