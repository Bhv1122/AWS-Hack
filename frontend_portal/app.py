"""
MedCoord Health - Patient-Doctor Medication Coordination Platform
Full-Stack Integrated Web Portal Server
-----------------------------------------------------------------
Bridges the frontend clinical & patient portal views with the
headless AWS Python backend (backend_lambdas) and root API Gateway
Lambda router (test_all_modules.py).
"""

import os
import sys
import json
import io
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Ensure project root is available on Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file

# Import unified API Gateway handler and backend engines
from test_all_modules import lambda_handler
from backend_lambdas.aws_core import (
    check_aws_integration_status,
    load_medicine_catalog,
    get_doctor_medicine_menu,
    search_medicine_catalog,
    get_medicine_by_id,
    record_audit_event,
    get_patient,
    get_patient_profile,
    list_all_prescriptions,
    local_store,
    convert_decimals,
    get_patient_timeline,
    generate_patient_prescription_pdf_export
)
from backend_lambdas.prescription_ai_engine import (
    get_doctor_patient_view,
    prescribe_medication,
    override_and_prescribe,
    manage_patient_allergies,
    modify_prescription_dosage,
    discontinue_prescription
)
from backend_lambdas.adherence_and_location import (
    get_patient_dashboard_view,
    get_caregiver_dashboard_view,
    log_medication_dose,
    find_nearby_stocked_pharmacies,
    locate_stocked_pharmacies,
    reserve_medication_at_pharmacy,
    request_prescription_refill
)
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


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("MedCoordPortal")

# Initialize Flask App
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=static_dir
)
app.config["JSON_SORT_KEYS"] = False
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "medcoord-secret-key-hipaa-compliant")


# ---------------------------------------------------------------------------
# Helper: Proxy Request to API Gateway Lambda Handler
# ---------------------------------------------------------------------------
def proxy_to_lambda(path: str, method: str, query_params: dict, headers: dict, body: Any):
    """
    Constructs a standard API Gateway v2 HTTP event and dispatches to
    our unified lambda_handler in test_all_modules.py.
    """
    event = {
        "rawPath": path,
        "path": path,
        "httpMethod": method,
        "queryStringParameters": query_params,
        "headers": headers,
        "body": json.dumps(body) if body is not None and not isinstance(body, str) else (body or ""),
        "requestContext": {
            "http": {
                "method": method,
                "path": path
            }
        }
    }
    response = lambda_handler(event, None)
    status_code = response.get("statusCode", 200)

    # Force flush and reload state store for mutating actions
    if method in ("POST", "PATCH", "PUT", "DELETE"):
        local_store.reload()

    response_body = response.get("body", "{}")
    if isinstance(response_body, str):
        try:
            parsed_data = json.loads(response_body)
        except Exception:
            parsed_data = {"raw": response_body}
    else:
        parsed_data = response_body
    return jsonify(parsed_data), status_code


# ---------------------------------------------------------------------------
# Frontend Page Routes (HTML Views)
# ---------------------------------------------------------------------------

@app.route("/")
def index_view():
    """Platform Hub / Landing Page with Role Navigation & Live AWS Health."""
    aws_status = check_aws_integration_status()
    return render_template(
        "index.html",
        aws_status=aws_status,
        active_role="DOCTOR",
        active_user_id="DOC-201"
    )


@app.route("/doctor")
def doctor_view():
    """
    Doctor Clinical Safety Workspace View.
    Pulls unified multi-doctor patient profiles, active prescriptions,
    verified allergies, adherence stats, and medicine catalog menu.
    """
    doctor_id = request.args.get("doctor_id", "DOC-201")
    patient_id = request.args.get("patient_id", "PAT-1001")
    local_store.reload()
    
    # Fetch real-time data directly from backend engine
    try:
        doctor_patient_data = get_doctor_patient_view(doctor_id, patient_id)
    except Exception as e:
        logger.error(f"Error fetching doctor patient view: {e}")
        doctor_patient_data = {"error": str(e), "patient_id": patient_id}

    # Fetch medicine menu categories for rapid prescription dropdown
    try:
        medicine_menu = get_doctor_medicine_menu(dosage_form="Tablet", limit=30)
    except Exception as e:
        logger.warning(f"Error fetching medicine menu: {e}")
        medicine_menu = {"categories": {}}

    aws_status = check_aws_integration_status()

    return render_template(
        "doctor.html",
        data=doctor_patient_data,
        medicine_menu=medicine_menu,
        aws_status=aws_status,
        doctor_id=doctor_id,
        patient_id=patient_id,
        active_role="DOCTOR"
    )


