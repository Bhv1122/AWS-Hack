"""
Test Suite: tests/test_seed_integrity.py
Validates:
1. All 15 seed datasets in seed_data/ meet minimum counts and schema requirements.
2. Referential integrity across patients, doctors, hospitals, prescriptions, reports, adherence, and audit logs.
3. All mandatory clinical scenarios (silicosis, byssinosis, DVT, HbA1c/INR trends, duplicate therapies, allergy conflicts).
4. DEMO_ACCOUNTS.md exists, non-empty, and satisfies all scenario credentials.
"""

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from seed_data.validate_seed import validate_seed


class TestSeedIntegrity(unittest.TestCase):
    def test_full_seed_validation(self):
        """Executes full Phase 1 synthetic seed dataset validation suite."""
        success = validate_seed()
        self.assertTrue(success, "Seed dataset validation failed. Check console output for details.")


if __name__ == "__main__":
    unittest.main()
