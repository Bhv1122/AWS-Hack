"""
Test Suite: tests/test_generic_resolution.py
Validates:
1. At least 20 brand -> generic resolution mappings against medicine_generics.json.
2. Clinical Safety Rule Interceptions triggered on generic active ingredients (DDI, Allergy, Duplicate).
"""

import os
import sys
import json
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend_lambdas.generic_resolver import resolve_brand_to_generics, evaluate_drug_safety_rules


class TestGenericResolution(unittest.TestCase):
    def test_01_twenty_brand_mappings(self):
        """Verifies at least 20 common Indian brand names accurately resolve to their generic active salts."""
        cases = [
            ("Augmentin 625 Duo Tablet", ["amoxicillin", "clavulanic acid"]),
            ("Ecosprin 75 Tablet", ["aspirin"]),
            ("Glycomet 500 Tablet", ["metformin"]),
            ("Lipitor 10mg", ["atorvastatin"]),
            ("Calpol 500 Tablet", ["paracetamol"]),
            ("Crocin Advance", ["paracetamol"]),
            ("Dolo 650", ["paracetamol"]),
            ("Pan 40 Tablet", ["pantoprazole"]),
            ("Omez 20mg Capsule", ["omeprazole"]),
            ("Zithromax 500", ["azithromycin"]),
            ("Combiflam Tablet", ["ibuprofen", "paracetamol"]),
            ("Voveran 50 GE", ["diclofenac"]),
            ("Telma 40 Tablet", ["telmisartan"]),
            ("Cifran 500 Tablet", ["ciprofloxacin"]),
            ("Allegra 120mg Tablet", ["fexofenadine"]),
            ("Septra DS", ["co-trimoxazole", "trimethoprim", "sulfamethoxazole"]),
            ("Bactrim DS", ["sulfamethoxazole", "trimethoprim"]),
            ("Plavix 75mg", ["clopidogrel"]),
            ("Coumadin 5mg", ["warfarin"]),
            ("Viagra 50mg", ["sildenafil"]),
            ("Ultram 50mg", ["tramadol"]),
            ("Zestril 10mg", ["lisinopril"]),
        ]
        
        verified_count = 0
        for brand, expected_generics in cases:
            resolved = resolve_brand_to_generics(brand)
            self.assertTrue(len(resolved) > 0, f"Failed resolving generics for '{brand}'")
            found = any(any(exp in r for r in resolved) for exp in expected_generics)
            self.assertTrue(found, f"Expected {expected_generics} for {brand}, resolved: {resolved}")
            verified_count += 1

        self.assertGreaterEqual(verified_count, 20)

    def test_02_penicillin_allergy_interception(self):
        """Augmentin (amoxicillin) must be BLOCKED when patient has Penicillin allergy."""
        active_rx = [{"medication_name": "Metformin 500mg", "dosage": "500mg"}]
        allergies = ["Penicillin"]
        result = evaluate_drug_safety_rules("Augmentin 625 Duo Tablet", active_rx, allergies)
        self.assertTrue(result.get("isBlocked"))
        self.assertEqual(result.get("conflictType"), "ALLERGY_CONFLICT")
        self.assertEqual(result.get("severity"), "SEVERE")
        self.assertEqual(result.get("source"), "RULES")
        self.assertIn("amoxicillin", result.get("matchedRule", {}).get("b", "").lower())

    def test_03_warfarin_aspirin_ddi_interception(self):
        """Aspirin / Ecosprin must be BLOCKED when patient is taking Warfarin."""
        active_rx = [{"medication_name": "Warfarin 5mg", "dosage": "5mg"}]
        allergies = []
        result = evaluate_drug_safety_rules("Ecosprin 75 Tablet", active_rx, allergies)
        self.assertTrue(result.get("isBlocked"))
        self.assertEqual(result.get("conflictType"), "DRUG_DRUG_INTERACTION")
        self.assertEqual(result.get("source"), "RULES")

    def test_04_warfarin_nsaid_ddi_interception(self):
        """Diclofenac (Voveran) must be BLOCKED when patient is taking Warfarin."""
        active_rx = [{"medication_name": "Warfarin 5mg", "dosage": "5mg"}]
        allergies = []
        result = evaluate_drug_safety_rules("Voveran 50 GE", active_rx, allergies)
        self.assertTrue(result.get("isBlocked"))
        self.assertEqual(result.get("conflictType"), "DRUG_DRUG_INTERACTION")

    def test_05_sulfa_allergy_interception(self):
        """Bactrim / Septra must be BLOCKED when patient has a Sulfa allergy."""
        active_rx = []
        allergies = ["Sulfa Drugs"]
        result = evaluate_drug_safety_rules("Bactrim DS Tablet", active_rx, allergies)
        self.assertTrue(result.get("isBlocked"))
        self.assertEqual(result.get("conflictType"), "ALLERGY_CONFLICT")

    def test_06_duplicate_therapy_interception(self):
        """Prescribing Telmisartan (Telma) when patient is on Ramipril must trigger DUPLICATE therapy alert."""
        active_rx = [{"medication_name": "Ramipril 5mg", "dosage": "5mg"}]
        allergies = []
        result = evaluate_drug_safety_rules("Telma 40 Tablet", active_rx, allergies)
        self.assertTrue(result.get("isBlocked"))
        self.assertEqual(result.get("conflictType"), "DUPLICATE_THERAPY")

    def test_07_clean_drug_passes(self):
        """Prescribing safe non-conflicting drug (e.g. Paracetamol) with no allergy returns unblocked."""
        active_rx = [{"medication_name": "Metformin 500mg", "dosage": "500mg"}]
        allergies = ["Penicillin"]
        result = evaluate_drug_safety_rules("Crocin Advance", active_rx, allergies)
        self.assertFalse(result.get("isBlocked"))
        self.assertEqual(result.get("severity"), "SAFE")


if __name__ == "__main__":
    unittest.main()
