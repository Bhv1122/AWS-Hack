# Risk Feature Notes: Clinical Risk Warnings & Deterministic Safer Replacements

## 1. Overview
The Clinical Risk and Decision Support Engine in SwasthyaSetu provides real-time, deterministic, zero-trust medication safety analysis for physicians during the prescription workflow.

- **Primary Goal**: Intercept adverse drug reactions, severe allergy cross-reactivities, hazardous drug-drug interactions, and duplicate therapies *before* a prescription is finalized.
- **Decision Support Philosophy**: The system acts strictly as decision support. It never automatically mutates or substitutes a physician's prescription without explicit, deliberate physician consent ("Use this instead").
- **Offline / Sandbox Reliability**: Operates with 100% fidelity without AWS credentials or internet connectivity, relying on deterministic clinical rule sets with sub-300ms response latencies.

---

## 2. Data Specification: `seed_data/drug_alternatives.json`
Located at `seed_data/drug_alternatives.json`. Contains 26 curated clinical entries formatted as follows:

```json
{
  "synthetic": true,
  "clinicallyReviewed": false,
  "rules": [
    {
      "riskKey": "PENICILLIN_ALLERGY",
      "appliesToGenerics": ["amoxicillin", "amoxicillin-clavulanate", "ampicillin", "piperacillin"],
      "indicationNeeded": false,
      "noSafeSubstitute": false,
      "specialistReview": false,
      "noSubstituteMessage": "",
      "alternatives": [
        {
          "generic": "azithromycin",
          "reason": "Macrolide antibiotic with no beta-lactam cross-reactivity for respiratory or skin infections.",
          "cautions": ["QT prolongation risk in patients with cardiac arrhythmias", "GI distress possible"],
          "suitableFor": ["Respiratory infection", "Skin infection"]
        },
        {
          "generic": "doxycycline",
          "reason": "Tetracycline class antibiotic offering broad coverage against atypical and respiratory pathogens.",
          "cautions": ["Contraindicated in pregnancy and young children (<8 years)", "Photosensitivity risk", "Take with plenty of water"],
          "suitableFor": ["Respiratory infection", "Skin infection"]
        },
        {
          "generic": "cefixime",
          "reason": "Third-generation cephalosporin; cross-reactivity with penicillin allergy is low (~1-2%) but doctor must exercise clinical judgement.",
          "cautions": ["Cross-reactivity possible, doctor to judge", "Monitor closely for rash or allergic signs"],
          "suitableFor": ["Urinary infection", "Respiratory infection"]
        }
      ]
    }
  ]
}
```

### Key Properties
- `riskKey`: Unique interaction or allergy rule identifier matching clinical rule engine keys.
- `appliesToGenerics`: List of normalized lowercase generic names to which the rule applies.
- `indicationNeeded`: Boolean. When `true`, alternatives vary based on clinical indication (e.g. Sulfa allergy requiring selection of Urinary vs Respiratory infection).
- `noSafeSubstitute`: Boolean. When `true`, safe drug-for-drug substitution is clinically contraindicated (e.g., Warfarin + Aspirin antiplatelet management).
- `noSubstituteMessage`: Human-readable explanation when no direct substitution exists.
- `specialistReview`: Boolean. Flags cases requiring specialist evaluation (e.g., cardiologist, pain specialist).
- `alternatives[].generic`: Generic name of candidate replacement.
- `alternatives[].reason`: Concise 1-sentence plain-language rationale for the substitution.
- `alternatives[].cautions`: Specific clinical contraindications or monitoring instructions.
- `alternatives[].suitableFor`: List of clinical indications for which this alternative is indicated.

---

## 3. Backend Endpoints

### 1. `POST /api/prescribe/check`
- **Security**: Requires active `Authorization: Bearer <token>` or session token with `DOCTOR` role, plus an active consent grant for the specified `patientId`. Returns `401 Unauthorized` without token, and `403 Forbidden` without active grant or after grant revocation.
- **Request Body**:
  ```json
  {
    "patientId": "PAT-SS-1001",
    "medicineName": "Augmentin 625 Duo Tablet",
    "dosage": "625 Duo",
    "indication": "Respiratory infection"
  }
  ```
