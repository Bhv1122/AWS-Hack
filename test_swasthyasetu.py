"""
Test Suite for SwasthyaSetu — AI-Powered Portable Healthcare Platform for Migrant Workers
Verifies all 5 modules:
  - Module A: SwasthyaID (Portable Health Passport & Consent QR Access)
  - Module B: BhashaSehat (Multilingual Translation & Clinical Extraction)
  - Module C: Document AI (Prescription Digitization & FHIR R4 Archive)
  - Module D: KaamSuraksha (Occupational Health Risk Engine)
  - Module E: SehatSetu (Cross-State Care Continuity & Multilingual Alerts)
"""

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 output on Windows consoles for Indic scripts
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend_lambdas.swasthyasetu_engine import (
    enrich_or_register_swasthya_profile,
    generate_swasthya_qr_token,
    verify_qr_consent_access,
    translate_medical_conversation,
    scan_and_digitize_prescription,
    assess_occupational_risk,
    schedule_cross_state_followup,
    get_swasthya_migrant_summary
)


def test_module_a():
    print("\n" + "=" * 60)
    print("TEST 1: MODULE A — SwasthyaID Portable Health Passport & Consent QR")
    print("=" * 60)

    # 1. Enrich migrant profile
    profile = enrich_or_register_swasthya_profile("PAT-1001")
    assert profile.get("abhaId") == "ABHA-21-9845-3310-7742", f"Unexpected abhaId: {profile.get('abhaId')}"
    assert profile.get("originState") == "Odisha", f"Unexpected originState: {profile.get('originState')}"
    assert "Bengaluru" in profile.get("currentLocation", ""), f"Unexpected currentLocation: {profile.get('currentLocation')}"
    assert profile.get("preferredLanguage") == "Odia", f"Unexpected preferredLanguage: {profile.get('preferredLanguage')}"
    assert profile.get("occupation") == "Construction Site Mason", f"Unexpected occupation: {profile.get('occupation')}"
    assert profile.get("exposureYears") == 6, f"Unexpected exposureYears: {profile.get('exposureYears')}"
    assert profile.get("ashaWorkerId") == "ASHA-OD-402", f"Unexpected ashaWorkerId: {profile.get('ashaWorkerId')}"
    assert profile.get("consentStatus") == "GRANTED_WITH_OTP", f"Unexpected consentStatus: {profile.get('consentStatus')}"
    print("  [PASS] Migrant worker profile enriched with required SwasthyaID attributes.")

    # 2. Generate QR Token
    qr_data = generate_swasthya_qr_token("PAT-1001", expiry_minutes=30)
    assert qr_data.get("status") == "SUCCESS", "Failed to generate QR token"
    assert "SWASTHYA-QR-PAT-1001-" in qr_data.get("qrToken", ""), f"Invalid token format: {qr_data.get('qrToken')}"
    assert qr_data.get("demoVerificationOtp") == "402198", "Expected demo OTP 402198"
    print(f"  [PASS] SwasthyaID QR token generated: {qr_data.get('qrToken')} (OTP: {qr_data.get('demoVerificationOtp')})")

    # 3. Verify QR Consent Access
    consent_result = verify_qr_consent_access(
        patient_id="PAT-1001",
        clinic_name="Bengaluru Urban Health Clinic",
        doctor_name="Dr. Sarah Jenkins",
        otp_code="402198"
    )
    assert consent_result.get("status") == "CONSENT_VERIFIED_ACCESS_GRANTED", "Failed consent verification"
    assert "QR Health Passport accessed by Dr. Sarah Jenkins" in consent_result.get("message", "")
    assert "activePrescriptions" in consent_result
    assert "allergies" in consent_result.get("patient", {})
    print("  [PASS] Consent verified and longitudinal cross-state history unlocked successfully.")

    # 4. Negative test: invalid OTP format
    try:
        verify_qr_consent_access("PAT-1001", otp_code="ABC")
        assert False, "Should have rejected non-numeric OTP"
    except ValueError as ve:
        print(f"  [PASS] Rejected invalid OTP as expected: {ve}")