@app.route("/patient")
@app.route("/patient/<patient_id>")
def patient_view(patient_id=None):
    """
    Patient Medication Portal View.
    Pulls chronological daily dose schedule (08:00, 14:00, 20:00, 22:00),
    adherence scorecard, plain-language safety warnings, and 1-click dose telemetry.
    """
    if not patient_id:
        patient_id = request.args.get("patient_id", "PAT-1001")
    local_store.reload()
    try:
        patient_data = get_patient_dashboard_view(patient_id)
    except Exception as e:
        logger.error(f"Error fetching patient dashboard view: {e}")
        patient_data = {"error": str(e), "patient_id": patient_id}

    aws_status = check_aws_integration_status()

    return render_template(
        "patient.html",
        data=patient_data,
        aws_status=aws_status,
        patient_id=patient_id,
        active_role="PATIENT"
    )


@app.route("/pharmacy")
def pharmacy_view():
    """
    Pharmacy Stock & Location Finder View.
    Pulls geospatial pharmacy search results sorted by distance in km
    and drive time in minutes, with 1-stop multi-drug stock fulfillment.
    """
    patient_id = request.args.get("patient_id", "PAT-1001")
    lat = float(request.args.get("lat", 13.1155))
    lon = float(request.args.get("lon", 77.6070))
    radius = float(request.args.get("radius", 15.0))
    
    # Get active medications for patient to power 1-stop regimen search
    med_list = []
    try:
        dash = get_patient_dashboard_view(patient_id)
        for med in dash.get("active_medications", []):
            med_list.append(med.get("medication_name", ""))
    except Exception:
        med_list = ["Warfarin", "Metformin"]

    try:
        geo_results = find_nearby_stocked_pharmacies(
            patient_lat=lat,
            patient_lon=lon,
            medication_list=med_list,
            radius_km=radius
        )
    except Exception as e:
        logger.error(f"Error locating pharmacies: {e}")
        geo_results = {"full_match_pharmacies": [], "partial_match_pharmacies": []}

    aws_status = check_aws_integration_status()

    return render_template(
        "pharmacy.html",
        patient_id=patient_id,
        geo_results=geo_results,
        med_list=med_list,
        aws_status=aws_status,
        active_role="PHARMACY"
    )


@app.route("/audit")
def audit_view():
    """
    Immutable CloudTrail & KMS Compliance Audit Feed.
    Displays all tamper-evident FHIR R4 security logs and encryption events.
    """
    aws_status = check_aws_integration_status()
    state = local_store.load_all()
    audit_logs = list(reversed(state.get("audit_logs", [])))[:100]

    return render_template(
        "audit.html",
        audit_logs=audit_logs,
        aws_status=aws_status,
        active_role="DOCTOR"
    )


@app.route("/swasthya")
@app.route("/swasthyasetu")
def swasthya_view():
    """
    SwasthyaSetu — Portable Migrant Healthcare Platform Suite.
    Integrates Modules A-E: SwasthyaID, BhashaSehat, Document AI,
    KaamSuraksha, and SehatSetu Cross-State Coordination.
    """
    patient_id = request.args.get("patient_id", "PAT-1001")
    local_store.reload()
    try:
        summary_data = get_swasthya_migrant_summary(patient_id)
    except Exception as e:
        logger.error(f"Error compiling SwasthyaSetu summary for {patient_id}: {e}")
        summary_data = {}

    aws_status = check_aws_integration_status()

    return render_template(
        "swasthya.html",
        data=summary_data,
        aws_status=aws_status,
        patient_id=patient_id,
        active_role="MIGRANT"
    )



# ---------------------------------------------------------------------------
# Backend REST API Endpoints (Direct JSON delegation & Proxy)
# ---------------------------------------------------------------------------

@app.route("/api/aws/status", methods=["GET"])
def api_aws_status():
    """Health check across all 19 AWS services."""
    return proxy_to_lambda("/aws/status", "GET", dict(request.args), dict(request.headers), None)


@app.route("/api/doctor/patients/<patient_id>", methods=["GET"])
def api_doctor_patient_view(patient_id):
    """Pulls unified multi-doctor patient clinical profile."""
    headers = dict(request.headers)
    headers["x-doctor-id"] = request.args.get("doctor_id", "DOC-201")
    headers["x-user-role"] = "DOCTOR"
    return proxy_to_lambda(f"/doctor/patients/{patient_id}", "GET", dict(request.args), headers, None)


