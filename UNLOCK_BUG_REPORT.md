# Bug Fix Report: Doctor Consent PIN Unlock Flow

**Platform:** SwasthyaSetu & AWS Medication Coordination Platform  
**Target View:** Doctor Clinical Safety Workspace (`/doctor`)  
**Demo Identities:** Doctor `DOC-IN-8841` (Dr. Sarah Jenkins), Patient `PAT-SS-1001` (Ramesh Kumar)  
**Date:** October 24, 2026  

---

## 1. Executive Summary & Root Cause Analysis

When a verified doctor entered Patient ID `PAT-SS-1001` and the patient's active 6-digit Consent PIN and clicked **"Unlock Record"**, the patient record did not open. 

Through step-by-step reproduction (CLI `tests/debug_unlock.py` + Browser Subagent session tracing), we identified **three cascading root causes**:

### Root Cause 1 (Primary Frontend Blocker — Fatal SyntaxError):
In `frontend_portal/static/js/doctor.js` around line 87, an unclosed `if (fDate)` block caused a fatal JavaScript compilation error:
```
SyntaxError: Unexpected token ')' at http://127.0.0.1:5000/static/js/doctor.js:100:1
```
Because `doctor.js` failed during initial script parsing, `setupPinBoxes` was never initialized, the click listener on `#btn-decrypt-chart` was never attached, and the PIN digit boxes remained dead to input.

### Root Cause 2 (API Route Gaps & Periodic Consent Re-lock):
1. **Missing `/api/profile` route (HTTP 404):** Post-unlock routines that refreshed patient profile called `GET /api/profile?patientId=...`, which returned 404 Not Found.
2. **Forbidden Doctor Status Poll (HTTP 403):** `doctor.js` polls `GET /api/consent/status?patientId=...` every 15 seconds via `pollPatientConsentStatus()`. In `app.py`, `api_consent_status` strictly threw 403 on non-PATIENT callers (`"Only patients may query consent status"`). Because doctors received 403 with `activeGrant: undefined`, the polling loop executed `lockPatientRecordNow('Patient has revoked access...')` and immediately re-locked the screen!

### Root Cause 3 (Rate-Limit Counter Accumulation & Contract Mismatches):
1. **No Rate-Limit Reset:** In `backend_lambdas/registry_engine.py`, `_WRONG_PIN_ATTEMPTS` accumulated failed attempts without ever clearing them upon a successful PIN entry.
2. **Response Contract Gap:** Active prescriptions were placed under `active_prescriptions`, but the UI looked at `patient.prescriptions`.
3. **Audit Log Store Inconsistency:** `add_audit_record` stored logs in `cloudtrail_audit_logs` and `audit_trail`, but `api_audit_trail` read `audit_logs`, causing post-unlock audit trail calls to return empty.

---

## 2. Suspect Checklist & Evidence (Step 3)

| # | Suspect Description | Status | Evidence & Resolution |
|---|---------------------|--------|-----------------------|
| 1 | PIN changes on every patient login / page load (stale PIN) | **PASS** | Verified via `tests/debug_unlock.py` and `tests/test_unlock_flow.py`: PIN is persistent across consecutive logins (`482910`). It rotates **only** upon explicit patient revocation or explicit rotation. |
| 2 | Six PIN boxes not joined into one string, paste doesn't fill all six, leading zeros dropped | **PASS / REINFORCED** | `components.js` correctly joins boxes into a string. Explicit string casting (`String(doctorPinHelper.getPin() || '').trim()`) and uppercase trimming on Patient ID reinforced in `doctor.js`. |
| 3 | Request field name mismatch (`consentPin` vs `pin`), un-sanitized IDs | **FIXED** | `doctor.js` and `app.py` standardized on `consentPin` (with fallback to `pin`), Patient ID is uppercased and trimmed, and `emergencyBreakGlass` is sent as a boolean. |
| 4 | Auth token missing or in wrong header | **PASS** | `api.js` attaches `Authorization: Bearer <token>`, `x-doctor-id`, and `x-user-role: DOCTOR`. |
| 5 | Grant stored under different key or re-locked by later calls | **FIXED** | Fixed `/api/consent/status` to allow doctors to query active grants; updated `has_active_grant()` to slide the 10-minute inactivity expiry window on access. |
| 6 | Response contract mismatch (missing `prescriptions`, `patient`) | **FIXED** | Backend and frontend updated so `patient.prescriptions` and root `prescriptions` are populated with active medications. |
| 7 | Render function throws on missing field and hides it | **FIXED** | Fixed `doctor.js` syntax error; added defensive `try/catch` boundaries around each history card in `updateWorkspaceUnlockedState()` with "Retry" buttons. |
| 8 | Wrong-attempt counter never reset on success | **FIXED** | Added `reset_pin_rate_limit(doctor_id, patient_id)` in `registry_engine.py` and called it in `auth_security_engine.py` upon successful PIN match. Returns `attemptsRemaining` and `retryAfterSeconds` on 403/429. |
| 9 | Container keeps hidden class or non-existent section ID | **PASS** | `#section-lookup` and `#section-overview` exist in `doctor.html` and switch smoothly once JS executes. |
| 10 | Browser running stale cached JS/CSS | **FIXED** | Added `Cache-Control: no-cache, no-store, must-revalidate` in Flask's `after_request` for `/static/`, and appended `?v=2.4.1` query strings to `app.css`, `api.js`, `components.js`, and `doctor.js`. |