def test_module_b():
    print("\n" + "=" * 60)
    print("TEST 2: MODULE B — BhashaSehat Multilingual Translator")
    print("=" * 60)

    # 1. English to Odia (Chest pain)
    res_odia = translate_medical_conversation(
        text="I have severe chest pain and tightness",
        source_lang="English",
        target_lang="Odia",
        speaker_role="PATIENT"
    )
    assert res_odia.get("originalText") == "I have severe chest pain and tightness"
    assert res_odia.get("translatedText") != ""
    assert "Chest Pain" in " ".join(res_odia.get("extractedClinicalSymptoms", []))
    assert res_odia.get("awsServiceUsed") != ""
    print(f"  [PASS] English -> Odia: {res_odia.get('translatedText')} (Phonetic: {res_odia.get('phonetic')})")
    print(f"         Symptoms extracted: {res_odia.get('extractedClinicalSymptoms')}")

    # 2. English to Kannada (Doctor dosage instructions)
    res_kannada = translate_medical_conversation(
        text="Take one tablet twice daily after meals",
        source_lang="English",
        target_lang="Kannada",
        speaker_role="DOCTOR"
    )
    assert res_kannada.get("translatedText") != ""
    assert res_kannada.get("phonetic") != ""
    print(f"  [PASS] English -> Kannada: {res_kannada.get('translatedText')} (Phonetic: {res_kannada.get('phonetic')})")

    # 3. Odia native script input to English (Construction dust cough)
    res_cough = translate_medical_conversation(
        text="ମୋତେ ବହୁତ ଶୁଖିଲା କାଶ ହେଉଛି",
        source_lang="Odia",
        target_lang="English",
        speaker_role="PATIENT"
    )
    assert "cough" in res_cough.get("translatedText", "").lower()
    assert any("Cough" in s for s in res_cough.get("extractedClinicalSymptoms", []))
    print(f"  [PASS] Odia Script -> English: {res_cough.get('translatedText')}")
    print(f"         Symptoms: {res_cough.get('extractedClinicalSymptoms')}")


def test_module_c():
    print("\n" + "=" * 60)
    print("TEST 3: MODULE C — Document AI Prescription Digitizer & FHIR Archive")
    print("=" * 60)

    res_doc = scan_and_digitize_prescription(
        patient_id="PAT-1001",
        document_title="Odisha District Hospital Historical Prescription",
        raw_ocr_text_or_sample_type="odisha_clinic_paper_rx"
    )
    assert res_doc.get("status") == "SUCCESS_DIGITIZED", "Document digitization failed"
    assert "s3://" in res_doc.get("s3Uri", ""), f"Missing S3 URI: {res_doc.get('s3Uri')}"
    assert len(res_doc.get("extractedMedications", [])) > 0, "No medications extracted"
    assert res_doc.get("fhirResource", {}).get("resourceType") == "DocumentReference"

    med_names = [m.get("medication_name") for m in res_doc.get("extractedMedications", [])]
    print(f"  [PASS] Paper prescription archived to: {res_doc.get('s3Uri')}")
    print(f"         Extracted medications: {med_names}")
    print(f"         Safety warnings detected: {len(res_doc.get('drugInteractionWarnings', []))}")
    print(f"         FHIR R4 Resource Type: {res_doc.get('fhirResource', {}).get('resourceType')}")