@app.route("/api/doctor/medicines/menu", methods=["GET"])
@app.route("/doctor/medicines/menu", methods=["GET"])
def api_doctor_medicines_menu():
    """Returns categorized medicine menu from the 253,973-medicine CSV dataset."""
    return proxy_to_lambda("/doctor/medicines/menu", "GET", dict(request.args), dict(request.headers), None)


@app.route("/api/doctor/medicines/search", methods=["GET"])
@app.route("/doctor/medicines/search", methods=["GET"])
def api_doctor_medicines_search():
    """Fast autocomplete search across medicine CSV dataset."""
    return proxy_to_lambda("/doctor/medicines/search", "GET", dict(request.args), dict(request.headers), None)


@app.route("/api/doctor/allergies", methods=["POST"])
@app.route("/doctor/allergies", methods=["POST"])
def api_doctor_allergies():
    """Add/update patient allergy and cross-check active prescriptions."""
    body = request.get_json(force=True, silent=True) or {}
    headers = dict(request.headers)
    headers["x-user-role"] = "DOCTOR"
    return proxy_to_lambda("/doctor/allergies", "POST", dict(request.args), headers, body)


@app.route("/api/doctor/prescriptions", methods=["POST"])
@app.route("/doctor/prescriptions", methods=["POST"])
def api_doctor_prescribe():
    """Feeds prescription input through the 3-Stage AI Safety Pipeline."""
    body = request.get_json(force=True, silent=True) or {}
    headers = dict(request.headers)
    headers["x-user-role"] = "DOCTOR"
    headers["x-doctor-id"] = body.get("doctor_id") or request.headers.get("x-doctor-id") or "DOC-201"
    return proxy_to_lambda("/doctor/prescriptions", "POST", dict(request.args), headers, body)


@app.route("/api/doctor/prescriptions/override", methods=["POST"])
@app.route("/doctor/prescriptions/override", methods=["POST"])
def api_doctor_override():
    """Doctor clinical override with mandatory high-priority clinical rationale."""
    body = request.get_json(force=True, silent=True) or {}
    headers = dict(request.headers)
    headers["x-user-role"] = "DOCTOR"
    headers["x-doctor-id"] = body.get("doctor_id") or request.headers.get("x-doctor-id") or "DOC-201"
    return proxy_to_lambda("/doctor/prescriptions/override", "POST", dict(request.args), headers, body)


@app.route("/api/doctor/prescriptions/<rx_id>", methods=["PATCH", "PUT", "DELETE", "POST"])
@app.route("/doctor/prescriptions/<rx_id>", methods=["PATCH", "PUT", "DELETE", "POST"])
def api_doctor_modify_prescription(rx_id):
    """Modify dosage or discontinue medication."""
    body = request.get_json(force=True, silent=True) or {}
    headers = dict(request.headers)
    headers["x-user-role"] = "DOCTOR"
    headers["x-doctor-id"] = body.get("doctor_id") or request.headers.get("x-doctor-id") or "DOC-201"
    res = proxy_to_lambda(f"/doctor/prescriptions/{rx_id}", request.method, dict(request.args), headers, body)
    local_store.reload()
    return res


@app.route("/api/doctor/prescriptions/<rx_id>/discontinue", methods=["POST", "PATCH", "DELETE"])
@app.route("/doctor/prescriptions/<rx_id>/discontinue", methods=["POST", "PATCH", "DELETE"])
def api_doctor_discontinue_prescription(rx_id):
    """Dedicated endpoint to discontinue medication."""
    body = request.get_json(force=True, silent=True) or {}
    body["action"] = "DISCONTINUE"
    body["status"] = "DISCONTINUED"
    headers = dict(request.headers)
    headers["x-user-role"] = "DOCTOR"
    headers["x-doctor-id"] = body.get("doctor_id") or request.headers.get("x-doctor-id") or "DOC-201"
    res = proxy_to_lambda(f"/doctor/prescriptions/{rx_id}/discontinue", "POST", dict(request.args), headers, body)
    local_store.reload()
    return res


