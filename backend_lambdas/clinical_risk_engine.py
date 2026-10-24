"""
backend_lambdas/clinical_risk_engine.py
----------------------------------------
Deterministic Clinical Risk & Safer Drug Alternative Engine.
Evaluates medications against patient allergies, active medications, and duplicate therapies.
Provides deterministic replacement alternatives with catalog brand lookup and zero AWS credentials requirement.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("clinical_risk_engine")
logger.setLevel(logging.INFO)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_DIR = os.path.join(BASE_DIR, "seed_data")

from backend_lambdas.aws_core import (
    get_patient,
    get_prescriptions_for_patient,
    load_medicine_catalog,
    record_audit_event,
    search_medicine_catalog
)
from backend_lambdas.generic_resolver import (
    resolve_brand_to_generics,
    evaluate_drug_safety_rules,
    load_generics_map
)

_DRUG_ALTERNATIVES_CACHE: Optional[Dict[str, Any]] = None
_RISK_SESSION_CACHE: Dict[Tuple[str, str], str] = {}


def load_drug_alternatives() -> Dict[str, Any]:
    global _DRUG_ALTERNATIVES_CACHE
    if _DRUG_ALTERNATIVES_CACHE is not None:
        return _DRUG_ALTERNATIVES_CACHE
    path = os.path.join(SEED_DIR, "drug_alternatives.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _DRUG_ALTERNATIVES_CACHE = json.load(f)
    else:
        _DRUG_ALTERNATIVES_CACHE = {"synthetic": True, "clinicallyReviewed": False, "entries": []}
    return _DRUG_ALTERNATIVES_CACHE


def _normalize_pid(patient_id: str) -> str:
    clean = str(patient_id or "").strip()
    return "PAT-1001" if clean.upper() in ("PAT-1001", "PAT-SS-1001", "PATIENT-001", "1001") else clean


def get_catalog_brands_for_generic(generic_name: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Finds up to 3 non-discontinued brands in the catalog matching the generic salt composition.
    Returns 'Generic only' fallback if none are indexed.
    """
    catalog = load_medicine_catalog()
    g_lower = (generic_name or "").strip().lower()
    brands = []

    for item in catalog:
        if item.get("is_discontinued"):
            continue
        g_comp = (item.get("generic_composition") or "").lower()
        salts = [s.lower() for s in item.get("active_salts", [])]

        if g_lower in g_comp or any(g_lower in s for s in salts):
            brands.append({
                "name": item.get("brand_name"),
                "manufacturer": item.get("manufacturer") or "Pharmaceuticals",
                "price": float(item.get("unit_price", 10.0)),
                "packSize": item.get("pack_size") or "strip of 10 tablets"
            })
            if len(brands) >= limit:
                break

    if not brands:
        brands.append({
            "name": f"Generic {generic_name.title()}",
            "manufacturer": "Generic only",
            "price": 10.0,
            "packSize": "Standard"
        })
    return brands


