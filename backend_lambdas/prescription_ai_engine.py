"""
Patient-Doctor Medication Coordination Platform - Prescription AI & Clinical Safety Engine
Region: us-east-1
Integrated Services:
  - Amazon Cognito: Role-Based Access Control (RBAC: DOCTOR, PATIENT, CAREGIVER, PHARMACY) & Scopes
  - Amazon Comprehend Medical: Clinical NLP entity extraction (detect_entities_v2)
  - Amazon Bedrock: AI clinical pharmacology risk scorecard (Claude 3 Haiku / Titan Text Express)
  - AWS Step Functions: 3-stage sequential clinical safety gatekeeper workflow
  - Amazon DynamoDB: PrescriptionsTable, PatientsTable & AdherenceScheduleTable CRUD with full version history
  - AWS CloudTrail: HIPAA immutable clinical audit trail & clinical override event logging
"""

import os
import sys
import json
import re
import uuid
import copy
import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

import boto3
from botocore.exceptions import ClientError, BotoCoreError

# ---------------------------------------------------------------------------
# Fallback Import Support (runs from AWS/ root or inside backend_lambdas/)
# ---------------------------------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    from backend_lambdas.aws_core import (
        AWS_REGION,
        PATIENTS_TABLE_NAME,
        PRESCRIPTIONS_TABLE_NAME,
        ADHERENCE_TABLE_NAME,
        verify_cognito_access,
        get_patient,
        save_patient,
        get_patient_profile,
        save_patient_profile,
        get_prescription,
        create_prescription,
        update_prescription,
        get_prescriptions_for_patient,
        list_all_prescriptions,
        record_audit_event,
        record_patient_timeline_event,
        get_patient_timeline,
        convert_decimals,
        local_store,
        dynamodb_resource,
        get_medicine_by_id,
        load_medicine_catalog,
        search_medicine_catalog,
        get_doctor_medicine_menu,
        get_safer_alternatives_from_catalog
    )
except ImportError:
    from aws_core import (
        AWS_REGION,
        PATIENTS_TABLE_NAME,
        PRESCRIPTIONS_TABLE_NAME,
        ADHERENCE_TABLE_NAME,
        verify_cognito_access,
        get_patient,
        save_patient,
        get_patient_profile,
        save_patient_profile,
        get_prescription,
        create_prescription,
        update_prescription,
        get_prescriptions_for_patient,
        list_all_prescriptions,
        record_audit_event,
        record_patient_timeline_event,
        get_patient_timeline,
        convert_decimals,
        local_store,
        dynamodb_resource,
        get_medicine_by_id,
        load_medicine_catalog,
        search_medicine_catalog,
        get_doctor_medicine_menu,
        get_safer_alternatives_from_catalog
    )

logger = logging.getLogger("medcoord_ai_engine")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Boto3 AI & Workflow Clients
# ---------------------------------------------------------------------------
def get_boto3_client(service_name: str):
    try:
        return boto3.client(service_name, region_name=AWS_REGION)
    except Exception as e:
        logger.debug(f"Client init notice for {service_name}: {e}")
        return None

comprehend_medical_client = get_boto3_client("comprehendmedical")
bedrock_runtime_client = get_boto3_client("bedrock-runtime")
stepfunctions_client = get_boto3_client("stepfunctions")
cognito_idp_client = get_boto3_client("cognito-idp")
sns_client = get_boto3_client("sns")

VALID_COGNITO_ROLES = {"DOCTOR", "PATIENT", "CAREGIVER", "PHARMACY"}


# ---------------------------------------------------------------------------
# Backward-Compatible Cognito Role Validator
# ---------------------------------------------------------------------------
def validate_cognito_role(
    user_context: Union[str, Dict[str, Any]],
    allowed_roles: List[str]
) -> Dict[str, Any]:
    """
    Validates Amazon Cognito user group / role permissions.
    Delegates to aws_core.verify_cognito_access.
    """
    return verify_cognito_access(user_context, required_roles=allowed_roles)


# ---------------------------------------------------------------------------
# Therapeutic Drug Classes for Multi-Doctor Duplication Detection
# ---------------------------------------------------------------------------
THERAPEUTIC_CLASSES: Dict[str, List[str]] = {
    "Anticoagulant": [
        "warfarin", "coumadin", "apixaban", "eliquis", "rivaroxaban", "xarelto",
        "dabigatran", "pradaxa", "heparin", "enoxaparin", "lovenox"
    ],
    "Antiplatelet": [
        "aspirin", "clopidogrel", "plavix", "ticagrelor", "brilinta", "prasugrel", "effient"
    ],
    "ACE_Inhibitor": [
        "lisinopril", "prinivil", "zestril", "enalapril", "vasotec", "ramipril", "altace",
        "benazepril", "lotensin", "captopril"
    ],
    "ARB": [
        "losartan", "cozaar", "valsartan", "diovan", "candesartan", "atacand",
        "irbesartan", "avapro", "olmesartan", "benicar"
    ],
    "Statin_HMG_CoA": [
        "atorvastatin", "lipitor", "rosuvastatin", "crestor", "simvastatin", "zocor",
        "pravastatin", "pravachol", "lovastatin"
    ],
    "Beta_Blocker": [
        "metoprolol", "lopressor", "toprol", "atenolol", "tenormin", "carvedilol", "coreg",
        "propranolol", "inderal", "bisoprolol"
    ],
    "Biguanide_Antidiabetic": [
        "metformin", "glucophage", "fortamet", "glumetza"
    ],
    "NSAID": [
        "ibuprofen", "advil", "motrin", "naproxen", "aleve", "ketorolac", "toradol",
        "celecoxib", "celebrex", "diclofenac", "voltaren", "meloxicam", "mobic"
    ],
    "Potassium_Sparing_Diuretic": [
        "spironolactone", "aldactone", "eplerenone", "inspra", "triamterene", "potassium"
    ]
}

def identify_therapeutic_class(drug_name: str) -> Optional[str]:
    """Identifies the clinical pharmacology class of a medication."""
    drug_lower = drug_name.strip().lower()
    for class_name, drugs in THERAPEUTIC_CLASSES.items():
        for d in drugs:
            if d in drug_lower or drug_lower in d:
                return class_name
    return None


# ---------------------------------------------------------------------------
# Deterministic Clinical Safety Knowledge Base
# ---------------------------------------------------------------------------
CLINICAL_DDI_RULES = [
    {
        "drugs": ("warfarin", "aspirin"),
        "severity": "CRITICAL",
        "title": "Severe Bleeding & Anticoagulant Disruption",
        "explanation": "Concurrent administration of Warfarin with Aspirin carries a life-threatening hemorrhage risk. Dual inhibition of coagulation factors and platelet aggregation drastically elevates GI and intracranial bleeding risks.",
        "safer_alternatives": ["Acetaminophen (Tylenol) <= 2000mg/day", "Topical Lidocaine Patch", "Physical Therapy", "Short-term Celecoxib with PPI under close monitoring"]
    },
    {
        "drugs": ("warfarin", "ibuprofen"),
        "severity": "CRITICAL",
        "title": "Severe Bleeding & NSAID Gastric Erosion Risk",
        "explanation": "Concurrent administration of Warfarin with Ibuprofen carries a severe bleeding risk. NSAIDs induce gastric mucosal injury and displace Warfarin from albumin binding sites.",
        "safer_alternatives": ["Acetaminophen (Tylenol) <= 2000mg/day", "Tramadol (short-term)", "Topical Analgesic"]
    },
    {
        "drugs": ("lisinopril", "spironolactone"),
        "severity": "CRITICAL",
        "title": "Severe Hyperkalemia & Arrhythmia Risk",
        "explanation": "Concurrent Lisinopril and Spironolactone presents a severe risk of life-threatening Hyperkalemia due to dual aldosterone suppression and impaired renal potassium clearance.",
        "safer_alternatives": ["Amlodipine (Calcium Channel Blocker)", "Hydralazine", "Chlorthalidone (Thiazide-like diuretic)"]
    },
    {
        "drugs": ("lisinopril", "potassium"),
        "severity": "CRITICAL",
        "title": "Severe Hyperkalemia Risk",
        "explanation": "Lisinopril impairs potassium elimination. Exogenous potassium supplementation carries severe risk of fatal hyperkalemic cardiac arrest.",
        "safer_alternatives": ["Dietary potassium monitoring without exogenous supplementation", "Amlodipine"]
    },
    {
        "drugs": ("metformin", "contrast"),
        "severity": "CRITICAL",
        "title": "Severe Lactic Acidosis Risk (MALA)",
        "explanation": "Metformin combined with iodinated radiocontrast media carries a severe lactic acidosis risk (MALA) secondary to contrast-induced acute kidney injury.",
        "safer_alternatives": ["Withhold Metformin 48 hours prior to contrast; restart after confirming normal eGFR", "Temporary short-acting insulin"]
    },
    {
        "drugs": ("simvastatin", "clarithromycin"),
        "severity": "CRITICAL",
        "title": "Severe Rhabdomyolysis & Acute Renal Failure",
        "explanation": "Clarithromycin is a potent CYP3A4 inhibitor that increases Simvastatin exposure up to 10-fold, precipitating massive muscle necrosis, rhabdomyolysis, and acute renal failure.",
        "safer_alternatives": ["Azithromycin (non-CYP3A4 inhibitor macrolide)", "Pravastatin / Rosuvastatin", "Temporary statin hold during macrolide therapy"]
    },
    {
        "drugs": ("sildenafil", "nitroglycerin"),
        "severity": "CRITICAL",
        "title": "Refractory Hypotension & Cardiovascular Collapse",
        "explanation": "Sildenafil combined with Nitroglycerin causes massive cGMP-mediated refractory vasodilation, precipitating catastrophic hypotension and syncope.",
        "safer_alternatives": ["Absolute contraindication. Never co-administer nitrates within 24-48 hours.", "Non-nitrate anti-anginal agents (Ranolazine, Beta-blockers)"]
    }
]

