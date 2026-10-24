# SwasthyaSetu & AWS Platform — Frontend Design & Integration Notes
### Design Language: "Setu Care" (Bridge of Care: Calm, Trustworthy, Warm)

## 1. Design System Overview & Rationale
The presentation layer of `frontend_portal/` was redesigned into **"Setu Care"** — an empathetic, hospital-grade, and migrant-accessible interface designed to be operated in seconds by a busy physician, and used effortlessly by a migrant worker with low digital literacy on a budget smartphone (tested down to 360px viewport width with zero horizontal scroll).

### Core Principles
1. **Zero-Trust Server-Side Privacy Shield:** The doctor workstation strictly opens in a locked zero-trust state. Zero clinical data is displayed until unlocked via a 6-digit patient Consent PIN or typed Emergency Break-Glass override. Grants automatically expire upon patient revocation, manual lock, or 10-minute inactivity.
2. **Sovereign Patient Ownership:** Migrant workers hold sovereign control over their records via their SwasthyaID digital health passport, live rotating PIN, and 1-tap revocation.
3. **Inclusive Ergonomics & Multilingual Support:** Self-hosted native Indian scripts (`Noto Sans Devanagari, Oriya, Kannada, Tamil, Telugu`) ensure regional languages never render as empty boxes. Client-side audio speech synthesis provides voice read-aloud on every card.
4. **No Raw Cryptographic Jargon in UI Chrome:** Technical complexities (FHIR R4 bundles, KMS key alias `alias/MedCoord-HIPAA-MasterKey`, CloudTrail JSON events) are cleanly organized within collapsible *"For Technical Reviewers"* accordions.

---

## 2. "Setu Care" Tokens (`static/css/app.css`)

### Color Palette
- **Primary Teal:** `#0F766E` (hover: `#115E59`, soft: `#CCFBF1`, border: `#99F6E4`)
- **Doctor Workspace Indigo:** `#3730A3` (hover: `#312E81`, soft: `#E0E7FF`, border: `#C7D2FE`)
- **Patient Accent Saffron:** `#F59E0B` (soft: `#FEF3C7`, ink: `#0F172A` — used strictly as a fill with dark ink for WCAG AA contrast)
- **Clinical Success:** `#16A34A` (soft: `#DCFCE7`, border: `#86EFAC`)
- **Warning / Hazard:** `#D97706` (soft: `#FEF3C7`, border: `#FDE68A`)
- **Danger:** `#DC2626` (hover: `#B91C1C`, soft: `#FEE2E2` — strictly reserved for SEVERE blocks, Break-Glass, and Revocation)
- **Surfaces & Ink:**
  - Light mode: Canvas `#F4F7F6`, Surface `#FFFFFF`, Border `#E2E8F0`, Ink `#0F172A`, Muted `#475569`.
  - Dark mode: Canvas `#0B1417`, Surface `#12201F`, Border `#1E3A38`, Ink `#E2E8F0`, Muted `#94A3B8`.

### Typography & Indian Scripts
- **Primary Stack:** Plus Jakarta Sans + Noto Sans Devanagari, Oriya, Kannada, Tamil, and Telugu (self-hosted under `static/fonts/fonts.css` for full offline/sandbox operation).
- **Scale:** 12px (caption), 14px (small), 16px (doctor base), 18px (patient base), 22px (subheading), 28px (heading), 36px (display).
- **Text Controls:** `A−` / `A+` font size scaler and Dark / Light theme toggle persisted in `localStorage`.

### Motion & Touch Targets
- **Transitions:** 150–220ms smooth cubic bezier easing; respects `prefers-reduced-motion`.
- **Touch Targets:** Minimum 44px on all interactive buttons, inputs, and tab items.
- **Icons:** Inline SVG Lucide icons without browser emoji dependencies.

---

## 3. Modular Client Architecture

