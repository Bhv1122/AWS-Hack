# SwasthyaSetu & AWS Platform - Demo Accounts & Verification Scenarios
*Auto-Generated at Seed Time (2026-10-23 21:34:19 UTC)*
*All accounts carry `"synthetic": true`. Passwords hashed with `werkzeug.security.generate_password_hash`.*

---

## 1. Quick Access Credentials
- **Default Universal Demo Password:** `Demo@123`
- **Universal Demo MFA OTP Code:** `654321`

---

## 2. Doctor Accounts & Registry Scenarios

| Scenario | License Number | Hospital Code | Specialty | Gov ID Last-4 | MFA OTP | Doctor ID | Status / Expected Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **VALID (Pre-Registered)** | `KMC-2019-88412` | `HOSP-BLR-990` | Cardiology | `4412` | `654321` | `DOC-IN-8841` | Dr. Ananya Sharma (Cardiologist, Bangalore). Full clinical permissions. |
| **VALID (Odisha Live Sign-Up)** | `NMC-IND-55201` | `AIIMS-BBSR-101` | Pulmonology | `5201` | `654321` | *(Registers Live)* | Dr. Debabrata Nayak (Odia-speaking Pulmonologist, AIIMS Bhubaneswar). |
| **SUSPENDED License** | `KMC-2016-10233` | `HOSP-BLR-102` | General Medicine | `1023` | `654321` | - | **Gate 1 Fails:** `400 / LICENSE_SUSPENDED` |
| **EXPIRED License** | `TNMC-2011-45110` | `HOSP-CHN-501` | Orthopaedics | `4511` | `654321` | - | **Gate 1 Fails:** `400 / LICENSE_EXPIRED` |
| **NOT IN REGISTRY** | `KMC-2024-00000` | Any | Any | `0000` | `654321` | - | **Gate 1 Fails:** `400 / LICENSE_NOT_FOUND` |
| **Wrong Hospital** | `KMC-2018-55120` | `HOSP-BLR-990` | Diabetology | `5512` | `654321` | - | **Gate 2 Fails:** `400 / HOSPITAL_NOT_AFFILIATED` (Affiliated only with HOSP-MYS-201) |
| **Wrong Govt ID** | `KMC-2020-77341` | `HOSP-BLR-990` | Occupational | `9999` *(Actual: 7734)* | `654321` | - | **Gate 3 Fails:** `400 / GOVID_MISMATCH` |
| **Wrong MFA OTP** | `KMC-2021-66219` | `HOSP-BLR-990` | Family Medicine | `6621` | `111111` *(Must be 654321)* | - | **Gate 4 Fails:** `401 / MFA_INVALID` |
| **Already Registered** | `KMC-2019-88412` | `HOSP-BLR-990` | Cardiology | `4412` | `654321` | `DOC-IN-8841` | **Re-registration Fails:** `409 ALREADY_REGISTERED` ("Sign in instead") |
| **Legacy Doctor 1** | `KMC-2015-20101` | `HOSP-BLR-990` | Cardiology | `2010` | `654321` | `DOC-201` | Dr. Sarah Jenkins (Backward compatibility anchor). |
| **Legacy Doctor 2** | `KMC-2017-20202` | `HOSP-BLR-104` | Diabetology | `2020` | `654321` | `DOC-202` | Dr. Rajesh Verma (Backward compatibility anchor). |

---

## 3. Key Patient Accounts & Clinical Scenarios

| Patient ID | Name | Origin -> Current | Occupation (Exposure) | ABHA Number | Active Consent PIN | Clinical Scenario / What It Demonstrates |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PAT-SS-1001** | Ramesh Kumar | Odisha (Ganjam) -> Bengaluru | Construction Mason (6 yrs) | `ABHA-21-9845-3310-7742` | `482910` | **Core Anchor:** Warfarin + Metformin + Atorvastatin. Penicillin allergy blocks Augmentin; Warfarin blocks Aspirin; KaamSuraksha returns HIGH silica risk; HbA1c/INR longitudinal trends. |
| **PAT-SS-1002** | Rajesh Yadav | Bihar (Gaya) -> Bengaluru | Textile / Garment (8 yrs) | `ABHA-14-3829-1102-4491` | `319402` | **Byssinosis Demo:** Cotton dust cough, Monday chest tightness. |
| **PAT-SS-1003** | Manjunath Gowda | Karnataka (Raichur) -> Bengaluru | Auto Driver (14 yrs) | `ABHA-29-7102-4910-8833` | `772184` | **Duplicate Therapy Demo:** 6+ active drugs, 2 concurrent NSAIDs (Diclofenac + Ibuprofen) and ACEI + ARB (Ramipril + Telmisartan). |
| **PAT-SS-1004** | Lakshmi Murugan | Tamil Nadu -> Bengaluru | Domestic Worker (9 yrs) | `ABHA-33-8812-4019-2210` | `551920` | **Sulfa Allergy Demo:** Documented sulfa allergy blocks Co-trimoxazole / Bactrim. |
| **PAT-SS-1005** | Santosh Pradhan | Odisha (Balasore) -> Bengaluru | Welder (7 yrs) | `ABHA-21-4401-9921-6677` | `620194` | **Aspirin-Sensitive Asthma:** Blocks Aspirin, Ibuprofen, Naproxen. |
| **PAT-SS-1006** | Bina Mondal | West Bengal -> Bengaluru | Kitchen Staff (4 yrs) | `ABHA-19-1029-4820-3344` | `184029` | **Clean Baseline Demo:** Zero allergies, clean history, new safe Rx returns SAVED cleanly; >95% adherence. |
| **PAT-SS-1007** | Dharmendra Paswan | Jharkhand -> Bengaluru | Stone Crusher (11 yrs) | `ABHA-10-8840-2219-5561` | `942103` | **Poor Adherence Escalation:** Missed 6 consecutive days, triggers ASHA / Doctor escalation. |
| **PAT-SS-1008** | Ankit Soren | Jharkhand -> Bengaluru | Delivery Rider (0 yrs) | `ABHA-20-9901-3312-8822` | `810294` | **Empty State Demo:** Arrived 5 days ago, empty medical history. |
| **PAT-SS-1009** | Suresh Reddy | Telangana -> Bengaluru | Security Guard (16 yrs) | `ABHA-36-5521-7788-1123` | `491023` | **Elderly & Break-Glass Audit:** Age 68, past consent revocation and past Break-Glass emergency override on audit trail. |
| **PAT-SS-1010** | Fatima Khatun | UP (Gorakhpur) -> Bengaluru | Sanitation Worker (3 yrs) | `ABHA-09-6612-4455-9988` | `719302` | **Pregnant Patient Demo:** 24 weeks gestation, antenatal care profile. |

---

## 4. Designated ASHA Worker Contacts
- **ASHA-OD-402:** Meena Majhi (Ganjam, Odisha) | Phone: `9000000301` | Languages: Odia, Hindi
- **ASHA-BH-501:** Sunita Devi (Gaya, Bihar) | Phone: `9000000302` | Languages: Hindi
- **ASHA-KA-101:** Parvathamma K. (Raichur, Karnataka) | Phone: `9000000303` | Languages: Kannada, Telugu

---

## 5. Security Note for Reviewers & Judges
1. All demo passwords hash to `Demo@123`.
2. In production or live AWS deployment, tokens rotate via Cognito User Pools.
3. Patient Consent PINs rotate upon patient revocation via the SwasthyaPassport screen.