ALLERGY_CONFLICT_RULES = {
    "penicillin": {
        "allergens": ["penicillin", "penicillins", "amoxicillin", "amoxycillin", "amoxyclav", "ampicillin", "augmentin", "piperacillin", "bicillin", "cloxacillin"],
        "severity": "CRITICAL",
        "title": "Penicillin Class Allergy Cross-Reactivity",
        "explanation": "Patient has documented Penicillin allergy. Beta-lactam core cross-reactivity poses severe risk of IgE-mediated anaphylaxis, angioedema, and bronchospasm.",
        "safer_alternatives": ["Azithromycin (Macrolide)", "Doxycycline", "Ciprofloxacin", "Vancomycin"]
    },
    "sulfa": {
        "allergens": ["sulfa", "sulfonamide", "sulfonamides", "sulfamethoxazole", "bactrim", "septra", "sulfasalazine"],
        "severity": "CRITICAL",
        "title": "Sulfa Class Allergy Cross-Reactivity",
        "explanation": "Patient has documented Sulfa allergy. Prescribing Sulfamethoxazole carries severe risk of cutaneous adverse reactions (Stevens-Johnson syndrome) and anaphylaxis.",
        "safer_alternatives": ["Nitrofurantoin", "Ciprofloxacin", "Fosfomycin", "Cephalexin (if non-penicillin allergic)"]
    },
    "nsaid": {
        "allergens": ["aspirin", "nsaids", "nsaid", "ibuprofen", "advil", "motrin", "naproxen", "aleve", "ketorolac", "toradol", "celecoxib", "diclofenac", "aceclofenac", "combiflam", "brufen"],
        "severity": "CRITICAL",
        "title": "Aspirin/NSAID Exacerbated Respiratory Reaction",
        "explanation": "Patient has documented Aspirin/NSAID hypersensitivity. Cross-inhibition of COX-1 risks severe bronchospasm, facial angioedema, and urticaria.",
        "safer_alternatives": ["Acetaminophen (Tylenol)", "Topical Analgesics (Lidocaine Patch)", "Physical Therapy"]
    }
}


# ---------------------------------------------------------------------------
# 1. Doctor Workspace Aggregator: get_doctor_patient_view()
# ---------------------------------------------------------------------------
def get_doctor_patient_view(doctor_id: str, patient_id: str) -> Dict[str, Any]:
    """
    Returns the complete backend JSON payload needed for the Doctor Clinical Workspace:
    - Decrypted patient demographics & contact
    - Active prescriptions categorized & sorted by prescribing doctor/hospital (highlighting overlaps)
    - Documented & verified allergies
    - 7-day & 30-day adherence percentages per drug and overall
    - Active clinical alert flags
    - Full prescription version history
    """
    verify_cognito_access(doctor_id, required_roles=["DOCTOR"])

    clean_pid = str(patient_id).strip()
    actual_id = "PAT-1001" if clean_pid.upper() in ("PATIENT-001", "1001", "PAT-1001", "PAT-SS-1001") else ("PAT-1002" if clean_pid.upper() in ("PATIENT-002", "1002", "PAT-1002", "PAT-SS-1002") else clean_pid)
    patient = get_patient(actual_id) or get_patient(clean_pid)
    if not patient:
        raise ValueError(f"Patient with ID '{patient_id}' not found.")

    doctor_info = local_store.load_all().get("cognito_users", {}).get(doctor_id, {
        "userId": doctor_id,
        "name": "Dr. Sarah Jenkins, MD, FACC",
        "hospitalAffiliation": "Manipal Hospital Heart Institute"
    })

    # Fetch all prescriptions with state reload
    local_store.reload()
    all_rx = get_prescriptions_for_patient(actual_id)
    for r in all_rx:
        r["prescription_id"] = r.get("prescriptionId") or r.get("prescription_id")
        r["prescriptionId"] = r.get("prescriptionId") or r.get("prescription_id")
        r["medication_name"] = r.get("medicationName") or r.get("medication_name")
        r["medicationName"] = r.get("medicationName") or r.get("medication_name")
        r["prescribed_by"] = r.get("prescribedBy") or r.get("prescribed_by")
        r["prescribedBy"] = r.get("prescribedBy") or r.get("prescribed_by")
        r["doctor_id"] = r.get("doctorId") or r.get("doctor_id")
        r["doctorId"] = r.get("doctorId") or r.get("doctor_id")
        r["discontinue_reason"] = r.get("discontinue_reason") or r.get("discontinueReason") or r.get("reason", "")

    active_rx = [r for r in all_rx if str(r.get("status", "")).upper() in ("ACTIVE", "MODIFIED")]
    discontinued_rx = [r for r in all_rx if str(r.get("status", "")).upper() == "DISCONTINUED"]

    # Prescriptions by doctor & hospital
    prescriptions_by_doctor: Dict[str, List[Dict[str, Any]]] = {}
    co_managing_physicians = set()

    for rx in active_rx:
        prescriber_id = rx.get("doctorId", "DOC-UNKNOWN")
        prescriber_name = rx.get("prescribedBy", "Attending Physician")
        hospital = rx.get("hospital", "Affiliated Hospital")
        group_key = f"{prescriber_name} ({hospital})"

        prescriptions_by_doctor.setdefault(group_key, []).append(rx)
        if prescriber_id != doctor_id:
            co_managing_physicians.add(prescriber_name)

    # Multi-Doctor Coordination Overlaps
    multi_doctor_coordination = {
        "primaryReviewingDoctor": doctor_info.get("name"),
        "coManagingPhysicians": list(co_managing_physicians),
        "multiDoctorOverlap": len(co_managing_physicians) > 0,
        "overlapNotes": (
            f"Patient is co-managed with {', '.join(co_managing_physicians)}. "
            f"Cross-specialty prescriptions are active across multiple facilities."
            if co_managing_physicians else "Sole managing physician."
        )
    }

    # Adherence metrics (Overall, 7-day & 30-day per drug)
    state_data = local_store.load_all()
    all_adh_items = local_store.list_table_items(ADHERENCE_TABLE_NAME)
    patient_adh = [a for a in all_adh_items if a.get("patientId") == actual_id]

    now_dt = datetime.now(timezone.utc)
    seven_days_ago = (now_dt - timedelta(days=7)).isoformat()
    thirty_days_ago = (now_dt - timedelta(days=30)).isoformat()

    per_drug_7d = {}
    per_drug_30d = {}

    for rx in active_rx:
        rx_id = rx.get("prescriptionId")
        med_name = rx.get("medicationName", "Medication")

        # 7-day window
        doses_7d = [a for a in patient_adh if a.get("prescriptionId") == rx_id and str(a.get("timestamp", "")) >= seven_days_ago]
        taken_7d = sum(1 for a in doses_7d if str(a.get("status", "")).upper() == "TAKEN")
        rate_7d = round((taken_7d / len(doses_7d) * 100.0), 1) if doses_7d else 100.0
        per_drug_7d[med_name] = {"taken": taken_7d, "totalScheduled": len(doses_7d), "adherencePercentage": rate_7d}

        # 30-day window
        doses_30d = [a for a in patient_adh if a.get("prescriptionId") == rx_id and str(a.get("timestamp", "")) >= thirty_days_ago]
        taken_30d = sum(1 for a in doses_30d if str(a.get("status", "")).upper() == "TAKEN")
        rate_30d = round((taken_30d / len(doses_30d) * 100.0), 1) if doses_30d else 100.0
        per_drug_30d[med_name] = {"taken": taken_30d, "totalScheduled": len(doses_30d), "adherencePercentage": rate_30d}

    total_doses = len(patient_adh)
    total_taken = sum(1 for a in patient_adh if str(a.get("status", "")).upper() == "TAKEN")
    cumulative_rate = round((total_taken / total_doses * 100.0), 1) if total_doses > 0 else 100.0

    # Active alert flags
    active_alerts = []
    doctor_notifs = state_data.get("notifications_inbox", {}).get("doctor", {}).get(doctor_id, [])
    for n in doctor_notifs:
        if not n.get("read", False):
            active_alerts.append(n)

    # Check for INR/vital flags
    if "Warfarin" in [r.get("medicationName") for r in active_rx]:
        active_alerts.append({
            "type": "LAB_MONITORING_REQUIRED",
            "title": "INR Lab Monitoring Schedule Due",
            "message": "Patient is on active Warfarin 5mg therapy. Routine PT/INR monitoring target: 2.0 - 3.0."
        })

    record_audit_event(
        action="GetDoctorPatientView",
        actor=doctor_id,
        resource=f"Patient/{actual_id}",
        details=f"Doctor {doctor_id} viewed clinical chart for patient {actual_id}."
    )

    result = {
        "doctorId": doctor_id,
        "doctorName": doctor_info.get("name"),
        "hospitalAffiliation": doctor_info.get("hospitalAffiliation"),
        "patient": {
            "patientId": actual_id,
            "name": patient.get("name"),
            "dob": patient.get("dob"),
            "age": patient.get("age"),
            "gender": patient.get("gender"),
            "bloodGroup": patient.get("bloodGroup"),
            "contact": patient.get("contact"),
            "email": patient.get("email"),
            "address": patient.get("address"),
            "vitalNotes": patient.get("vital_notes"),
            "caregiver": patient.get("caregiver_contact"),
            "allergies": patient.get("allergies", []),
            "allergyDetails": patient.get("allergy_details", [])
        },
        "multiDoctorCoordination": multi_doctor_coordination,
        "prescriptionsByDoctor": prescriptions_by_doctor,
        "activePrescriptions": active_rx,
        "active_prescriptions": active_rx,
        "discontinuedPrescriptions": discontinued_rx,
        "discontinued_prescriptions": discontinued_rx,
        "adherenceMetrics": {
            "cumulativeOverallAdherenceRate": cumulative_rate,
            "totalRecordedDoses": total_doses,
            "perDrug7DayAdherence": per_drug_7d,
            "perDrug30DayAdherence": per_drug_30d
        },
        "activeAlertFlags": active_alerts,
        "timelineEvents": get_patient_timeline(actual_id, limit=50),
        "timeline_events": get_patient_timeline(actual_id, limit=50),
        "medicineMenuCatalog": get_doctor_medicine_menu(dosage_form="Tablet", limit=20),
        "scheduleSlots": state_data.get("medication_schedule_slots", []),
        "generatedAt": now_dt.isoformat()
    }

    return convert_decimals(result)