@app.route("/api/patient/<patient_id>/dashboard", methods=["GET"])
@app.route("/patient/<patient_id>/dashboard", methods=["GET"])
def api_patient_dashboard(patient_id):
    """Pulls patient timetable, scorecards, and safety warnings."""
    local_store.reload()
    headers = dict(request.headers)
    headers["x-user-role"] = "PATIENT"
    return proxy_to_lambda(f"/patient/{patient_id}/dashboard", "GET", dict(request.args), headers, None)


@app.route("/api/patient/adherence/log", methods=["POST"])
@app.route("/patient/adherence/log", methods=["POST"])
def api_patient_adherence_log():
    """1-Click dose telemetry logging (TAKEN/MISSED/SKIPPED) + side-effect triage."""
    body = request.get_json(force=True, silent=True) or {}
    headers = dict(request.headers)
    headers["x-user-role"] = "PATIENT"
    return proxy_to_lambda("/patient/adherence/log", "POST", dict(request.args), headers, body)


@app.route("/api/patient/refills", methods=["POST"])
@app.route("/patient/refills", methods=["POST"])
def api_patient_refills():
    """Submit prescription refill request to preferred pharmacy."""
    body = request.get_json(force=True, silent=True) or {}
    headers = dict(request.headers)
    headers["x-user-role"] = "PATIENT"
    return proxy_to_lambda("/patient/refills", "POST", dict(request.args), headers, body)


@app.route("/api/pharmacies/locate", methods=["GET"])
@app.route("/pharmacies/locate", methods=["GET"])
def api_pharmacies_locate():
    """Geospatial pharmacy search with stock & route estimation."""
    return proxy_to_lambda("/pharmacies/locate", "GET", dict(request.args), dict(request.headers), None)


@app.route("/api/pharmacies/reserve", methods=["POST"])
@app.route("/pharmacies/reserve", methods=["POST"])
def api_pharmacies_reserve():
    """Reserve medication stock at selected pharmacy and generate pickup code."""
    body = request.get_json(force=True, silent=True) or {}
    headers = dict(request.headers)
    return proxy_to_lambda("/pharmacies/reserve", "POST", dict(request.args), headers, body)


@app.route("/api/security/audit-logs", methods=["GET"])
@app.route("/security/audit-logs", methods=["GET"])
def api_audit_logs():
    """CloudTrail + KMS security and compliance audit event stream."""
    return proxy_to_lambda("/security/audit-logs", "GET", dict(request.args), dict(request.headers), None)


# ---------------------------------------------------------------------------
# Feature 1: Downloadable Patient Prescription & Medication History PDF
# ---------------------------------------------------------------------------
@app.route("/patient/<patient_id>/prescription-pdf", methods=["GET"])
@app.route("/patients/<patient_id>/prescription-pdf", methods=["GET"])
@app.route("/api/patient/<patient_id>/prescription-pdf", methods=["GET"])
@app.route("/api/patients/<patient_id>/prescription-pdf", methods=["GET"])
def patient_prescription_pdf_view(patient_id):
    """
    Feature 1: Downloadable Patient Prescription & Medication History PDF.
    Generates a clinical-grade PDF compiled with patient demographics,
    verified allergies, active prescriptions table, revision lifecycle,
    adherence stats, and HIPAA audit footers.
    """
    actual_id = "PAT-1001" if patient_id in ("PATIENT-001", "1001", "PAT-1001") else patient_id
    try:
        local_store.reload()
        pdf_bytes = generate_patient_prescription_pdf_export(actual_id)
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        filename = f"MedCoord_Clinical_Prescription_History_{actual_id}_{now_str}.pdf"
        
        # Log download action in CloudTrail audit ledger
        record_audit_event(
            action="DownloadPrescriptionPDF",
            actor=actual_id,
            resource=f"Patient/{actual_id}/PrescriptionPDF",
            details=f"Generated and downloaded official clinical medication record PDF ({len(pdf_bytes)} bytes) for {actual_id}."
        )

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error generating prescription PDF for {patient_id}: {e}")
        return jsonify({"error": "PDFGenerationError", "message": str(e)}), 500


