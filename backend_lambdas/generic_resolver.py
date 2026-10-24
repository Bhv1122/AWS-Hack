"""
Generic Drug Resolution & Interaction Engine
Maps commercial Indian brand names to active generic ingredients from
medicine_generics.json and evaluates clinical safety against the 42-rule
drug_interactions.json dataset.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_DIR = os.path.join(BASE_DIR, "seed_data")

_GENERICS_MAP: Optional[Dict[str, List[str]]] = None
_INTERACTION_RULES: Optional[List[Dict[str, Any]]] = None


def load_generics_map() -> Dict[str, List[str]]:
    global _GENERICS_MAP
    if _GENERICS_MAP is not None:
        return _GENERICS_MAP
    g_path = os.path.join(SEED_DIR, "medicine_generics.json")
    if os.path.exists(g_path):
        with open(g_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            # Store lowercased keys and values
            _GENERICS_MAP = {k.strip().lower(): [v.strip().lower() for v in vals] for k, vals in raw.items()}
    else:
        _GENERICS_MAP = {}
    return _GENERICS_MAP


def load_interaction_rules() -> List[Dict[str, Any]]:
    global _INTERACTION_RULES
    if _INTERACTION_RULES is not None:
        return _INTERACTION_RULES
    r_path = os.path.join(SEED_DIR, "drug_interactions.json")
    if os.path.exists(r_path):
        with open(r_path, "r", encoding="utf-8") as f:
            _INTERACTION_RULES = json.load(f)
    else:
        _INTERACTION_RULES = []
    return _INTERACTION_RULES


def resolve_brand_to_generics(brand_or_med_name: str) -> List[str]:
    """
    Resolves commercial brand name (e.g., 'Augmentin 625 Duo Tablet', 'Ecosprin 75', 'Bactrim DS')
    to its constituent active generic salts:
      'Augmentin 625 Duo' -> ['amoxicillin', 'clavulanic acid']
      'Ecosprin 75'       -> ['aspirin']
      'Bactrim DS'        -> ['trimethoprim', 'sulfamethoxazole']
    """
    if not brand_or_med_name or not isinstance(brand_or_med_name, str):
        return []
    
    clean = brand_or_med_name.strip().lower()
    # Strip common dosage form suffixes for matching
    clean_stripped = re.sub(r"\b(tablet|capsule|syrup|injection|drops|inhaler|gel|cream|mg|mcg|gm|ml|duo|ds|sr|er|xl)\b", "", clean).strip()
    clean_stripped = re.sub(r"\s+", " ", clean_stripped).strip()

    g_map = load_generics_map()

    # 1. Exact match in catalog
    if clean in g_map:
        return g_map[clean]
    if clean_stripped in g_map:
        return g_map[clean_stripped]

    # 2. Check words or partial key matching
    for k, v in g_map.items():
        if k == clean or k == clean_stripped:
            return v
        if len(k) >= 5 and (k in clean or clean in k):
            return v

    # 3. Common built-in aliases
    aliases = {
        "augmentin": ["amoxicillin", "clavulanic acid"],
        "amoxyclav": ["amoxicillin", "clavulanic acid"],
        "ecosprin": ["aspirin"],
        "disprin": ["aspirin"],
        "aspro": ["aspirin"],
        "bactrim": ["trimethoprim", "sulfamethoxazole"],
        "septra": ["trimethoprim", "sulfamethoxazole"],
        "zifi": ["cefixime"],
        "azithral": ["azithromycin"],
        "azee": ["azithromycin"],
        "zithromax": ["azithromycin"],
        "calpol": ["paracetamol"],
        "crocin": ["paracetamol"],
        "dolo": ["paracetamol"],
        "glycomet": ["metformin"],
        "atorva": ["atorvastatin"],
        "lipitor": ["atorvastatin"],
        "pan": ["pantoprazole"],
        "pantocid": ["pantoprazole"],
        "cifran": ["ciprofloxacin"],
        "plavix": ["clopidogrel"],
        "deplatt": ["clopidogrel"],
        "clopilet": ["clopidogrel"],
        "coumadin": ["warfarin"],
        "viagra": ["sildenafil"],
        "ultram": ["tramadol"],
        "zestril": ["lisinopril"],
        "asthalin": ["salbutamol"],
        "deriphyllin": ["theophylline", "etofylline"]
    }

    for a_key, a_vals in aliases.items():
        if a_key in clean or a_key in clean_stripped:
            return a_vals

    # Fallback: treat the cleaned string itself as a candidate generic name
    return [clean_stripped or clean]


def evaluate_drug_safety_rules(
    new_medicine: str,
    active_prescriptions: List[Dict[str, Any]],
    patient_allergies: List[str]
) -> Dict[str, Any]:
    """
    Evaluates new medication against the 42-rule interaction dataset:
      1. Allergy conflicts (Penicillin class, Sulfa class, Aspirin/NSAID sensitivity)
      2. Drug-Drug Interactions (DDI: Warfarin + Aspirin/NSAID, Clopidogrel + Omeprazole, etc.)
      3. Duplicate therapies (2 concurrent NSAIDs, ACE-I + ARB)
    
    Returns structured result including 'source': 'RULES' and 'matchedRule'.
    """
    new_generics = resolve_brand_to_generics(new_medicine)
    new_generics_set = set(new_generics)
    new_med_lower = new_medicine.strip().lower()

    # Active medications resolved to generics
    active_drugs_resolved: List[Tuple[Dict[str, Any], List[str]]] = []
    for rx in active_prescriptions:
        rx_status = str(rx.get("status", "ACTIVE")).upper()
        if rx_status in ("ACTIVE", "MODIFIED"):
            rx_name = rx.get("medicationName") or rx.get("medication_name") or ""
            rx_generics = resolve_brand_to_generics(rx_name)
            active_drugs_resolved.append((rx, rx_generics))

    # Clean patient allergies
    norm_allergies = [a.strip().lower() for a in patient_allergies if a and str(a).strip()]

    rules = load_interaction_rules()

    # --- CHECK 1: ALLERGY RULES ---
    for rule in rules:
        if rule.get("type") == "ALLERGY":
            rule_a = rule.get("a", "").strip().lower()
            rule_b = rule.get("b", "").strip().lower()
            
            # Check if patient has allergy to rule_a (e.g. penicillin, sulfa, aspirin)
            allergy_match = any(rule_a in alg or alg in rule_a for alg in norm_allergies)
            if allergy_match:
                # Check if new medicine contains rule_b (e.g. amoxicillin, amoxicillin-clavulanate, sulfamethoxazole)
                target_matches = False
                for g in new_generics:
                    if rule_b in g or g in rule_b or rule_b in new_med_lower:
                        target_matches = True
                        break
                
                # Broad class check: penicillin allergy blocks amoxicillin, augmentin, ampicillin
                if rule_a in ("penicillin", "beta-lactam") and any(
                    x in g or x in new_med_lower for g in new_generics for x in ("amox", "ampicil", "penicil", "clav")
                ):
                    target_matches = True

                # Sulfa allergy blocks sulfamethoxazole, cotrimoxazole, bactrim
                if rule_a == "sulfa" and any(
                    x in g or x in new_med_lower for g in new_generics for x in ("sulfa", "trimethoprim", "bactrim", "septra")
                ):
                    target_matches = True

                # Aspirin allergy blocks NSAIDs
                if rule_a in ("aspirin", "nsaids") and any(
                    x in g or x in new_med_lower for g in new_generics for x in ("aspirin", "ibuprofen", "diclofenac", "naproxen")
                ):
                    target_matches = True

                if target_matches:
                    return {
                        "isBlocked": True,
                        "severity": rule.get("severity", "SEVERE"),
                        "source": "RULES",
                        "matchedRule": rule,
                        "conflictType": "ALLERGY_CONFLICT",
                        "explanation": rule.get("clinicalExplanation") or f"Patient has documented {rule_a.title()} allergy which cross-reacts with {new_medicine}.",
                        "clinicianNote": rule.get("clinicianNote", ""),
                        "monitoring": rule.get("monitoring", ""),
                        "safer_alternatives": rule.get("alternatives", []),
                        "mechanism": rule.get("mechanism", "")
                    }

    # --- CHECK 2: DRUG-DRUG INTERACTIONS (DDI) ---
    for rule in rules:
        if rule.get("type") == "DDI":
            rule_a = rule.get("a", "").strip().lower()
            rule_b = rule.get("b", "").strip().lower()

            for rx, rx_generics in active_drugs_resolved:
                rx_name = rx.get("medicationName") or rx.get("medication_name") or ""
                rx_name_lower = rx_name.lower()

                # Check if new_med has rule_a and rx has rule_b, or vice-versa
                new_has_a = any(rule_a in g or rule_a in new_med_lower for g in new_generics)
                new_has_b = any(rule_b in g or rule_b in new_med_lower for g in new_generics)
                rx_has_a = any(rule_a in g or rule_a in rx_name_lower for g in rx_generics)
                rx_has_b = any(rule_b in g or rule_b in rx_name_lower for g in rx_generics)

                # Special generic aliases (e.g. nsaids class)
                if rule_b == "nsaids":
                    new_has_b = any(x in g for g in new_generics for x in ("ibuprofen", "diclofenac", "naproxen", "etodolac"))
                    rx_has_b = any(x in g for g in rx_generics for x in ("ibuprofen", "diclofenac", "naproxen", "etodolac"))

                if (new_has_a and rx_has_b) or (new_has_b and rx_has_a):
                    return {
                        "isBlocked": rule.get("severity") in ("SEVERE", "CRITICAL"),
                        "severity": rule.get("severity", "SEVERE"),
                        "source": "RULES",
                        "matchedRule": rule,
                        "conflictType": "DRUG_DRUG_INTERACTION",
                        "interactingWith": rx_name,
                        "prescribedBy": rx.get("prescribedBy") or rx.get("doctor_name", "Previous Attending Physician"),
                        "explanation": rule.get("clinicalExplanation") or f"Severe interaction between {new_medicine} and active {rx_name}.",
                        "clinicianNote": rule.get("clinicianNote", ""),
                        "monitoring": rule.get("monitoring", ""),
                        "safer_alternatives": rule.get("alternatives", []),
                        "mechanism": rule.get("mechanism", "")
                    }

    # --- CHECK 3: DUPLICATE THERAPY ---
    for rule in rules:
        if rule.get("type") == "DUPLICATE":
            rule_a = rule.get("a", "").strip().lower()
            rule_b = rule.get("b", "").strip().lower()

            for rx, rx_generics in active_drugs_resolved:
                rx_name = rx.get("medicationName") or rx.get("medication_name") or ""
                rx_name_lower = rx_name.lower()

                # Check duplicate NSAIDs or ACEI + ARB or exact drug duplicate
                new_has_a = any(rule_a in g or rule_a in new_med_lower for g in new_generics)
                new_has_b = any(rule_b in g or rule_b in new_med_lower for g in new_generics)
                rx_has_a = any(rule_a in g or rule_a in rx_name_lower for g in rx_generics)
                rx_has_b = any(rule_b in g or rule_b in rx_name_lower for g in rx_generics)

                is_duplicate = False
                if rule_a == rule_b and (new_has_a and rx_has_b):
                    is_duplicate = True
                elif (new_has_a and rx_has_b) or (new_has_b and rx_has_a):
                    is_duplicate = True

                if is_duplicate:
                    return {
                        "isBlocked": rule.get("severity") in ("SEVERE", "CRITICAL"),
                        "severity": rule.get("severity", "MODERATE"),
                        "source": "RULES",
                        "matchedRule": rule,
                        "conflictType": "DUPLICATE_THERAPY",
                        "interactingWith": rx_name,
                        "explanation": rule.get("clinicalExplanation") or f"Duplicate therapy: {new_medicine} overlaps with active {rx_name}.",
                        "clinicianNote": rule.get("clinicianNote", ""),
                        "monitoring": rule.get("monitoring", ""),
                        "safer_alternatives": rule.get("alternatives", [])
                    }

    # Clean pass
    return {
        "isBlocked": False,
        "severity": "SAFE",
        "source": "RULES",
        "matchedRule": None,
        "explanation": "No clinical conflicts detected.",
        "safer_alternatives": []
    }