# ---------------------------------------------------------------------------
# 2. Patient Allergy & Condition Manager: manage_patient_allergies()
# ---------------------------------------------------------------------------
def manage_patient_allergies(
    doctor_id: str,
    patient_id: str,
    action: str,
    allergen: str,
    reaction: str = "",
    severity: str = "high"
) -> Dict[str, Any]:
    """
    Allows doctors to ADD, UPDATE, or REMOVE patient allergies and immediately
    cross-checks currently active prescriptions to detect any newly introduced conflicts.
    """
    verify_cognito_access(doctor_id, required_roles=["DOCTOR"])

    actual_id = "PAT-1001" if patient_id == "PATIENT-001" else patient_id
    patient = get_patient(actual_id)
    if not patient:
        raise ValueError(f"Patient with ID '{patient_id}' not found.")

    act = action.strip().upper()
    allergen_clean = allergen.strip()
    allergies = patient.setdefault("allergies", [])
    allergy_details = patient.setdefault("allergy_details", [])

    conflicts_detected = []

    if act in ("ADD", "UPDATE"):
        # Add to allergies list if not present
        if not any(a.lower() == allergen_clean.lower() for a in allergies):
            allergies.append(allergen_clean)

        # Update details list
        existing_detail = next((d for d in allergy_details if d.get("substance", "").lower() == allergen_clean.lower()), None)
        detail_obj = {
            "substance": allergen_clean,
            "criticality": severity.lower(),
            "verificationStatus": "confirmed",
            "clinicalStatus": "active",
            "reaction": reaction or f"Reported {severity} allergic sensitivity.",
            "recordedDate": datetime.now(timezone.utc).isoformat(),
            "recorder": doctor_id
        }
        if existing_detail:
            existing_detail.update(detail_obj)
        else:
            allergy_details.append(detail_obj)

        # Immediate cross-check against currently active prescriptions
        active_rx = get_prescriptions_for_patient(actual_id)
        for rx in active_rx:
            if str(rx.get("status", "")).upper() not in ("ACTIVE", "MODIFIED"):
                continue

            rx_name = rx.get("medicationName", "").lower()
            allergen_lower = allergen_clean.lower()

            is_conflict = False
            explanation = ""

            for rule_key, rule in ALLERGY_CONFLICT_RULES.items():
                if rule_key in allergen_lower or allergen_lower in rule_key:
                    for cross_drug in rule["allergens"]:
                        if cross_drug in rx_name or rx_name in cross_drug:
                            is_conflict = True
                            explanation = rule["explanation"]
                            break

            BRAND_SYNONYMS = {
                "coumadin": "warfarin", "warfarin": "coumadin",
                "glucophage": "metformin", "metformin": "glucophage",
                "lipitor": "atorvastatin", "atorvastatin": "lipitor",
                "zocor": "simvastatin", "simvastatin": "zocor",
                "prinivil": "lisinopril", "zestril": "lisinopril", "lisinopril": "prinivil"
            }
            allergen_synonym = BRAND_SYNONYMS.get(allergen_lower, "")

            if not is_conflict and (
                allergen_lower in rx_name or rx_name in allergen_lower or
                (allergen_synonym and (allergen_synonym in rx_name or rx_name in allergen_synonym))
            ):
                is_conflict = True
                explanation = f"Patient active medication '{rx.get('medicationName')}' directly matches newly recorded allergen '{allergen_clean}'."

            if is_conflict:
                conflicts_detected.append({
                    "conflictingPrescriptionId": rx.get("prescriptionId"),
                    "medicationName": rx.get("medicationName"),
                    "dosage": rx.get("dosage"),
                    "prescribedBy": rx.get("prescribedBy"),
                    "severity": "CRITICAL",
                    "explanation": explanation
                })

    elif act == "REMOVE":
        patient["allergies"] = [a for a in allergies if a.lower() != allergen_clean.lower()]
        patient["allergy_details"] = [d for d in allergy_details if d.get("substance", "").lower() != allergen_clean.lower()]

    else:
        raise ValueError(f"Invalid allergy management action '{action}'. Must be ADD, UPDATE, or REMOVE.")

    # Save updated patient profile
    save_patient(patient)

    try:
        record_patient_timeline_event(
            patient_id=actual_id,
            action="ALLERGY_UPDATED",
            title=f"Allergy Profile Updated: {act} {allergen_clean}",
            details=f"Severity: {severity}. Reaction: {reaction or 'Documented hypersensitivity'}.",
            actor=doctor_id,
            actor_id=doctor_id,
            role="DOCTOR",
            category="ALLERGY",
            metadata={"allergen": allergen_clean, "severity": severity, "action": act}
        )
    except Exception as te:
        logger.debug(f"Notice recording timeline event in manage_patient_allergies: {te}")

    # Record CloudTrail audit log
    audit_sev = "CRITICAL" if conflicts_detected else "INFO"
    record_audit_event(
        action=f"ManagePatientAllergy_{act}",
        actor=doctor_id,
        resource=f"Patient/{actual_id}",
        details=f"Doctor {doctor_id} executed {act} for allergen '{allergen_clean}'. Active conflicts found: {len(conflicts_detected)}.",
        severity=audit_sev
    )

    return convert_decimals({
        "status": "WARNING_ACTIVE_PRESCRIPTION_CONFLICT" if conflicts_detected else "SUCCESS",
        "action": act,
        "allergen": allergen_clean,
        "conflictsDetected": conflicts_detected,
        "patientId": actual_id,
        "updatedAllergies": patient["allergies"]
    })


# ---------------------------------------------------------------------------
# 3. Stage A: Amazon Comprehend Medical NLP & Fallback
# ---------------------------------------------------------------------------
COMMON_DRUGS_REGEX = [
    "warfarin", "coumadin", "aspirin", "clopidogrel", "plavix", "apixaban", "eliquis", "rivaroxaban", "xarelto", "heparin",
    "amoxicillin", "ampicillin", "augmentin", "penicillin", "piperacillin", "cephalexin", "keflex", "ceftriaxone",
    "bactrim", "sulfamethoxazole", "septra", "ciprofloxacin", "cipro", "levofloxacin", "azithromycin", "clarithromycin",
    "metronidazole", "vancomycin", "doxycycline", "lisinopril", "enalapril", "losartan", "valsartan", "spironolactone",
    "furosemide", "hydrochlorothiazide", "amlodipine", "metoprolol", "atenolol", "diltiazem", "metformin", "glucophage",
    "glipizide", "insulin", "empagliflozin", "atorvastatin", "lipitor", "rosuvastatin", "simvastatin", "zocor",
    "ibuprofen", "advil", "motrin", "naproxen", "aleve", "ketorolac", "celecoxib", "paracetamol", "acetaminophen",
    "tylenol", "tramadol", "contrast", "sildenafil", "viagra", "nitroglycerin"
]

def fallback_clinical_regex_parser(text: str) -> Dict[str, Any]:
    """Deterministic clinical NLP regex fallback parser."""
    text_clean = text.strip()
    text_lower = text.lower()

    detected_med = None
    for drug in COMMON_DRUGS_REGEX:
        pattern = r"\b" + re.escape(drug) + r"\b"
        if re.search(pattern, text_lower):
            detected_med = drug.capitalize()
            brand_map = {
                "Coumadin": "Warfarin", "Plavix": "Clopidogrel", "Eliquis": "Apixaban",
                "Xarelto": "Rivaroxaban", "Augmentin": "Amoxicillin-Clavulanate",
                "Keflex": "Cephalexin", "Bactrim": "Sulfamethoxazole", "Septra": "Sulfamethoxazole",
                "Lipitor": "Atorvastatin", "Zocor": "Simvastatin", "Advil": "Ibuprofen",
                "Aleve": "Naproxen", "Glucophage": "Metformin", "Viagra": "Sildenafil"
            }
            if detected_med in brand_map:
                detected_med = brand_map[detected_med]
            break

    if not detected_med:
        rx_match = re.search(r"(?:rx|prescribe|order|start|administer|take)\s*[:\-]?\s*([A-Za-z]+)", text_clean, re.IGNORECASE)
        if rx_match:
            candidate = rx_match.group(1).capitalize()
            if candidate.lower() not in ("one", "two", "tablet", "oral", "daily", "the", "a"):
                detected_med = candidate

    detected_med = detected_med or "Unspecified Medication"

    dosage_match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?|tablets?|capsules?))\b", text_clean, re.IGNORECASE)
    detected_dosage = dosage_match.group(1).strip() if dosage_match else "Standard Dosage"
    detected_dosage = re.sub(r"(\d+)\s+([a-zA-Z]+)", r"\1\2", detected_dosage)

    freq_patterns = [
        (r"\b(?:once\s+daily|daily\s+at\s+bedtime|daily\s+in\s+the\s+morning|daily\s+at\s+20:00|daily\s+at\s+08:00|q\.?d\.?|qd|once\s+a\s+day)\b", "Once daily"),
        (r"\b(?:twice\s+daily|two\s+times\s+daily|b\.?i\.?d\.?|bid|every\s+12\s+hours?)\b", "Twice daily"),
        (r"\b(?:three\s+times\s+daily|t\.?i\.?d\.?|tid|every\s+8\s+hours?)\b", "Three times daily"),
        (r"\b(?:as\s+needed|prn|p\.r\.n\.)\b", "As needed (PRN)")
    ]
    detected_freq = "Once daily"
    for pat, label in freq_patterns:
        if re.search(pat, text_lower):
            detected_freq = label
            break

    detected_route = "Oral"
    if re.search(r"\b(?:sublingual|sl)\b", text_lower):
        detected_route = "Sublingual"
    elif re.search(r"\b(?:intravenous|iv)\b", text_lower):
        detected_route = "Intravenous"

    return {
        "medication_name": detected_med,
        "dosage": detected_dosage,
        "frequency": detected_freq,
        "route": detected_route,
        "instructions": f"Take {detected_dosage} {detected_route.lower()} {detected_freq.lower()}.",
        "extraction_engine": "Deterministic Clinical NLP Engine (Regex Fallback)"
    }