- **Response**:
  ```json
  {
    "riskLevel": "SEVERE",
    "resolvedGeneric": "amoxicillin-clavulanate",
    "findings": [
      {
        "type": "ALLERGY",
        "severity": "SEVERE",
        "with": "Penicillin allergy",
        "plainExplanation": "Patient has a documented severe allergy to Penicillin. Prescribing Amoxicillin-Clavulanate carries high risk of anaphylaxis.",
        "clinicianNote": "Beta-lactam core cross-reactivity with Penicillin allergy. Avoid all aminopenicillins."
      }
    ],
    "alternatives": [
      {
        "generic": "azithromycin",
        "reason": "Macrolide antibiotic with no beta-lactam cross-reactivity for respiratory or skin infections.",
        "cautions": ["QT prolongation risk in patients with cardiac arrhythmias", "GI distress possible"],
        "riskLevel": "NONE",
        "brands": [
          {
            "name": "Azithral 500 Tablet",
            "manufacturer": "Alembic Pharmaceuticals Ltd",
            "price": 132.36,
            "packSize": "strip of 5 tablets"
          }
        ],
        "action": null
      }
    ],
    "noSafeSubstitute": false,
    "noSubstituteMessage": "",
    "specialistReview": false,
    "needsIndication": false,
    "source": "RULES"
  }
  ```

### 2. `POST /api/prescribe/accept-alternative`
- **Security**: Doctor session + active patient unlock grant.
- **Request**:
  ```json
  {
    "patientId": "PAT-SS-1001",
    "originalMedicine": "Augmentin 625 Duo Tablet",
    "replacementMedicine": "Azithral 500 Tablet"
  }
  ```
- **Audit**: Writes `ALTERNATIVE_ACCEPTED` event to immutable HIPAA CloudTrail ledger. Never exposes patient Consent PIN.

### 3. Extended `GET /api/medicines-catalog?q=...&limit=15&patientId=...`
- Attaches `risk` field (`NONE` | `CAUTION` | `SEVERE` | `UNKNOWN`) to each of the 15 search results.
- Cached per `(patientId, generic)` in session memory, maintaining sub-300ms search latency.

---

## 4. UI Behavior & Clinical Decision Support

### Doctor Interface
1. **Catalog Search Badges**: Dropdown options display colored badges:
   - Red: `Risky for this patient`
   - Amber: `Use with caution`
   - Grey: `Can't check`
   - Green: `No conflicts found` (Never uses the word "Safe")
2. **Safety Panel**: Rendered directly under the medicine input upon selection:
   - `NONE`: Slim green accent with "No conflicts found with this patient's allergies and current medicines."
   - `CAUTION`: Amber warning container with plain-language explanation.
   - `SEVERE`: High-contrast red alert titled "Risky for <Patient Name>", presenting 2-sentence rationale and expandable "Why?" clinician note.
   - `UNKNOWN`: Amber alert instructing "We couldn't check this automatically, please review manually."
3. **Safer Option Cards**:
   - Displays up to 3 vetted cards containing generic name, 1-sentence reason, caution chips, and non-discontinued brand pills with pricing.
   - Primary Action Button: "Use this instead". One click swaps the medicine name, preserves already entered dosage/frequency, re-evaluates safety, scrolls to the dose input, and presents a confirmation toast.
   - Indication Filter: If `needsIndication: true`, renders a clean "What is it for?" selector before filtering appropriate candidates.
   - Duplicate Therapy (`AVOID_DUPLICATE`): Recommends "Keep current <medicine>" with anchor link to the active prescription.
   - Specialist Review (`noSafeSubstitute: true`): Shows clear guidance note and "Request specialist review" prompt.
4. **Prescribe Button Gate**: If risk is `SEVERE`, button transforms to secondary style "Prescribe anyway…" and requires mandatory typed clinical justification and monitoring plan.

### Patient View Safety Guard
- Patient medicines view presents a plain-language caution banner: *"Ask your doctor about this medicine; it may not suit your allergy"* with Read aloud audio assistance.
- **Strict Clinical Boundary**: Patient view NEVER displays replacement drug suggestions, clinical notes, or prompts instructing patient to switch/discontinue medication independently.

---

## 5. How to Add a New Risk Rule and Alternative
To add a new clinical rule (e.g., ACE Inhibitors + Spironolactone hyperkalemia risk):

1. **Edit `seed_data/drug_alternatives.json`**:
   ```json
   {
     "riskKey": "ACE_INHIBITOR_HYPERKALEMIA",
     "appliesToGenerics": ["ramipril", "enalapril", "lisinopril"],
     "indicationNeeded": false,
     "noSafeSubstitute": false,
     "specialistReview": false,
     "noSubstituteMessage": "",
     "alternatives": [
       {
         "generic": "amlodipine",
         "reason": "Calcium channel blocker for hypertension without risk of potassium retention.",
         "cautions": ["Peripheral edema possible"],
         "suitableFor": ["Hypertension"]
       }
     ]
   }
   ```
2. **Deterministic Engine Matching**:
   Ensure `backend_lambdas/clinical_risk_engine.py` maps the generic name or drug class to the `riskKey` under `evaluate_medicine_safety()`.
3. **Re-Checking Guarantee**:
   The engine automatically runs candidate generics back through the full multi-stage patient check to verify that the proposed replacement is not contradicted by other patient factors.