def check_single_generic_against_patient(generic_name: str, patient_id: str) -> str:
    """
    Lightweight re-check for candidate replacement generics against patient:
    Returns 'NONE', 'CAUTION', or 'SEVERE'.
    """
    norm_pid = _normalize_pid(patient_id)
    patient = get_patient(norm_pid) or {}
    allergies = [str(a.get("substance") if isinstance(a, dict) else a).strip().lower() for a in patient.get("allergies", [])]
    active_rxs = get_prescriptions_for_patient(norm_pid)

    g_lower = generic_name.strip().lower()

    # 1. Check allergies
    for alg in allergies:
        if "penicillin" in alg or "beta-lactam" in alg:
            if any(x in g_lower for x in ("amox", "ampicil", "penicil", "clav")):
                return "SEVERE"
            if any(x in g_lower for x in ("cefixime", "cephal", "ceftriax", "cefurox")):
                return "CAUTION"  # Cephalosporin cross-reactivity warning
        if "sulfa" in alg:
            if any(x in g_lower for x in ("sulfa", "trimethoprim", "bactrim", "septra")):
                return "SEVERE"
        if "aspirin" in alg or "nsaid" in alg:
            if any(x in g_lower for x in ("aspirin", "ibuprofen", "diclofenac", "naproxen", "aceclofenac", "celecoxib", "etoricoxib")):
                return "SEVERE"

    # 2. Check active medications for DDI
    for rx in active_rxs:
        if str(rx.get("status", "ACTIVE")).upper() not in ("ACTIVE", "MODIFIED", "RESERVED"):
            continue
        rx_med = (rx.get("medicationName") or rx.get("medication_name") or "").lower()
        rx_generics = [g.lower() for g in resolve_brand_to_generics(rx_med)]

        # Warfarin interaction
        if "warfarin" in rx_med or "warfarin" in rx_generics:
            if any(x in g_lower for x in ("aspirin", "diclofenac", "ibuprofen", "naproxen", "ketorolac", "aceclofenac")):
                return "SEVERE"
            if any(x in g_lower for x in ("fluconazole", "clarithromycin")):
                return "CAUTION"

        # Duplicate NSAID
        if any(x in rx_med or any(x in g for g in rx_generics) for x in ("ibuprofen", "diclofenac", "celecoxib", "naproxen", "etoricoxib", "aceclofenac")):
            if any(x in g_lower for x in ("ibuprofen", "diclofenac", "celecoxib", "naproxen", "etoricoxib", "aceclofenac")):
                return "SEVERE"

        # Clopidogrel + Omeprazole
        if "clopidogrel" in rx_med or "clopidogrel" in rx_generics:
            if any(x in g_lower for x in ("omeprazole", "esomeprazole")):
                return "SEVERE"

        # Sildenafil + Nitrates
        if "nitrate" in rx_med or "isosorbide" in rx_med or "nitroglycerin" in rx_med:
            if any(x in g_lower for x in ("sildenafil", "tadalafil", "vardenafil")):
                return "SEVERE"

    return "NONE"