def extract_medical_entities(text: str) -> Dict[str, Any]:
    """
    Extracts Medication Name, Dosage, Frequency, and Route using Amazon Comprehend Medical.
    """
    if not text or not str(text).strip():
        return {
            "medication_name": "Unknown",
            "dosage": "Standard Dosage",
            "frequency": "Once daily",
            "route": "Oral",
            "instructions": "As directed",
            "extraction_engine": "None"
        }

    text_str = str(text)
    try:
        if comprehend_medical_client:
            response = comprehend_medical_client.detect_entities_v2(Text=text_str)
            entities = response.get("Entities", [])
            med_name, dosage, frequency, route = None, None, None, None

            for ent in entities:
                cat = ent.get("Category")
                ent_type = ent.get("Type")
                ent_text = ent.get("Text")

                if cat == "MEDICATION":
                    if ent_type == "NAME" and not med_name:
                        med_name = ent_text
                    elif ent_type == "DOSAGE" and not dosage:
                        dosage = ent_text
                    elif ent_type == "FREQUENCY" and not frequency:
                        frequency = ent_text
                    elif ent_type == "ROUTE_OR_MODE" and not route:
                        route = ent_text

            if med_name:
                return {
                    "medication_name": med_name.capitalize(),
                    "dosage": dosage or "Standard Dosage",
                    "frequency": frequency or "Once daily",
                    "route": route or "Oral",
                    "instructions": f"Take {dosage or 'standard dose'} {route or 'oral'} {frequency or 'as directed'}.",
                    "extraction_engine": "Amazon Comprehend Medical (detect_entities_v2)"
                }
    except Exception as e:
        logger.debug(f"Comprehend Medical notice: {e}. Fallback to regex.")

    return fallback_clinical_regex_parser(text_str)


# ---------------------------------------------------------------------------
# 4. Stage B: Deterministic Clinical Safety Gate
# ---------------------------------------------------------------------------
def run_deterministic_safety_gate(
    patient_id: str,
    new_medicine: str,
    dosage: str,
    doctor_id: str,
    active_salts: Optional[List[str]] = None,
    generic_composition: Optional[str] = None,
    med_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stage B Hard Checks:
    1. Severe Drug-Drug Interactions (Warfarin+Aspirin, Lisinopril+Spironolactone, Metformin+Contrast, Simvastatin+Clarithromycin)
    2. Allergy & Cross-Reactivity Matrix (Penicillin, Sulfa, NSAIDs)
    3. Multi-Doctor Duplicate Therapy (flags same drug or same therapeutic class across doctors)
    4. CSV Active Salt Composition & Safer Alternatives from Catalog
    """
    actual_id = "PAT-1001" if patient_id == "PATIENT-001" else patient_id
    patient = get_patient(actual_id) or {"allergies": [], "active_medications": []}

    # Resolve active salts & composition from CSV catalog if available
    catalog_item = get_medicine_by_id(med_id) if med_id else None
    if not catalog_item:
        catalog_item = get_medicine_by_id(new_medicine)

    if catalog_item:
        if not active_salts:
            active_salts = catalog_item.get("active_salts", [])
        if not generic_composition:
            generic_composition = catalog_item.get("generic_composition")

    med_lower = new_medicine.strip().lower()
    search_terms = {med_lower}
    if generic_composition:
        search_terms.add(generic_composition.lower())
    if active_salts:
        for s in active_salts:
            search_terms.add(s.lower())

    conflicts = []
    highest_severity = "SAFE"
    safer_alternatives = []
    explanations = []
    matched_eval_rule = None

    # 0. Comprehensive 42-rule safety evaluation via generic_resolver
    try:
        from generic_resolver import evaluate_drug_safety_rules
        eval_res = evaluate_drug_safety_rules(
            new_medicine=new_medicine,
            active_prescriptions=get_prescriptions_for_patient(actual_id),
            patient_allergies=patient.get("allergies", [])
        )
        if eval_res.get("isBlocked"):
            highest_severity = "CRITICAL"
            matched_eval_rule = eval_res.get("matchedRule")
            conflicts.append({
                "type": eval_res.get("conflictType", "DRUG_SAFETY_CONFLICT"),
                "severity": "CRITICAL",
                "explanation": eval_res.get("explanation"),
                "matchedRule": matched_eval_rule,
                "source": "RULES",
                "safer_alternatives": eval_res.get("safer_alternatives", [])
            })
            explanations.append(eval_res.get("explanation"))
            safer_alternatives.extend(eval_res.get("safer_alternatives", []))
    except Exception as _e:
        logger.debug(f"Notice evaluating generic rules: {_e}")

    # 1. Allergy Conflicts
    patient_allergies = patient.get("allergies", [])
    for allergy_item in patient_allergies:
        allergy_name = allergy_item.get("substance") if isinstance(allergy_item, dict) else str(allergy_item)
        allergy_key = allergy_name.strip().lower()

        for group_key, rule in ALLERGY_CONFLICT_RULES.items():
            if group_key in allergy_key:
                matched_cross = None
                for cross_drug in rule["allergens"]:
                    for term in search_terms:
                        if cross_drug in term or (len(term) >= 4 and term in cross_drug.lower()):
                            matched_cross = cross_drug
                            break
                    if matched_cross:
                        break

                if matched_cross:
                    highest_severity = "CRITICAL"
                    target_cls = "Antibiotic" if group_key == "penicillin" else ("Analgesic" if group_key == "nsaid" else "General Therapeutics")
                    cat_alts = get_safer_alternatives_from_catalog(group_key, target_class=target_cls, limit=3)
                    combined_alts = list(rule["safer_alternatives"])
                    for ca in cat_alts:
                        combined_alts.append(f"{ca['brand_name']} ({ca['generic_composition']}) - INR {ca['unit_price']}")

                    conflicts.append({
                        "type": "ALLERGY_CROSS_REACTIVITY",
                        "severity": "CRITICAL",
                        "patientAllergy": allergy_name,
                        "offendingDrug": new_medicine,
                        "detectedAllergen": matched_cross,
                        "title": rule["title"],
                        "explanation": rule["explanation"],
                        "safer_alternatives": combined_alts
                    })
                    explanations.append(f"ALLERGY CONFLICT ({allergy_name}): {rule['explanation']}")
                    safer_alternatives.extend(combined_alts)
                    break

    # 2. Drug-Drug Interactions & Multi-Doctor Duplicate Therapy
    active_prescriptions = get_prescriptions_for_patient(actual_id)
    new_class = identify_therapeutic_class(new_medicine) or (catalog_item.get("therapeutic_class") if catalog_item else None)

    for rx in active_prescriptions:
        if str(rx.get("status", "")).upper() not in ("ACTIVE", "MODIFIED"):
            continue

        rx_name = rx.get("medicationName", "").strip()
        rx_name_lower = rx_name.lower()
        prescriber_id = rx.get("doctorId", "DOC-UNKNOWN")
        prescriber_name = rx.get("prescribedBy", "Attending Physician")
        hospital = rx.get("hospital", "Affiliated Hospital")

        # 2a. Multi-Doctor Duplication Check
        is_same_drug = (rx_name_lower == med_lower) or any(len(term) >= 4 and term in rx_name_lower for term in search_terms)
        rx_class = identify_therapeutic_class(rx_name) or rx.get("therapeuticClass")
        is_same_class = (new_class is not None and rx_class is not None and new_class == rx_class)

        if is_same_drug or is_same_class:
            sev = "CRITICAL" if is_same_drug else "MODERATE"
            if highest_severity != "CRITICAL" or sev == "CRITICAL":
                highest_severity = sev

            dup_type = "EXACT_MEDICATION_DUPLICATION" if is_same_drug else f"THERAPEUTIC_CLASS_DUPLICATION ({new_class})"
            dup_msg = (
                f"Multi-Doctor Overlap: '{rx_name}' was already prescribed by {prescriber_name} ({hospital}). "
                f"Concurrent order of '{new_medicine}' risks therapeutic duplication or overdose."
            )
            conflicts.append({
                "type": dup_type,
                "severity": sev,
                "existingPrescriptionId": rx.get("prescriptionId"),
                "existingDoctor": prescriber_name,
                "existingHospital": hospital,
                "explanation": dup_msg,
                "safer_alternatives": [f"Adjust dosage of active {rx_name} or coordinate directly with {prescriber_name}"]
            })
            explanations.append(dup_msg)
            safer_alternatives.append(f"Consult {prescriber_name} ({hospital}) regarding existing {rx_name}")

        # 2b. Severe Drug-Drug Interactions
        for rule in CLINICAL_DDI_RULES:
            drug_a, drug_b = rule["drugs"]
            a_in_new = any(drug_a in term for term in search_terms)
            b_in_new = any(drug_b in term for term in search_terms)

            if (a_in_new and drug_b in rx_name_lower) or (b_in_new and drug_a in rx_name_lower):
                highest_severity = "CRITICAL"
                combined_alts = list(rule["safer_alternatives"])
                if drug_a in ("aspirin", "ibuprofen") or drug_b in ("aspirin", "ibuprofen"):
                    cat_alts = get_safer_alternatives_from_catalog("aspirin", target_class="Analgesic", limit=3)
                    for ca in cat_alts:
                        combined_alts.append(f"{ca['brand_name']} ({ca['generic_composition']}) - INR {ca['unit_price']}")

                conflicts.append({
                    "type": "DRUG_DRUG_INTERACTION",
                    "severity": "CRITICAL",
                    "activeMedication": rx_name,
                    "prescribedBy": prescriber_name,
                    "newMedication": new_medicine,
                    "title": rule["title"],
                    "explanation": rule["explanation"],
                    "safer_alternatives": combined_alts
                })
                explanations.append(f"DRUG-DRUG INTERACTION ({rx_name} + {new_medicine}): {rule['explanation']}")
                safer_alternatives.extend(combined_alts)

    unique_alts = list(dict.fromkeys(safer_alternatives))
    return {
        "hasConflicts": len(conflicts) > 0,
        "severity": highest_severity,
        "explanation": " | ".join(explanations) if explanations else "No deterministic clinical blocks detected.",
        "conflicts": conflicts,
        "safer_alternatives": unique_alts,
        "source": "RULES",
        "matchedRule": matched_eval_rule
    }


def check_drug_interactions(
    patient_id: str,
    medication_name: str,
    current_medicines: Optional[List[str]] = None,
    dosage: str = "Standard Dosage"
) -> Dict[str, Any]:
    """
    Checks severe drug-drug interactions and documented allergy conflicts
    for a medication against the patient's active regimen.
    """
    actual_id = "PAT-1001" if patient_id in ("PATIENT-001", "1001", "PAT-1001") else patient_id
    res = run_deterministic_safety_gate(
        patient_id=actual_id,
        new_medicine=medication_name,
        dosage=dosage,
        doctor_id="DOC-201"
    )
    return {
        "hasInteractions": res.get("hasConflicts", False),
        "severity": res.get("severity", "SAFE"),
        "conflicts": res.get("conflicts", []),
        "explanation": res.get("explanation", ""),
        "safer_alternatives": res.get("safer_alternatives", [])
    }


# ---------------------------------------------------------------------------
# 5. Stage C: Amazon Bedrock Clinical Pharmacology LLM
# ---------------------------------------------------------------------------
def call_bedrock_clinical_scorecard(
    patient_id: str,
    new_medicine: str,
    dosage: str,
    deterministic_gate: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Invokes Amazon Bedrock (anthropic.claude-3-haiku-20240307-v1:0) to synthesize
    a clinical risk scorecard (risk_score 0-100, severity, mechanism, safer_alternatives).
    """
    has_critical = deterministic_gate.get("severity") == "CRITICAL"
    has_conflicts = deterministic_gate.get("hasConflicts", False)

    default_score = 95 if has_critical else 45 if has_conflicts else 10
    default_sev = "CRITICAL" if has_critical else "MODERATE" if has_conflicts else "SAFE"

    fallback_report = {
        "risk_score": default_score,
        "severity": default_sev,
        "mechanism": deterministic_gate.get("explanation"),
        "safer_alternatives": deterministic_gate.get("safer_alternatives", ["Standard therapeutic alternatives apply."]),
        "engine": "Deterministic Clinical Pharmacology Engine (Sandbox-Fallback)"
    }

    if not bedrock_runtime_client:
        return fallback_report

    prompt = f"""You are an expert Clinical Pharmacologist AI.
Perform a clinical safety analysis for this patient:
- Patient ID: {patient_id}
- Prescribing Drug: {new_medicine} ({dosage})
- Detected Clinical Rules: {deterministic_gate.get('explanation')}

Return ONLY a valid JSON object matching this schema:
{{
  "risk_score": <int 0-100>,
  "severity": "SAFE" | "MODERATE" | "CRITICAL",
  "mechanism": "<clinical pharmacology explanation of interaction/allergy>",
  "safer_alternatives": ["<Drug 1>", "<Drug 2>"]
}}
"""
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": prompt}]
        })
        resp = bedrock_runtime_client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=body
        )
        resp_body = json.loads(resp["body"].read().decode("utf-8"))
        text_out = resp_body.get("content", [{}])[0].get("text", "")
        clean_json = re.sub(r"```json|```", "", text_out).strip()
        parsed = json.loads(clean_json)
        parsed["engine"] = f"Amazon Bedrock ({model_id})"
        return parsed
    except Exception as e:
        logger.debug(f"Bedrock invocation notice: {e}. Utilizing clinical fallback scorecard.")

    return fallback_report