def test_module_d():
    print("\n" + "=" * 60)
    print("TEST 4: MODULE D — KaamSuraksha Occupational Health Risk Engine")
    print("=" * 60)

    # 1. Construction / Masonry with silica dust
    occ_res = assess_occupational_risk(
        patient_id="PAT-1001",
        occupation="Construction Site Mason",
        exposure_years=6,
        reported_symptoms=["persistent cough", "chest tightness"]
    )
    assert occ_res.get("riskLevel") == "HIGH", f"Expected HIGH risk, got {occ_res.get('riskLevel')}"
    conds = [c.get("condition") for c in occ_res.get("predictedOccupationalConditions", [])]
    assert any("Silicosis" in c for c in conds), f"Silicosis not found in: {conds}"
    assert any("COPD" in c for c in conds), f"COPD not found in: {conds}"
    screenings = occ_res.get("recommendedScreenings", [])
    assert any("Chest X-Ray" in s for s in screenings), "Expected Chest X-Ray recommendation"
    assert any("Spirometry" in s for s in screenings), "Expected Spirometry recommendation"
    print(f"  [PASS] Construction Masonry Risk: {occ_res.get('riskLevel')} (Score: {occ_res.get('riskScore')}/100)")
    print(f"         Predicted Conditions: {conds}")
    print(f"         Recommended Screenings: {screenings}")

    # 2. Textile / Garment (Byssinosis / Monday fever)
    textile_res = assess_occupational_risk(
        patient_id="PAT-1001",
        occupation="Textile Mill Spinner",
        exposure_years=4
    )
    t_conds = [c.get("condition") for c in textile_res.get("predictedOccupationalConditions", [])]
    assert any("Byssinosis" in c for c in t_conds), f"Byssinosis not found in: {t_conds}"
    print(f"  [PASS] Textile Worker Risk: {textile_res.get('riskLevel')} (Found Byssinosis / Monday Fever)")

    # 3. Agriculture / Pesticide
    agri_res = assess_occupational_risk(
        patient_id="PAT-1001",
        occupation="Agricultural Farm Spraying Worker",
        exposure_years=3
    )
    a_conds = [c.get("condition") for c in agri_res.get("predictedOccupationalConditions", [])]
    assert any("Organophosphate" in c for c in a_conds), f"Organophosphate not found in: {a_conds}"
    print(f"  [PASS] Agriculture Worker Risk: {agri_res.get('riskLevel')} (Found Organophosphate toxicity)")

    # 4. Factory / Welding
    weld_res = assess_occupational_risk(
        patient_id="PAT-1001",
        occupation="Arc Welder & Grinder",
        exposure_years=5
    )
    w_conds = [c.get("condition") for c in weld_res.get("predictedOccupationalConditions", [])]
    assert any("Metal Fume" in c for c in w_conds), f"Metal Fume Fever not found in: {w_conds}"
    print(f"  [PASS] Welding Worker Risk: {weld_res.get('riskLevel')} (Found Metal Fume Fever & NIHL)")


def test_module_e():
    print("\n" + "=" * 60)
    print("TEST 5: MODULE E — SehatSetu Cross-State Care Continuity & Alerts")
    print("=" * 60)

    sync_res = schedule_cross_state_followup(
        patient_id="PAT-1001",
        followup_date="2026-11-20",
        current_clinic="Manipal Hospital Whitefield, Bengaluru",
        home_state_asha_id="ASHA-OD-402",
        notes="Monitor fasting blood sugar and check INR monthly; continue N95 dust protection.",
        preferred_language="Odia"
    )
    assert sync_res.get("status") == "SYNCHRONIZED_ACTIVE", "Care synchronization failed"
    alerts = sync_res.get("alerts", {})
    assert alerts.get("workerSmsEnglish") != "", "Missing English SMS"
    assert alerts.get("workerSmsNative") != "", "Missing Native Odia SMS"
    assert alerts.get("ashaCoordinatorAlert") != "", "Missing ASHA coordinator alert"
    assert "ASHA-OD-402" in alerts.get("ashaCoordinatorAlert", "")
    print("  [PASS] Care plan synchronized between Bengaluru and Odisha ASHA coordinator.")
    print(f"         English SMS: {alerts.get('workerSmsEnglish')[:120]}...")
    print(f"         Native Odia SMS: {alerts.get('workerSmsNative')[:120]}...")
    print(f"         ASHA Dispatch: {alerts.get('ashaCoordinatorAlert')[:120]}...")


def test_unified_summary():
    print("\n" + "=" * 60)
    print("TEST 6: Unified SwasthyaSetu Summary Aggregator")
    print("=" * 60)

    summary = get_swasthya_migrant_summary("PAT-1001")
    assert summary.get("patientId") == "PAT-1001"
    assert summary.get("swasthyaId", {}).get("abhaId") == "ABHA-21-9845-3310-7742"
    assert summary.get("occupationalRisk", {}).get("riskLevel") in ("HIGH", "MODERATE", "LOW")
    assert len(summary.get("digitizedPrescriptions", [])) > 0
    print("  [PASS] Unified SwasthyaSetu Migrant Summary compiled cleanly across all 5 modules.")


if __name__ == "__main__":
    print("Starting SwasthyaSetu End-to-End Validation...")
    test_module_a()
    test_module_b()
    test_module_c()
    test_module_d()
    test_module_e()
    test_unified_summary()
    print("\n" + "*" * 60)
    print("ALL SWASTHYA-SETU ENGINE TESTS PASSED WITH 100% SUCCESS!")
    print("*" * 60)