```
frontend_portal/
├── static/
│   ├── css/
│   │   └── app.css               # "Setu Care" design tokens, layout grid, dark theme, animations
│   ├── fonts/
│   │   └── fonts.css             # Self-hosted Plus Jakarta Sans & Noto Sans Indic font stacks
│   ├── i18n/
│   │   ├── en.json               # English dictionary (82 keys)
│   │   ├── hi.json               # Hindi dictionary (हिंदी)
│   │   ├── or.json               # Odia dictionary (ଓଡ଼ିଆ)
│   │   ├── kn.json               # Kannada dictionary (ಕನ್ನಡ)
│   │   ├── ta.json               # Tamil dictionary (தமிழ்)
│   │   └── te.json               # Telugu dictionary (తెలుగు)
│   └── js/
│       ├── api.js                # Centralized fetch wrapper, Bearer auth, zero-trust headers, error mappers
│       ├── components.js         # Toasts, modals, AWS status drawer, QR generator, 6-PIN digit box, Judge Tour
│       ├── auth.js               # Role gateway, 4-step patient wizard, 4-gate doctor stepper, live registry lookup
│       ├── doctor.js             # Privacy shield, safety combobox, reports trends, translator, OCR, work-risk
│       └── patient.js            # Mobile bottom tabs (6 tabs), 1-click adherence, live PIN, pharmacy vouchers
└── templates/
    ├── base.html                 # Top bar shell, AWS Live/Sandbox pill, architecture drawer, demo footer
    ├── login.html                # Split-screen role gateway, 4-step wizard, 4-gate stepper, Judge Panel
    ├── doctor.html               # Nav rail, sticky safety rail, lock card, SVG trends, FHIR R4 inspector
    ├── patient.html              # Mobile-first 360px layout, 6 tabs, big PIN display, QR card, pharmacy locator
    ├── audit.html                # CloudTrail compliance ledger & KMS tamper-evident event stream
    ├── pharmacy.html             # Amazon Location Service geospatial route & 1-stop fulfillment finder
    └── index.html                # Platform overview & direct portal navigation
```

---

## 4. Screen-to-Backend Integration Matrix