---

## 3. Code Modifications & Files Changed

1. **[doctor.js](file:///d:/AWS/frontend_portal/static/js/doctor.js)**
   - Fixed unclosed `if (fDate)` block around line 87 (eliminated fatal `SyntaxError`).
   - In `handleDoctorUnlock()`, ensured sanitized input (`patientId.trim().toUpperCase()`, `pin.trim()`).
   - Added specific friendly error handling for `PIN_INVALID` (with `attemptsRemaining`), `TOO_MANY_ATTEMPTS` (with `retryAfterSeconds`), `CONSENT_REVOKED`, `PATIENT_NOT_FOUND`, and `SESSION_EXPIRED`.
   - Populated `currentPatientProfile.prescriptions` from `res.prescriptions || res.active_prescriptions`.
   - Wrapped every dashboard card in `updateWorkspaceUnlockedState()` inside its own `try/catch` block with retry fallbacks.

2. **[app.py](file:///d:/AWS/frontend_portal/app.py)**
   - Added `@app.route("/api/profile")` with zero-trust validation and doctor PIN stripping.
   - Updated `api_auth_lookup_patient` to return specific codes: `PIN_INVALID` (with `attemptsRemaining`, 403), `TOO_MANY_ATTEMPTS` (with `retryAfterSeconds`, 429), `CONSENT_REVOKED` (403).
   - Updated `api_consent_status` to allow doctors to check `has_active_grant()` without receiving 403.
   - Updated `api_audit_trail` to aggregate all audit sources (`audit_logs`, `cloudtrail_audit_logs`, `audit_trail`) and return `auditLogs`, `audit_logs`, and `events`.
   - Added `Cache-Control: no-cache, no-store, must-revalidate` in `after_request` for `/static/` assets.

3. **[auth_security_engine.py](file:///d:/AWS/backend_lambdas/auth_security_engine.py)**
   - In `auth_lookup_patient`, added rate limit check and `reset_pin_rate_limit()` on correct PIN match.
   - Returned `accessGranted: True`, `kmsDecrypted: True`, `breakGlass: is_emergency`, `unlockedViaBreakGlass: is_emergency`, `prescriptions`, `active_prescriptions`, `reports`, `auditTrail`, `fhirBundle`.
   - In `has_active_grant()`, renewed sliding 10-minute expiration window on active doctor access.

4. **[registry_engine.py](file:///d:/AWS/backend_lambdas/registry_engine.py)**
   - Updated `check_pin_rate_limit()` to track and return `(is_allowed, remaining_cooldown_seconds, attempts_remaining)`.
   - Added `reset_pin_rate_limit(doctor_id, patient_id)` to reset the attempt count on success.

5. **[aws_core.py](file:///d:/AWS/backend_lambdas/aws_core.py)**
   - In `add_audit_record()`, synced audit entries to `audit_logs` in addition to `cloudtrail_audit_logs` and `audit_trail`.

6. **[base.html](file:///d:/AWS/frontend_portal/templates/base.html)** and **[doctor.html](file:///d:/AWS/frontend_portal/templates/doctor.html)**
   - Added `?v=2.4.1` cache-busting query strings to all static CSS and JavaScript imports.

7. **[show_demo_pin.py](file:///d:/AWS/tests/show_demo_pin.py)** (New Tool)
   - Created standalone local CLI script to view the live Consent PIN for any patient directly from the local store without exposing any HTTP endpoint.

8. **[test_unlock_flow.py](file:///d:/AWS/tests/test_unlock_flow.py)** (New Regression Test)
   - Implemented automated test covering patient login, PIN stability, doctor login, wrong PIN 403 rejection, live PIN unlock, post-unlock data retrieval, patient revoke & re-lock, and break-glass override.

---

## 4. Verification & Test Results

### 1. Automated Unlock Flow Regression Test (`tests/test_unlock_flow.py`):
```
=======================================================
RUNNING UNLOCK FLOW TEST SUITE
=======================================================
--- 1. Patient Login (PAT-SS-1001) ---
[PASS] Patient logged in successfully. Consent PIN: 482910

--- 2. PIN Stability across 3 Logins ---
[PASS] Login 1: PIN matches (482910)
[PASS] Login 2: PIN matches (482910)
[PASS] Login 3: PIN matches (482910)

--- 3. Doctor Login (DOC-IN-8841) ---
[PASS] Doctor logged in successfully. Token: TOKEN-DOC-DOC-IN..., Doctor ID: DOC-IN-8841

--- 4. Wrong PIN Rejection ---
[PASS] Wrong PIN returned 403 PIN_INVALID with attemptsRemaining=4

--- 5. Doctor Unlock with Live PIN ---
[PASS] Unlock succeeded. Patient: Ramesh Kumar, KMS Decrypted: True

--- 6. Post-Unlock Clinical Data Fetch ---
[PASS] /api/profile returned 200 OK (Patient: Ramesh Kumar)
[PASS] /api/reports returned 200 OK (Report count: 11)
[PASS] /api/doctor/patients/PAT-1001 returned 200 OK
[PASS] /api/audit returned 200 OK (Audit count: 207)

--- 7. Patient Revokes Consent ---
[PASS] Patient consent revoked: Consent revoked. Active doctor sessions invalidated and Consent PIN rotated to 219865.
[PASS] Old PIN rejected with 403 after revocation (PIN_INVALID)
[PASS] Doctor subsequent clinical call returned 403 FORBIDDEN after revocation

--- 8. Emergency Break-Glass Override ---
[PASS] Emergency Break-Glass succeeded with 200 OK. accessGranted: True
[PASS] Break-Glass action audited in CloudTrail stream

--- Cleanup / Reset Patient Consent ---
[PASS] Patient consent state reset to active.
=======================================================
ALL UNLOCK FLOW REGRESSION TESTS PASSED!
=======================================================
```

### 2. Browser Agent Verification:
- **Wrong PIN (`000000`):** PIN boxes shook, error `#pin-feedback-error` displayed `"Invalid Consent PIN. 4 attempt(s) remaining before security cooldown."`, and `#section-overview` remained hidden and locked.
- **Valid PIN (`219865`):** Automatically validated upon typing 6th digit, displayed `"Health record for Ramesh Kumar unlocked!"`, hid `#section-lookup`, and made `#section-overview` visible.
- **Content Verified in DOM:** Patient Name `"Ramesh Kumar"`, Allergies `"Penicillin (Severe)"`, Active Prescriptions (Warfarin 5mg, Metformin 500mg, etc.).
- **Browser Console:** `0` errors.

### 3. Existing Test Suites:
- `python tests/test_checklist.py`: **ALL 12/12 TESTS PASSED (100%)**
- `python test_all_modules.py`: **ALL 15/15 SCENARIOS PASSED (100%)**
- `python test_swasthyasetu.py`: **ALL 6/6 SWASTHYA-SETU ENGINE TESTS PASSED (100%)**
- `python test_frontend_integration.py`: **ALL 16/16 INTEGRATION TESTS PASSED (100%)**

---

## 5. Manual Verification Instructions

To manually verify the fix:

### Step 1: Inspect the current Consent PIN from CLI
Run the local CLI tool:
```bash
python tests/show_demo_pin.py PAT-SS-1001
```
Sample output:
```
Patient ID:  PAT-SS-1001
Name:        Ramesh Kumar
Consent PIN: 229286
Revoked:     False
```

### Step 2: Test in the Browser
1. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001
   ```
2. **Test Wrong PIN:**
   - In the 6 PIN boxes, enter `0 0 0 0 0 0`.
   - Click **"Unlock Patient Record"**.
   - Notice the boxes shake, an error message shows `"Invalid Consent PIN. 4 attempt(s) remaining before security cooldown."`, and the Privacy Shield remains locked.
3. **Test Valid Unlock:**
   - Enter the 6 digits obtained from Step 1 (or paste the 6-digit PIN).
   - Click **"Unlock Patient Record"** (or let auto-submit trigger).
   - The Privacy Shield immediately disappears, and the patient history view opens:
     - Name: **Ramesh Kumar**
     - Verified Allergies: **Penicillin (Severe)**
     - Active Prescriptions: **Warfarin 5mg**, **Metformin 500mg**
     - Reports, Adherence, and FHIR Bundle are populated.
4. **Test Emergency Break-Glass:**
   - Click **"Lock Now"** to re-engage the Privacy Shield.
   - Click **"Emergency Break-Glass Override"**.
   - Enter at least 15 characters of clinical justification (e.g., `Patient admitted unconscious to ICU protocol`), check the audit acknowledgment, and submit.
   - The chart immediately decrypts with an active Emergency Banner and logs to the CloudTrail audit stream.

---

## 6. Bug 2: "Getting Out" When Changing a Prescription (Suspects 1–6 Investigation)

When attempting to modify a dose or discontinue medication in the Doctor view, users reported getting "thrown out" (either redirected to `/login?expired=1` or kicked back to the locked Privacy Shield). We evaluated all six suspects with real runtime evidence:

| # | Suspect Description | Status | Evidence & Resolution |
|---|---------------------|--------|-----------------------|
| **1** | **Full Page Reload / Uncontrolled Form Submit** | **PASS** | **Finding:** The modify and discontinue dialogs used standard `<button>` tags without explicit `type="button"`, and certain click handlers did not call `e.preventDefault()`. On click, form submission caused a browser navigation that reloaded the page, wiping in-memory unlocked state and resetting to the shield.<br>**Fix:** Added `type="button"` to all action buttons in `doctor.html`, prevented form defaults, and updated DOM in-place without page reloads. |
| **2** | **Global Error Handler Treating Any Error as Full Logout** | **PASS** | **Finding:** `frontend_portal/static/js/api.js` previously contained a blanket 401 interceptor: `window.location.href = '/login?expired=1'`. Any 401/403 (such as a 403 on missing grant or a 400 on prescription misrouting) triggered an immediate redirect to login.<br>**Fix:** Implemented precise error categorization: `401 SESSION_EXPIRED` navigates to login with an informational notice; `403 NO_ACTIVE_GRANT` / `CONSENT_REVOKED` re-engages the shield in place with the patient ID prefilled; other errors (`400`, `404`, `500`) show a notification toast and keep the doctor on the unlocked chart. |
| **3** | **Prescriptions Endpoint Contract Mismatch & Slow Synchronous AI Stalls** | **PASS** | **Finding:** 1) Frontend sent `action: "MODIFY_DOSAGE"` and `dosage: "..."`, which `app.py` failed to match, falling through to `api_doctor_prescribe()` (the new prescription AI check pipeline) and raising HTTP 400 `Prescription not found`. 2) Endpoint expected `doctorId` in body which was sometimes undefined.<br>**Fix:** Added `@app.route("/api/prescriptions", methods=["POST", "PUT"])` accepting `MODIFY`, `MODIFIED`, and `MODIFY_DOSAGE`. Takes `doctorId` from the verified session, matches composite key `PAT-1001#<rx_id>` with fallback catalog lookup, and completes in < 700 ms without running slow synchronous AI checks. |
| **4** | **Sessions Overwritten Across Roles (Single Storage Key)** | **PASS** | **Finding:** `sessionStorage` used a single shared key `medcoord_session`. Testing the patient role in one tab to copy the PIN and returning to the doctor tab in the same browser session resulted in the patient token overwriting the doctor session, making subsequent doctor calls fail with 401/403.<br>**Fix:** Role-namespaced storage keys: `doctor_session` and `patient_session`. Authentication tokens are transmitted in `Authorization: Bearer <token>` and `x-doctor-id` / `x-user-role` headers. Logging in or out of one role never mutates or clears the other role's session or grant. |
| **5** | **Auto-Refresh Destructively Locking on Transient Failures** | **PASS** | **Finding:** The 20–30s polling timer in `doctor.js` called `lockPatientRecordNow()` whenever `!status.activeGrant` was evaluated, including on transient network hiccups or aborted requests.<br>**Fix:** Polling timer locks ONLY upon an explicit server response of `hasActiveAccess === false` or `code === "CONSENT_REVOKED"`. Transient errors display a non-blocking `"Reconnecting..."` indicator. Every successful authorized request renews the sliding 10-minute inactivity grant. |
| **6** | **Hard Refresh Behavior (Zero-Trust Resume Button)** | **PASS** | **Finding:** Hard refreshing previously dropped state completely, forcing a re-entry of the PIN.<br>**Fix:** Tab-scoped `sessionStorage` stores only the active `unlockedPatientId` (no raw clinical data). On page reload, the client queries `/api/consent/status`. If the server grant is still active, a single prominent button appears: **"Resume Ramesh Kumar's record"**. Clinical data remains zero-trust protected until the doctor taps Resume. If expired or revoked, the shield displays with the ID prefilled. |