# ---------------------------------------------------------------------------
# Feature 2: Comprehensive Shared Audit & Timeline Log (Doctor & Patient View)
# ---------------------------------------------------------------------------
@app.route("/patient/<patient_id>/timeline", methods=["GET"])
@app.route("/patients/<patient_id>/timeline", methods=["GET"])
@app.route("/api/patient/<patient_id>/timeline", methods=["GET"])
@app.route("/api/patients/<patient_id>/timeline", methods=["GET"])
def api_patient_timeline(patient_id):
    """
    Feature 2: Comprehensive Shared Audit & Activity Timeline Log (Doctor & Patient View).
    Returns unified chronological events showing every mutating action taken in the system.
    """
    actual_id = "PAT-1001" if patient_id in ("PATIENT-001", "1001", "PAT-1001") else patient_id
    local_store.reload()
    limit = int(request.args.get("limit", 50))
    reverse = request.args.get("order", "desc").lower() != "asc"
    events = get_patient_timeline(actual_id, limit=limit, reverse=reverse)
    return jsonify({
        "patientId": actual_id,
        "count": len(events),
        "timelineEvents": events,
        "timeline_events": events
    })


# ===========================================================================
# SWASTHYA-SETU: AI-Powered Portable Healthcare for Migrant Workers Endpoints
# ===========================================================================

@app.route("/api/swasthya/summary/<patient_id>", methods=["GET"])
@app.route("/api/swasthya/patient/<patient_id>/summary", methods=["GET"])
def api_swasthya_summary(patient_id):
    """Aggregated SwasthyaSetu migrant health summary (Modules A-E)."""
    try:
        data = get_swasthya_migrant_summary(patient_id)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching Swasthya summary for {patient_id}: {e}")
        return jsonify({"error": "SwasthyaSummaryError", "message": str(e)}), 500


@app.route("/api/swasthya/profile/enrich", methods=["POST"])
def api_swasthya_enrich_profile():
    """Module A: Enrich or register migrant worker profile."""
    body = request.get_json(silent=True) or {}
    patient_id = body.get("patientId") or body.get("patient_id") or "PAT-1001"
    try:
        res = enrich_or_register_swasthya_profile(patient_id, profile_data=body)
        return jsonify(res)
    except Exception as e:
        logger.error(f"Error enriching Swasthya profile: {e}")
        return jsonify({"error": "SwasthyaProfileError", "message": str(e)}), 400


@app.route("/api/swasthya/qr/generate", methods=["POST"])
def api_swasthya_generate_qr():
    """Module A: Generate cryptographically verifiable SwasthyaID QR token."""
    body = request.get_json(silent=True) or {}
    patient_id = body.get("patientId") or body.get("patient_id") or "PAT-1001"
    expiry = int(body.get("expiryMinutes") or body.get("expiry_minutes") or 30)
    try:
        res = generate_swasthya_qr_token(patient_id, expiry_minutes=expiry)
        return jsonify(res)
    except Exception as e:
        logger.error(f"Error generating Swasthya QR token: {e}")
        return jsonify({"error": "QRGenerationError", "message": str(e)}), 400