# ---------------------------------------------------------------------------
# 6. 3-Stage Safety Step Function: run_safety_pipeline()
# ---------------------------------------------------------------------------
def run_safety_pipeline(
    doctor_id: str,
    patient_id: str,
    new_medicine: str,
    dosage: str,
    notes: str = "",
    frequency: str = "Once daily",
    route: str = "Oral",
    active_salts: Optional[List[str]] = None,
    generic_composition: Optional[str] = None,
    med_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes the 3-Stage AI Clinical Safety Gatekeeper Pipeline:
    - Stage A (Comprehend Medical): Clinical entity extraction from doctor notes
    - Stage B (Deterministic Clinical Gate): Severe DDIs, allergies, and multi-doctor duplication
    - Stage C (Bedrock AI Synthesis): Clinical risk scorecard with safer alternatives
    """
    actual_id = "PAT-1001" if patient_id == "PATIENT-001" else patient_id

    # Stage A: Entity Extraction
    if notes and (not new_medicine or not dosage):
        stage_a = extract_medical_entities(notes)
        new_medicine = new_medicine or stage_a.get("medication_name", "Medication")
        dosage = dosage or stage_a.get("dosage", "Standard Dosage")
        frequency = frequency or stage_a.get("frequency", "Once daily")
        route = route or stage_a.get("route", "Oral")
    else:
        stage_a = {
            "medication_name": new_medicine,
            "dosage": dosage,
            "frequency": frequency,
            "route": route,
            "extraction_engine": "Structured Doctor Input"
        }

    # Stage B: Deterministic Clinical Rule Gate (checking brand name, active salts & composition)
    stage_b = run_deterministic_safety_gate(
        actual_id,
        new_medicine,
        dosage,
        doctor_id,
        active_salts=active_salts,
        generic_composition=generic_composition,
        med_id=med_id
    )

    # Stage C: Bedrock Risk Scorecard
    stage_c = call_bedrock_clinical_scorecard(actual_id, new_medicine, dosage, stage_b)

    is_blocked = (stage_b["severity"] == "CRITICAL") or (stage_c["severity"] == "CRITICAL")

    return convert_decimals({
        "executionId": f"STEP-EXEC-{uuid.uuid4().hex[:8].upper()}",
        "patientId": actual_id,
        "doctorId": doctor_id,
        "medicationName": new_medicine,
        "dosage": dosage,
        "frequency": frequency,
        "route": route,
        "decision": "BLOCKED" if is_blocked else "APPROVED",
        "stageA_ComprehendMedical": stage_a,
        "stageB_DeterministicGate": stage_b,
        "stageC_BedrockScorecard": stage_c,
        "severity": "CRITICAL" if is_blocked else stage_c.get("severity", "SAFE"),
        "risk_score": stage_c.get("risk_score", 95 if is_blocked else 10),
        "clinicalExplanation": stage_b["explanation"] or stage_c.get("mechanism"),
        "safer_alternatives": stage_b.get("safer_alternatives") or stage_c.get("safer_alternatives", [])
    })


def execute_safety_step_function(patient_id: str, new_medicine: str, dosage: str, notes: str = "", force_override: bool = False) -> Dict[str, Any]:
    """Backward-compatible wrapper for run_safety_pipeline."""
    pipeline = run_safety_pipeline(
        doctor_id="DOC-201",
        patient_id=patient_id,
        new_medicine=new_medicine,
        dosage=dosage,
        notes=notes
    )
    # Map back to old schema for seamless integration
    decision = "APPROVED_OVERRIDDEN" if force_override else pipeline["decision"]
    return {
        "executionId": pipeline["executionId"],
        "patientId": patient_id,
        "medicationName": new_medicine,
        "dosage": dosage,
        "decision": decision,
        "safetyCheck": {
            "hasInteraction": pipeline["decision"] == "BLOCKED",
            "severity": "SEVERE" if pipeline["severity"] == "CRITICAL" else pipeline["severity"],
            "clinicalExplanation": pipeline["clinicalExplanation"],
            "safeAlternatives": pipeline["safer_alternatives"]
        },
        "extractedEntities": pipeline["stageA_ComprehendMedical"],
        "forceOverride": force_override
    }


def check_drug_interactions(
    patient_id: str,
    new_medicine: str,
    dosage: str = "Standard Dosage",
    notes: str = "",
    current_medicines: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Backward-compatible helper evaluating drug safety and drug-drug interactions."""
    dose_val = dosage if dosage and str(dosage).strip() else "Standard Dosage"
    pipeline = run_safety_pipeline("DOC-201", patient_id, new_medicine, dose_val, notes=notes)
    sev = "SEVERE" if pipeline.get("severity") == "CRITICAL" else pipeline.get("severity", "SAFE")
    has_blocked = pipeline.get("decision") == "BLOCKED"
    has_conflicts = has_blocked or len(pipeline.get("stageB_DeterministicSafety", {}).get("conflicts", [])) > 0
    conflicts = pipeline.get("stageB_DeterministicSafety", {}).get("conflicts", [])
    if not conflicts and has_blocked:
        conflicts = [{
            "type": "DRUG_SAFETY_INTERACTION",
            "severity": sev,
            "explanation": pipeline.get("clinicalExplanation", "Identified clinical risk or contraindication."),
            "safer_alternatives": pipeline.get("safer_alternatives", [])
        }]
    return convert_decimals({
        "hasInteraction": has_conflicts,
        "hasInteractions": has_conflicts,
        "severity": sev,
        "clinicalExplanation": pipeline.get("clinicalExplanation", ""),
        "explanation": pipeline.get("clinicalExplanation", ""),
        "conflicts": conflicts,
        "safeAlternatives": pipeline.get("safer_alternatives", []),
        "safer_alternatives": pipeline.get("safer_alternatives", []),
        "risk_score": pipeline.get("risk_score", 0)
    })



# ---------------------------------------------------------------------------
# 7. Full Prescription Lifecycle & Clinical Override Workflow
# ---------------------------------------------------------------------------
def prescribe_medication(
    patient_id: str,
    new_medicine: str,
    dosage: str = "",
    frequency: str = "Once daily",
    doctor_name: str = "Dr. Sarah Jenkins, MD",
    notes: str = "",
    force_override: bool = False,
    user_role: str = "DOCTOR",
    doctor_id: str = "DOC-201",
    **kwargs
) -> Dict[str, Any]:
    """
    Standard prescription issuance with 3-stage safety evaluation.
    Supports prescribing by CSV Medicine Menu (med_id or brand name), automatically
    resolving active salts, composition, and dosage forms.
    Blocks CRITICAL interactions by default and returns AI risk report + safer alternatives.
    """
    validate_cognito_role(user_role, allowed_roles=["DOCTOR"])
    actual_id = "PAT-1001" if patient_id == "PATIENT-001" else patient_id

    # Resolve from CSV Catalog if med_id or recognized brand is passed
    med_id = kwargs.get("med_id") or kwargs.get("medId")
    catalog_item = get_medicine_by_id(med_id) if med_id else None
    if not catalog_item and new_medicine:
        catalog_item = get_medicine_by_id(new_medicine)

    if catalog_item:
        if not new_medicine or new_medicine in ("Medication", "Standard Medication"):
            new_medicine = catalog_item["brand_name"]
        if not dosage or dosage in ("Standard Dosage", ""):
            dosage = catalog_item.get("default_strength", "Standard Dosage")
        generic_comp = catalog_item.get("generic_composition")
        active_salts = catalog_item.get("active_salts", [])
        therapeutic_class = catalog_item.get("therapeutic_class")
        dosage_form = catalog_item.get("dosage_form", "Tablet")
        unit_price = float(catalog_item.get("unit_price", 10.0))
        catalog_med_id = catalog_item.get("med_id")
    else:
        generic_comp = kwargs.get("generic_composition")
        active_salts = kwargs.get("active_salts", [])
        therapeutic_class = kwargs.get("therapeutic_class") or identify_therapeutic_class(new_medicine)
        dosage_form = kwargs.get("dosage_form", "Tablet")
        unit_price = float(kwargs.get("unit_price", 10.0))
        catalog_med_id = med_id
        if not dosage:
            dosage = "Standard Dosage"

    # Run 3-Stage Safety Pipeline with active salt resolution
    pipeline_res = run_safety_pipeline(
        doctor_id=doctor_id,
        patient_id=actual_id,
        new_medicine=new_medicine,
        dosage=dosage,
        notes=notes,
        frequency=frequency,
        route=kwargs.get("route", "Oral"),
        active_salts=active_salts,
        generic_composition=generic_comp,
        med_id=catalog_med_id
    )

    if pipeline_res["decision"] == "BLOCKED" and not force_override:
        logger.warning(f"Prescription for {new_medicine} BLOCKED by safety gatekeeper.")
        record_audit_event(
            action="PrescriptionBlocked",
            actor=doctor_name,
            resource=f"Patient/{actual_id}",
            details=f"Blocked {new_medicine} {dosage}: {pipeline_res['clinicalExplanation']}",
            severity="WARNING",
            role="DOCTOR"
        )
        source_val = pipeline_res.get("stageB_DeterministicGate", {}).get("source") or ("AWS_LIVE" if bedrock_client else "RULES")
        matched_rule = pipeline_res.get("stageB_DeterministicGate", {}).get("matchedRule")

        from backend_lambdas.clinical_risk_engine import evaluate_medicine_safety
        alt_res = evaluate_medicine_safety(
            patient_id=actual_id,
            medicine_name=new_medicine,
            dosage=dosage,
            doctor_id=doctor_id
        )

        return convert_decimals({
            "status": "BLOCKED",
            "riskLevel": alt_res.get("riskLevel", "SEVERE"),
            "resolvedGeneric": alt_res.get("resolvedGeneric", generic_comp or new_medicine),
            "findings": alt_res.get("findings", []),
            "alternatives": alt_res.get("alternatives", []),
            "noSafeSubstitute": alt_res.get("noSafeSubstitute", False),
            "noSubstituteMessage": alt_res.get("noSubstituteMessage", ""),
            "specialistReview": alt_res.get("specialistReview", False),
            "needsIndication": alt_res.get("needsIndication", False),
            "source": source_val,
            "matchedRule": matched_rule,
            "safetyCheck": {
                "hasInteraction": True,
                "severity": "SEVERE" if pipeline_res["severity"] == "CRITICAL" else pipeline_res["severity"],
                "clinicalExplanation": pipeline_res["clinicalExplanation"],
                "safeAlternatives": alt_res.get("alternatives", []) or pipeline_res.get("safer_alternatives", []),
                "risk_score": pipeline_res["risk_score"],
                "source": source_val,
                "matchedRule": matched_rule
            },
            "safeAlternatives": alt_res.get("alternatives", []) or pipeline_res.get("safer_alternatives", []),
            "pipelineReport": pipeline_res
        })

    # Save prescription with version history and CSV catalog attributes
    rx_id = kwargs.get("prescriptionId") or f"RX-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    rx_payload = {
        "prescriptionId": rx_id,
        "patientId": actual_id,
        "medicationName": new_medicine,
        "brandName": new_medicine,
        "genericComposition": generic_comp,
        "activeSalts": active_salts,
        "catalogMedId": catalog_med_id,
        "therapeuticClass": therapeutic_class,
        "dosageForm": dosage_form,
        "unitPriceINR": unit_price,
        "dosage": dosage,
        "frequency": frequency,
        "route": kwargs.get("route", "Oral"),
        "instructions": kwargs.get("instructions", f"Take {dosage} {kwargs.get('route', 'Oral').lower()} {frequency.lower()}."),
        "prescribedBy": doctor_name,
        "doctorId": doctor_id,
        "hospital": kwargs.get("hospital", "Manipal Hospital Heart Institute"),
        "status": "ACTIVE",
        "version": 1,
        "prescribedDate": now_iso,
        "clinicalNotes": notes,
        "version_history": [
            {
                "version": 1,
                "timestamp": now_iso,
                "doctor": doctor_name,
                "doctorId": doctor_id,
                "action": "INITIAL_PRESCRIPTION",
                "dosage": dosage,
                "frequency": frequency,
                "notes": notes or "Initial prescription issued."
            }
        ],
        "history_log": [
            {
                "version": 1,
                "timestamp": now_iso,
                "doctor": doctor_name,
                "action": "PRESCRIBED",
                "dosage": dosage,
                "status": "ACTIVE"
            }
        ]
    }

    saved_rx = create_prescription(actual_id, rx_payload)

    record_audit_event(
        action="PrescriptionAuthorized",
        actor=doctor_name,
        resource=f"Prescription/{rx_id}",
        details=f"Authorized {new_medicine} {dosage} for {actual_id}. Override: {force_override}."
    )

    return convert_decimals({
        "status": "SAVED",
        "prescription": saved_rx,
        "safetyCheck": {
            "hasInteraction": False,
            "severity": "SAFE",
            "clinicalExplanation": pipeline_res["clinicalExplanation"],
            "safeAlternatives": pipeline_res["safer_alternatives"]
        }
    })