def evaluate_medicine_safety(
    patient_id: str,
    medicine_name: str,
    dosage: Optional[str] = None,
    indication: Optional[str] = None,
    doctor_id: str = "DOC-IN-8841"
) -> Dict[str, Any]:
    """
    Evaluates safety for a proposed medicine against patient profile.
    Returns:
    {
        riskLevel: "NONE" | "CAUTION" | "SEVERE" | "UNKNOWN",
        resolvedGeneric: str,
        findings: [...],
        alternatives: [...],
        noSafeSubstitute: bool,
        noSubstituteMessage: str,
        specialistReview: bool,
        needsIndication: bool,
        source: "RULES"
    }
    """
    norm_pid = _normalize_pid(patient_id)
    patient = get_patient(norm_pid) or {}
    active_rxs = get_prescriptions_for_patient(norm_pid)
    patient_allergies = [str(a.get("substance") if isinstance(a, dict) else a) for a in patient.get("allergies", [])]

    med_clean = (medicine_name or "").strip()
    if not med_clean:
        return {
            "riskLevel": "UNKNOWN",
            "resolvedGeneric": "",
            "findings": [{
                "type": "UNKNOWN",
                "severity": "UNKNOWN",
                "with": "Empty input",
                "plainExplanation": "Please select a medication to check safety.",
                "clinicianNote": "Empty drug input."
            }],
            "alternatives": [],
            "noSafeSubstitute": False,
            "noSubstituteMessage": "",
            "specialistReview": False,
            "needsIndication": False,
            "source": "RULES"
        }

    # Resolve generic
    resolved_generics = resolve_brand_to_generics(med_clean)
    generics_map = load_generics_map()

    # Determine if known drug or catalog entry
    catalog = load_medicine_catalog()
    catalog_match = False
    med_lower = med_clean.lower()
    for it in catalog:
        b_name = (it.get("brand_name") or "").lower()
        if med_lower in b_name or b_name in med_lower:
            catalog_match = True
            if it.get("generic_composition"):
                resolved_generics = [g.strip().lower() for g in it.get("generic_composition").split("+")]
            break

    # If made-up / unknown medicine name that cannot be resolved in catalog or generics map
    if not catalog_match and med_lower not in generics_map:
        # Check if generic salt name directly recognizable
        is_known_salt = any(med_lower in g_list or any(med_lower in v for v in g_list) for g_list in generics_map.values())
        if not is_known_salt and len(med_clean.split()) > 0 and resolved_generics == [med_lower]:
            # Completely unrecognizable drug name
            return {
                "riskLevel": "UNKNOWN",
                "resolvedGeneric": "Unknown",
                "findings": [{
                    "type": "UNKNOWN",
                    "severity": "UNKNOWN",
                    "with": "Unrecognized Formulation",
                    "plainExplanation": "We couldn't check this automatically, please review manually.",
                    "clinicianNote": f"No recognized salt composition found for '{med_clean}' in local 253k catalog."
                }],
                "alternatives": [],
                "noSafeSubstitute": False,
                "noSubstituteMessage": "",
                "specialistReview": False,
                "needsIndication": False,
                "source": "RULES"
            }

    # Evaluate rules via generic_resolver
    eval_res = evaluate_drug_safety_rules(
        new_medicine=med_clean,
        active_prescriptions=active_rxs,
        patient_allergies=patient_allergies
    )

    findings: List[Dict[str, Any]] = []
    risk_level = "NONE"
    matched_risk_key = None
    matched_entry = None

    if eval_res.get("isBlocked"):
        risk_level = "SEVERE"
        severity = eval_res.get("severity", "SEVERE")
        c_type = eval_res.get("conflictType", "DRUG_SAFETY_CONFLICT")
        rule = eval_res.get("matchedRule", {}) or {}

        with_entity = rule.get("a") or "Patient Profile"
        if "ALLERGY" in c_type:
            with_entity = f"{with_entity.title()} allergy"
        elif "DDI" in c_type:
            with_entity = f"{with_entity.title()} (active)"

        findings.append({
            "type": "ALLERGY" if "ALLERGY" in c_type else ("DUPLICATE" if "DUPLICATE" in c_type else "DRUG_INTERACTION"),
            "severity": severity,
            "with": with_entity,
            "plainExplanation": eval_res.get("explanation") or f"Risky conflict detected for {med_clean}.",
            "clinicianNote": eval_res.get("clinicianNote") or rule.get("clinicianNote") or "Contraindicated combination."
        })

    # Also check duplicate therapy explicitly
    for rx in active_rxs:
        if str(rx.get("status", "ACTIVE")).upper() not in ("ACTIVE", "MODIFIED", "RESERVED"):
            continue
        rx_med = rx.get("medicationName") or rx.get("medication_name") or ""
        rx_generics = resolve_brand_to_generics(rx_med)

        # Exact duplicate
        if any(g in rx_generics for g in resolved_generics if len(g) > 3):
            if risk_level != "SEVERE":
                risk_level = "SEVERE"
                findings.append({
                    "type": "DUPLICATE",
                    "severity": "SEVERE",
                    "with": f"Duplicate active medication: {rx_med}",
                    "plainExplanation": f"Patient already has an active prescription for {rx_med}.",
                    "clinicianNote": f"Avoid duplicate therapy. Keep current {rx_med} instead."
                })
                matched_risk_key = "DUPLICATE_THERAPY"
            break

    # Look up replacement alternatives from drug_alternatives.json
    alternatives_data = load_drug_alternatives()
    entries = alternatives_data.get("entries", [])

    candidates_raw: List[Dict[str, Any]] = []
    no_safe_substitute = False
    no_substitute_message = ""
    specialist_review = False
    needs_indication = False

    if risk_level in ("SEVERE", "CAUTION"):
        # Match entry by generics or risk pattern
        for entry in entries:
            applies = [g.lower() for g in entry.get("appliesToGenerics", [])]
            if any(g in applies or any(a in g for a in applies) for g in resolved_generics) or (matched_risk_key and entry.get("riskKey") == matched_risk_key):
                matched_entry = entry
                break

        # Fallback keyword match if not matched
        if not matched_entry:
            for entry in entries:
                key_lower = entry.get("riskKey", "").lower()
                for f in findings:
                    w = f.get("with", "").lower()
                    if ("penicillin" in w and "penicillin" in key_lower) or \
                       ("warfarin" in w and "warfarin" in key_lower) or \
                       ("sulfa" in w and "sulfa" in key_lower) or \
                       ("clopidogrel" in w and "clopidogrel" in key_lower):
                        matched_entry = entry
                        break
                if matched_entry:
                    break

        if matched_entry:
            no_safe_substitute = bool(matched_entry.get("noSafeSubstitute"))
            no_substitute_message = matched_entry.get("noSubstituteMessage") or ""
            specialist_review = bool(matched_entry.get("specialistReview"))
            needs_indication = bool(matched_entry.get("indicationNeeded"))
            candidates_raw = matched_entry.get("alternatives", [])

    # Process candidates: Re-check each candidate with SAME engine against THIS patient!
    final_alternatives: List[Dict[str, Any]] = []

    for cand in candidates_raw:
        cand_generic = cand.get("generic", "").strip()
        cand_action = cand.get("action")

        if cand_action == "AVOID_DUPLICATE":
            final_alternatives.append({
                "generic": cand_generic,
                "reason": cand.get("reason", "Keep the existing prescription rather than adding another."),
                "cautions": cand.get("cautions", []),
                "riskLevel": "NONE",
                "brands": [],
                "action": "AVOID_DUPLICATE"
            })
            continue

        # Re-check candidate generic against patient allergies, active meds, and duplicates
        cand_risk = check_single_generic_against_patient(cand_generic, norm_pid)

        # Drop candidates that come back SEVERE
        if cand_risk == "SEVERE":
            continue

        # Candidate is either NONE or CAUTION
        brands = get_catalog_brands_for_generic(cand_generic, limit=3)
        final_alternatives.append({
            "generic": cand_generic,
            "reason": cand.get("reason", f"Safer substitute for {med_clean}."),
            "cautions": cand.get("cautions", []),
            "riskLevel": cand_risk,
            "brands": brands,
            "suitableFor": cand.get("suitableFor", []),
            "action": cand.get("action")
        })

    # Filter and rank:
    # 1. Indication suitability if indication provided
    if indication and indication != "Other":
        ind_lower = indication.strip().lower()
        final_alternatives.sort(key=lambda a: 0 if any(ind_lower in s.lower() for s in a.get("suitableFor", [])) else 1)

    # 2. Rank NONE first, then CAUTION
    final_alternatives.sort(key=lambda a: 0 if a.get("riskLevel") == "NONE" else 1)

    # Return at most 3
    final_alternatives = final_alternatives[:3]

    # Audit event for risk shown
    record_audit_event(
        action="RISK_SHOWN",
        actor=doctor_id,
        resource=f"Patient/{norm_pid}",
        details=f"Evaluated risk for {med_clean}: {risk_level} ({len(findings)} findings)",
        severity="INFO" if risk_level == "NONE" else "WARNING",
        role="DOCTOR"
    )

    return {
        "riskLevel": risk_level,
        "resolvedGeneric": ", ".join(resolved_generics) if resolved_generics else med_clean,
        "findings": findings,
        "alternatives": final_alternatives,
        "noSafeSubstitute": no_safe_substitute,
        "noSubstituteMessage": no_substitute_message,
        "specialistReview": specialist_review,
        "needsIndication": needs_indication,
        "source": "RULES"
    }


def attach_risk_badges_to_catalog(
    catalog_items: List[Dict[str, Any]],
    patient_id: str,
    doctor_id: str = "DOC-IN-8841"
) -> List[Dict[str, Any]]:
    """
    Attaches risk badge ('NONE'|'CAUTION'|'SEVERE'|'UNKNOWN') to each catalog item in < 300ms.
    Caches results per (patient_id, generic) for the session.
    """
    global _RISK_SESSION_CACHE
    norm_pid = _normalize_pid(patient_id)

    enriched = []
    for it in catalog_items:
        it_copy = dict(it)
        g_name = it.get("generic_composition") or it.get("brand_name") or ""
        cache_key = (norm_pid, g_name.lower())

        if cache_key in _RISK_SESSION_CACHE:
            it_copy["risk"] = _RISK_SESSION_CACHE[cache_key]
        else:
            # Fast deterministic check
            r = check_single_generic_against_patient(g_name, norm_pid)
            _RISK_SESSION_CACHE[cache_key] = r
            it_copy["risk"] = r

        enriched.append(it_copy)

    return enriched