@app.route("/api/swasthya/qr-access", methods=["POST"])
@app.route("/api/swasthya/qr/verify", methods=["POST"])
def api_swasthya_verify_qr():
    """Module A: Verify patient consent OTP and unlock portable longitudinal record."""
    body = request.get_json(silent=True) or {}
    patient_id = body.get("patientId") or body.get("patient_id") or "PAT-1001"
    clinic = body.get("clinicName") or body.get("clinic") or "Bengaluru Urban Health Clinic"
    doctor = body.get("doctorName") or body.get("doctor") or "Dr. Sarah Jenkins, MD"
    otp = body.get("otpCode") or body.get("otp") or ""
    try:
        res = verify_qr_consent_access(patient_id, clinic_name=clinic, doctor_name=doctor, otp_code=otp)
        return jsonify(res)
    except ValueError as ve:
        return jsonify({"error": "InvalidConsentOTP", "message": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error verifying Swasthya QR consent: {e}")
        return jsonify({"error": "ConsentVerificationError", "message": str(e)}), 500


@app.route("/api/swasthya/translate", methods=["POST"])
def api_swasthya_translate():
    """Module B: BhashaSehat Multilingual Doctor-Patient clinical translation."""
    body = request.get_json(silent=True) or {}
    text = body.get("text", "")
    src = body.get("sourceLanguage") or body.get("source_lang") or "Odia"
    tgt = body.get("targetLanguage") or body.get("target_lang") or "English"
    role = body.get("speakerRole") or body.get("speaker_role") or "PATIENT"
    try:
        res = translate_medical_conversation(text, source_lang=src, target_lang=tgt, speaker_role=role)
        return jsonify(res)
    except Exception as e:
        logger.error(f"Error translating medical conversation: {e}")
        return jsonify({"error": "TranslationError", "message": str(e)}), 500


@app.route("/api/swasthya/ocr-scan", methods=["POST"])
@app.route("/api/swasthya/documents/scan", methods=["POST"])
def api_swasthya_scan_document():
    """Module C: Document AI - Scan and digitize old paper prescription to S3 and FHIR R4."""
    patient_id = "PAT-1001"
    title = "Historical District Clinic Prescription"
    raw_ocr = "odisha_clinic_paper_rx"

    # Support multipart/form-data or application/json
    if request.content_type and "multipart/form-data" in request.content_type:
        patient_id = request.form.get("patientId") or request.form.get("patient_id") or "PAT-1001"
        title = request.form.get("documentTitle") or request.form.get("title") or "Uploaded Paper Prescription Scan"
        file = request.files.get("file") or request.files.get("document")
        if file:
            filename = file.filename or "paper_rx.pdf"
            title = f"Paper Rx: {filename}"
        raw_ocr = request.form.get("rawOcrText") or request.form.get("sampleType") or "odisha_clinic_paper_rx"
    else:
        body = request.get_json(silent=True) or {}
        patient_id = body.get("patientId") or body.get("patient_id") or "PAT-1001"
        title = body.get("documentTitle") or body.get("title") or "Historical District Clinic Prescription"
        raw_ocr = body.get("rawOcrText") or body.get("sampleType") or body.get("raw_ocr_text_or_sample_type") or "odisha_clinic_paper_rx"

    try:
        res = scan_and_digitize_prescription(patient_id, document_title=title, raw_ocr_text_or_sample_type=raw_ocr)
        return jsonify(res)
    except Exception as e:
        logger.error(f"Error scanning prescription: {e}")
        return jsonify({"error": "DocumentScanError", "message": str(e)}), 500


@app.route("/api/swasthya/occupational-risk", methods=["POST"])
@app.route("/api/swasthya/occupational/assess", methods=["POST"])
def api_swasthya_assess_occupational():
    """Module D: KaamSuraksha Occupational Health Risk Assessment."""
    body = request.get_json(silent=True) or {}
    patient_id = body.get("patientId") or body.get("patient_id") or "PAT-1001"
    occupation = body.get("occupation") or "Construction Site Mason"
    years = int(body.get("exposureYears") or body.get("exposure_years") or 6)
    symptoms = body.get("reportedSymptoms") or body.get("symptoms") or []
    try:
        res = assess_occupational_risk(patient_id, occupation=occupation, exposure_years=years, reported_symptoms=symptoms)
        return jsonify(res)
    except Exception as e:
        logger.error(f"Error assessing occupational risk: {e}")
        return jsonify({"error": "OccupationalRiskError", "message": str(e)}), 500


@app.route("/api/swasthya/followup", methods=["POST"])
@app.route("/api/swasthya/followup/schedule", methods=["POST"])
def api_swasthya_schedule_followup():
    """Module E: SehatSetu Cross-State Care Continuity & Multilingual Alert Dispatch."""
    body = request.get_json(silent=True) or {}
    patient_id = body.get("patientId") or body.get("patient_id") or "PAT-1001"
    followup_date = body.get("followupDate") or body.get("followup_date") or "2026-11-20"
    clinic = body.get("currentClinic") or body.get("clinic") or "Manipal Hospital Whitefield, Bengaluru"
    asha_id = body.get("homeStateAshaId") or body.get("ashaWorkerId") or "ASHA-OD-402"
    notes = body.get("notes") or ""
    lang = body.get("preferredLanguage") or body.get("preferred_language") or "Odia"
    try:
        res = schedule_cross_state_followup(
            patient_id,
            followup_date=followup_date,
            current_clinic=clinic,
            home_state_asha_id=asha_id,
            notes=notes,
            preferred_language=lang
        )
        return jsonify(res)
    except Exception as e:
        logger.error(f"Error scheduling cross-state followup: {e}")
        return jsonify({"error": "CareContinuityError", "message": str(e)}), 500




# ---------------------------------------------------------------------------
# Global Error Handlers & CORS
# ---------------------------------------------------------------------------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, X-User-Role, X-Doctor-Id, X-User-Id"
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"\n=======================================================")
    print(f"MedCoord Integrated Web Portal running at:")
    print(f" -> Local URL:   http://127.0.0.1:{port}")
    print(f" -> Network URL: http://{host}:{port}")
    print(f"=======================================================\n")
    app.run(host=host, port=port, debug=False)