def override_and_prescribe(
    doctor_id: str,
    patient_id: str,
    prescription_data: Dict[str, Any],
    clinical_justification: str,
    monitoring_plan: str
) -> Dict[str, Any]:
    """
    Allows a doctor to force-approve a flagged prescription ONLY if they provide
    a rigorous clinical justification (>15 chars) and monitoring plan (>10 chars).
    Logs a high-priority CLINICAL_OVERRIDE event to CloudTrail and notifies co-managing physicians.
    """
    verify_cognito_access(doctor_id, required_roles=["DOCTOR"])

    if not clinical_justification or len(clinical_justification.strip()) <= 15:
        raise ValueError("Clinical justification must provide a detailed pharmacological rationale (>15 characters).")

    if not monitoring_plan or len(monitoring_plan.strip()) <= 10:
        raise ValueError("A clear clinical monitoring and mitigation plan is required (>10 characters).")

    actual_id = "PAT-1001" if patient_id == "PATIENT-001" else patient_id
    now_iso = datetime.now(timezone.utc).isoformat()
    override_id = f"OVR-{uuid.uuid4().hex[:6].upper()}"

    doc_info = local_store.load_all().get("cognito_users", {}).get(doctor_id, {
        "name": "Dr. Sarah Jenkins, MD, FACC",
        "hospitalAffiliation": "Manipal Hospital Heart Institute"
    })
    doctor_name = doc_info.get("name")

    med_name = prescription_data.get("medicationName") or prescription_data.get("new_medicine", "Medication")
    dosage = prescription_data.get("dosage", "Standard Dosage")

    # Save override record to state
    override_record = {
        "overrideId": override_id,
        "patientId": actual_id,
        "requestingDoctorId": doctor_id,
        "requestingDoctorName": doctor_name,
        "medication": f"{med_name} {dosage}",
        "clinicalJustification": clinical_justification.strip(),
        "monitoringPlan": monitoring_plan.strip(),
        "status": "FORCE_APPROVED_BY_PHYSICIAN",
        "timestamp": now_iso
    }

    state = local_store.load_all()
    state.setdefault("clinical_override_requests", []).append(override_record)

    # Notify other coordinating doctors
    patient = get_patient(actual_id)
    if patient:
        for med in patient.get("active_medications", []):
            co_doc_id = med.get("doctorId")
            if co_doc_id and co_doc_id != doctor_id:
                state.setdefault("notifications_inbox", {}).setdefault("doctor", {}).setdefault(co_doc_id, []).append({
                    "notificationId": f"NOTIF-OVR-{uuid.uuid4().hex[:6].upper()}",
                    "type": "CLINICAL_OVERRIDE_ALERT",
                    "title": f"Physician Override for {patient.get('name')}",
                    "message": f"{doctor_name} has authorized {med_name} {dosage} with clinical override: {clinical_justification[:80]}...",
                    "timestamp": now_iso,
                    "read": False
                })

    local_store.save_all(state)

    # Prescribe with override flag
    prescription_data["force_override"] = True
    prescription_data["clinicalNotes"] = f"PHYSICIAN CLINICAL OVERRIDE [{override_id}]: {clinical_justification} | Plan: {monitoring_plan}"

    saved_result = prescribe_medication(
        patient_id=actual_id,
        new_medicine=med_name,
        dosage=dosage,
        frequency=prescription_data.get("frequency", "Once daily"),
        doctor_name=doctor_name,
        notes=prescription_data["clinicalNotes"],
        force_override=True,
        doctor_id=doctor_id
    )

    # CloudTrail High-Priority Audit Logging
    record_audit_event(
        action="CLINICAL_OVERRIDE",
        actor=doctor_name,
        resource=f"Patient/{actual_id}",
        details=f"Physician override authorized for {med_name} {dosage}. Override ID: {override_id}. Justification: {clinical_justification}",
        severity="CRITICAL",
        role="DOCTOR"
    )

    try:
        record_patient_timeline_event(
            patient_id=actual_id,
            action="CLINICAL_OVERRIDE",
            title=f"Clinical override authorized for {med_name} {dosage} by {doctor_name}",
            details=f"Override ID: {override_id}. Justification: {clinical_justification}. Monitoring: {monitoring_plan}.",
            actor=doctor_name,
            actor_id=doctor_id,
            role="DOCTOR",
            category="OVERRIDE",
            metadata={"overrideId": override_id, "medication": med_name, "dosage": dosage, "justification": clinical_justification}
        )
    except Exception as te:
        logger.debug(f"Notice recording timeline event in override_and_prescribe: {te}")

    return convert_decimals({
        "status": "OVERRIDE_APPROVED",
        "overrideId": override_id,
        "prescription": saved_result.get("prescription"),
        "justification": clinical_justification,
        "monitoringPlan": monitoring_plan
    })


