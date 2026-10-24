#!/usr/bin/env python3
"""
show_demo_pin.py - Local command-line tool to inspect active Consent PIN
Reads directly from backend_lambdas/local_state.json (zero HTTP endpoints exposed).
Usage:
  python tests/show_demo_pin.py [patient_id]
"""

import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend_lambdas.aws_core import get_patient, local_store

def main():
    target_id = sys.argv[1] if len(sys.argv) > 1 else "PAT-SS-1001"
    clean_id = target_id.strip()
    norm_id = "PAT-1001" if clean_id.upper() in ("PAT-1001", "PAT-SS-1001", "PATIENT-001", "1001") else clean_id
    
    local_store.reload()
    p = get_patient(norm_id) or get_patient(clean_id)
    if not p:
        # Check swasthya_patients table or patient list
        state = local_store.load_all()
        for patient in state.get("patients", []):
            if patient.get("uniquePatientId") == clean_id or patient.get("patientId") == norm_id or patient.get("id") == norm_id:
                p = patient
                break
                
    if not p:
        print(f"Error: Patient '{target_id}' not found in local data store.", file=sys.stderr)
        sys.exit(1)
        
    pin = p.get("consentPin") or p.get("activeConsentPin") or "482910"
    name = p.get("name", "Unknown")
    revoked = p.get("consentRevoked", False)
    
    print(f"Patient ID:  {p.get('uniquePatientId') or target_id}")
    print(f"Name:        {name}")
    print(f"Consent PIN: {pin}")
    print(f"Revoked:     {revoked}")

if __name__ == "__main__":
    main()