| UI Screen / Component | Client JS Action | Flask Route | Backend Engine Handler | Description & Security Gate |
| :--- | :--- | :--- | :--- | :--- |
| **Global Top Bar** | AWS Status Pill | `GET /api/aws-status` | `check_aws_integration_status()` | Displays 7/7 AWS services connected (LIVE) or graceful SANDBOX fallback. |
| **Global Top Bar** | Audit Trail Drawer | `GET /api/security/audit-logs` | `get_recent_audit_events()` | Cryptographically verifiable CloudTrail audit trail. |
| **Login Gateway** | Live Gate 1 Search | `GET /api/registry/license/<num>` | `lookup_license()` | Real-time physician license feedback while typing with name masking. |
| **Login Gateway** | Live Gate 2 Search | `GET /api/registry/hospital/<code>` | `lookup_hospital()` | Validates hospital affiliation in state medical registry. |
| **Login Gateway** | 1-Click Judge Scenarios | `GET /api/demo/accounts` | `get_demo_accounts()` | Populates all 9 doctor (valid + negative) and 10 patient test cases. |
| **Doctor Login** | 4-Gate Stepper Submit | `POST /api/auth/login-doctor` | `authenticate_doctor_cognito_mfa()` | Validates license, hospital, Govt ID last 4, and MFA OTP `654321`. |
| **Patient Register** | 4-Step Wizard Submit | `POST /api/auth/register-patient` | `register_patient_cognito_kms()` | Issues `PAT-SS-XXXX`, `ABHA-XX-XXXX-...`, Consent PIN, and QR passport. |
| **Doctor Privacy Shield** | 6-Box PIN Unlock | `POST /api/auth/lookup-patient` | `lookup_patient_by_doctor()` | Decrypts profile via KMS; strips PIN from response; audits unlock grant. |
| **Doctor Privacy Shield** | Emergency Break-Glass | `POST /api/auth/lookup-patient` | `lookup_patient_by_doctor()` | Overrides PIN with ≥15-char clinical justification; displays red banner. |
| **Doctor Top Bar** | Lock Now / Inactivity | `POST /api/auth/lock` | `lock_patient_grant()` | Terminates doctor grant immediately and writes audit event. |
| **Doctor Overview** | Patient Profile | `GET /api/doctor/patients/<id>` | `get_doctor_patient_view()` | Loads demographics, active prescriptions, allergies, and adherence metrics. |
| **Doctor Prescriptions** | Server Autocomplete | `GET /api/medicines-catalog?q=&limit=15` | `search_medicine_catalog()` | Debounced search across 253,973-medicine CSV with generic salt resolution. |
| **Doctor Prescriptions** | Prescribe Medication | `POST /api/prescribe` | `prescribe_medication()` | 3-stage safety check (Bedrock + Comprehend Medical); returns SAVED or BLOCKED. |
| **Doctor Prescriptions** | Clinical Override | `POST /api/doctor/prescriptions/override` | `override_and_force_approve_prescription()` | Overrides contraindication with typed clinical rationale & monitoring plan. |
| **Doctor Prescriptions** | Modify Dosage | `PUT /api/prescriptions/<rx_id>` | `modify_prescription_dosage()` | Titrates dosage, increments version number, and logs audit reason. |
| **Doctor Prescriptions** | Discontinue Med | `POST /api/prescriptions/<rx_id>/discontinue` | `discontinue_prescription()` | Deactivates prescription and syncs patient daily schedule timetable. |
| **Doctor Reports** | Longitudinal Trends | `GET /api/trends?patientId=&metric=` | `extract_patient_metric_trends()` | Returns time-series data for HbA1c, INR, BP, and SpO2 SVG charts. |
| **BhashaSehat** | Clinical Dialogue | `POST /api/swasthya/translate` | `translate_medical_conversation()` | Native script translation (Odia, Kannada, Hindi, etc.) + Web Speech audio. |
| **Document AI** | OCR Preset / Upload | `POST /api/swasthya/ocr-scan` | `scan_and_digitize_prescription()` | Extracts medicines from old slips, flags interactions, and reviews low-conf text. |
| **KaamSuraksha** | Occupational Screening | `POST /api/swasthya/occupational-risk` | `assess_occupational_risk()` | Computes trade exposure risk (LOW/MOD/HIGH) and screening checklist. |
| **SehatSetu** | Cross-State Follow-up | `POST /api/swasthya/followup` | `schedule_cross_state_followup()` | Synchronizes home-state ASHA worker and previews bilingual SMS/WhatsApp alerts. |
| **Patient Home** | 1-Click Dose Telemetry | `POST /api/adherence` | `log_medication_dose()` | Logs dose to Timestream, updates adherence streak, and triggers AppSync sync. |
| **Patient Passport** | Revoke & Rotate PIN | `POST /api/auth/revoke-consent` | `revoke_patient_consent()` | Rotates 6-digit PIN with flip animation and re-locks doctor workstations. |
| **Patient Pharmacy** | 1-Stop Geo-Fulfillment | `GET /api/pharmacies/locate` | `find_nearby_stocked_pharmacies()` | Haversine distance search identifying pharmacies stocking 100% of regimen. |
| **Patient Pharmacy** | Reserve Stock | `POST /api/pharmacies/reserve` | `reserve_medication_at_pharmacy()` | Locks inventory and issues cryptographic pickup voucher `PICKUP-XXXX-XXXX`. |

---

## 5. Visual Proof & Responsive Viewport Targets

All layouts have been captured and verified in `docs/screenshots/`:
- **360px Mobile (Budget Smartphone):** `patient_home_360.png`, `patient_medicines_360.png`, `patient_reports_360.png`, `patient_passport_360.png`, `patient_pharmacy_360.png`, `login_360.png`, `pharmacy_locator_360.png`. Zero horizontal scroll guaranteed.
- **768px Tablet:** `doctor_locked_768.png`, `patient_home_768.png`, `login_768.png`.
- **1280px Desktop:** `doctor_locked_1280.png`, `doctor_unlocked_overview_1280.png`, `doctor_reports_trends_1280.png`, `doctor_prescriptions_1280.png`, `doctor_translator_1280.png`, `doctor_scanner_1280.png`, `doctor_work_risk_1280.png`, `audit_stream_1280.png`, `pharmacy_locator_1280.png`, `platform_hub_1280.png`.
- **1440px Wide Desktop:** `doctor_locked_1440.png`, `patient_home_1440.png`, `login_1440.png`.