def modify_prescription_dosage(
    doctor_id: str = "DOC-201",
    prescription_id: Optional[str] = None,
    new_dosage: str = "Standard Dosage",
    new_frequency: Optional[str] = None,
    reason: str = "Clinical dosage adjustment",
    patient_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Updates prescription dosage and frequency, increments the prescription version number,
    appends the previous state to version_history, and recalculates the patient's daily dose schedule slots.
    """
    if doctor_id.startswith("PAT-") or doctor_id.startswith("PATIENT-"):
        if not patient_id:
            patient_id = doctor_id
        doctor_id = kwargs.get("doctor_id") or kwargs.get("doctorId") or "DOC-201"

    if not prescription_id:
        prescription_id = kwargs.get("prescription_id") or kwargs.get("prescriptionId")
    if kwargs.get("new_dosage"):
        new_dosage = kwargs["new_dosage"]
    if kwargs.get("new_frequency"):
        new_frequency = kwargs["new_frequency"]

    verify_cognito_access(doctor_id, required_roles=["DOCTOR"])

    doc_info = local_store.load_all().get("cognito_users", {}).get(doctor_id, {
        "name": kwargs.get("doctor_name", "Dr. Sarah Jenkins, MD, FACC")
    })
    doctor_name = kwargs.get("doctor_name") or doc_info.get("name")

    # Locate prescription
    rx_item = None
    target_pid = patient_id
    if target_pid:
        clean_pid = str(target_pid).strip()
        target_pid = "PAT-1001" if clean_pid.upper() in ("PATIENT-001", "1001", "PAT-1001", "PAT-SS-1001") else clean_pid
        rx_item = get_prescription(target_pid, prescription_id)

    if not rx_item:
        all_rx = list_all_prescriptions()
        for r in all_rx:
            if r.get("prescriptionId") == prescription_id:
                rx_item = r
                target_pid = r.get("patientId")
                break

    if not rx_item:
        raise ValueError(f"Prescription '{prescription_id}' not found.")

    actual_id = "PAT-1001" if target_pid in ("PATIENT-001", "1001", "PAT-1001", "PAT-SS-1001") else target_pid
    now_iso = datetime.now(timezone.utc).isoformat()

    old_version = int(rx_item.get("version", 1))
    new_version = old_version + 1
    old_dosage = rx_item.get("dosage")
    old_frequency = rx_item.get("frequency", "Once daily")
    freq = new_frequency or old_frequency

    # Version history revision
    v_history = rx_item.setdefault("version_history", [])
    v_history.append({
        "version": new_version,
        "timestamp": now_iso,
        "doctor": doctor_name,
        "doctorId": doctor_id,
        "action": "MODIFIED_DOSAGE",
        "reason": reason,
        "previousDosage": old_dosage,
        "newDosage": new_dosage,
        "previousFrequency": old_frequency,
        "newFrequency": freq,
        "status": "MODIFIED"
    })

    h_log = rx_item.setdefault("history_log", [])
    h_log.append({
        "version": new_version,
        "timestamp": now_iso,
        "doctor": doctor_name,
        "action": "MODIFIED_DOSAGE",
        "reason": reason,
        "previousDosage": old_dosage,
        "newDosage": new_dosage,
        "status": "MODIFIED"
    })

    updates = {
        "dosage": new_dosage,
        "frequency": freq,
        "status": "MODIFIED",
        "version": new_version,
        "updatedAt": now_iso,
        "lastModifiedBy": doctor_name,
        "reason": reason,
        "doctor_name": doctor_name,
        "doctor_id": doctor_id,
        "version_history": v_history,
        "history_log": h_log
    }

    updated_rx = update_prescription(actual_id, prescription_id, updates)

    # Recalculate patient's schedule slots & active_medications
    patient = get_patient(actual_id)
    if patient:
        for m in patient.get("active_medications", []):
            if m.get("medicationId") == prescription_id or m.get("name", "").lower() == rx_item.get("medicationName", "").lower():
                m["dosage"] = new_dosage
                m["frequency"] = freq
                m["status"] = "MODIFIED"
                m["updatedAt"] = now_iso
        save_patient(patient)

    # Synchronize medication schedule slots in local state
    state = local_store.load_all()
    slots = state.get("medication_schedule_slots", [])
    med_name_clean = str(rx_item.get("medicationName", "")).lower()
    for s in slots:
        if (s.get("prescriptionId") == prescription_id or s.get("prescription_id") == prescription_id
            or str(s.get("medicationName", "")).lower() == med_name_clean or str(s.get("medication_name", "")).lower() == med_name_clean):
            s["dosage"] = new_dosage
            s["status"] = "MODIFIED"
    state["medication_schedule_slots"] = slots
    local_store.save_all(state)

    record_audit_event(
        action="ModifyPrescriptionDosage",
        actor=doctor_name,
        resource=f"Prescription/{prescription_id}",
        details=f"Modified dosage from {old_dosage} to {new_dosage} (v{new_version}) for {actual_id}. Reason: {reason}."
    )

    return convert_decimals({
        "status": "MODIFIED",
        "prescription": updated_rx,
        **updated_rx
    })


def modify_prescription(patient_id: str, prescription_id: str, new_dosage: str, doctor_name: str = "Dr. Sarah Jenkins, MD", reason: str = "Clinical dosage adjustment", user_role: str = "DOCTOR") -> Dict[str, Any]:
    """Backward-compatible alias for modify_prescription_dosage."""
    return modify_prescription_dosage(
        doctor_id="DOC-201",
        prescription_id=prescription_id,
        new_dosage=new_dosage,
        reason=reason,
        patient_id=patient_id
    )


def discontinue_prescription(
    doctor_id: str = "DOC-201",
    prescription_id: Optional[str] = None,
    reason: str = "Therapy discontinued per clinical decision",
    patient_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Marks the medication DISCONTINUED, increments version number,
    removes future dose slots from patient active schedule, and updates patient profile.
    Supports both discontinue_prescription(doctor_id, rx_id, ...) and discontinue_prescription(patient_id, rx_id, ...).
    """
    if doctor_id.startswith("PAT-") or doctor_id.startswith("PATIENT-"):
        if not patient_id:
            patient_id = doctor_id
        doctor_id = kwargs.get("doctor_id") or kwargs.get("doctorId") or "DOC-201"

    if not prescription_id:
        prescription_id = kwargs.get("prescription_id") or kwargs.get("prescriptionId")

    verify_cognito_access(doctor_id, required_roles=["DOCTOR"])

    doc_info = local_store.load_all().get("cognito_users", {}).get(doctor_id, {
        "name": kwargs.get("doctor_name", "Dr. Sarah Jenkins, MD, FACC")
    })
    doctor_name = kwargs.get("doctor_name") or doc_info.get("name")

    rx_item = None
    target_pid = patient_id
    if target_pid:
        clean_pid = str(target_pid).strip()
        target_pid = "PAT-1001" if clean_pid.upper() in ("PATIENT-001", "1001", "PAT-1001", "PAT-SS-1001") else clean_pid
        rx_item = get_prescription(target_pid, prescription_id)

    if not rx_item:
        all_rx = list_all_prescriptions()
        for r in all_rx:
            if r.get("prescriptionId") == prescription_id:
                rx_item = r
                target_pid = r.get("patientId")
                break

    if not rx_item:
        raise ValueError(f"Prescription '{prescription_id}' not found.")

    actual_id = "PAT-1001" if target_pid in ("PATIENT-001", "1001", "PAT-1001", "PAT-SS-1001") else target_pid
    now_iso = datetime.now(timezone.utc).isoformat()

    old_version = int(rx_item.get("version", 1))
    new_version = old_version + 1

    v_history = rx_item.setdefault("version_history", [])
    v_history.append({
        "version": new_version,
        "timestamp": now_iso,
        "doctor": doctor_name,
        "doctorId": doctor_id,
        "action": "DISCONTINUED",
        "reason": reason,
        "status": "DISCONTINUED"
    })

    h_log = rx_item.setdefault("history_log", [])
    h_log.append({
        "version": new_version,
        "timestamp": now_iso,
        "doctor": doctor_name,
        "action": "DISCONTINUED",
        "reason": reason,
        "status": "DISCONTINUED"
    })

    updates = {
        "status": "DISCONTINUED",
        "version": new_version,
        "updatedAt": now_iso,
        "lastModifiedBy": doctor_name,
        "discontinue_reason": reason,
        "discontinueReason": reason,
        "reason": reason,
        "doctor_name": doctor_name,
        "doctor_id": doctor_id,
        "version_history": v_history,
        "history_log": h_log
    }

    updated_rx = update_prescription(actual_id, prescription_id, updates)

    # Remove drug from patient active medications
    patient = get_patient(actual_id)
    if patient:
        patient["active_medications"] = [
            m for m in patient.get("active_medications", [])
            if m.get("medicationId") != prescription_id and m.get("name", "").lower() != rx_item.get("medicationName", "").lower()
        ]
        save_patient(patient)

    # Remove active daily schedule slots for this discontinued drug from local state
    state = local_store.load_all()
    slots = state.get("medication_schedule_slots", [])
    med_name_clean = str(rx_item.get("medicationName", "")).lower()
    updated_slots = [
        s for s in slots
        if s.get("prescriptionId") != prescription_id
        and s.get("prescription_id") != prescription_id
        and str(s.get("medicationName", "")).lower() != med_name_clean
        and str(s.get("medication_name", "")).lower() != med_name_clean
    ]
    state["medication_schedule_slots"] = updated_slots
    local_store.save_all(state)

    record_audit_event(
        action="DiscontinuePrescription",
        actor=doctor_name,
        resource=f"Prescription/{prescription_id}",
        details=f"Discontinued prescription {prescription_id} for {actual_id}. Reason: {reason}."
    )

    return convert_decimals({
        "status": "DISCONTINUED",
        "prescription": updated_rx,
        **updated_rx
    })


# ---------------------------------------------------------------------------
# Backward-Compatible Aliases
# ---------------------------------------------------------------------------
def orchestrate_prescription_workflow(patient_id=None, new_medicine=None, dosage=None, frequency=None, doctor_name=None, notes="", force_override=False, **kwargs):
    """Backward-compatible alias."""
    if isinstance(patient_id, dict):
        p = patient_id
        patient_id = p.get("patient_id") or p.get("patientId")
        new_medicine = p.get("new_medicine") or p.get("medication_name")
        dosage = p.get("dosage")
        frequency = p.get("frequency")
        doctor_name = p.get("doctor_name")
        notes = p.get("notes") or ""
        force_override = p.get("force_override", False)

    return prescribe_medication(
        patient_id=patient_id or "PAT-1001",
        new_medicine=new_medicine or "Medication",
        dosage=dosage or "Standard Dosage",
        frequency=frequency or "Once daily",
        doctor_name=doctor_name or "Dr. Sarah Jenkins, MD",
        notes=notes,
        force_override=force_override,
        user_role="DOCTOR",
        **kwargs
    )


def modify_or_discontinue_prescription(patient_id: str, prescription_id: str, new_dosage: Optional[str] = None, new_status: str = "DISCONTINUED", doctor_name: str = "Dr. Sarah Jenkins, MD") -> Dict[str, Any]:
    """Backward-compatible routing."""
    if new_status.upper() == "DISCONTINUED":
        return discontinue_prescription("DOC-201", prescription_id, patient_id=patient_id)
    else:
        return modify_prescription(patient_id, prescription_id, new_dosage=new_dosage or "Standard", doctor_name=doctor_name)


# ---------------------------------------------------------------------------
# Self-Test Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 75)
    print("DOCTOR CLINICAL WORKSPACE & PRESCRIPTION AI ENGINE - TEST SUITE")
    print("=" * 75)

    test_doc = "DOC-201"
    test_pat = "PAT-1001"

    # 1. Doctor Workspace Aggregator View
    print("\n[1] Testing get_doctor_patient_view(DOC-201, PAT-1001):")
    chart = get_doctor_patient_view(test_doc, test_pat)
    print(f"  Doctor In-Charge     : {chart['doctorName']} ({chart['hospitalAffiliation']})")
    print(f"  Patient Chart Name   : {chart['patient']['name']} | Age: {chart['patient']['age']}")
    print(f"  Co-Managing Overlaps : {chart['multiDoctorCoordination']['overlapNotes']}")
    print(f"  Active Rx Count      : {len(chart['activePrescriptions'])}")
    print(f"  Cumulative Adherence : {chart['adherenceMetrics']['cumulativeOverallAdherenceRate']}%")
    print(f"  Per-Drug 7D Adherence: {chart['adherenceMetrics']['perDrug7DayAdherence']}")

    # 2. Manage Patient Allergies with Cross-Check
    print("\n[2] Testing manage_patient_allergies (Adding Cephalosporin allergy):")
    alg_res = manage_patient_allergies(test_doc, test_pat, "ADD", "Cephalosporins", "Skin Rash", "moderate")
    print(f"  Action Status        : {alg_res['status']}")
    print(f"  Updated Allergies    : {alg_res['updatedAllergies']}")
    print(f"  Conflicts Detected   : {len(alg_res['conflictsDetected'])}")

    # 3. 3-Stage Safety Pipeline: Aspirin on Warfarin (Expected: BLOCKED)
    print("\n[3] Testing run_safety_pipeline (Prescribing Aspirin 81mg on Warfarin):")
    pipeline = run_safety_pipeline(test_doc, test_pat, "Aspirin", "81mg", notes="Rx: Aspirin 81mg PO daily")
    print(f"  Stage A (Comprehend) : {pipeline['stageA_ComprehendMedical']['medication_name']} {pipeline['stageA_ComprehendMedical']['dosage']}")
    print(f"  Stage B (Gatekeeper) : Severity: {pipeline['stageB_DeterministicGate']['severity']}")
    print(f"  Stage C (Scorecard)  : Risk Score: {pipeline['risk_score']} | Severity: {pipeline['severity']}")
    print(f"  Gatekeeper Decision  : {pipeline['decision']}")
    print(f"  Safer Alternatives   : {pipeline['safer_alternatives']}")

    # 4. Standard prescribe_medication (Blocked)
    print("\n[4] Testing prescribe_medication (Aspirin -> BLOCKED):")
    blocked = prescribe_medication(
        patient_id=test_pat,
        new_medicine="Aspirin",
        dosage="81mg",
        doctor_name="Dr. Sarah Jenkins, MD",
        doctor_id=test_doc
    )
    print(f"  Prescription Status  : {blocked['status']}")
    print(f"  Risk Explanation     : {blocked['safetyCheck']['clinicalExplanation'][:75]}...")

    # 5. Physician Clinical Override Workflow
    print("\n[5] Testing override_and_prescribe (Physician Clinical Override):")
    override_res = override_and_prescribe(
        doctor_id=test_doc,
        patient_id=test_pat,
        prescription_data={"medicationName": "Aspirin", "dosage": "81mg", "frequency": "Once daily"},
        clinical_justification="Cardioprotection required post-stent with weekly INR monitoring and strict GI prophylaxis.",
        monitoring_plan="Weekly INR laboratory draws, hemoccult checks, and Omeprazole 20mg co-prescription."
    )
    print(f"  Override Status      : {override_res['status']}")
    print(f"  Override ID          : {override_res['overrideId']}")
    ovr_rx_id = override_res["prescription"]["prescriptionId"]
    print(f"  Authorized Rx ID     : {ovr_rx_id} (Version: {override_res['prescription']['version']})")

    # 6. Modify Dosage (v1 -> v2)
    print("\n[6] Testing modify_prescription_dosage (81mg -> 100mg):")
    mod = modify_prescription_dosage(
        doctor_id=test_doc,
        prescription_id=ovr_rx_id,
        new_dosage="100mg",
        reason="Dose optimization",
        patient_id=test_pat
    )
    print(f"  Updated Dosage       : {mod['dosage']} (Version: {mod['version']})")
    print(f"  Version History Log  : {len(mod['version_history'])} revisions recorded")

    # 7. Discontinue Prescription (v2 -> v3)
    print("\n[7] Testing discontinue_prescription:")
    disc = discontinue_prescription(test_doc, ovr_rx_id, reason="Completed therapeutic bridge", patient_id=test_pat)
    print(f"  Final Status         : {disc['status']} (Version: {disc['version']})")

    print("\n" + "=" * 75)
    print("ALL DOCTOR CLINICAL WORKSPACE CAPABILITIES OPERATIONAL.")
    print("=" * 75 + "\n")
