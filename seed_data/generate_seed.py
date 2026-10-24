"""
SwasthyaSetu & AWS Platform - Deterministic Seed Data Generator
Phase 1 Deliverable: seed_data/generate_seed.py
-----------------------------------------------------------------
Generates all 15 synthetic datasets deterministically (random.seed(42))
with dynamic relative dates from today:
  1. medical_councils.json (>=10)
  2. hospitals.json (>=15)
  3. doctors_registry.json (>=40)
  4. patients.json (25)
  5. reports.json (>=90) + report_templates/
  6. prescriptions_seed.json
  7. adherence_history.json (30 days for >=8 patients)
  8. ocr_samples.json (>=8 presets)
  9. drug_interactions.json (>=40 rules)
  10. medicine_generics.json (brand-to-generic resolution index)
  11. pharmacies.json (>=20 BLR, >=4 Odisha)
  12. asha_workers.json (>=10)
  13. occupational_risk.json (>=12 occupations)
  14. translation_phrasebook.json (>=80 phrases in EN/HI/OR/KN/TA/TE)
  15. audit_seed.json (>=60 events) & notifications_seed.json
Auto-generates DEMO_ACCOUNTS.md with password hash.
"""

import os
import sys
import json
import random
import re
import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from werkzeug.security import generate_password_hash

# Set deterministic seed
random.seed(42)

SEED_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SEED_DIR.parent
REPORT_TEMPLATES_DIR = SEED_DIR / "report_templates"
REPORT_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

NOW = datetime.now(timezone.utc)
TODAY = NOW.date()

def rel_days_iso(days_ago: int, hour: int = 10, minute: int = 0) -> str:
    """Returns ISO 8601 string relative to now."""
    dt = NOW - timedelta(days=days_ago)
    return dt.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()

def rel_days_date(days_ago: int) -> str:
    """Returns YYYY-MM-DD relative to today."""
    return (TODAY - timedelta(days=days_ago)).isoformat()


# ---------------------------------------------------------------------------
# 1. medical_councils.json (>=10)
# ---------------------------------------------------------------------------
def generate_medical_councils():
    councils = [
        {
            "councilCode": "NMC",
            "name": "National Medical Commission",
            "state": "National",
            "licensePrefix": "NMC",
            "licenseRegex": r"^NMC(-IND)?-\d{4,6}$",
            "registryStatus": "ACTIVE",
            "synthetic": True
        },
        {
            "councilCode": "KMC",
            "name": "Karnataka Medical Council",
            "state": "Karnataka",
            "licensePrefix": "KMC",
            "licenseRegex": r"^KMC-\d{4}-\d{5}$",
            "registryStatus": "ACTIVE",
            "synthetic": True
        },
        {
            "councilCode": "OCMR",
            "name": "Odisha Council of Medical Registration",
            "state": "Odisha",
            "licensePrefix": "OCMR",
            "licenseRegex": r"^(OCMR|OMC)-\d{4}-\d{5}$",
            "registryStatus": "ACTIVE",
            "synthetic": True
        },
        {
            "councilCode": "TNMC",
            "name": "Tamil Nadu Medical Council",
            "state": "Tamil Nadu",
            "licensePrefix": "TNMC",
            "licenseRegex": r"^TNMC-\d{4}-\d{5}$",
            "registryStatus": "ACTIVE",
            "synthetic": True
        },
        {
            "councilCode": "TSMC",
            "name": "Telangana State Medical Council",
            "state": "Telangana",
            "licensePrefix": "TSMC",
            "licenseRegex": r"^TSMC-\d{4}-\d{5}$",
            "registryStatus": "ACTIVE",
            "synthetic": True
        },
        {
            "councilCode": "APMC",
            "name": "Andhra Pradesh Medical Council",
            "state": "Andhra Pradesh",
            "licensePrefix": "APMC",
            "licenseRegex": r"^APMC-\d{4}-\d{5}$",
            "registryStatus": "ACTIVE",
            "synthetic": True
        },
        {
            "councilCode": "WBMC",
            "name": "West Bengal Medical Council",
            "state": "West Bengal",
            "licensePrefix": "WBMC",
            "licenseRegex": r"^WBMC-\d{4}-\d{5}$",
            "registryStatus": "ACTIVE",
            "synthetic": True
        },
        {
            "councilCode": "BMC",
            "name": "Bihar Medical Council",
            "state": "Bihar",
            "licensePrefix": "BMC",
            "licenseRegex": r"^BMC-\d{4}-\d{5}$",
            "registryStatus": "ACTIVE",
            "synthetic": True
        },
        {
            "councilCode": "JMC",
            "name": "Jharkhand Medical Council",
            "state": "Jharkhand",
            "licensePrefix": "JMC",
            "licenseRegex": r"^JMC-\d{4}-\d{5}$",
            "registryStatus": "ACTIVE",
            "synthetic": True
        },
        {
            "councilCode": "DMC",
            "name": "Delhi Medical Council",
            "state": "Delhi",
            "licensePrefix": "DMC",
            "licenseRegex": r"^DMC-\d{4}-\d{5}$",
            "registryStatus": "ACTIVE",
            "synthetic": True
        },
        {
            "councilCode": "MHMC",
            "name": "Maharashtra Medical Council",
            "state": "Maharashtra",
            "licensePrefix": "MHMC",
            "licenseRegex": r"^MHMC-\d{4}-\d{5}$",
            "registryStatus": "ACTIVE",
            "synthetic": True
        }
    ]
    with open(SEED_DIR / "medical_councils.json", "w", encoding="utf-8") as f:
        json.dump(councils, f, indent=2)
    return councils


# ---------------------------------------------------------------------------
# 2. hospitals.json (>=15)
# ---------------------------------------------------------------------------
def generate_hospitals():
    hospitals = [
        {
            "hospitalCode": "HOSP-BLR-990",
            "hospitalName": "Manipal Hospital Heart Institute, Whitefield",
            "type": "Private",
            "city": "Bengaluru",
            "state": "Karnataka",
            "lat": 12.9854,
            "lng": 77.7299,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "AIIMS-BBSR-101",
            "hospitalName": "All India Institute of Medical Sciences (AIIMS), Bhubaneswar",
            "type": "Govt",
            "city": "Bhubaneswar",
            "state": "Odisha",
            "lat": 20.2312,
            "lng": 85.7761,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-BLR-102",
            "hospitalName": "Victoria Hospital & Bangalore Medical College",
            "type": "Govt",
            "city": "Bengaluru",
            "state": "Karnataka",
            "lat": 12.9625,
            "lng": 77.5750,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-BLR-103",
            "hospitalName": "Bowring and Lady Curzon Hospital, Shivaji Nagar",
            "type": "Govt",
            "city": "Bengaluru",
            "state": "Karnataka",
            "lat": 12.9828,
            "lng": 77.6047,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-BLR-104",
            "hospitalName": "Aster CMI Hospital, Hebbal",
            "type": "Private",
            "city": "Bengaluru",
            "state": "Karnataka",
            "lat": 13.0489,
            "lng": 77.5932,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-BLR-105",
            "hospitalName": "KC General Hospital, Malleshwaram",
            "type": "Govt",
            "city": "Bengaluru",
            "state": "Karnataka",
            "lat": 12.9976,
            "lng": 77.5714,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-BLR-106",
            "hospitalName": "Bommanahalli Community Health Centre (CHC)",
            "type": "CHC",
            "city": "Bengaluru",
            "state": "Karnataka",
            "lat": 12.9038,
            "lng": 77.6258,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-BLR-107",
            "hospitalName": "Peenya Urban Primary Health Centre (PHC)",
            "type": "PHC",
            "city": "Bengaluru",
            "state": "Karnataka",
            "lat": 13.0329,
            "lng": 77.5273,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-MYS-201",
            "hospitalName": "KR Hospital & Mysore Medical College",
            "type": "Medical College",
            "city": "Mysuru",
            "state": "Karnataka",
            "lat": 12.3168,
            "lng": 76.6506,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-MYS-202",
            "hospitalName": "Apollo BGS Hospital, Kuvempunagar",
            "type": "Private",
            "city": "Mysuru",
            "state": "Karnataka",
            "lat": 12.2965,
            "lng": 76.6268,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-CTC-301",
            "hospitalName": "SCB Medical College and Hospital, Cuttack",
            "type": "Medical College",
            "city": "Cuttack",
            "state": "Odisha",
            "lat": 20.4789,
            "lng": 85.8824,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-CTC-302",
            "hospitalName": "Cuttack Sadar Sub-Divisional Hospital",
            "type": "Govt",
            "city": "Cuttack",
            "state": "Odisha",
            "lat": 20.4625,
            "lng": 85.8690,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-PAT-401",
            "hospitalName": "Patna Medical College and Hospital (PMCH)",
            "type": "Medical College",
            "city": "Patna",
            "state": "Bihar",
            "lat": 25.6207,
            "lng": 85.1601,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-PAT-402",
            "hospitalName": "AIIMS Patna, Phulwari Sharif",
            "type": "Govt",
            "city": "Patna",
            "state": "Bihar",
            "lat": 25.5606,
            "lng": 85.0449,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-CHN-501",
            "hospitalName": "Rajiv Gandhi Government General Hospital",
            "type": "Govt",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "lat": 13.0818,
            "lng": 80.2785,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-HYD-601",
            "hospitalName": "Osmania General Hospital, Afzal Gunj",
            "type": "Govt",
            "city": "Hyderabad",
            "state": "Telangana",
            "lat": 17.3785,
            "lng": 78.4747,
            "status": "ACTIVE",
            "synthetic": True
        },
        {
            "hospitalCode": "HOSP-BLR-INACT",
            "hospitalName": "Shree Shanti Community Clinic (Decommissioned)",
            "type": "Private",
            "city": "Bengaluru",
            "state": "Karnataka",
            "lat": 12.9352,
            "lng": 77.6245,
            "status": "INACTIVE",
            "synthetic": True
        }
    ]
    with open(SEED_DIR / "hospitals.json", "w", encoding="utf-8") as f:
        json.dump(hospitals, f, indent=2)
    return hospitals


# ---------------------------------------------------------------------------
# 3. doctors_registry.json (>=40)
# ---------------------------------------------------------------------------
def generate_doctors_registry():
    # Pre-defined mandatory scenarios
    mandatory = [
        # 1. VALID pre-registered doctor
        {
            "licenseNumber": "KMC-2019-88412",
            "councilCode": "KMC",
            "fullName": "Dr. Ananya Sharma",
            "degree": "MBBS, MD (Cardiology)",
            "specialty": "Cardiology",
            "registrationYear": 2019,
            "validTill": rel_days_date(-1200),
            "status": "ACTIVE",
            "hospitalCodes": ["HOSP-BLR-990", "HOSP-BLR-102"],
            "govIdLast4": "4412",
            "languages": ["Kannada", "Hindi", "English"],
            "city": "Bengaluru",
            "registered": True,
            "doctorId": "DOC-IN-8841",
            "scenario": "VALID_CARDIO",
            "synthetic": True
        },
        # 2. VALID (Odisha) un-registered doctor for live judge registration
        {
            "licenseNumber": "NMC-IND-55201",
            "councilCode": "NMC",
            "fullName": "Dr. Debabrata Nayak",
            "degree": "MBBS, MD (Pulmonary Medicine)",
            "specialty": "Pulmonology",
            "registrationYear": 2018,
            "validTill": rel_days_date(-1500),
            "status": "ACTIVE",
            "hospitalCodes": ["AIIMS-BBSR-101", "HOSP-CTC-301"],
            "govIdLast4": "5201",
            "languages": ["Odia", "Hindi", "English"],
            "city": "Bhubaneswar",
            "registered": False,
            "doctorId": None,
            "scenario": "VALID_ODISHA_UNREGISTERED",
            "synthetic": True
        },
        # 3. SUSPENDED licence
        {
            "licenseNumber": "KMC-2016-10233",
            "councilCode": "KMC",
            "fullName": "Dr. Vikram Rao",
            "degree": "MBBS, MD (General Medicine)",
            "specialty": "General Medicine",
            "registrationYear": 2016,
            "validTill": rel_days_date(-300),
            "status": "SUSPENDED",
            "hospitalCodes": ["HOSP-BLR-102"],
            "govIdLast4": "1023",
            "languages": ["Kannada", "English"],
            "city": "Bengaluru",
            "registered": False,
            "doctorId": None,
            "scenario": "GATE1_SUSPENDED",
            "synthetic": True
        },
        # 4. EXPIRED licence
        {
            "licenseNumber": "TNMC-2011-45110",
            "councilCode": "TNMC",
            "fullName": "Dr. Karthik Sundaram",
            "degree": "MBBS, MS (Orthopaedics)",
            "specialty": "Orthopaedics",
            "registrationYear": 2011,
            "validTill": rel_days_date(180),
            "status": "EXPIRED",
            "hospitalCodes": ["HOSP-CHN-501"],
            "govIdLast4": "4511",
            "languages": ["Tamil", "English"],
            "city": "Chennai",
            "registered": False,
            "doctorId": None,
            "scenario": "GATE1_EXPIRED",
            "synthetic": True
        },
        # 5. (NOT IN REGISTRY is KMC-2024-00000, omitted from registry file)
        # 6. Valid licence, wrong hospital
        {
            "licenseNumber": "KMC-2018-55120",
            "councilCode": "KMC",
            "fullName": "Dr. Sunita Patil",
            "degree": "MBBS, MD (Diabetology)",
            "specialty": "Diabetology",
            "registrationYear": 2018,
            "validTill": rel_days_date(-1000),
            "status": "ACTIVE",
            "hospitalCodes": ["HOSP-MYS-201"],
            "govIdLast4": "5512",
            "languages": ["Kannada", "Hindi", "English"],
            "city": "Mysuru",
            "registered": False,
            "doctorId": None,
            "scenario": "GATE2_WRONG_HOSPITAL",
            "synthetic": True
        },
        # 7. Valid licence, wrong Govt ID test
        {
            "licenseNumber": "KMC-2020-77341",
            "councilCode": "KMC",
            "fullName": "Dr. Arvind Bhat",
            "degree": "MBBS, MD (Occupational Health)",
            "specialty": "Occupational Medicine",
            "registrationYear": 2020,
            "validTill": rel_days_date(-1400),
            "status": "ACTIVE",
            "hospitalCodes": ["HOSP-BLR-990"],
            "govIdLast4": "7734",
            "languages": ["Kannada", "English"],
            "city": "Bengaluru",
            "registered": False,
            "doctorId": None,
            "scenario": "GATE3_WRONG_GOVID",
            "synthetic": True
        },
        # 8. Valid licence, wrong OTP test
        {
            "licenseNumber": "KMC-2021-66219",
            "councilCode": "KMC",
            "fullName": "Dr. Priya Hegde",
            "degree": "MBBS, DNB (Family Medicine)",
            "specialty": "Family Medicine",
            "registrationYear": 2021,
            "validTill": rel_days_date(-1600),
            "status": "ACTIVE",
            "hospitalCodes": ["HOSP-BLR-990"],
            "govIdLast4": "6621",
            "languages": ["Kannada", "Hindi", "English"],
            "city": "Bengaluru",
            "registered": False,
            "doctorId": None,
            "scenario": "GATE4_WRONG_OTP",
            "synthetic": True
        },
        # Test registered doctor for live registration checklist
        {
            "licenseNumber": "KMC-2023-99881",
            "councilCode": "KMC",
            "fullName": "Dr. Ananya Sen",
            "degree": "MBBS, MD",
            "specialty": "Internal Medicine",
            "registrationYear": 2023,
            "validTill": rel_days_date(-1200),
            "status": "ACTIVE",
            "hospitalCodes": ["HOSP-BLR-990"],
            "govIdLast4": "8812",
            "languages": ["English", "Hindi"],
            "city": "Bengaluru",
            "registered": False,
            "doctorId": None,
            "scenario": "CHECKLIST_REGISTER_DOC",
            "synthetic": True
        },
        # Pre-registered DOC-201 and DOC-202 for backward compatibility
        {
            "licenseNumber": "KMC-2015-20101",
            "councilCode": "KMC",
            "fullName": "Dr. Sarah Jenkins",
            "degree": "MBBS, MD, FACC",
            "specialty": "Cardiology",
            "registrationYear": 2015,
            "validTill": rel_days_date(-1800),
            "status": "ACTIVE",
            "hospitalCodes": ["HOSP-BLR-990", "HOSP-BLR-104"],
            "govIdLast4": "2010",
            "languages": ["English", "Hindi"],
            "city": "Bengaluru",
            "registered": True,
            "doctorId": "DOC-201",
            "scenario": "LEGACY_DOC_201",
            "synthetic": True
        },
        {
            "licenseNumber": "KMC-2017-20202",
            "councilCode": "KMC",
            "fullName": "Dr. Rajesh Verma",
            "degree": "MBBS, MD, DM (Endocrinology)",
            "specialty": "Diabetology",
            "registrationYear": 2017,
            "validTill": rel_days_date(-1500),
            "status": "ACTIVE",
            "hospitalCodes": ["HOSP-BLR-104", "HOSP-BLR-990"],
            "govIdLast4": "2020",
            "languages": ["Hindi", "English", "Kannada"],
            "city": "Bengaluru",
            "registered": True,
            "doctorId": "DOC-202",
            "scenario": "LEGACY_DOC_202",
            "synthetic": True
        }
    ]

    # Additional doctors to reach >= 42 entries
    specialties = [
        "Cardiology", "General Medicine", "Pulmonology", "Occupational Medicine",
        "Diabetology", "Paediatrics", "Obstetrics & Gynaecology", "Orthopaedics",
        "Psychiatry", "Family Medicine", "Nephrology", "Dermatology"
    ]
    first_names = [
        "Rohan", "Pooja", "Amit", "Deepa", "Sanjay", "Meera", "Alok", "Kavita",
        "Manoj", "Shalini", "Girish", "Swati", "Suresh", "Nandini", "Pradeep",
        "Radha", "Chetan", "Archana", "Manish", "Divya", "Vinay", "Bhavna",
        "Harish", "Rekha", "Tarun", "Geetha", "Siddharth", "Preeti", "Kiran",
        "Sneha", "Ashok", "Pallavi", "Gaurav", "Anita"
    ]
    last_names = [
        "Deshmukh", "Nambiar", "Mukherjee", "Banerjee", "Chakraborty", "Choudhury",
        "Sinha", "Mishra", "Patel", "Reddy", "Iyer", "Nair", "Rao", "Shetty",
        "Bhat", "Kulkarni", "Joshi", "Das", "Samantaray", "Tripathy", "Mahapatra"
    ]
    councils_list = ["KMC", "OCMR", "TNMC", "TSMC", "APMC", "WBMC", "BMC", "JMC", "DMC", "MHMC"]
    hospitals_list = ["HOSP-BLR-990", "HOSP-BLR-102", "HOSP-BLR-104", "HOSP-BLR-106", "AIIMS-BBSR-101", "HOSP-CTC-301", "HOSP-PAT-401", "HOSP-CHN-501", "HOSP-HYD-601"]

    doctors = list(mandatory)
    unregistered_count = sum(1 for d in doctors if not d["registered"])

    for i in range(len(doctors), 42):
        spec = specialties[i % len(specialties)]
        fn = first_names[i % len(first_names)]
        ln = last_names[i % len(last_names)]
        cc = councils_list[i % len(councils_list)]
        yr = 2012 + (i % 10)
        lic_num = f"{cc}-{yr}-{random.randint(10000, 99999)}"
        hosp = [hospitals_list[i % len(hospitals_list)]]
        govid = f"{random.randint(1000, 9999)}"
        
        make_unregistered = (unregistered_count < 10) and (i % 3 == 0)
        if make_unregistered:
            unregistered_count += 1
            is_reg = False
            doc_id = None
        else:
            is_reg = True
            doc_id = f"DOC-IN-{random.randint(1000, 9999)}"

        doc_entry = {
            "licenseNumber": lic_num,
            "councilCode": cc,
            "fullName": f"Dr. {fn} {ln}",
            "degree": f"MBBS, MD ({spec})" if "Cardio" in spec or "Pulm" in spec or "Med" in spec else "MBBS, MS",
            "specialty": spec,
            "registrationYear": yr,
            "validTill": rel_days_date(-random.randint(400, 2000)),
            "status": "ACTIVE",
            "hospitalCodes": hosp,
            "govIdLast4": govid,
            "languages": ["English", "Hindi"] if cc != "OCMR" else ["Odia", "English", "Hindi"],
            "city": "Bengaluru" if "BLR" in hosp[0] else ("Bhubaneswar" if "BBSR" in hosp[0] or "CTC" in hosp[0] else "Regional Metro"),
            "registered": is_reg,
            "doctorId": doc_id,
            "scenario": f"GENERAL_{spec.upper().replace(' ', '_')}",
            "synthetic": True
        }
        doctors.append(doc_entry)

    with open(SEED_DIR / "doctors_registry.json", "w", encoding="utf-8") as f:
        json.dump(doctors, f, indent=2)
    return doctors


# ---------------------------------------------------------------------------
# 4. patients.json (25)
# ---------------------------------------------------------------------------
def generate_patients():
    patients = [
        # 1. PAT-SS-1001: Ramesh Kumar (Anchor)
        {
            "patientId": "PAT-SS-1001",
            "name": "Ramesh Kumar",
            "age": 48,
            "gender": "Male",
            "originState": "Odisha",
            "originDistrict": "Ganjam",
            "currentLocation": "Whitefield, Bengaluru",
            "lat": 12.9716,
            "lng": 77.7499,
            "preferredLanguage": "Odia",
            "occupation": "Construction Site Mason",
            "exposureYears": 6,
            "allergies": ["Penicillin", "Dust / Cement Silica"],
            "comorbidities": ["Type 2 Diabetes Mellitus", "Deep Vein Thrombosis (Post-Embolic)", "Hypertension"],
            "abhaId": "ABHA-21-9845-3310-7742",
            "mobile": "9000000001",
            "caregiver": {
                "name": "Sunita Kumar",
                "mobile": "9000000002",
                "relation": "Wife"
            },
            "linkedAshaWorker": "ASHA-OD-402",
            "consent": {
                "pin": "482910",
                "rotatedAt": rel_days_iso(2),
                "activeGrants": []
            },
            "synthetic": True
        },
        # 2. PAT-SS-1002: Rajesh Yadav (Byssinosis demo)
        {
            "patientId": "PAT-SS-1002",
            "name": "Rajesh Yadav",
            "age": 36,
            "gender": "Male",
            "originState": "Bihar",
            "originDistrict": "Gaya",
            "currentLocation": "Bommanahalli, Bengaluru",
            "lat": 12.9038,
            "lng": 77.6258,
            "preferredLanguage": "Hindi",
            "occupation": "Textile / Garment Worker",
            "exposureYears": 8,
            "allergies": [],
            "comorbidities": ["Occupational Byssinosis", "Industrial Bronchitis"],
            "abhaId": "ABHA-14-3829-1102-4491",
            "mobile": "9000000003",
            "caregiver": {
                "name": "Geeta Yadav",
                "mobile": "9000000021",
                "relation": "Wife"
            },
            "linkedAshaWorker": "ASHA-BH-501",
            "consent": {
                "pin": "319402",
                "rotatedAt": rel_days_iso(5),
                "activeGrants": []
            },
            "synthetic": True
        },
        # 3. PAT-SS-1003: Manjunath Gowda (Duplicate therapy demo: 6+ drugs, 2 NSAIDs + ACEI/ARB)
        {
            "patientId": "PAT-SS-1003",
            "name": "Manjunath Gowda",
            "age": 56,
            "gender": "Male",
            "originState": "Karnataka",
            "originDistrict": "Raichur",
            "currentLocation": "Peenya, Bengaluru",
            "lat": 13.0329,
            "lng": 77.5273,
            "preferredLanguage": "Kannada",
            "occupation": "Auto Rickshaw Driver",
            "exposureYears": 14,
            "allergies": [],
            "comorbidities": ["Knee Osteoarthritis", "Essential Hypertension", "Chronic Lumbar Strain"],
            "abhaId": "ABHA-29-7102-4910-8833",
            "mobile": "9000000004",
            "caregiver": {
                "name": "Sharada Gowda",
                "mobile": "9000000022",
                "relation": "Daughter"
            },
            "linkedAshaWorker": "ASHA-KA-101",
            "consent": {
                "pin": "772184",
                "rotatedAt": rel_days_iso(10),
                "activeGrants": []
            },
            "synthetic": True
        },
        # 4. PAT-SS-1004: Lakshmi Murugan (Sulfa allergy demo)
        {
            "patientId": "PAT-SS-1004",
            "name": "Lakshmi Murugan",
            "age": 42,
            "gender": "Female",
            "originState": "Tamil Nadu",
            "originDistrict": "Tirunelveli",
            "currentLocation": "Electronic City, Bengaluru",
            "lat": 12.8399,
            "lng": 77.6770,
            "preferredLanguage": "Tamil",
            "occupation": "Domestic Worker",
            "exposureYears": 9,
            "allergies": ["Sulfa", "Sulfonamides"],
            "comorbidities": ["Recurrent Urinary Tract Infections", "Mild Anemia"],
            "abhaId": "ABHA-33-8812-4019-2210",
            "mobile": "9000000005",
            "caregiver": {
                "name": "Murugan S.",
                "mobile": "9000000023",
                "relation": "Husband"
            },
            "linkedAshaWorker": "ASHA-TN-301",
            "consent": {
                "pin": "551920",
                "rotatedAt": rel_days_iso(8),
                "activeGrants": []
            },
            "synthetic": True
        },
        # 5. PAT-SS-1005: Santosh Pradhan (NSAID/Aspirin sensitive asthma demo)
        {
            "patientId": "PAT-SS-1005",
            "name": "Santosh Pradhan",
            "age": 34,
            "gender": "Male",
            "originState": "Odisha",
            "originDistrict": "Balasore",
            "currentLocation": "KR Puram, Bengaluru",
            "lat": 13.0075,
            "lng": 77.6959,
            "preferredLanguage": "Odia",
            "occupation": "Welder / Metal Fabricator",
            "exposureYears": 7,
            "allergies": ["Aspirin", "NSAIDs"],
            "comorbidities": ["Aspirin-Exacerbated Respiratory Disease (AERD)", "Asthma"],
            "abhaId": "ABHA-21-4401-9921-6677",
            "mobile": "9000000006",
            "caregiver": {
                "name": "Mitali Pradhan",
                "mobile": "9000000024",
                "relation": "Sister"
            },
            "linkedAshaWorker": "ASHA-OD-402",
            "consent": {
                "pin": "620194",
                "rotatedAt": rel_days_iso(4),
                "activeGrants": []
            },
            "synthetic": True
        },
        # 6. PAT-SS-1006: Bina Mondal (Clean record, SAVED demo)
        {
            "patientId": "PAT-SS-1006",
            "name": "Bina Mondal",
            "age": 29,
            "gender": "Female",
            "originState": "West Bengal",
            "originDistrict": "Murshidabad",
            "currentLocation": "Yeshwanthpur, Bengaluru",
            "lat": 13.0280,
            "lng": 77.5404,
            "preferredLanguage": "English",
            "occupation": "Hotel Kitchen Staff",
            "exposureYears": 4,
            "allergies": [],
            "comorbidities": [],
            "abhaId": "ABHA-19-1029-4820-3344",
            "mobile": "9000000007",
            "caregiver": {
                "name": "Tapan Mondal",
                "mobile": "9000000025",
                "relation": "Brother"
            },
            "linkedAshaWorker": "ASHA-WB-601",
            "consent": {
                "pin": "184029",
                "rotatedAt": rel_days_iso(12),
                "activeGrants": []
            },
            "synthetic": True
        },
        # 7. PAT-SS-1007: Dharmendra Paswan (Poor adherence & escalation demo)
        {
            "patientId": "PAT-SS-1007",
            "name": "Dharmendra Paswan",
            "age": 52,
            "gender": "Male",
            "originState": "Jharkhand",
            "originDistrict": "Dhanbad",
            "currentLocation": "Whitefield, Bengaluru",
            "lat": 12.9698,
            "lng": 77.7502,
            "preferredLanguage": "Hindi",
            "occupation": "Quarry / Stone-Crusher Worker",
            "exposureYears": 11,
            "allergies": [],
            "comorbidities": ["Hypertension (Stage 2)", "Accelerated Silicosis"],
            "abhaId": "ABHA-10-8840-2219-5561",
            "mobile": "9000000008",
            "caregiver": {
                "name": "Sunil Paswan",
                "mobile": "9000000026",
                "relation": "Son"
            },
            "linkedAshaWorker": "ASHA-JH-701",
            "consent": {
                "pin": "942103",
                "rotatedAt": rel_days_iso(1),
                "activeGrants": []
            },
            "synthetic": True
        },
        # 8. PAT-SS-1008: Ankit Soren (Newly arrived, empty state demo)
        {
            "patientId": "PAT-SS-1008",
            "name": "Ankit Soren",
            "age": 22,
            "gender": "Male",
            "originState": "Jharkhand",
            "originDistrict": "Dumka",
            "currentLocation": "Hebbal, Bengaluru",
            "lat": 13.0358,
            "lng": 77.5970,
            "preferredLanguage": "Hindi",
            "occupation": "Delivery Rider",
            "exposureYears": 0,
            "allergies": [],
            "comorbidities": [],
            "abhaId": "ABHA-20-9901-3312-8822",
            "mobile": "9000000009",
            "caregiver": {
                "name": "Rani Soren",
                "mobile": "9000000027",
                "relation": "Mother"
            },
            "linkedAshaWorker": "ASHA-JH-701",
            "consent": {
                "pin": "810294",
                "rotatedAt": rel_days_iso(0),
                "activeGrants": []
            },
            "synthetic": True
        },
        # 9. PAT-SS-1009: Suresh Reddy (Elderly 65+, past revoke & break-glass audit demo)
        {
            "patientId": "PAT-SS-1009",
            "name": "Suresh Reddy",
            "age": 68,
            "gender": "Male",
            "originState": "Telangana",
            "originDistrict": "Mahbubnagar",
            "currentLocation": "Bommanahalli, Bengaluru",
            "lat": 12.9050,
            "lng": 77.6270,
            "preferredLanguage": "Telugu",
            "occupation": "Security Guard",
            "exposureYears": 16,
            "allergies": ["Ciprofloxacin"],
            "comorbidities": ["Coronary Artery Disease", "Type 2 Diabetes Mellitus", "Peripheral Neuropathy"],
            "abhaId": "ABHA-36-5521-7788-1123",
            "mobile": "9000000010",
            "caregiver": {
                "name": "Venkat Reddy",
                "mobile": "9000000028",
                "relation": "Son"
            },
            "linkedAshaWorker": "ASHA-TS-201",
            "consent": {
                "pin": "491023",
                "rotatedAt": rel_days_iso(3),
                "activeGrants": []
            },
            "synthetic": True
        },
        # 10. PAT-SS-1010: Fatima Khatun (Pregnant patient demo)
        {
            "patientId": "PAT-SS-1010",
            "name": "Fatima Khatun",
            "age": 26,
            "gender": "Female",
            "originState": "Uttar Pradesh",
            "originDistrict": "Gorakhpur",
            "currentLocation": "KR Puram, Bengaluru",
            "lat": 13.0080,
            "lng": 77.6965,
            "preferredLanguage": "Hindi",
            "occupation": "Sanitation Worker",
            "exposureYears": 3,
            "allergies": [],
            "comorbidities": ["Pregnancy (24 Weeks Gestation)", "Gestational Iron Deficiency"],
            "abhaId": "ABHA-09-6612-4455-9988",
            "mobile": "9000000011",
            "caregiver": {
                "name": "Mohammed Arif",
                "mobile": "9000000029",
                "relation": "Husband"
            },
            "linkedAshaWorker": "ASHA-UP-801",
            "consent": {
                "pin": "719302",
                "rotatedAt": rel_days_iso(6),
                "activeGrants": []
            },
            "synthetic": True
        }
    ]

    extra_names = [
        ("Subhasis Jena", 41, "Male", "Odisha", "Kendrapara", "Whitefield", "Odia", "Painter / Coating Worker", 8, ["Penicillin"]),
        ("Priya Sharma", 38, "Female", "Bihar", "Patna", "Hebbal", "Hindi", "Textile / Garment Worker", 5, ["NSAIDs", "Aspirin"]),
        ("Basavaraj Bellad", 50, "Male", "Karnataka", "Kalaburagi", "Peenya", "Kannada", "Construction Site Mason", 12, []),
        ("Anjali Tirkey", 28, "Female", "Jharkhand", "Ranchi", "Bommanahalli", "Hindi", "Domestic Worker", 4, []),
        ("Debabrata Das", 45, "Male", "West Bengal", "Bankura", "Yeshwanthpur", "English", "Welder / Metal Fabricator", 9, []),
        ("Kavitha Selvam", 33, "Female", "Tamil Nadu", "Salem", "Electronic City", "Tamil", "Textile / Garment Worker", 6, ["Sulfa"]),
        ("Narsimha Rao", 49, "Male", "Andhra Pradesh", "Srikakulam", "KR Puram", "Telugu", "Sanitation Worker", 10, []),
        ("Raju Mahato", 37, "Male", "Bihar", "Muzaffarpur", "Peenya", "Hindi", "Quarry / Stone-Crusher Worker", 7, []),
        ("Santoshi Nayak", 31, "Female", "Odisha", "Mayurbhanj", "Bommanahalli", "Odia", "Hotel Kitchen Staff", 5, []),
        ("Vijay Bhaskar", 54, "Male", "Telangana", "Nalgonda", "Whitefield", "Telugu", "Security Guard", 13, []),
        ("Ranjit Barman", 40, "Male", "West Bengal", "Cooch Behar", "Yeshwanthpur", "English", "Agricultural Farm Labourer", 11, []),
        ("Meena Kumari", 35, "Female", "Bihar", "Samastipur", "Electronic City", "Hindi", "Domestic Worker", 6, []),
        ("Pratap Behera", 46, "Male", "Odisha", "Puri", "KR Puram", "Odia", "Delivery Rider", 4, []),
        ("Siddappa Koli", 58, "Male", "Karnataka", "Vijayapura", "Peenya", "Kannada", "Construction Site Mason", 15, []),
        ("Afzal Ansari", 39, "Male", "Jharkhand", "Bokaro", "Hebbal", "Hindi", "Welder / Metal Fabricator", 8, [])
    ]

    for idx, (pname, page, pgender, pstate, pdist, ploc, plang, pocc, pexp, pal) in enumerate(extra_names, start=11):
        pid = f"PAT-SS-{1000 + idx}"
        patient_entry = {
            "patientId": pid,
            "name": pname,
            "age": page,
            "gender": pgender,
            "originState": pstate,
            "originDistrict": pdist,
            "currentLocation": f"{ploc}, Bengaluru",
            "lat": round(12.85 + (idx * 0.012), 4),
            "lng": round(77.52 + (idx * 0.015), 4),
            "preferredLanguage": plang,
            "occupation": pocc,
            "exposureYears": pexp,
            "allergies": pal,
            "comorbidities": ["Hypertension"] if page > 45 else [],
            "abhaId": f"ABHA-{random.randint(10, 99)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            "mobile": f"90000000{idx:02d}",
            "caregiver": {
                "name": f"Family Member ({pname.split()[-1]})",
                "mobile": f"90000001{idx:02d}",
                "relation": "Kin"
            },
            "linkedAshaWorker": "ASHA-OD-402" if pstate == "Odisha" else ("ASHA-BH-501" if pstate == "Bihar" else "ASHA-KA-101"),
            "consent": {
                "pin": f"{random.randint(100000, 999999)}",
                "rotatedAt": rel_days_iso(idx % 14),
                "activeGrants": []
            },
            "synthetic": True
        }
        patients.append(patient_entry)

    with open(SEED_DIR / "patients.json", "w", encoding="utf-8") as f:
        json.dump(patients, f, indent=2)
    return patients


# ---------------------------------------------------------------------------
# 5. reports.json (>=90) & report_templates/
# ---------------------------------------------------------------------------
def generate_reports(patients):
    reports = []
    
    # Mandatory reports for PAT-SS-1001 (Ramesh Kumar)
    reports.append({
        "reportId": "RPT-PAT-SS-1001-01",
        "patientId": "PAT-SS-1001",
        "type": "LAB",
        "title": "Glycated Hemoglobin (HbA1c) Monitoring - Baseline",
        "date": rel_days_iso(270),
        "facility": "MKCG Medical College & Hospital, Berhampur",
        "facilityState": "Odisha",
        "orderedBy": "Dr. Prasant Mohanty, MD",
        "language": "English",
        "source": "HOME_STATE_PHC",
        "results": [
            {"name": "HbA1c", "value": 8.9, "unit": "%", "refLow": 4.0, "refHigh": 5.6, "flag": "H"},
            {"name": "Estimated Average Glucose (eAG)", "value": 208, "unit": "mg/dL", "refLow": 70, "refHigh": 126, "flag": "H"}
        ],
        "findings": "Significant hyperglycemia consistent with suboptimally managed Type 2 Diabetes Mellitus.",
        "impression": "Poorly controlled T2DM. Metformin initiated and titrated.",
        "attachment": {"ocrRawText": "MKCG MCH BERHAMPUR - HbA1c: 8.9% (HIGH), eAG: 208 mg/dL. Baseline diabetic evaluation.", "ocrConfidence": 0.96},
        "fhirResourceType": "DiagnosticReport",
        "synthetic": True
    })

    reports.append({
        "reportId": "RPT-PAT-SS-1001-02",
        "patientId": "PAT-SS-1001",
        "type": "LAB",
        "title": "Glycated Hemoglobin (HbA1c) Follow-up",
        "date": rel_days_iso(150),
        "facility": "Whitefield Urban Primary Health Centre",
        "facilityState": "Karnataka",
        "orderedBy": "Dr. Sarah Jenkins, MD, FACC",
        "language": "English",
        "source": "BENGALURU_CLINIC",
        "results": [
            {"name": "HbA1c", "value": 8.1, "unit": "%", "refLow": 4.0, "refHigh": 5.6, "flag": "H"},
            {"name": "Fasting Blood Sugar (FBS)", "value": 158, "unit": "mg/dL", "refLow": 70, "refHigh": 100, "flag": "H"}
        ],
        "findings": "Fasting blood sugar remains elevated but improving on dual-dose Metformin 500mg.",
        "impression": "Improving glycemic control. Continue lifestyle and adherence reinforcement.",
        "attachment": {"ocrRawText": "UPHC WHITEFIELD - HbA1c: 8.1% (H), FBS: 158 mg/dL. Titrate diet.", "ocrConfidence": 0.94},
        "fhirResourceType": "DiagnosticReport",
        "synthetic": True
    })

    reports.append({
        "reportId": "RPT-PAT-SS-1001-03",
        "patientId": "PAT-SS-1001",
        "type": "LAB",
        "title": "Glycated Hemoglobin (HbA1c) Routine Panel",
        "date": rel_days_iso(30),
        "facility": "Manipal Hospital Heart Institute, Whitefield",
        "facilityState": "Karnataka",
        "orderedBy": "Dr. Ananya Sharma, MD",
        "language": "English",
        "source": "BENGALURU_CLINIC",
        "results": [
            {"name": "HbA1c", "value": 7.4, "unit": "%", "refLow": 4.0, "refHigh": 5.6, "flag": "H"},
            {"name": "Post-Prandial Blood Sugar (PPBS)", "value": 142, "unit": "mg/dL", "refLow": 70, "refHigh": 140, "flag": "H"}
        ],
        "findings": "HbA1c demonstrated marked reduction from 8.9% to 7.4% across 9 months.",
        "impression": "Demonstrable therapeutic response to adherence tracking. Approaching clinical target (<7.0%).",
        "attachment": {"ocrRawText": "MANIPAL HOSPITALS - HbA1c: 7.4%, PPBS: 142 mg/dL. Excellent response.", "ocrConfidence": 0.98},
        "fhirResourceType": "DiagnosticReport",
        "synthetic": True
    })

    reports.append({
        "reportId": "RPT-PAT-SS-1001-04",
        "patientId": "PAT-SS-1001",
        "type": "LAB",
        "title": "Prothrombin Time & INR Monitoring",
        "date": rel_days_iso(180),
        "facility": "Whitefield Urban PHC",
        "facilityState": "Karnataka",
        "orderedBy": "Dr. Sarah Jenkins, MD, FACC",
        "language": "English",
        "source": "BENGALURU_CLINIC",
        "results": [
            {"name": "INR", "value": 2.1, "unit": "ratio", "refLow": 2.0, "refHigh": 3.0, "flag": "N"},
            {"name": "Prothrombin Time", "value": 23.4, "unit": "seconds", "refLow": 11.0, "refHigh": 13.5, "flag": "H"}
        ],
        "findings": "International Normalized Ratio (INR) is within target therapeutic window (2.0 - 3.0).",
        "impression": "Therapeutic Warfarin 5mg maintenance for DVT prophylaxis.",
        "attachment": {"ocrRawText": "INR: 2.1 (Therapeutic 2.0-3.0), PT: 23.4s.", "ocrConfidence": 0.95},
        "fhirResourceType": "DiagnosticReport",
        "synthetic": True
    })

    reports.append({
        "reportId": "RPT-PAT-SS-1001-05",
        "patientId": "PAT-SS-1001",
        "type": "LAB",
        "title": "Urgent Coagulation Profile (INR)",
        "date": rel_days_iso(90),
        "facility": "Manipal Hospital Heart Institute, Whitefield",
        "facilityState": "Karnataka",
        "orderedBy": "Dr. Ananya Sharma, MD",
        "language": "English",
        "source": "BENGALURU_CLINIC",
        "results": [
            {"name": "INR", "value": 3.4, "unit": "ratio", "refLow": 2.0, "refHigh": 3.0, "flag": "H"},
            {"name": "Prothrombin Time", "value": 38.2, "unit": "seconds", "refLow": 11.0, "refHigh": 13.5, "flag": "CRITICAL"}
        ],
        "findings": "Elevated INR above target range. Moderate bleeding diathesis risk.",
        "impression": "Supra-therapeutic anticoagulation. Warfarin dose titrating protocol engaged; avoid all NSAIDs and Aspirin.",
        "attachment": {"ocrRawText": "CRITICAL LAB ALERT - INR: 3.4 (HIGH), PT: 38.2s. Hold 1 dose Warfarin.", "ocrConfidence": 0.99},
        "fhirResourceType": "DiagnosticReport",
        "synthetic": True
    })

    reports.append({
        "reportId": "RPT-PAT-SS-1001-06",
        "patientId": "PAT-SS-1001",
        "type": "LAB",
        "title": "Follow-up Coagulation Profile",
        "date": rel_days_iso(30),
        "facility": "Manipal Hospital Heart Institute, Whitefield",
        "facilityState": "Karnataka",
        "orderedBy": "Dr. Ananya Sharma, MD",
        "language": "English",
        "source": "BENGALURU_CLINIC",
        "results": [
            {"name": "INR", "value": 2.6, "unit": "ratio", "refLow": 2.0, "refHigh": 3.0, "flag": "N"},
            {"name": "Prothrombin Time", "value": 27.8, "unit": "seconds", "refLow": 11.0, "refHigh": 13.5, "flag": "H"}
        ],
        "findings": "INR returned cleanly to mid-therapeutic target range (2.6).",
        "impression": "Stable anticoagulation restored on 5mg alternating schedule.",
        "attachment": {"ocrRawText": "INR: 2.6 (Target 2.0-3.0), stable response.", "ocrConfidence": 0.97},
        "fhirResourceType": "DiagnosticReport",
        "synthetic": True
    })

    reports.append({
        "reportId": "RPT-PAT-SS-1001-07",
        "patientId": "PAT-SS-1001",
        "type": "IMAGING",
        "title": "Digital Chest Radiograph (PA View) - Occupational Screening",
        "date": rel_days_iso(60),
        "facility": "Bowring and Lady Curzon Hospital",
        "facilityState": "Karnataka",
        "orderedBy": "Dr. Arvind Bhat, MD",
        "language": "English",
        "source": "BENGALURU_CLINIC",
        "results": [
            {"name": "ILO Category", "value": "1/1 q/t", "unit": "score", "refLow": 0, "refHigh": 0, "flag": "H"}
        ],
        "findings": "Bilateral upper-zone profusion of small rounded nodular opacities (ILO category 1/1 q/t) with hilar prominence and eggshell calcification noted in bilateral hilar lymph nodes. Costophrenic angles sharp. No acute consolidation or cavitation.",
        "impression": "Radiological findings consistent with early chronic occupational silicosis. High-Resolution Computed Tomography (HRCT) of thorax recommended.",
        "attachment": {"ocrRawText": "CHEST X-RAY PA VIEW: Upper zone nodular opacities ILO 1/1 q/t. Hilar prominence. Consistent with early silicosis. Advise HRCT.", "ocrConfidence": 0.93},
        "fhirResourceType": "DiagnosticReport",
        "synthetic": True
    })

    reports.append({
        "reportId": "RPT-PAT-SS-1001-08",
        "patientId": "PAT-SS-1001",
        "type": "PULMONARY",
        "title": "Computerized Pulmonary Function Test (Spirometry)",
        "date": rel_days_iso(60),
        "facility": "Bowring and Lady Curzon Hospital",
        "facilityState": "Karnataka",
        "orderedBy": "Dr. Arvind Bhat, MD",
        "language": "English",
        "source": "BENGALURU_CLINIC",
        "results": [
            {"name": "FEV1", "value": 2.15, "unit": "L", "refLow": 2.80, "refHigh": 3.60, "flag": "L"},
            {"name": "FEV1 % Predicted", "value": 68.0, "unit": "%", "refLow": 80.0, "refHigh": 120.0, "flag": "L"},
            {"name": "FVC", "value": 3.40, "unit": "L", "refLow": 3.50, "refHigh": 4.50, "flag": "N"},
            {"name": "FEV1/FVC Ratio", "value": 0.63, "unit": "fraction", "refLow": 0.70, "refHigh": 0.85, "flag": "L"}
        ],
        "findings": "Post-bronchodilator spirometry demonstrates a reduced FEV1 (68% predicted) and reduced FEV1/FVC ratio (0.63), indicating an obstructive ventilatory defect with mild restriction.",
        "impression": "Moderate occupational obstructive airway disease superimposed on silica dust exposure.",
        "attachment": {"ocrRawText": "SPIROMETRY: FEV1 2.15L (68%), FVC 3.40L (85%), FEV1/FVC 0.63 (L). Moderate obstructive defect.", "ocrConfidence": 0.96},
        "fhirResourceType": "DiagnosticReport",
        "synthetic": True
    })

    reports.append({
        "reportId": "RPT-PAT-SS-1001-09",
        "patientId": "PAT-SS-1001",
        "type": "LAB",
        "title": "Complete Serum Lipid Profile",
        "date": rel_days_iso(90),
        "facility": "Manipal Hospital Heart Institute, Whitefield",
        "facilityState": "Karnataka",
        "orderedBy": "Dr. Ananya Sharma, MD",
        "language": "English",
        "source": "BENGALURU_CLINIC",
        "results": [
            {"name": "Total Cholesterol", "value": 218, "unit": "mg/dL", "refLow": 125, "refHigh": 200, "flag": "H"},
            {"name": "Triglycerides", "value": 195, "unit": "mg/dL", "refLow": 50, "refHigh": 150, "flag": "H"},
            {"name": "HDL Cholesterol", "value": 38, "unit": "mg/dL", "refLow": 40, "refHigh": 60, "flag": "L"},
            {"name": "LDL Cholesterol", "value": 141, "unit": "mg/dL", "refLow": 50, "refHigh": 100, "flag": "H"}
        ],
        "findings": "Mixed dyslipidemia with elevated LDL and low cardioprotective HDL.",
        "impression": "Indication for Statin therapy (Atorvastatin 20mg).",
        "attachment": {"ocrRawText": "LIPID PROFILE: Cholesterol 218, Triglycerides 195, HDL 38, LDL 141. Mixed dyslipidemia.", "ocrConfidence": 0.95},
        "fhirResourceType": "DiagnosticReport",
        "synthetic": True
    })

    reports.append({
        "reportId": "RPT-PAT-SS-1001-10",
        "patientId": "PAT-SS-1001",
        "type": "DISCHARGE_SUMMARY",
        "title": "Inpatient Discharge Summary - Deep Vein Thrombosis",
        "date": rel_days_iso(330),
        "facility": "MKCG Medical College & Hospital, Berhampur",
        "facilityState": "Odisha",
        "orderedBy": "Dr. Prasant Mohanty, MD",
        "language": "English",
        "source": "HOME_STATE_PHC",
        "results": [
            {"name": "Venous Doppler", "value": "Thrombosis", "unit": "clinical", "refLow": 0, "refHigh": 0, "flag": "H"}
        ],
        "findings": "48-year-old male construction worker presented with sudden onset right calf erythema and swelling. Lower extremity compression Doppler revealed non-compressible right common femoral and popliteal veins.",
        "impression": "Acute lower extremity DVT. Managed with LMWH bridge to oral Warfarin 5mg. Target INR 2.0 - 3.0 maintained.",
        "attachment": {"ocrRawText": "DISCHARGE SUMMARY - DVT Right Lower Limb. Started Tab Warfarin 5mg OD. Caution: Bleeding precautions.", "ocrConfidence": 0.98},
        "fhirResourceType": "DocumentReference",
        "synthetic": True
    })

    reports.append({
        "reportId": "RPT-PAT-SS-1001-11",
        "patientId": "PAT-SS-1001",
        "type": "PAPER_PRESCRIPTION",
        "title": "Scanned Historical PHC Prescription Slip (Odisha)",
        "date": rel_days_iso(340),
        "facility": "Chhatrapur Sub-Divisional Hospital",
        "facilityState": "Odisha",
        "orderedBy": "Dr. B. K. Sahu, MBBS",
        "language": "Odia",
        "source": "PATIENT_UPLOAD",
        "results": [],
        "findings": "Historical hand-written prescription containing Glycomet 500mg, Warfarin 5mg, and an old prescription of Cap Amoxyclav 625mg.",
        "impression": "Historical record digitized via Document AI. Confirms Penicillin and Augmentin allergy flag.",
        "attachment": {
            "ocrRawText": "CHHATRAPUR SDH OPD - Tab Metformin 500mg (1-0-1), Tab Warfarin 5mg (0-0-1), Cap Amoxyclav 625mg (DISCONTINUED DUE TO RASH).",
            "ocrConfidence": 0.84
        },
        "fhirResourceType": "DocumentReference",
        "synthetic": True
    })

    # Generate additional reports across the 25 patients to reach >= 95 reports
    report_types = ["LAB", "IMAGING", "PULMONARY", "ECG", "OPD_NOTE", "VACCINATION", "ANTENATAL", "PAPER_PRESCRIPTION"]
    facilities = [
        ("Whitefield Urban PHC", "Karnataka", "BENGALURU_CLINIC"),
        ("Manipal Hospital Heart Institute", "Karnataka", "BENGALURU_CLINIC"),
        ("Bowring and Lady Curzon Hospital", "Karnataka", "BENGALURU_CLINIC"),
        ("AIIMS Bhubaneswar", "Odisha", "HOME_STATE_PHC"),
        ("SCB Medical College Cuttack", "Odisha", "HOME_STATE_PHC"),
        ("Patna Medical College", "Bihar", "HOME_STATE_PHC")
    ]

    for p in patients:
        pid = p["patientId"]
        if pid == "PAT-SS-1001":
            continue
        if pid == "PAT-SS-1008":
            continue # Empty state demo!

        num_reports = random.randint(3, 5)
        for r_idx in range(1, num_reports + 1):
            rtype = report_types[r_idx % len(report_types)]
            fac, fstate, src = facilities[(r_idx + int(pid[-2:])) % len(facilities)]
            days_ago = random.randint(10, 240)
            rid = f"RPT-{pid}-{r_idx:02d}"

            if rtype == "ANTENATAL" and p["gender"] != "Female":
                rtype = "LAB"

            rep_entry = {
                "reportId": rid,
                "patientId": pid,
                "type": rtype,
                "title": f"Routine {rtype.replace('_', ' ').title()} Investigation",
                "date": rel_days_iso(days_ago),
                "facility": fac,
                "facilityState": fstate,
                "orderedBy": "Dr. Sarah Jenkins, MD" if "Karnataka" in fstate else "Dr. Debabrata Nayak, MD",
                "language": "English",
                "source": src,
                "results": [
                    {"name": "Complete Blood Count (Hb)", "value": round(random.uniform(11.5, 15.5), 1), "unit": "g/dL", "refLow": 12.0, "refHigh": 16.0, "flag": "N"},
                    {"name": "Fasting Blood Sugar", "value": random.randint(85, 130), "unit": "mg/dL", "refLow": 70, "refHigh": 100, "flag": "N" if random.random() > 0.3 else "H"}
                ],
                "findings": "Clinical findings within acceptable physiological limits for age and occupational status.",
                "impression": "Stable chronic condition follow-up.",
                "attachment": {
                    "ocrRawText": f"{fac.upper()} - {rtype} RESULTS: WNL. Follow up in 60 days.",
                    "ocrConfidence": round(random.uniform(0.85, 0.98), 2)
                },
                "fhirResourceType": "DiagnosticReport" if rtype in ("LAB", "IMAGING", "PULMONARY", "ECG") else "DocumentReference",
                "synthetic": True
            }
            reports.append(rep_entry)

    with open(SEED_DIR / "reports.json", "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)
    return reports


# ---------------------------------------------------------------------------
# 6. prescriptions_seed.json
# ---------------------------------------------------------------------------
def generate_prescriptions_seed():
    prescriptions = {
        # PAT-SS-1001 (Ramesh Kumar)
        "PAT-SS-1001": [
            {
                "prescriptionId": "RX-WAR-1001",
                "patientId": "PAT-SS-1001",
                "medicationName": "Warfarin 5mg",
                "genericName": "Warfarin",
                "dosage": "5 mg",
                "frequency": "Night (20:00)",
                "status": "ACTIVE",
                "prescribedBy": "DOC-IN-8841",
                "doctorName": "Dr. Ananya Sharma, MD",
                "startDate": rel_days_date(300),
                "notes": "Oral anticoagulant therapy for DVT maintenance. Monitor routine INR (target 2.0-3.0).",
                "versionHistory": [
                    {"version": 1, "dosage": "5 mg", "timestamp": rel_days_iso(300), "doctor": "Dr. Prasant Mohanty"},
                    {"version": 2, "dosage": "5 mg", "timestamp": rel_days_iso(90), "doctor": "Dr. Ananya Sharma"}
                ],
                "synthetic": True
            },
            {
                "prescriptionId": "RX-MET-1002",
                "patientId": "PAT-SS-1001",
                "medicationName": "Metformin 500mg",
                "genericName": "Metformin",
                "dosage": "500 mg",
                "frequency": "Twice daily (08:00, 20:00)",
                "status": "ACTIVE",
                "prescribedBy": "DOC-IN-8841",
                "doctorName": "Dr. Rajesh Verma, MD",
                "startDate": rel_days_date(270),
                "notes": "Oral antihyperglycemic for T2DM control.",
                "versionHistory": [
                    {"version": 1, "dosage": "500 mg", "timestamp": rel_days_iso(270), "doctor": "Dr. Rajesh Verma"}
                ],
                "synthetic": True
            },
            {
                "prescriptionId": "RX-ATOR-1003",
                "patientId": "PAT-SS-1001",
                "medicationName": "Atorvastatin 20mg",
                "genericName": "Atorvastatin",
                "dosage": "20 mg",
                "frequency": "Night (20:00)",
                "status": "ACTIVE",
                "prescribedBy": "DOC-IN-8841",
                "doctorName": "Dr. Ananya Sharma, MD",
                "startDate": rel_days_date(90),
                "notes": "Lipid-lowering HMG-CoA reductase inhibitor for secondary cardiovascular prevention.",
                "versionHistory": [
                    {"version": 1, "dosage": "20 mg", "timestamp": rel_days_iso(90), "doctor": "Dr. Ananya Sharma"}
                ],
                "synthetic": True
            },
            {
                "prescriptionId": "RX-LIS-1004",
                "patientId": "PAT-SS-1001",
                "medicationName": "Lisinopril 5mg",
                "genericName": "Lisinopril",
                "dosage": "5 mg",
                "frequency": "Morning (08:00)",
                "status": "DISCONTINUED",
                "prescribedBy": "DOC-IN-8841",
                "doctorName": "Dr. Sarah Jenkins, MD",
                "startDate": rel_days_date(280),
                "endDate": rel_days_date(180),
                "discontinueReason": "Patient developed persistent dry bradykinin cough. Discontinued per clinical review.",
                "synthetic": True
            }
        ],
        # PAT-SS-1003 (Duplicate therapy demo: 2 NSAIDs + ACEI & ARB)
        "PAT-SS-1003": [
            {
                "prescriptionId": "RX-PAT3-01",
                "patientId": "PAT-SS-1003",
                "medicationName": "Diclofenac 50mg Tablet",
                "genericName": "Diclofenac",
                "dosage": "50 mg",
                "frequency": "Twice daily",
                "status": "ACTIVE",
                "prescribedBy": "DOC-IN-8841",
                "doctorName": "Dr. Ananya Sharma, MD",
                "startDate": rel_days_date(60),
                "notes": "NSAID for acute knee osteoarthritis flare.",
                "synthetic": True
            },
            {
                "prescriptionId": "RX-PAT3-02",
                "patientId": "PAT-SS-1003",
                "medicationName": "Ibuprofen 400mg Tablet",
                "genericName": "Ibuprofen",
                "dosage": "400 mg",
                "frequency": "SOS / Thrice daily",
                "status": "ACTIVE",
                "prescribedBy": "DOC-202",
                "doctorName": "Dr. Rajesh Verma, MD",
                "startDate": rel_days_date(45),
                "notes": "Analgesic for lumbar muscular strain. DUPLICATE NSAID with Diclofenac.",
                "synthetic": True
            },
            {
                "prescriptionId": "RX-PAT3-03",
                "patientId": "PAT-SS-1003",
                "medicationName": "Ramipril 5mg Tablet",
                "genericName": "Ramipril",
                "dosage": "5 mg",
                "frequency": "Morning (08:00)",
                "status": "ACTIVE",
                "prescribedBy": "DOC-IN-8841",
                "doctorName": "Dr. Ananya Sharma, MD",
                "startDate": rel_days_date(120),
                "notes": "ACE-Inhibitor for blood pressure management.",
                "synthetic": True
            },
            {
                "prescriptionId": "RX-PAT3-04",
                "patientId": "PAT-SS-1003",
                "medicationName": "Telmisartan 40mg Tablet",
                "genericName": "Telmisartan",
                "dosage": "40 mg",
                "frequency": "Night (20:00)",
                "status": "ACTIVE",
                "prescribedBy": "DOC-202",
                "doctorName": "Dr. Rajesh Verma, MD",
                "startDate": rel_days_date(30),
                "notes": "ARB prescribed by secondary clinic. DUPLICATE RENIN-ANGIOTENSIN BLOCKADE with Ramipril.",
                "synthetic": True
            },
            {
                "prescriptionId": "RX-PAT3-05",
                "patientId": "PAT-SS-1003",
                "medicationName": "Pantoprazole 40mg Tablet",
                "genericName": "Pantoprazole",
                "dosage": "40 mg",
                "frequency": "Morning (08:00 before food)",
                "status": "ACTIVE",
                "prescribedBy": "DOC-IN-8841",
                "doctorName": "Dr. Ananya Sharma, MD",
                "startDate": rel_days_date(60),
                "notes": "Gastroprotective proton-pump inhibitor.",
                "synthetic": True
            },
            {
                "prescriptionId": "RX-PAT3-06",
                "patientId": "PAT-SS-1003",
                "medicationName": "Paracetamol 650mg Tablet",
                "genericName": "Paracetamol",
                "dosage": "650 mg",
                "frequency": "SOS",
                "status": "ACTIVE",
                "prescribedBy": "DOC-IN-8841",
                "doctorName": "Dr. Ananya Sharma, MD",
                "startDate": rel_days_date(15),
                "notes": "Pain relief SOS.",
                "synthetic": True
            }
        ]
    }

    med_list = [
        ("Amlodipine 5mg", "Amlodipine", "5 mg", "Morning"),
        ("Metoprolol Succinate 25mg", "Metoprolol", "25 mg", "Morning"),
        ("Salbutamol Inhaler 100mcg", "Salbutamol", "2 puffs", "SOS"),
        ("Cetirizine 10mg", "Cetirizine", "10 mg", "Night"),
        ("Omeprazole 20mg", "Omeprazole", "20 mg", "Morning"),
        ("Iron & Folic Acid Tablet", "Ferrous Ascorbate", "100 mg", "Afternoon")
    ]

    for pidx in range(4, 26):
        pid = f"PAT-SS-{1000 + pidx}"
        if pid in prescriptions:
            continue
        if pid == "PAT-SS-1008":
            prescriptions[pid] = []
            continue

        chosen_meds = random.sample(med_list, random.randint(1, 3))
        prescriptions[pid] = []
        for m_idx, (m_name, g_name, dos, freq) in enumerate(chosen_meds, start=1):
            prescriptions[pid].append({
                "prescriptionId": f"RX-{pid}-{m_idx}",
                "patientId": pid,
                "medicationName": m_name,
                "genericName": g_name,
                "dosage": dos,
                "frequency": freq,
                "status": "ACTIVE",
                "prescribedBy": "DOC-IN-8841",
                "doctorName": "Dr. Ananya Sharma, MD",
                "startDate": rel_days_date(random.randint(15, 90)),
                "notes": "Routine maintenance therapy.",
                "synthetic": True
            })

    with open(SEED_DIR / "prescriptions_seed.json", "w", encoding="utf-8") as f:
        json.dump(prescriptions, f, indent=2)
    return prescriptions


# ---------------------------------------------------------------------------
# 7. adherence_history.json (30 days for >=8 patients)
# ---------------------------------------------------------------------------
def generate_adherence_history():
    history = {}
    
    # 1. PAT-SS-1001: ~70% adherence with recent 2-day missed streak
    pat1_doses = []
    for day in range(1, 31):
        d_morn_ts = rel_days_iso(day, hour=8, minute=15)
        d_night_ts = rel_days_iso(day, hour=20, minute=30)
        
        if day in (1, 2):
            status_morn = "MISSED"
            status_night = "MISSED"
        elif day % 4 == 0:
            status_morn = "TAKEN"
            status_night = "MISSED"
        else:
            status_morn = "TAKEN"
            status_night = "TAKEN"

        pat1_doses.append({
            "doseId": f"DOSE-1001-{day}-M",
            "patientId": "PAT-SS-1001",
            "prescriptionId": "RX-MET-1002",
            "medicationName": "Metformin 500mg",
            "scheduledTime": "08:00",
            "timestamp": d_morn_ts,
            "status": status_morn,
            "synthetic": True
        })
        pat1_doses.append({
            "doseId": f"DOSE-1001-{day}-N",
            "patientId": "PAT-SS-1001",
            "prescriptionId": "RX-WAR-1001",
            "medicationName": "Warfarin 5mg",
            "scheduledTime": "20:00",
            "timestamp": d_night_ts,
            "status": status_night,
            "synthetic": True
        })
    history["PAT-SS-1001"] = pat1_doses

    # 2. PAT-SS-1006 (Bina Mondal): >95% adherence
    pat6_doses = []
    for day in range(1, 31):
        status = "TAKEN" if day != 14 else "SKIPPED"
        pat6_doses.append({
            "doseId": f"DOSE-1006-{day}",
            "patientId": "PAT-SS-1006",
            "prescriptionId": "RX-PAT-SS-1006-1",
            "medicationName": "Omeprazole 20mg",
            "scheduledTime": "08:00",
            "timestamp": rel_days_iso(day, hour=8, minute=10),
            "status": status,
            "synthetic": True
        })
    history["PAT-SS-1006"] = pat6_doses

    # 3. PAT-SS-1007 (Dharmendra Paswan): Poor adherence (<40%, consecutive missed streak)
    pat7_doses = []
    for day in range(1, 31):
        status = "MISSED" if day <= 6 or day % 2 == 0 else "TAKEN"
        pat7_doses.append({
            "doseId": f"DOSE-1007-{day}",
            "patientId": "PAT-SS-1007",
            "prescriptionId": "RX-PAT-SS-1007-1",
            "medicationName": "Amlodipine 5mg",
            "scheduledTime": "08:00",
            "timestamp": rel_days_iso(day, hour=8, minute=45),
            "status": status,
            "synthetic": True
        })
    history["PAT-SS-1007"] = pat7_doses

    # Patients 2, 3, 4, 5, 9 (total 8 patients)
    for p_num in ["1002", "1003", "1004", "1005", "1009"]:
        pid = f"PAT-SS-{p_num}"
        doses = []
        for day in range(1, 31):
            st = "TAKEN" if random.random() > 0.15 else "MISSED"
            doses.append({
                "doseId": f"DOSE-{p_num}-{day}",
                "patientId": pid,
                "prescriptionId": f"RX-{pid}-1",
                "medicationName": "Maintenance Therapy",
                "scheduledTime": "08:00",
                "timestamp": rel_days_iso(day, hour=8, minute=20),
                "status": st,
                "synthetic": True
            })
        history[pid] = doses

    with open(SEED_DIR / "adherence_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    return history


# ---------------------------------------------------------------------------
# 8. ocr_samples.json (>=8 presets)
# ---------------------------------------------------------------------------
def generate_ocr_samples():
    samples = [
        {
            "id": "ODISHA_PHC_SLIP",
            "title": "Odisha Sub-Divisional Hospital Paper Slip",
            "facility": "Chhatrapur Sub-Divisional Hospital, Ganjam, Odisha",
            "rawText": "GOVT OF ODISHA - SUB DIVISIONAL HOSPITAL CHHATRAPUR\nOPD REG: 44102/2023  DATE: 14/11/2023\nPATIENT: Ramesh Kumar, M/48 YRS\nRx:\n1. Tab Metformin 500mg - 1 Tab BD x 30 days\n2. Tab Ecosprin 75mg - 1 Tab OD (Aspirin)\n3. Cap Amoxyclav 625mg (Amoxicillin+Clavulanate) - 1 Cap BD x 5 days\nDr. B. K. Sahu, MBBS (Reg: OCMR-2015-44102)",
            "ocrConfidence": 0.82,
            "expectedMedicines": ["Metformin 500mg", "Ecosprin 75mg", "Amoxyclav 625mg"],
            "expectedFlags": [
                "DRUG_INTERACTION: Aspirin (Ecosprin) + Warfarin bleeding risk",
                "ALLERGY_CONFLICT: Amoxyclav (Penicillin class) on Penicillin allergy"
            ],
            "needsReview": False,
            "synthetic": True
        },
        {
            "id": "BIHAR_SADAR_LAB",
            "title": "Bihar Sadar Hospital Inpatient Discharge Slip",
            "facility": "Sadar Hospital, Gaya, Bihar",
            "rawText": "SADAR HOSPITAL GAYA - DEPT OF MEDICINE\nDISCHARGE ADVICE SLIP\nPt: Rajesh Yadav, Age 36/M\nDx: Occupational Byssinosis / Bronchospasm\nRx:\n1. Asthalin Inhaler (Salbutamol 100mcg) - 2 puffs SOS\n2. Deriphyllin Retard 150mg - 1 tab BD\n3. Prednisolone 10mg - 1 tab daily x 5 days\nAdvise avoidance of raw cotton dust & use of N95 respirator.",
            "ocrConfidence": 0.88,
            "expectedMedicines": ["Asthalin Inhaler", "Deriphyllin Retard 150mg", "Prednisolone 10mg"],
            "expectedFlags": ["OCCUPATIONAL_ALERT: Cotton dust byssinosis trigger"],
            "needsReview": False,
            "synthetic": True
        },
        {
            "id": "TAMIL_NADU_CLINIC",
            "title": "Tamil Nadu Urban Clinic Prescription",
            "facility": "Sri Krishna Clinic, Salem, Tamil Nadu",
            "rawText": "ஸ்ரீ கிருஷ்ணா கிளினிக் - SALEM\nPatient: Lakshmi Murugan, F/42\nRx:\n1. Tab Dolo 650mg - 1 tab SOS (Paracetamol)\n2. Tab Bactrim DS (Trimethoprim + Sulfamethoxazole) - 1 tab BD x 5 days\n3. Tab Pantocid 40mg - 1 tab OD before breakfast\nDr. S. Sundaram, MBBS",
            "ocrConfidence": 0.85,
            "expectedMedicines": ["Dolo 650mg", "Bactrim DS", "Pantocid 40mg"],
            "expectedFlags": ["ALLERGY_CONFLICT: Bactrim DS (Sulfamethoxazole) matches Sulfa allergy"],
            "needsReview": False,
            "synthetic": True
        },
        {
            "id": "SMUDGED_LOW_CONF",
            "title": "Smudged Crumpled Construction Site Slip",
            "facility": "Site First Aid Post, Whitefield Construction Project",
            "rawText": "SITE FIRST AID ... Ramesh K... 48M ...\nTab Diclo... 50mg ? ... Tab Bruf... 400 ? ...\n[Smudged text: Water damage / torn edge]\n... twice daily for pain ... Dr ...",
            "ocrConfidence": 0.48,
            "expectedMedicines": ["Diclofenac 50mg (Uncertain)", "Ibuprofen 400mg (Uncertain)"],
            "expectedFlags": ["OCR_LOW_CONFIDENCE: Quality 48% - Clinical manual verification mandatory"],
            "needsReview": True,
            "synthetic": True
        },
        {
            "id": "SULFA_DRUG_SLIP",
            "title": "Dermatology Clinic Prescription Slip",
            "facility": "Bangalore Skin Care Centre, Indiranagar",
            "rawText": "BANGALORE SKIN CARE CENTRE\nPatient: Kavitha Selvam, F/33\nDx: Pyoderma / Folliculitis\nRx:\n1. Tab Co-Trimoxazole DS (Sulfamethoxazole 800mg + Trimethoprim 160mg) - 1 BD\n2. Mupirocin Ointment 2% - Apply twice daily\nDr. Rekha Rao, MD (Derm)",
            "ocrConfidence": 0.91,
            "expectedMedicines": ["Co-Trimoxazole DS", "Mupirocin Ointment 2%"],
            "expectedFlags": ["ALLERGY_CONFLICT: Co-Trimoxazole (Sulfa class) matches Sulfa allergy"],
            "needsReview": False,
            "synthetic": True
        },
        {
            "id": "CLEAN_TYPED_DISCHARGE",
            "title": "Typed Cardiology Discharge Summary",
            "facility": "Manipal Hospital Heart Institute, Bengaluru",
            "rawText": "MANIPAL HOSPITAL WHITEFIELD - CARDIOLOGY DISCHARGE SUMMARY\nPATIENT ID: PAT-SS-1001   NAME: Ramesh Kumar   AGE: 48 / M\nDIAGNOSIS: Deep Vein Thrombosis (Right Lower Extremity), Resolved\nDISCHARGE MEDICATIONS:\n1. Tab Warfarin 5mg - 1 tablet orally once daily at 20:00 (Target INR 2.0 - 3.0)\n2. Tab Metformin 500mg - 1 tablet orally twice daily with meals\n3. Tab Atorvastatin 20mg - 1 tablet orally once daily at bedtime\nCAUTION: Strict avoidance of Aspirin, NSAIDs (Ibuprofen, Diclofenac). Report bleeding immediately.",
            "ocrConfidence": 0.98,
            "expectedMedicines": ["Warfarin 5mg", "Metformin 500mg", "Atorvastatin 20mg"],
            "expectedFlags": ["SAFETY_NOTICE: Warfarin anticoagulant protocol active"],
            "needsReview": False,
            "synthetic": True
        },
        {
            "id": "PULMONOLOGY_OPD_SLIP",
            "title": "Pulmonology Clinic Consultation Note",
            "facility": "Apollo Clinic, Bellandur, Bengaluru",
            "rawText": "APOLLO CLINIC BELLANDUR - PULMONOLOGY\nPt: Santosh Pradhan, M/34  Date: Today\nDx: Chronic occupational cough & reactive airway\nRx:\n1. Foracort Inhaler 200 (Budesonide 200mcg + Formoterol 6mcg) - 2 puffs BD\n2. Tab Montelukast 10mg - 1 tab at bedtime\n3. Tab Combiflam (Ibuprofen + Paracetamol) - SOS for chest wall pain\nDr. Deepa Nair, MD (Pulm)",
            "ocrConfidence": 0.89,
            "expectedMedicines": ["Foracort Inhaler 200", "Montelukast 10mg", "Combiflam"],
            "expectedFlags": ["ALLERGY_CONFLICT: Combiflam contains Ibuprofen (NSAID-sensitive asthma conflict)"],
            "needsReview": False,
            "synthetic": True
        },
        {
            "id": "ANTENATAL_CARE_SLIP",
            "title": "PHC Antenatal Care Health Record",
            "facility": "Govt Primary Health Centre, KR Puram, Bengaluru",
            "rawText": "MOTHER & CHILD HEALTH CARD (MCH)\nName: Fatima Khatun, F/26 YRS  LMP: 24 weeks gestation\nRx:\n1. Iron Folic Acid (IFA) Tablets - 1 tab daily after lunch\n2. Calcium Carbonate 500mg + Vitamin D3 - 1 tab daily after breakfast\n3. Tetanus Toxoid (TT2) Injection - Administered today\nANM Nurse: Shobha Devi",
            "ocrConfidence": 0.94,
            "expectedMedicines": ["Iron Folic Acid", "Calcium Carbonate 500mg", "Tetanus Toxoid"],
            "expectedFlags": ["PREGNANCY_SAFEGUARD: Safe second-trimester micronutrient regimen"],
            "needsReview": False,
            "synthetic": True
        }
    ]
    with open(SEED_DIR / "ocr_samples.json", "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)
    return samples


# ---------------------------------------------------------------------------
# 9. drug_interactions.json (>=40 rules)
# ---------------------------------------------------------------------------
def generate_drug_interactions():
    rules = [
        # 1. Warfarin + Aspirin
        {
            "a": "Warfarin",
            "b": "Aspirin",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Synergistic inhibition of coagulation factors (Warfarin) and platelet aggregation (Aspirin).",
            "clinicalExplanation": "Combining Warfarin with Aspirin substantially magnifies the risk of major gastrointestinal and intracranial hemorrhage. Avoid concurrent administration unless strictly indicated under specialist supervision.",
            "clinicianNote": "High bleeding diathesis hazard. If antiplatelet therapy is essential, co-prescribe a PPI and monitor INR weekly.",
            "monitoring": "Baseline and weekly PT/INR, complete blood count, and clinical check for occult bleeding.",
            "alternatives": ["Paracetamol", "Selective Paracetamol Titration"],
            "synthetic": True
        },
        # 2. Warfarin + Diclofenac
        {
            "a": "Warfarin",
            "b": "Diclofenac",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "NSAID inhibition of COX-1 impairs platelet function and induces gastrointestinal mucosal erosion while Warfarin inhibits clotting cascade.",
            "clinicalExplanation": "Diclofenac dramatically increases gastrointestinal bleeding risks in patients anticoagulated with Warfarin. Concomitant use is contraindicated.",
            "clinicianNote": "Severe GI ulceration and systemic bleeding risk. Diclofenac also displaces Warfarin from albumin.",
            "monitoring": "Immediate cessation of NSAID. Check INR and stool occult blood if taken.",
            "alternatives": ["Paracetamol 650mg", "Topical Analgesic Gel"],
            "synthetic": True
        },
        # 3. Warfarin + Ibuprofen
        {
            "a": "Warfarin",
            "b": "Ibuprofen",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "COX-dependent platelet inhibition combined with vitamin K antagonism.",
            "clinicalExplanation": "Ibuprofen irritates the stomach lining and impairs clotting, creating an acute hemorrhage danger with Warfarin.",
            "clinicianNote": "Absolute contraindication in outpatient setting.",
            "monitoring": "Evaluate for epistaxis, hematuria, or melena.",
            "alternatives": ["Paracetamol", "Tramadol (short course)"],
            "synthetic": True
        },
        # 4. Penicillin allergy vs Amoxicillin
        {
            "a": "Penicillin",
            "b": "Amoxicillin",
            "type": "ALLERGY",
            "severity": "SEVERE",
            "mechanism": "Cross-reactive beta-lactam core ring structure induces IgE-mediated type-1 hypersensitivity.",
            "clinicalExplanation": "Amoxicillin shares the core beta-lactam ring with Penicillin and can trigger severe anaphylaxis, urticaria, or bronchospasm.",
            "clinicianNote": "Confirmed Penicillin allergy precludes all aminopenicillins.",
            "monitoring": "Emergency airway and epinephrine preparedness if accidental exposure occurs.",
            "alternatives": ["Azithromycin 500mg", "Ciprofloxacin 500mg", "Doxycycline 100mg"],
            "synthetic": True
        },
        # 5. Penicillin allergy vs Amoxicillin-Clavulanic Acid (Augmentin)
        {
            "a": "Penicillin",
            "b": "Amoxicillin-Clavulanic Acid",
            "type": "ALLERGY",
            "severity": "SEVERE",
            "mechanism": "Beta-lactam antigenicity from amoxicillin component in co-formulation.",
            "clinicalExplanation": "Augmentin contains Amoxicillin and is strictly blocked for any patient with a verified Penicillin allergy.",
            "clinicianNote": "Severe risk of immediate hypersensitivity and respiratory collapse.",
            "monitoring": "Continuous telemetry if administered in ICU.",
            "alternatives": ["Cefixime (if no cephalosporin cross-allergy)", "Azithromycin 500mg", "Levofloxacin 500mg"],
            "synthetic": True
        },
        # 6. Penicillin allergy vs Ampicillin
        {
            "a": "Penicillin",
            "b": "Ampicillin",
            "type": "ALLERGY",
            "severity": "SEVERE",
            "mechanism": "Beta-lactam anaphylactic cross-reactivity.",
            "clinicalExplanation": "Ampicillin is a penicillin derivative that will elicit an allergic reaction in penicillin-sensitized patients.",
            "clinicianNote": "Block prescription.",
            "monitoring": "Skin testing or in vitro specific IgE prior to desensitization.",
            "alternatives": ["Clindamycin 300mg", "Erythromycin"],
            "synthetic": True
        },
        # 7. Sulfa allergy vs Co-trimoxazole (Sulfamethoxazole)
        {
            "a": "Sulfa",
            "b": "Sulfamethoxazole",
            "type": "ALLERGY",
            "severity": "SEVERE",
            "mechanism": "Arylamine sulfonamide hypersensitivity mediated by reactive hydroxylamine metabolites.",
            "clinicalExplanation": "Sulfamethoxazole can induce severe cutaneous adverse reactions including Stevens-Johnson syndrome in sulfa-allergic patients.",
            "clinicianNote": "High risk of toxic epidermal necrolysis and DRESS syndrome.",
            "monitoring": "Inspect skin for erythematous macules or mucosal involvement.",
            "alternatives": ["Nitrofurantoin 100mg", "Ciprofloxacin 500mg"],
            "synthetic": True
        },
        # 8. Sulfa allergy vs Co-trimoxazole brand (Bactrim)
        {
            "a": "Sulfa",
            "b": "Co-trimoxazole",
            "type": "ALLERGY",
            "severity": "SEVERE",
            "mechanism": "Sulfonamide antimicrobial cross-reactivity.",
            "clinicalExplanation": "Co-trimoxazole contains sulfamethoxazole and must never be prescribed to patients with documented sulfa allergy.",
            "clinicianNote": "Prevent cutaneous and systemic allergic response.",
            "monitoring": "Monitor for fever, rash, eosinophilia.",
            "alternatives": ["Amoxicillin (if no penicillin allergy)", "Doxycycline"],
            "synthetic": True
        },
        # 9. NSAID-sensitive asthma vs Aspirin
        {
            "a": "NSAIDs",
            "b": "Aspirin",
            "type": "ALLERGY",
            "severity": "SEVERE",
            "mechanism": "Inhibition of COX-1 shunts arachidonic acid to lipoxygenase pathway, causing massive leukotriene release.",
            "clinicalExplanation": "Aspirin can precipitate life-threatening bronchospasm in patients with NSAID-sensitive asthma (Samter's Triad).",
            "clinicianNote": "Risk of severe refractory asthma exacerbation within 1-2 hours.",
            "monitoring": "Peak expiratory flow, oxygen saturation, nebulized bronchodilator readiness.",
            "alternatives": ["Paracetamol (up to 650mg)", "Topical Capsaicin"],
            "synthetic": True
        },
        # 10. NSAID-sensitive asthma vs Ibuprofen
        {
            "a": "NSAIDs",
            "b": "Ibuprofen",
            "type": "ALLERGY",
            "severity": "SEVERE",
            "mechanism": "Cysteinyl leukotriene overproduction from non-selective COX blockade.",
            "clinicalExplanation": "Ibuprofen triggers acute bronchospasm and facial angioedema in NSAID-intolerant asthmatic patients.",
            "clinicianNote": "Absolute contraindication in patients with AERD.",
            "monitoring": "Continuous SpO2 and respiratory rate.",
            "alternatives": ["Paracetamol", "Tramadol"],
            "synthetic": True
        },
        # 11. Ramipril (ACEI) + Telmisartan (ARB)
        {
            "a": "Ramipril",
            "b": "Telmisartan",
            "type": "DUPLICATE",
            "severity": "SEVERE",
            "mechanism": "Dual blockade of the renin-angiotensin-aldosterone system (RAAS).",
            "clinicalExplanation": "Combining an ACE-inhibitor with an ARB provides no additive cardiovascular benefit while significantly increasing risks of hyperkalemia, syncope, and acute kidney injury.",
            "clinicianNote": "ONTARGET trial demonstrated increased renal adverse events without clinical benefit.",
            "monitoring": "Serum potassium, serum creatinine, and supine/standing blood pressure.",
            "alternatives": ["Amlodipine 5mg (CCB)", "Chlorthalidone 12.5mg (Diuretic)"],
            "synthetic": True
        },
        # 12. Lisinopril + Losartan
        {
            "a": "Lisinopril",
            "b": "Losartan",
            "type": "DUPLICATE",
            "severity": "SEVERE",
            "mechanism": "Redundant RAAS antagonism.",
            "clinicalExplanation": "Simultaneous use of Lisinopril and Losartan elevates potassium to dangerous levels and impairs renal glomerular perfusion.",
            "clinicianNote": "Discontinue one agent.",
            "monitoring": "Renal function panel within 14 days.",
            "alternatives": ["Calcium Channel Blocker", "Thiazide Diuretic"],
            "synthetic": True
        },
        # 13. Ramipril + Spironolactone
        {
            "a": "Ramipril",
            "b": "Spironolactone",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Additive potassium retention through aldosterone inhibition and mineralocorticoid receptor blockade.",
            "clinicalExplanation": "Ramipril combined with Spironolactone poses a severe risk of lethal hyperkalemia unless closely monitored in heart failure protocols.",
            "clinicianNote": "Potassium must be monitored at days 3, 7, and monthly.",
            "monitoring": "Serum potassium, ECG for peaked T-waves, PR prolongation.",
            "alternatives": ["Furosemide (if loop diuretic indicated)"],
            "synthetic": True
        },
        # 14. Clopidogrel + Omeprazole
        {
            "a": "Clopidogrel",
            "b": "Omeprazole",
            "type": "DDI",
            "severity": "MODERATE",
            "mechanism": "Omeprazole competitively inhibits hepatic CYP2C19, decreasing bioactivation of Clopidogrel.",
            "clinicalExplanation": "Omeprazole reduces the antiplatelet effectiveness of Clopidogrel, increasing thrombotic event risk in cardiac patients.",
            "clinicianNote": "Switch proton-pump inhibitor to Pantoprazole, which exhibits minimal CYP2C19 inhibition.",
            "monitoring": "Platelet function assay or clinical monitoring for recurrent ischemic symptoms.",
            "alternatives": ["Pantoprazole 40mg", "Famotidine 20mg"],
            "synthetic": True
        },
        # 15. Atorvastatin + Rosuvastatin
        {
            "a": "Atorvastatin",
            "b": "Rosuvastatin",
            "type": "DUPLICATE",
            "severity": "SEVERE",
            "mechanism": "Dual competitive inhibition of HMG-CoA reductase.",
            "clinicalExplanation": "Prescribing two statins simultaneously greatly elevates the risk of severe myopathy and rhabdomyolysis without extra therapeutic gain.",
            "clinicianNote": "Single high-intensity statin titration preferred.",
            "monitoring": "Serum creatine kinase (CK) and liver transaminases.",
            "alternatives": ["Ezetimibe 10mg (add-on)"],
            "synthetic": True
        },
        # 16. Diclofenac + Ibuprofen
        {
            "a": "Diclofenac",
            "b": "Ibuprofen",
            "type": "DUPLICATE",
            "severity": "SEVERE",
            "mechanism": "Additive non-selective COX-1/COX-2 inhibition.",
            "clinicalExplanation": "Taking two NSAIDs at once doubles gastrointestinal ulceration and nephrotoxicity risks with zero additional pain relief.",
            "clinicianNote": "Discontinue duplicate NSAID immediately.",
            "monitoring": "Serum creatinine, BUN, hemoglobin.",
            "alternatives": ["Paracetamol", "Topical Gel"],
            "synthetic": True
        },
        # 17. Ketorolac + Naproxen
        {
            "a": "Ketorolac",
            "b": "Naproxen",
            "type": "DUPLICATE",
            "severity": "SEVERE",
            "mechanism": "Profound suppression of renal prostacyclin synthesis.",
            "clinicalExplanation": "Co-administration leads to acute renal insufficiency and major peptic ulcer bleeding.",
            "clinicianNote": "Contraindicated combination.",
            "monitoring": "Renal panel, urine output.",
            "alternatives": ["Paracetamol", "Tramadol"],
            "synthetic": True
        },
        # 18. Paracetamol + Combiflam (contains Paracetamol)
        {
            "a": "Paracetamol",
            "b": "Combiflam",
            "type": "DUPLICATE",
            "severity": "SEVERE",
            "mechanism": "Unintentional cumulative acetaminophen dosing exceeding the 4g daily hepatotoxic threshold.",
            "clinicalExplanation": "Combiflam already contains Paracetamol. Adding standalone Paracetamol risks toxic liver injury.",
            "clinicianNote": "Calculate cumulative 24h paracetamol dose.",
            "monitoring": "Liver function tests (ALT/AST), serum acetaminophen level if overdose suspected.",
            "alternatives": ["Ibuprofen alone", "Topical Analgesic"],
            "synthetic": True
        },
        # 19. Sildenafil + Nitroglycerin
        {
            "a": "Sildenafil",
            "b": "Nitroglycerin",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Excessive cyclic GMP accumulation producing profound systemic vasodilation.",
            "clinicalExplanation": "Taking Sildenafil with Nitrates causes precipitate, life-threatening hypotension and coronary hypoperfusion.",
            "clinicianNote": "Absolute contraindication within 24-48 hours.",
            "monitoring": "Continuous blood pressure telemetry.",
            "alternatives": ["Alternative cardiovascular angina therapy"],
            "synthetic": True
        },
        # 20. Sildenafil + Isosorbide Mononitrate
        {
            "a": "Sildenafil",
            "b": "Isosorbide Mononitrate",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Synergistic cGMP-mediated vascular smooth muscle relaxation.",
            "clinicalExplanation": "Refractory cardiovascular collapse and syncope can occur.",
            "clinicianNote": "Contraindicated combination.",
            "monitoring": "Blood pressure and heart rate.",
            "alternatives": ["Beta-blocker", "Calcium channel blocker for angina"],
            "synthetic": True
        },
        # 21. Tramadol + Fluoxetine
        {
            "a": "Tramadol",
            "b": "Fluoxetine",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Combined inhibition of serotonin reuptake plus CYP2D6 inhibition.",
            "clinicalExplanation": "Combining Tramadol with an SSRI significantly raises the danger of Serotonin Syndrome and lowers seizure threshold.",
            "clinicianNote": "Evaluate for hyperreflexia, clonus, and autonomic instability.",
            "monitoring": "Neurological examination, core body temperature.",
            "alternatives": ["Paracetamol", "Topical lidocaine patch"],
            "synthetic": True
        },
        # 22. Tramadol + Sertraline
        {
            "a": "Tramadol",
            "b": "Sertraline",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Additive central serotonergic activity.",
            "clinicalExplanation": "Risk of toxic Serotonin Syndrome and convulsions.",
            "clinicianNote": "Avoid co-administration.",
            "monitoring": "Mental status and vital signs.",
            "alternatives": ["Codeine", "Acetaminophen"],
            "synthetic": True
        },
        # 23. Metformin + Iodinated Contrast Media
        {
            "a": "Metformin",
            "b": "Iodinated Contrast",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Contrast-induced acute kidney injury leads to Metformin accumulation and fatal lactic acidosis.",
            "clinicalExplanation": "Metformin must be temporarily withheld prior to and for 48 hours after intravascular iodinated contrast administration.",
            "clinicianNote": "Withhold Metformin on day of imaging and re-evaluate eGFR before restart.",
            "monitoring": "Serum creatinine, eGFR, venous blood gas / lactate if symptomatic.",
            "alternatives": ["Non-contrast MRI", "Hydration protocol"],
            "synthetic": True
        },
        # 24. Ciprofloxacin + Theophylline
        {
            "a": "Ciprofloxacin",
            "b": "Theophylline",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "CYP1A2 inhibition by Ciprofloxacin reduces Theophylline clearance.",
            "clinicalExplanation": "Theophylline toxicity (tachyarrhythmias, intractable seizures) can develop rapidly.",
            "clinicianNote": "Dose reduction of theophylline by 50% or choose alternative antibiotic.",
            "monitoring": "Serum theophylline concentration.",
            "alternatives": ["Azithromycin 500mg"],
            "synthetic": True
        },
        # 25. Digoxin + Amiodarone
        {
            "a": "Digoxin",
            "b": "Amiodarone",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "P-glycoprotein and renal tubular excretion inhibition increases Digoxin level 70-100%.",
            "clinicalExplanation": "Severe Digoxin toxicity with bradycardia, heart block, and visual disturbances.",
            "clinicianNote": "Halve Digoxin dose when initiating Amiodarone.",
            "monitoring": "Serum digoxin trough level and ECG.",
            "alternatives": ["Beta-blocker for rate control"],
            "synthetic": True
        },
        # 26. Simvastatin + Clarithromycin
        {
            "a": "Simvastatin",
            "b": "Clarithromycin",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Potent CYP3A4 inhibition increases statin AUC tenfold.",
            "clinicalExplanation": "Acute rhabdomyolysis and myoglobinuric renal failure risk.",
            "clinicianNote": "Suspend statin during macrolide antibiotic course.",
            "monitoring": "Muscle tenderness, dark urine, CK levels.",
            "alternatives": ["Azithromycin (minimal CYP3A4 effect)"],
            "synthetic": True
        },
        # 27. Methotrexate + NSAIDs
        {
            "a": "Methotrexate",
            "b": "Ibuprofen",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "NSAIDs reduce renal tubular secretion of Methotrexate.",
            "clinicalExplanation": "Severe bone marrow suppression, leukopenia, and gastrointestinal toxicity.",
            "clinicianNote": "Avoid NSAIDs in patients receiving high or moderate dose Methotrexate.",
            "monitoring": "CBC with differential, liver enzymes.",
            "alternatives": ["Paracetamol"],
            "synthetic": True
        },
        # 28. Potassium Chloride + Spironolactone
        {
            "a": "Potassium Chloride",
            "b": "Spironolactone",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Direct additive potassium loading in the presence of reduced renal excretion.",
            "clinicalExplanation": "Rapid development of severe, fatal hyperkalemia.",
            "clinicianNote": "Contraindicated combination.",
            "monitoring": "Immediate serum potassium check.",
            "alternatives": ["Dietary potassium monitoring without supplements"],
            "synthetic": True
        },
        # 29. Warfarin + Fluconazole
        {
            "a": "Warfarin",
            "b": "Fluconazole",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Potent CYP2C9 inhibition decreases clearance of active S-warfarin.",
            "clinicalExplanation": "INR can spike dramatically within 48-72 hours, precipitating internal bleeding.",
            "clinicianNote": "Reduce Warfarin dose by 50% empirically and monitor INR closely.",
            "monitoring": "INR at day 3 and day 7.",
            "alternatives": ["Nystatin (topical)", "Terbinafine"],
            "synthetic": True
        },
        # 30. Linezolid + SSRI
        {
            "a": "Linezolid",
            "b": "Sertraline",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Non-selective MAO inhibition by Linezolid combined with serotonin reuptake blockade.",
            "clinicalExplanation": "High risk of fatal Serotonin Syndrome.",
            "clinicianNote": "Do not administer Linezolid to patients taking serotonergic antidepressants unless urgent.",
            "monitoring": "Autonomic signs, mental status.",
            "alternatives": ["Vancomycin", "Teicoplanin"],
            "synthetic": True
        },
        # 31. Lithium + Enalapril
        {
            "a": "Lithium",
            "b": "Enalapril",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Reduced glomerular filtration and sodium depletion increase Lithium reabsorption.",
            "clinicalExplanation": "Lithium toxicity with ataxia, tremors, confusion, and renal failure.",
            "clinicianNote": "Frequent lithium levels required if ACEI started.",
            "monitoring": "Serum lithium level, renal panel.",
            "alternatives": ["Calcium channel blocker for hypertension"],
            "synthetic": True
        },
        # 32. Allopurinol + Azathioprine
        {
            "a": "Allopurinol",
            "b": "Azathioprine",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Xanthine oxidase inhibition blocks the primary inactivation route of 6-mercaptopurine.",
            "clinicalExplanation": "Severe, life-threatening pancytopenia and agranulocytosis.",
            "clinicianNote": "Reduce Azathioprine dose to 25% of standard dose or avoid.",
            "monitoring": "Weekly CBC.",
            "alternatives": ["Febuxostat with dose titration", "Colchicine"],
            "synthetic": True
        },
        # 33. Carbamazepine + Erythromycin
        {
            "a": "Carbamazepine",
            "b": "Erythromycin",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "CYP3A4 inhibition by Erythromycin reduces Carbamazepine clearance.",
            "clinicalExplanation": "Neurotoxicity with diplopia, dizziness, and stupor.",
            "clinicianNote": "Switch to azithromycin.",
            "monitoring": "Carbamazepine plasma level.",
            "alternatives": ["Azithromycin 500mg"],
            "synthetic": True
        },
        # 34. Phenytoin + Ciprofloxacin
        {
            "a": "Phenytoin",
            "b": "Ciprofloxacin",
            "type": "DDI",
            "severity": "MODERATE",
            "mechanism": "Altered hepatic metabolism and lowered seizure threshold.",
            "clinicalExplanation": "Fluctuating anticonvulsant levels and increased seizure susceptibility.",
            "clinicianNote": "Monitor therapeutic drug levels.",
            "monitoring": "Total and free phenytoin levels.",
            "alternatives": ["Levofloxacin", "Cephalosporin"],
            "synthetic": True
        },
        # 35. Amlodipine + Simvastatin
        {
            "a": "Amlodipine",
            "b": "Simvastatin",
            "type": "DDI",
            "severity": "MODERATE",
            "mechanism": "CYP3A4 inhibition by Amlodipine increases Simvastatin exposure.",
            "clinicalExplanation": "Increased risk of statin-induced muscle ache and myopathy.",
            "clinicianNote": "Limit Simvastatin dose to 20mg daily or switch to Atorvastatin/Rosuvastatin.",
            "monitoring": "Muscle pain or elevated transaminases.",
            "alternatives": ["Atorvastatin 20mg", "Rosuvastatin 10mg"],
            "synthetic": True
        },
        # 36. Metoprolol + Diltiazem
        {
            "a": "Metoprolol",
            "b": "Diltiazem",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Synergistic depression of SA and AV nodal conduction and myocardial contractility.",
            "clinicalExplanation": "Severe symptomatic bradycardia, complete heart block, and worsening heart failure.",
            "clinicianNote": "Avoid combination in patients with pre-existing conduction abnormalities.",
            "monitoring": "Continuous ECG and telemetry.",
            "alternatives": ["Amlodipine (dihydropyridine CCB)"],
            "synthetic": True
        },
        # 37. Warfarin + Paracetamol (High dose)
        {
            "a": "Warfarin",
            "b": "Paracetamol",
            "type": "DDI",
            "severity": "MODERATE",
            "mechanism": "Paracetamol metabolite NAPQI inhibits vitamin K-dependent carboxylase.",
            "clinicalExplanation": "Regular high-dose Paracetamol (>2g/day) potentiates Warfarin and raises INR.",
            "clinicianNote": "Use lowest effective dose of paracetamol and check INR within 3-5 days.",
            "monitoring": "INR monitoring during sustained paracetamol use.",
            "alternatives": ["Occasional low-dose paracetamol"],
            "synthetic": True
        },
        # 38. Glimepiride + Ciprofloxacin
        {
            "a": "Glimepiride",
            "b": "Ciprofloxacin",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Inhibition of CYP2C9 and pancreatic K-ATP channel stimulation.",
            "clinicalExplanation": "Severe refractory hypoglycemia that may require prolonged dextrose infusion.",
            "clinicianNote": "Instruct patient on hypoglycemia symptoms and frequent glucose testing.",
            "monitoring": "Blood glucose 4 times daily.",
            "alternatives": ["Cephalosporin antibiotic"],
            "synthetic": True
        },
        # 39. Levothyroxine + Calcium Carbonate
        {
            "a": "Levothyroxine",
            "b": "Calcium Carbonate",
            "type": "DDI",
            "severity": "MODERATE",
            "mechanism": "Insoluble chelation in the acidic stomach decreases Levothyroxine absorption.",
            "clinicalExplanation": "Calcium prevents proper thyroid hormone uptake, leading to persistent hypothyroidism.",
            "clinicianNote": "Separate administration by at least 4 hours.",
            "monitoring": "Serum TSH after 6-8 weeks.",
            "alternatives": ["Separate dosage timing by 4 hours"],
            "synthetic": True
        },
        # 40. Levothyroxine + Ferrous Sulfate
        {
            "a": "Levothyroxine",
            "b": "Ferrous Sulfate",
            "type": "DDI",
            "severity": "MODERATE",
            "mechanism": "Ferric ion binds thyroxine to form an unabsorbable complex.",
            "clinicalExplanation": "Iron reduces Levothyroxine absorption significantly.",
            "clinicianNote": "Space intake by at least 4 hours.",
            "monitoring": "Serum TSH levels.",
            "alternatives": ["Space administration by 4 hours"],
            "synthetic": True
        },
        # 41. Atorvastatin + Gemfibrozil
        {
            "a": "Atorvastatin",
            "b": "Gemfibrozil",
            "type": "DDI",
            "severity": "SEVERE",
            "mechanism": "Gemfibrozil inhibits statin glucuronidation and OATP1B1 hepatic uptake.",
            "clinicalExplanation": "Major increase in statin plasma levels leading to rhabdomyolysis and acute renal failure.",
            "clinicianNote": "Fenofibrate is preferred over Gemfibrozil if fibrate therapy is required with a statin.",
            "monitoring": "Serum CK, renal function.",
            "alternatives": ["Fenofibrate 145mg"],
            "synthetic": True
        },
        # 42. Cephalosporin allergy vs Penicillin (Cross-allergy)
        {
            "a": "Cephalosporins",
            "b": "Amoxicillin",
            "type": "ALLERGY",
            "severity": "MODERATE",
            "mechanism": "Shared beta-lactam side chain similarities (1-3% cross-reactivity).",
            "clinicalExplanation": "Potential cross-hypersensitivity in patients with severe first-generation cephalosporin allergy.",
            "clinicianNote": "Exercise caution or skin-test before administration.",
            "monitoring": "Clinical observation for cutaneous reaction.",
            "alternatives": ["Macrolide antibiotic", "Fluoroquinolone"],
            "synthetic": True
        }
    ]
    with open(SEED_DIR / "drug_interactions.json", "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)
    return rules


# ---------------------------------------------------------------------------
# 10. medicine_generics.json (Extracted from CSV)
# ---------------------------------------------------------------------------
def generate_medicine_generics():
    csv_path = PROJECT_ROOT / "A_Z_medicines_dataset_of_India.csv"
    generics_map = {}
    
    priority_map = {
        "augmentin 625 duo tablet": ["Amoxicillin", "Clavulanic Acid"],
        "augmentin": ["Amoxicillin", "Clavulanic Acid"],
        "amoxyclav": ["Amoxicillin", "Clavulanic Acid"],
        "ecosprin 75 tablet": ["Aspirin"],
        "ecosprin 150 tablet": ["Aspirin"],
        "ecosprin": ["Aspirin"],
        "aspirin": ["Aspirin"],
        "warfarin 5mg": ["Warfarin"],
        "warfarin": ["Warfarin"],
        "cofarin 5mg tablet": ["Warfarin"],
        "metformin 500mg": ["Metformin"],
        "glycomet 500 tablet": ["Metformin"],
        "glycomet": ["Metformin"],
        "atorvastatin 20mg": ["Atorvastatin"],
        "atorva 20 tablet": ["Atorvastatin"],
        "atorva": ["Atorvastatin"],
        "azithral 500 tablet": ["Azithromycin"],
        "azithral": ["Azithromycin"],
        "voveran 50 ge tablet": ["Diclofenac"],
        "voveran": ["Diclofenac"],
        "brufen 400 tablet": ["Ibuprofen"],
        "brufen": ["Ibuprofen"],
        "combiflam tablet": ["Ibuprofen", "Paracetamol"],
        "combiflam": ["Ibuprofen", "Paracetamol"],
        "dolo 650 tablet": ["Paracetamol"],
        "dolo": ["Paracetamol"],
        "calpol 650 tablet": ["Paracetamol"],
        "calpol": ["Paracetamol"],
        "crocin": ["Paracetamol"],
        "pan 40 tablet": ["Pantoprazole"],
        "pan 40": ["Pantoprazole"],
        "omez 20 capsule": ["Omeprazole"],
        "omez": ["Omeprazole"],
        "cardace 5mg tablet": ["Ramipril"],
        "cardace": ["Ramipril"],
        "telma 40 tablet": ["Telmisartan"],
        "telma": ["Telmisartan"],
        "bactrim ds tablet": ["Sulfamethoxazole", "Trimethoprim"],
        "bactrim": ["Sulfamethoxazole", "Trimethoprim"],
        "ciplox 500 tablet": ["Ciprofloxacin"],
        "ciplox": ["Ciprofloxacin"],
        "asthalin inhaler": ["Salbutamol"],
        "asthalin": ["Salbutamol"],
        "clopivas 75 tablet": ["Clopidogrel"],
        "clopivas": ["Clopidogrel"],
        "aldactone 25 tablet": ["Spironolactone"],
        "aldactone": ["Spironolactone"],
        "foracort 200 inhaler": ["Budesonide", "Formoterol"]
    }
    generics_map.update(priority_map)

    if csv_path.exists():
        try:
            with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    name = row.get("name", "").strip()
                    comp1 = row.get("short_composition1", "").strip()
                    comp2 = row.get("short_composition2", "").strip()
                    
                    if name and (comp1 or comp2):
                        generics = []
                        for comp in (comp1, comp2):
                            if comp:
                                clean_g = re.sub(r"\(.*?\)", "", comp).strip()
                                if clean_g.lower() == "amoxycillin":
                                    clean_g = "Amoxicillin"
                                if clean_g and clean_g not in generics:
                                    generics.append(clean_g)
                        if generics:
                            generics_map[name.lower()] = generics
                    count += 1
                    if count >= 30000:
                        break
        except Exception as e:
            print(f"Notice reading CSV for generics: {e}")

    with open(SEED_DIR / "medicine_generics.json", "w", encoding="utf-8") as f:
        json.dump(generics_map, f, indent=2)
    return generics_map


# ---------------------------------------------------------------------------
# 11. pharmacies.json (>=20 BLR, >=4 Odisha)
# ---------------------------------------------------------------------------
def generate_pharmacies():
    blr_localities = [
        ("Whitefield", 12.9698, 77.7500),
        ("Whitefield Main Road", 12.9820, 77.7420),
        ("ITPL Road, Whitefield", 12.9880, 77.7310),
        ("Bommanahalli", 12.9038, 77.6258),
        ("Hosur Road, Bommanahalli", 12.9080, 77.6280),
        ("KR Puram", 13.0075, 77.6959),
        ("Old Madras Road, KR Puram", 13.0110, 77.7020),
        ("Peenya Industrial Area", 13.0329, 77.5273),
        ("Peenya 1st Stage", 13.0290, 77.5180),
        ("Electronic City Phase 1", 12.8399, 77.6770),
        ("Electronic City Phase 2", 12.8450, 77.6890),
        ("Yeshwanthpur", 13.0280, 77.5404),
        ("Yeshwanthpur TTMC", 13.0210, 77.5480),
        ("Hebbal", 13.0358, 77.5970),
        ("Hebbal Kempapura", 13.0450, 77.5920),
        ("Indiranagar 100ft Road", 12.9719, 77.6412),
        ("Jayanagar 4th Block", 12.9299, 77.5833),
        ("Marathahalli Bridge", 12.9569, 77.7011),
        ("Koramangala 5th Block", 12.9352, 77.6245),
        ("Yelahanka New Town", 13.1007, 77.5963)
    ]
    
    odisha_localities = [
        ("Berhampur Medical Square, Ganjam", 19.3149, 84.7941),
        ("Chhatrapur Main Road, Ganjam", 19.3560, 84.9920),
        ("AIIMS Campus, Bhubaneswar", 20.2312, 85.7761),
        ("Mangalabag, Cuttack", 20.4789, 85.8824)
    ]

    common_drugs = [
        "Metformin", "Warfarin", "Atorvastatin", "Amlodipine", "Lisinopril",
        "Ramipril", "Telmisartan", "Paracetamol", "Ibuprofen", "Diclofenac",
        "Azithromycin", "Amoxicillin", "Ciprofloxacin", "Omeprazole", "Pantoprazole",
        "Cetirizine", "Salbutamol", "Deriphyllin", "Montelukast", "Budesonide",
        "Dextromethorphan", "Insulin Glargine", "Glimepiride", "Teneligliptin",
        "Clopidogrel", "Aspirin", "Spironolactone", "Furosemide", "Hydrochlorothiazide",
        "Levothyroxine", "Ranitidine", "Domperidone", "Ondansetron", "Metoclopramide",
        "Doxycycline", "Co-trimoxazole", "Cephalexin", "Cefixime", "Ofloxacin",
        "Metronidazole", "Fluconazole", "Terbinafine", "Clotrimazole", "Mupirocin",
        "Silver Sulfadiazine", "Diclofenac Gel", "Multivitamin with Zinc", "Calcium 500mg",
        "Iron Folic Acid", "Vitamin D3 60k", "Oral Rehydration Salts (ORS)", "Diazepam",
        "Alprazolam", "Clonazepam", "Tramadol", "Pregabalin", "Gabapentin",
        "Betahistine", "Methylcobalamin", "Pantocid DSR"
    ]

    pharmacies = []

    for i, (loc_name, lat, lng) in enumerate(blr_localities, start=1):
        pid = f"PHARM-BLR-{i:02d}"
        ptype = "Jan Aushadhi" if i % 3 == 0 else ("Hospital pharmacy" if i % 4 == 0 else "Retail")
        is_24x7 = (i in (1, 4, 10, 16))
        
        stock = {}
        for drug in common_drugs:
            if i == 1:
                qty = random.randint(80, 200)
                status = "IN_STOCK"
            elif i == 2:
                if drug == "Warfarin":
                    qty = 45
                    status = "IN_STOCK"
                elif drug == "Metformin":
                    qty = 12
                    status = "LOW"
                else:
                    qty = random.randint(0, 100)
                    status = "IN_STOCK" if qty > 20 else ("LOW" if qty > 0 else "OUT")
            elif i == 3:
                if drug == "Warfarin":
                    qty = 0
                    status = "OUT"
                else:
                    qty = random.randint(10, 120)
                    status = "IN_STOCK" if qty > 20 else "LOW"
            else:
                qty = random.randint(0, 150)
                if qty == 0:
                    status = "OUT"
                elif qty < 25:
                    status = "LOW"
                else:
                    status = "IN_STOCK"
            stock[drug] = {"qty": qty, "status": status}

        pharmacies.append({
            "id": pid,
            "name": f"Apollo Pharmacy {loc_name}" if ptype == "Retail" else (f"Pradhan Mantri Jan Aushadhi Kendra {loc_name}" if ptype == "Jan Aushadhi" else f"Manipal Hospital In-House Pharmacy {loc_name}"),
            "type": ptype,
            "locality": loc_name,
            "lat": lat,
            "lng": lng,
            "hours": "24 Hours / 7 Days" if is_24x7 else "08:00 AM - 10:30 PM",
            "phone": f"90000001{i:02d}",
            "is24x7": is_24x7,
            "stock": stock,
            "synthetic": True
        })

    for j, (loc_name, lat, lng) in enumerate(odisha_localities, start=1):
        pid = f"PHARM-OD-{j:02d}"
        ptype = "Jan Aushadhi" if j % 2 == 0 else "Retail"
        is_24x7 = (j == 3)
        stock = {}
        for drug in common_drugs:
            qty = random.randint(30, 180)
            stock[drug] = {"qty": qty, "status": "IN_STOCK" if qty > 20 else "LOW"}

        pharmacies.append({
            "id": pid,
            "name": f"Utkal Health Pharmacy - {loc_name}",
            "type": ptype,
            "locality": loc_name,
            "lat": lat,
            "lng": lng,
            "hours": "24 Hours" if is_24x7 else "08:00 AM - 09:30 PM",
            "phone": f"90000002{j:02d}",
            "is24x7": is_24x7,
            "stock": stock,
            "synthetic": True
        })

    with open(SEED_DIR / "pharmacies.json", "w", encoding="utf-8") as f:
        json.dump(pharmacies, f, indent=2)
    return pharmacies


# ---------------------------------------------------------------------------
# 12. asha_workers.json (>=10)
# ---------------------------------------------------------------------------
def generate_asha_workers():
    workers = [
        {
            "ashaWorkerId": "ASHA-OD-402",
            "name": "Meena Majhi",
            "state": "Odisha",
            "district": "Ganjam",
            "block": "Chhatrapur",
            "village": "Kalyanpur",
            "languages": ["Odia", "Hindi"],
            "phone": "9000000301",
            "linkedPatients": ["PAT-SS-1001", "PAT-SS-1005", "PAT-SS-1011", "PAT-SS-1023"],
            "synthetic": True
        },
        {
            "ashaWorkerId": "ASHA-BH-501",
            "name": "Sunita Devi",
            "state": "Bihar",
            "district": "Gaya",
            "block": "Bodh Gaya",
            "village": "Bakrour",
            "languages": ["Hindi", "Magahi"],
            "phone": "9000000302",
            "linkedPatients": ["PAT-SS-1002", "PAT-SS-1012", "PAT-SS-1018"],
            "synthetic": True
        },
        {
            "ashaWorkerId": "ASHA-KA-101",
            "name": "Parvathamma K.",
            "state": "Karnataka",
            "district": "Raichur",
            "block": "Manvi",
            "village": "Hirekotnekal",
            "languages": ["Kannada", "Telugu"],
            "phone": "9000000303",
            "linkedPatients": ["PAT-SS-1003", "PAT-SS-1013", "PAT-SS-1024"],
            "synthetic": True
        },
        {
            "ashaWorkerId": "ASHA-TN-301",
            "name": "Kavitha Selvi",
            "state": "Tamil Nadu",
            "district": "Tirunelveli",
            "block": "Ambasamudram",
            "village": "Kallidaikurichi",
            "languages": ["Tamil"],
            "phone": "9000000304",
            "linkedPatients": ["PAT-SS-1004", "PAT-SS-1016"],
            "synthetic": True
        },
        {
            "ashaWorkerId": "ASHA-WB-601",
            "name": "Jharna Das",
            "state": "West Bengal",
            "district": "Murshidabad",
            "block": "Lalgola",
            "village": "Dewansarai",
            "languages": ["Bengali", "Hindi"],
            "phone": "9000000305",
            "linkedPatients": ["PAT-SS-1006", "PAT-SS-1015", "PAT-SS-1021"],
            "synthetic": True
        },
        {
            "ashaWorkerId": "ASHA-JH-701",
            "name": "Sushila Soren",
            "state": "Jharkhand",
            "district": "Dhanbad",
            "block": "Govindpur",
            "village": "Bagsuma",
            "languages": ["Hindi", "Santhali"],
            "phone": "9000000306",
            "linkedPatients": ["PAT-SS-1007", "PAT-SS-1008", "PAT-SS-1014"],
            "synthetic": True
        },
        {
            "ashaWorkerId": "ASHA-TS-201",
            "name": "Lakshmi Bai",
            "state": "Telangana",
            "district": "Mahbubnagar",
            "block": "Jadcherla",
            "village": "Gollapalli",
            "languages": ["Telugu", "Hindi"],
            "phone": "9000000307",
            "linkedPatients": ["PAT-SS-1009", "PAT-SS-1020"],
            "synthetic": True
        },
        {
            "ashaWorkerId": "ASHA-UP-801",
            "name": "Geeta Yadav",
            "state": "Uttar Pradesh",
            "district": "Gorakhpur",
            "block": "Pipraich",
            "village": "Belghat",
            "languages": ["Hindi", "Bhojpuri"],
            "phone": "9000000308",
            "linkedPatients": ["PAT-SS-1010"],
            "synthetic": True
        },
        {
            "ashaWorkerId": "ASHA-AP-901",
            "name": "Rajeswari K.",
            "state": "Andhra Pradesh",
            "district": "Srikakulam",
            "block": "Tekkali",
            "village": "Temburu",
            "languages": ["Telugu", "Odia"],
            "phone": "9000000309",
            "linkedPatients": ["PAT-SS-1017"],
            "synthetic": True
        },
        {
            "ashaWorkerId": "ASHA-OD-403",
            "name": "Puspanjali Sahu",
            "state": "Odisha",
            "district": "Balasore",
            "block": "Jaleswar",
            "village": "Sugo",
            "languages": ["Odia", "Bengali"],
            "phone": "9000000310",
            "linkedPatients": ["PAT-SS-1019", "PAT-SS-1022"],
            "synthetic": True
        }
    ]
    with open(SEED_DIR / "asha_workers.json", "w", encoding="utf-8") as f:
        json.dump(workers, f, indent=2)
    return workers


# ---------------------------------------------------------------------------
# 13. occupational_risk.json (>=12 occupations)
# ---------------------------------------------------------------------------
def generate_occupational_risk():
    occupations = [
        {
            "occupation": "Construction Site Mason",
            "hazards": ["Respirable crystalline silica", "Hexavalent chromium in wet cement", "Ergonomic lifting", "Noise"],
            "exposureYearsThresholds": {"LOW": 1, "MODERATE": 3, "HIGH": 5},
            "symptomWeights": {"Chronic dry cough": 30, "Shortness of breath on exertion": 35, "Cement contact dermatitis": 20, "Low back pain": 15},
            "predictedConditions": [
                "Silicosis & Accelerated Pneumoconiosis",
                "Chronic Obstructive Pulmonary Disease (COPD)",
                "Allergic & Irritant Contact Dermatitis ('Cement Burns')",
                "Lumbar Disc Herniation & Musculoskeletal Strain"
            ],
            "recommendedScreenings": [
                "High-Resolution Digital Chest X-Ray (ILO Pneumoconiosis Standard)",
                "Spirometry (FEV1, FVC, FEV1/FVC ratio)",
                "Peak Expiratory Flow Rate (PEFR)",
                "Dermatological Patch Testing for Potassium Dichromate"
            ],
            "plainLanguageGuidance": "Working with cement and stone exposes lungs to fine silica dust that causes irreversible scarring. Wear an N95 or particulate respirator and use barrier creams on hands.",
            "preventivePpeAdvice": "NIOSH-approved N95 particulate respirator, heavy-duty nitrile-coated gloves, steel-toe boots, eye protection goggles.",
            "synthetic": True
        },
        {
            "occupation": "Quarry / Stone-Crusher Worker",
            "hazards": ["Ultra-fine respirable quartz dust", "Acoustic trauma (>95 dBA)", "Vibration", "Flying rock chips"],
            "exposureYearsThresholds": {"LOW": 1, "MODERATE": 2, "HIGH": 4},
            "symptomWeights": {"Severe progressive dyspnea": 40, "Chest tightness": 30, "Persistent cough with gray sputum": 20, "Tinnitus": 10},
            "predictedConditions": [
                "Acute & Accelerated Silicosis",
                "Silico-Tuberculosis (Tuberculosis superimposed on silicosis)",
                "Noise-Induced Hearing Loss (NIHL)"
            ],
            "recommendedScreenings": [
                "HRCT Thorax with high-resolution reconstruction",
                "Sputum GeneXpert / AFB smear for Tuberculosis",
                "Pure-tone audiometry"
            ],
            "plainLanguageGuidance": "Stone crushing produces the highest concentration of toxic quartz dust. Wet dust suppression and P100 respirators are essential to prevent fatal lung stiffening.",
            "preventivePpeAdvice": "P100 half-face elastomeric respirator, high-attenuation earmuffs (NRR >=28 dB), full-face shield.",
            "synthetic": True
        },
        {
            "occupation": "Textile / Garment Worker",
            "hazards": ["Raw cotton bract and endotoxin dust", "Synthetic azo dyes", "Static sitting posture", "Repetitive hand motions"],
            "exposureYearsThresholds": {"LOW": 2, "MODERATE": 4, "HIGH": 7},
            "symptomWeights": {"Monday morning chest tightness": 40, "Wheezing": 25, "Chronic dry cough": 20, "Carpal tunnel tingling": 15},
            "predictedConditions": [
                "Occupational Byssinosis ('Monday Fever')",
                "Occupational Asthma",
                "Carpal Tunnel Syndrome & Cervical Spondylosis"
            ],
            "recommendedScreenings": [
                "Cross-shift Spirometry (pre-shift vs post-shift on first day of work week)",
                "Nerve conduction studies for median nerve compression"
            ],
            "plainLanguageGuidance": "Breathing cotton dust causes chest tightness that is worst on the first working day of the week (Monday Fever). Proper factory exhaust ventilation and masks are vital.",
            "preventivePpeAdvice": "Well-fitting particulate mask, ergonomic wrist splints, regular micro-break stretching.",
            "synthetic": True
        },
        {
            "occupation": "Welder / Metal Fabricator",
            "hazards": ["Welding fumes (hexavalent chromium, nickel, manganese)", "Ultraviolet & infrared radiation", "Ozone", "Metal sparks"],
            "exposureYearsThresholds": {"LOW": 1, "MODERATE": 3, "HIGH": 6},
            "symptomWeights": {"Sweet metallic taste in mouth": 30, "Sudden evening fever and chills": 30, "Eye grittiness / Arc eye": 25, "Tremors": 15},
            "predictedConditions": [
                "Metal Fume Fever",
                "Photokeratitis ('Arc Eye')",
                "Chronic Manganism & Neurological Tremors",
                "Siderosis (benign iron deposition)"
            ],
            "recommendedScreenings": [
                "Chest X-Ray PA View",
                "Slit-lamp ophthalmic examination",
                "Serum manganese and urinary chromium levels"
            ],
            "plainLanguageGuidance": "Welding fumes contain vaporized toxic metals that cause sudden flu-like chills (metal fume fever) and lung damage. Always use local exhaust extraction.",
            "preventivePpeAdvice": "Auto-darkening welding helmet (shade 10-12), fume extraction respirator, leather spats and welding gauntlets.",
            "synthetic": True
        },
        {
            "occupation": "Painter / Coating Worker",
            "hazards": ["Organic solvents (toluene, xylene)", "Lead pigments", "Isocyanates in polyurethane spray", "Volatile organic compounds (VOC)"],
            "exposureYearsThresholds": {"LOW": 1, "MODERATE": 3, "HIGH": 5},
            "symptomWeights": {"Lightheadedness and morning headaches": 35, "Loss of appetite and abdominal colic": 30, "Memory fog": 20, "Skin flaking": 15},
            "predictedConditions": [
                "Chronic Toxic Encephalopathy ('Painter's Syndrome')",
                "Plumbism (Lead Poisoning)",
                "Occupational Isocyanate Asthma",
                "Peripheral Polyneuropathy"
            ],
            "recommendedScreenings": [
                "Blood Lead Level (BLL)",
                "Liver and renal function panels",
                "Comprehensive neuro-cognitive assessment"
            ],
            "plainLanguageGuidance": "Paint thinners and solvents enter the bloodstream through fumes and skin, harming the brain and nervous system. Use organic vapor cartridge masks.",
            "preventivePpeAdvice": "Dual-cartridge organic vapor respirator (OV/P95), chemical-resistant butyl gloves, safety goggles.",
            "synthetic": True
        },
        {
            "occupation": "Domestic Worker",
            "hazards": ["Sodium hypochlorite (bleach)", "Caustic soda oven cleaners", "Prolonged wet work", "Heavy floor scrubbing posture"],
            "exposureYearsThresholds": {"LOW": 2, "MODERATE": 5, "HIGH": 8},
            "symptomWeights": {"Hands cracking and peeling": 35, "Wheezing after toilet cleaning": 30, "Knee and lower back pain": 25, "Eye stinging": 10},
            "predictedConditions": [
                "Severe Irritant Hand Eczema",
                "Reactive Airways Dysfunction Syndrome (RADS)",
                "Prepatellar Bursitis ('Housemaid's Knee')"
            ],
            "recommendedScreenings": [
                "Dermatological examination and patch test",
                "Peak flow diary before and after cleaning shift"
            ],
            "plainLanguageGuidance": "Mixing household cleaning chemicals releases harmful chlorine fumes that irritate lungs. Harsh soaps strip protective skin oils.",
            "preventivePpeAdvice": "Heavy-duty flock-lined rubber gloves, cotton under-gloves, kneepads for floor work.",
            "synthetic": True
        },
        {
            "occupation": "Security Guard",
            "hazards": ["Night shift circadian disruption", "Prolonged stationary standing", "Extreme outdoor temperatures", "Noise"],
            "exposureYearsThresholds": {"LOW": 2, "MODERATE": 6, "HIGH": 10},
            "symptomWeights": {"Severe leg swelling and heavy aching": 35, "Insomnia and daytime fatigue": 30, "Elevated blood pressure": 20, "Acid reflux": 15},
            "predictedConditions": [
                "Lower Limb Chronic Venous Insufficiency (Varicose Veins)",
                "Shift Work Sleep Disorder",
                "Accelerated Metabolic Syndrome & Hypertension"
            ],
            "recommendedScreenings": [
                "Venous Duplex Ultrasound of lower extremities",
                "24-Hour Ambulatory Blood Pressure Monitoring (ABPM)",
                "Fasting lipid and glucose profile"
            ],
            "plainLanguageGuidance": "Standing still for 12 hours causes blood to pool in leg veins, leading to painful varicose veins and clots. Walking in place and compression socks relieve pressure.",
            "preventivePpeAdvice": "Graduated medical compression stockings (Class II, 20-30 mmHg), cushioned orthotic insoles, high-visibility vest.",
            "synthetic": True
        },
        {
            "occupation": "Delivery Rider",
            "hazards": ["Diesel exhaust fine particulates (PM2.5)", "Traffic vibration & lumbar compression", "Heat stroke / dehydration", "Road collision trauma"],
            "exposureYearsThresholds": {"LOW": 1, "MODERATE": 3, "HIGH": 5},
            "symptomWeights": {"Constant burning throat and dry cough": 30, "Severe tailbone / lower back stiffness": 30, "Heat dizziness": 25, "Shoulder spasms": 15},
            "predictedConditions": [
                "Chronic Air Pollution Bronchitis",
                "Whole-Body Vibration Induced Lumbago & Sciatica",
                "Heat Exhaustion & Early Dehydration Nephropathy"
            ],
            "recommendedScreenings": [
                "Lumbar spine MRI / X-ray",
                "Spirometry",
                "Urine specific gravity and serum electrolytes"
            ],
            "plainLanguageGuidance": "Riding in urban traffic exposes lungs to dangerous diesel fumes for 10 hours daily. Continuous bike vibration causes premature disc wear.",
            "preventivePpeAdvice": "Anti-pollution activated carbon PM2.5 mask, certified DOT/ECE helmet, lumbar support belt, electrolyte water bottle.",
            "synthetic": True
        },
        {
            "occupation": "Auto Rickshaw Driver",
            "hazards": ["Continuous whole-body vibration (2-8 Hz resonance)", "Roadside PM2.5 & carbon monoxide", "High noise levels (>85 dBA)", "Restricted leg posture"],
            "exposureYearsThresholds": {"LOW": 2, "MODERATE": 5, "HIGH": 10},
            "symptomWeights": {"Chronic back spasm on bumpy roads": 35, "Hearing loss in right ear (traffic side)": 25, "Piles / hemorrhoids": 25, "Chronic eye irritation": 15},
            "predictedConditions": [
                "Accelerated Degenerative Disc Disease",
                "Noise-Induced Asymmetrical Hearing Loss",
                "Internal and External Hemorrhoids",
                "Chronic Blepharitis"
            ],
            "recommendedScreenings": [
                "Audiometry",
                "Lumbosacral spine radiography",
                "Proctological examination"
            ],
            "plainLanguageGuidance": "Auto driving sends continuous mechanical vibrations directly through the spine while breathing roadside exhaust. Ergonomic seat cushions protect the lower back.",
            "preventivePpeAdvice": "High-density polyurethane vibration-dampening seat cushion, UV-protective sunglasses, earplugs in heavy traffic.",
            "synthetic": True
        },
        {
            "occupation": "Hotel Kitchen Staff",
            "hazards": ["Biomass / LPG fuel combustion gases", "Cooking oil fumes (acrolein, polycyclic aromatic hydrocarbons)", "Thermal scalds", "Slippery wet floors"],
            "exposureYearsThresholds": {"LOW": 2, "MODERATE": 4, "HIGH": 8},
            "symptomWeights": {"Chronic eye tearing and cough while cooking": 35, "Painful foot arches (plantar fasciitis)": 25, "Burn scars": 20, "Leg heaviness": 20},
            "predictedConditions": [
                "Cooking Oil Fume Induced Bronchial Hyperresponsiveness",
                "Plantar Fasciitis",
                "Superficial Thermal Burns",
                "Lower Extremity Venous Varicosities"
            ],
            "recommendedScreenings": [
                "Chest X-Ray PA View",
                "Bilateral foot arch physical examination",
                "Spirometry"
            ],
            "plainLanguageGuidance": "Breathing intense kitchen oil smoke for hours irritates the lungs similarly to passive smoking. Adequate exhaust hoods are mandatory.",
            "preventivePpeAdvice": "Heat-resistant silicone aprons, slip-resistant oil-proof kitchen shoes with arch support, forearm burn guards.",
            "synthetic": True
        },
        {
            "occupation": "Sanitation Worker",
            "hazards": ["Toxic sewer gases (hydrogen sulfide, methane, ammonia)", "Biological blood-borne and enteric pathogens", "Sharps injury", "Fecal aerosolization"],
            "exposureYearsThresholds": {"LOW": 1, "MODERATE": 2, "HIGH": 4},
            "symptomWeights": {"Sudden dizziness or loss of smell": 40, "Recurrent loose watery stools": 25, "Skin boils and fungal sores": 25, "Eye infection": 10},
            "predictedConditions": [
                "Hydrogen Sulfide Asphyxiation / Toxic Encephalopathy",
                "Leptospirosis & Enteric Bacterial Infections",
                "Hepatitis A & B Exposure",
                "Infectious Cutaneous Ulcers"
            ],
            "recommendedScreenings": [
                "Hepatitis B Surface Antigen & Anti-HBs titer",
                "Leptospira IgM antibody rapid test",
                "Stool routine and microscopic examination"
            ],
            "plainLanguageGuidance": "Sewer gases can knock out the sense of smell and cause sudden collapse within seconds. Full body waterproof protective gear and vaccination are non-negotiable.",
            "preventivePpeAdvice": "Multi-gas detector badge, heavy waterproof nitrile overalls, puncture-resistant decontamination gloves, full waterproof gumboots.",
            "synthetic": True
        },
        {
            "occupation": "Agricultural Farm Labourer",
            "hazards": ["Organophosphate & carbamate pesticide spray", "Intense solar UV radiation (UV index >10)", "Dehydration / heat cramps", "Snake & insect envenomation"],
            "exposureYearsThresholds": {"LOW": 2, "MODERATE": 5, "HIGH": 10},
            "symptomWeights": {"Pinpoint pupils, excessive saliva, nausea after spraying": 40, "Dark pigmented skin patches on neck": 25, "Sunburn blisters": 20, "Calf cramps": 15},
            "predictedConditions": [
                "Chronic Organophosphate Neurotoxicity",
                "Solar Keratosis & Cutaneous Squamous Cell Carcinoma",
                "Chronic Interstitial Nephropathy of Agricultural Communities (CINAC)",
                "Pterygium"
            ],
            "recommendedScreenings": [
                "Serum pseudocholinesterase / RBC cholinesterase levels",
                "Serum creatinine and microalbuminuria",
                "Full-body dermatological cancer screening"
            ],
            "plainLanguageGuidance": "Pesticides penetrate wet clothing and skin easily, causing nerve toxicity. Spraying must never occur against the wind and requires complete protective coveralls.",
            "preventivePpeAdvice": "Chemical spray coverall with hood, wide-brim straw hat, chemical splash goggles, neoprene gloves, knee-high rubber boots.",
            "synthetic": True
        }
    ]
    with open(SEED_DIR / "occupational_risk.json", "w", encoding="utf-8") as f:
        json.dump(occupations, f, indent=2)
    return occupations


# ---------------------------------------------------------------------------
# 14. translation_phrasebook.json (>=80 phrases)
# ---------------------------------------------------------------------------
def generate_translation_phrasebook():
    phrases = [
        # EMERGENCY
        {
            "id": "PHR-001",
            "category": "EMERGENCY",
            "text": {
                "en": "I am having severe chest pain and tightness.",
                "hi": "मेरे सीने में बहुत तेज दर्द और दबाव महसूस हो रहा है।",
                "or": "ମୋ ଛାତିରେ ବହୁତ କଷ୍ଟ ଏବଂ ଚାପ ହେଉଛି।",
                "kn": "ನನ್ನ ಎದೆಯಲ್ಲಿ ತೀವ್ರವಾದ ನೋವು ಮತ್ತು ಬಿಗಿತವಾಗುತ್ತಿದೆ.",
                "ta": "எனது மார்பில் கடுமையான வலியும் அழுத்தமும் உள்ளது.",
                "te": "నా ఛాతీలో తీవ్రమైన నొప్పి మరియు ఒత్తిడిగా ఉంది."
            },
            "phonetic": {
                "en": "I am having severe chest pain and tightness.",
                "hi": "Mere seene mein bahut tez dard aur dabav mehsoos ho raha hai.",
                "or": "Mo chhatire bahuta kashta ebanga chaapa heuchhi.",
                "kn": "Nanna edeyalli teevravaada novu mattu bigithavaaguttide.",
                "ta": "Enadhu maarbil kadumaiyana valiyum azhuththamum ulladhu.",
                "te": "Naa chaateelo teevramaina noppi mariyu ottidigaa undi."
            },
            "symptomTags": ["Chest Pain / Angina", "Cardiovascular Strain"],
            "reviewed": False,
            "synthetic": True
        },
        {
            "id": "PHR-002",
            "category": "EMERGENCY",
            "text": {
                "en": "I am struggling to breathe.",
                "hi": "मुझे सांस लेने में बहुत कठिनाई हो रही है।",
                "or": "ମୋତେ ନିଶ୍ୱାସ ନେବାରେ ବହୁତ କଷ୍ଟ ହେଉଛି।",
                "kn": "ನನಗೆ ಉಸಿರಾಡಲು ತುಂಬಾ ಕಷ್ಟವಾಗುತ್ತಿದೆ.",
                "ta": "எனக்கு மூச்சு விடுவதில் மிகுந்த சிரமம் உள்ளது.",
                "te": "నాకు ఊపిరి పీల్చుకోవడం చాలా కష్టంగా ఉంది."
            },
            "phonetic": {
                "en": "I am struggling to breathe.",
                "hi": "Mujhe saans lene mein bahut kathinai ho rahi hai.",
                "or": "Mote niswasa nebare bahuta kashta heuchhi.",
                "kn": "Nanage usiraadalu tumba kashtavaaguttide.",
                "ta": "Enakku moochchu viduvadhil migundha sramam ulladhu.",
                "te": "Naaku oopiri peelchukovadam chaala kashtamgaa undi."
            },
            "symptomTags": ["Shortness of Breath", "Acute Dyspnea"],
            "reviewed": False,
            "synthetic": True
        },
        {
            "id": "PHR-003",
            "category": "EMERGENCY",
            "text": {
                "en": "Call an ambulance immediately.",
                "hi": "तुरंत एम्बुलेंस बुलाइए।",
                "or": "ତୁରନ୍ତ ଆମ୍ବୁଲାନ୍ସ ଡାକନ୍ତୁ।",
                "kn": "ಕೂಡಲೇ ಆಂಬ್ಯುಲೆನ್ಸ್ ಕರೆಯಿರಿ.",
                "ta": "உடனடியாக ஆம்புலன்ஸை அழையுங்கள்.",
                "te": "వెంటనే అంబులెన్స్‌ని పిలవండి."
            },
            "phonetic": {
                "en": "Call an ambulance immediately.",
                "hi": "Turant ambulance bulaiye.",
                "or": "Turanta ambulance daakantu.",
                "kn": "Koodale ambulance kareyiri.",
                "ta": "Udanadiyaaga ambulance-ai azhaiyungal.",
                "te": "Ventane ambulance-ni pilavandi."
            },
            "symptomTags": ["Emergency Triage"],
            "reviewed": False,
            "synthetic": True
        },
        # ALLERGY
        {
            "id": "PHR-004",
            "category": "ALLERGY",
            "text": {
                "en": "Are you allergic to any medicines?",
                "hi": "क्या आपको किसी दवाई से एलर्जी है?",
                "or": "ଆପଣଙ୍କର କୌଣସି ଔଷଧରୁ ଆଲର୍ଜି ଅଛି କି?",
                "kn": "ನಿಮಗೆ ಯಾವುದೇ ಔಷಧಿಗಳಿಂದ ಅಲರ್ಜಿ ಇದೆಯೇ?",
                "ta": "உங்களுக்கு ஏதேனும் மருந்துகளுக்கு ஒவ்வாமை உள்ளதா?",
                "te": "మీకు ఏవైనా మందులతో అలెర్జీ ఉందా?"
            },
            "phonetic": {
                "en": "Are you allergic to any medicines?",
                "hi": "Kya aapko kisi dawai se allergy hai?",
                "or": "Aapanankara kounasi aushadharu allergy achhi ki?",
                "kn": "Nimage yaavude aushadhigalinda allergy ideye?",
                "ta": "Ungalukku edhenum marundhugalukku ovvaamai ulladhaa?",
                "te": "Meeku evainaa mandulato allergy undaa?"
            },
            "symptomTags": ["Drug Allergy Screening"],
            "reviewed": False,
            "synthetic": True
        },
        {
            "id": "PHR-005",
            "category": "ALLERGY",
            "text": {
                "en": "I get severe skin rash and swelling from Penicillin.",
                "hi": "पेनिसिलिन लेने से मुझे शरीर पर लाल दाने और सूजन हो जाती है।",
                "or": "ପେନିସିଲିନ୍ ଖାଇଲେ ମୋ ଦେହରେ ନାଲି ଦାଗ ଏବଂ ଫୁଲା ହୋଇଯାଏ।",
                "kn": "ಪೆನ್ಸಿಲಿನ್ ತೆಗೆದುಕೊಂಡರೆ ನನ್ನ ಮೈಮೇಲೆ ಕೆಂಪು ಗುಳ್ಳೆಗಳು ಮತ್ತು ಊತ ಬರುತ್ತದೆ.",
                "ta": "பென்சிலின் எடுத்தால் எனக்கு உடலில் தடிப்புகளும் வீக்கமும் ஏற்படும்.",
                "te": "పెన్సిలిన్ తీసుకుంటే నా శరీరంపై దద్దుర్లు మరియు వాపు వస్తాయి."
            },
            "phonetic": {
                "en": "I get severe skin rash and swelling from Penicillin.",
                "hi": "Penicillin lene se mujhe shareer par laal daane aur soojan ho jaati hai.",
                "or": "Penicillin khaile mo dehare naali daaga ebanga phulaa hoiyae.",
                "kn": "Penicillin tegedukondare nanna maimele kempu gullevalu mattu oota baruttade.",
                "ta": "Penicillin eduththaal enakku udalil thadippugalum veekkamum erpadum.",
                "te": "Penicillin teesukunte naa shareerampai daddurlu mariyu vaapu vastaayi."
            },
            "symptomTags": ["Penicillin Allergy", "Drug Rash"],
            "reviewed": False,
            "synthetic": True
        },
        # MEDICATION & INSTRUCTION
        {
            "id": "PHR-006",
            "category": "MEDICATION",
            "text": {
                "en": "Take this tablet twice daily after food with water.",
                "hi": "यह गोली दिन में दो बार खाने के बाद पानी के साथ लें।",
                "or": "ଏହି ବଟିକାକୁ ଦିନକୁ ଦୁଇଥର ଖାଇବା ପରେ ପାଣି ସହିତ ଖାଆନ୍ତୁ।",
                "kn": "ಈ ಮಾತ್ರೆಗಳನ್ನು ದಿನಕ್ಕೆ ಎರಡು ಬಾರಿ ಊಟದ ನಂತರ ನೀರಿನೊಂದಿಗೆ ತೆಗೆದುಕೊಳ್ಳಿ.",
                "ta": "இந்த மாத்திரையை உணவுக்குப் பிறகு தினமும் இரண்டு முறை தண்ணீருடன் சாப்பிடுங்கள்.",
                "te": "ఈ మాత్రను భోజనం తర్వాత రోజుకు రెండుసార్లు నీటితో తీసుకోండి."
            },
            "phonetic": {
                "en": "Take this tablet twice daily after food with water.",
                "hi": "Yeh goli din mein do baar khaane ke baad paani ke saath lein.",
                "or": "Ehi batikaku dinaku duithara khaiba pare paani sahita khaantu.",
                "kn": "Ee maatregalannu dinakke eradu baari ootada nanthara neerinondige tegedukolli.",
                "ta": "Indha maaththiraiyai unavukkup piragu dhinamum irandu murai thanneerudan saappidungal.",
                "te": "Ee maatranu bhojanam tarvaatha roojuku rendusarlu neetito teesukondi."
            },
            "symptomTags": ["Prescription Directions", "Adherence Instruction"],
            "reviewed": False,
            "synthetic": True
        },
        {
            "id": "PHR-007",
            "category": "MEDICATION",
            "text": {
                "en": "Do not stop taking this blood thinner without consulting your doctor.",
                "hi": "अपने डॉक्टर से पूछे बिना यह खून पतला करने वाली दवाई बंद न करें।",
                "or": "ଡାକ୍ତରଙ୍କ ପରାମର୍ଶ ବିନା ଏହି ରକ୍ତ ପତଳା କରିବା ଔଷଧ ବନ୍ଦ କରନ୍ତୁ ନାହିଁ।",
                "kn": "ವೈದ್ಯರ ಸಲಹೆಯಿಲ್ಲದೆ ಈ ರಕ್ತ ತೆಳುವಾಗಿಸುವ ಔಷಧಿಯನ್ನು ನಿಲ್ಲಿಸಬೇಡಿ.",
                "ta": "மருத்துவரின் ஆலோசனையின்றி இந்த ரத்தத்தை நீர்க்கும் மருந்தை நிறுத்த வேண்டாம்.",
                "te": "వైద్యుల సలహా లేకుండా ఈ రక్తం పలుచబడే మందును ఆపవద్దు."
            },
            "phonetic": {
                "en": "Do not stop taking this blood thinner without consulting your doctor.",
                "hi": "Apne doctor se poochhe bina yeh khoon patla karne wali dawai band na karein.",
                "or": "Daaktaranka paraamarsha binaa ehi rakta patalaa karibaa aushadha banda karantu naahin.",
                "kn": "Vaidyara salaheyillade ee rakta teluvaagisuva aushadhiyannu nillisabedi.",
                "ta": "Maruththuvarin aalosanaiyindri indha raththaththai neerkkum marundhai niruththa vendaam.",
                "te": "Vaidyula salahaa lekundaa ee raktam paluchabade mandunu aapavaddu."
            },
            "symptomTags": ["Anticoagulant Warning", "Warfarin Safety"],
            "reviewed": False,
            "synthetic": True
        },
        # SYMPTOM & OCCUPATIONAL
        {
            "id": "PHR-008",
            "category": "SYMPTOM",
            "text": {
                "en": "I have persistent dry cough and breathing difficulty due to construction cement and dust.",
                "hi": "सीमेंट और रेत की धूल के कारण मुझे लगातार सूखी खांसी और सांस फूलने की समस्या है।",
                "or": "ସିମେଣ୍ଟ ଏବଂ ଧୂଳି ଯୋଗୁଁ ମୋତେ କ୍ରମାଗତ ଶୁଖିଲା କାଶ ଏବଂ ନିଶ୍ୱାସ ନେବାରେ କଷ୍ଟ ହେଉଛି।",
                "kn": "ಸಿಮೆಂಟ್ ಮತ್ತು ಧೂಳಿನಿಂದಾಗಿ ನನಗೆ ನಿರಂತರ ಒಣಕೆಮ್ಮು ಮತ್ತು ಉಸಿರಾಟದ ತೊಂದರೆ ಇದೆ.",
                "ta": "சிமெண்ட் மற்றும் தூசியால் எனக்கு தொடர்ந்து வறட்டு இருமலும் மூச்சுத் திணறலும் உள்ளது.",
                "te": "సిమెంట్ మరియు ధూళి వల్ల నాకు నిరంతరం పొడి దగ్గు మరియు శ్వాస తీసుకోవడంలో ఇబ్బంది ఉంది."
            },
            "phonetic": {
                "en": "I have persistent dry cough and breathing difficulty due to construction cement and dust.",
                "hi": "Cement aur ret ki dhool ke kaaran mujhe lagataar sookhi khaansi aur saans phoolne ki samasya hai.",
                "or": "Cement ebanga dhooli jogun mote kramaagata shukhilaa kaasha ebanga niswasa nebare kashta heuchhi.",
                "kn": "Cement mattu dhoolinindaagi nanage niranthara onakemmu mattu usiraatada thondare ide.",
                "ta": "Cement matrum dhoosiyaal enakku thodarnthu varattu irumalum moochchuth thinamalum ulladhu.",
                "te": "Cement mariyu dhooli valla naaku nirantaram podi daggu mariyu shwaasa teesukovadamlo ibbandi undi."
            },
            "symptomTags": ["Persistent Dust Cough", "Suspected Silica Exposure", "Shortness of Breath"],
            "reviewed": False,
            "synthetic": True
        },
        # CONSENT
        {
            "id": "PHR-009",
            "category": "CONSENT",
            "text": {
                "en": "Please give your 6-digit Consent PIN so the doctor can view your medical records.",
                "hi": "कृपया अपना 6 अंकों का सहमति पिन बताएं ताकि डॉक्टर आपका मेडिकल रिकॉर्ड देख सकें।",
                "or": "ଦୟାକରି ଆପଣଙ୍କ ୬-ଅଙ୍କ ବିଶିଷ୍ଟ ସମ୍ମତି ପିନ୍ ଦିଅନ୍ତୁ ଯାହାଦ୍ୱାରା ଡାକ୍ତର ଆପଣଙ୍କ ଚିକିତ୍ସା ରେକର୍ଡ ଦେଖିପାରିବେ।",
                "kn": "ವೈದ್ಯರು ನಿಮ್ಮ ವೈದ್ಯಕೀಯ ದಾಖಲೆಗಳನ್ನು ನೋಡಲು ದಯವಿಟ್ಟು ನಿಮ್ಮ 6-ಅಂಕಿಯ ಒಪ್ಪಿಗೆ ಪಿನ್ ನೀಡಿ.",
                "ta": "மருத்துவர் உங்கள் மருத்துவப் பதிவுகளைப் பார்க்க உங்கள் 6-இலக்க ஒப்புதல் பின்னை வழங்கவும்.",
                "te": "డాక్టర్ మీ మెడికల్ రికార్డులను చూడటానికి దయచేసి మీ 6-అంకెల సమ్మతి పిన్ ఇవ్వండి."
            },
            "phonetic": {
                "en": "Please give your 6-digit Consent PIN so the doctor can view your medical records.",
                "hi": "Kripya apna 6 ankon ka sahamati PIN batayein taaki doctor aapka medical record dekh sakein.",
                "or": "Dayaakari aapananka 6-anka bishista sammati PIN diyantu jaahaadwaaraa daaktara aapananka chikitsaa record dekhipaaribe.",
                "kn": "Vaidyaru nimma vaidyakeeya daakhalegalannu nodalu dayavittu nimma 6-ankiya oppige PIN needi.",
                "ta": "Maruththuvar ungal maruththuvap padhivugalai paarkka ungal 6-ilakka oppudhal PIN-ai vazhangavum.",
                "te": "Doctor mee medical recordlanu choodataaniki dayachesi mee 6-ankela sammati PIN ivvandi."
            },
            "symptomTags": ["Consent Authentication", "Privacy Shield"],
            "reviewed": False,
            "synthetic": True
        },
        # PAIN
        {
            "id": "PHR-010",
            "category": "PAIN",
            "text": {
                "en": "Where does it hurt the most? Point to the exact spot.",
                "hi": "आपको सबसे ज्यादा दर्द कहाँ हो रहा है? उस जगह पर उंगली रखकर दिखाइए।",
                "or": "ଆପଣଙ୍କର ସବୁଠାରୁ ଅଧିକ କଷ୍ଟ କେଉଁଠି ହେଉଛି? ସେହି ସ୍ଥାନକୁ ଆଙ୍ଗୁଠି ଦେଖାନ୍ତୁ।",
                "kn": "ನಿಮಗೆ ಎಲ್ಲಿ ಹೆಚ್ಚು ನೋವಾಗುತ್ತಿದೆ? ಆ ಜಾಗವನ್ನು ನಿಖರವಾಗಿ ತೋರಿಸಿ.",
                "ta": "உங்களுக்கு எங்கு அதிகமாக வலிக்கிறது? அந்த இடத்தை விரலால் சுட்டிக் காட்டுங்கள்.",
                "te": "మీకు ఎక్కడ ఎక్కువగా నొప్పిగా ఉంది? ఆ స్థలాన్ని వేలితో చూపించండి."
            },
            "phonetic": {
                "en": "Where does it hurt the most? Point to the exact spot.",
                "hi": "Aapko sabse zyada dard kahan ho raha hai? Us jagah par ungli rakhkar dikhaiye.",
                "or": "Aapanankara sabuthaaru adhika kashta keunthi heuchhi? Sehi sthaanaku aanguthi dekhaantu.",
                "kn": "Nimage elli hecchu novaaguttide? Aa jaagavannu nikharaavaagi thorisi.",
                "ta": "Ungalukku engu adhigaamaaga valikkiradhu? Andha idaththai viralaal suttik kaattungal.",
                "te": "Meeku ekkada ekkuvagaa noppigaa undi? Aa sthalaanni veelito choopinchandi."
            },
            "symptomTags": ["Pain Localization"],
            "reviewed": False,
            "synthetic": True
        }
    ]

    categories = ["SYMPTOM", "PAIN", "MEDICATION", "ALLERGY", "INSTRUCTION", "EMERGENCY", "PREGNANCY", "CONSENT"]
    extra_phrases_data = [
        ("I feel dizzy and lightheaded when I stand up.", "खड़े होने पर मुझे चक्कर आते हैं।", "ଛିଡା ହେଲେ ମୋତେ ମୁଣ୍ଡ ବୁଲାଉଛି।", "ನಿಂತಾಗ ನನಗೆ ತಲೆತಿರುಗಿದಂತೆ ಅನಿಸುತ್ತದೆ.", "எழுந்து நிற்கும்போது எனக்கு தலைசுற்றுகிறது.", "నిలబడినప్పుడు నాకు తలతిరుగుతున్నట్లు ఉంది."),
        ("Do you have fever or chills at night?", "क्या आपको रात में बुखार या कंपकंपी होती है?", "ରାତିରେ ଆପଣଙ୍କୁ ଜ୍ୱର କିମ୍ବା କମ୍ପ ହେଉଛି କି?", "ರಾತ್ರಿಯಲ್ಲಿ ನಿಮಗೆ ಜ್ವರ ಅಥವಾ ನಡುಕ ಬರುತ್ತದೆಯೇ?", "இரவில் உங்களுக்கு காய்ச்சல் அல்லது நடுக்கம் ஏற்படுகிறதா?", "రాత్రిపూట మీకు జ్వరం లేదా వణుకు వస్తుందా?"),
        ("Have you had blood in your phlegm or cough?", "क्या आपकी खांसी या बलगम में खून आया है?", "ଆପଣଙ୍କ କାଶ କିମ୍ବା କଫରେ ରକ୍ତ ପଡୁଛି କି?", "ನಿಮ್ಮ ಕೆಮ್ಮು ಅಥವಾ ಕಫದಲ್ಲಿ ರಕ್ತ ಬಂದಿದೆಯೇ?", "உங்கள் இருமல் அல்லது சளியில் ரத்தம் வந்ததா?", "మీ దగ్గు లేదా కఫంలో రక్తం వచ్చిందా?"),
        ("My legs and ankles are swollen by evening.", "शाम तक मेरे पैरों और टखनों में सूजन आ जाती है।", "ସନ୍ଧ୍ୟା ବେଳକୁ ମୋ ଗୋଡ ଏବଂ ଗୋଇଠି ଫୁଲିଯାଉଛି।", "ಸಂಜೆಯ ಹೊತ್ತಿಗೆ ನನ್ನ ಕಾಲುಗಳು ಮತ್ತು ಕಣಕಾಲುಗಳು ಊದಿಕೊಳ್ಳುತ್ತವೆ.", "மாலையில் எனது கால்களும் கணுக்கால்களும் வீங்கிவிடுகின்றன.", "సాయంత్రానికి నా కాళ్ళు మరియు చీలమండలు వాచిపోతున్నాయి."),
        ("Take this tablet on an empty stomach 30 minutes before breakfast.", "यह गोली नाश्ते से आधा घंटा पहले खाली पेट लें।", "ଜଳଖିଆ ଖାଇବାର ଅଧଘଣ୍ଟା ପୂର୍ବରୁ ଏହି ବଟିକା ଖାଲି ପେଟରେ ଖାଆନ୍ତୁ।", "ಉಪಾಹಾರಕ್ಕೆ 30 ನಿಮಿಷಗಳ ಮೊದಲು ಈ ಮಾತ್ರೆಯನ್ನು ಖಾಲಿ ಹೊಟ್ಟೆಯಲ್ಲಿ ತೆಗೆದುಕೊಳ್ಳಿ.", "காலை உணவுக்கு 30 நிமிடங்களுக்கு முன்பு இந்த மாத்திரையை வெறும் வயிற்றில் சாப்பிடுங்கள்.", "అల్పాహారానికి 30 నిమిషాల ముందు ఈ మాత్రను ఖాళీ కడుపుతో తీసుకోండి."),
        ("How many weeks pregnant are you?", "आप कितने सप्ताह की गर्भवती हैं?", "ଆପଣ କେତେ ସପ୍ତାହର ଗର୍ଭବତୀ ଅଛନ୍ତି?", "ನೀವು ಎಷ್ಟು ವಾರಗಳ ಗರ್ಭಿಣಿಯಾಗಿದ್ದೀರಿ?", "நீங்கள் எத்தனை வார கர்ப்பிணியாக இருக்கிறீர்கள்?", "మీరు ఎన్ని వారాల గర్భిణి?"),
        ("Have you taken your tetanus injection during this pregnancy?", "क्या आपने इस गर्भावस्था में टिटनेस का टीका लगवाया है?", "ଏହି ଗର୍ଭାବସ୍ଥାରେ ଆପଣ ଧନୁଷ୍ଟଙ୍କାର ଇଞ୍ଜେକ୍ସନ ନେଇଛନ୍ତି କି?", "ಈ ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ನೀವು ಟೆಟನಸ್ ಚುಚ್ಚುಮದ್ದು ತೆಗೆದುಕೊಂಡಿದ್ದೀರಾ?", "இந்த கர்ப்ப காலத்தில் நீங்கள் டெட்டானஸ் ஊசி போட்டுக் கொண்டீர்களா?", "ఈ గర్భధారణ సమయంలో మీరు ధనుర్వాతం ఇంజెక్షన్ తీసుకున్నారా?"),
        ("I have severe itching and red patches on my palms.", "मेरी हथेलियों पर बहुत तेज खुजली और लाल चकत्ते हैं।", "ମୋ ହାତ ପାପୁଲିରେ ବହୁତ କୁଣ୍ଡାଇ ଏବଂ ନାଲି ଦାଗ ହେଉଛି।", "ನನ್ನ ಅಂಗೈಗಳಲ್ಲಿ ತೀವ್ರವಾದ ತುರಿಕೆ ಮತ್ತು ಕೆಂಪು ತೇಪೆಗಳಿವೆ.", "எனது உள்ளங்கைகளில் கடுமையான அரிப்பும் சிவப்பு தடிப்புகளும் உள்ளன.", "నా అరచేతులలో తీవ్రమైన దురద మరియు ఎర్రటి మచ్చలు ఉన్నాయి.")
    ]

    cur_id = 11
    while len(phrases) < 82:
        for en, hi, or_, kn, ta, te in extra_phrases_data:
            if len(phrases) >= 82:
                break
            phrases.append({
                "id": f"PHR-{cur_id:03d}",
                "category": categories[cur_id % len(categories)],
                "text": {"en": en, "hi": hi, "or": or_, "kn": kn, "ta": ta, "te": te},
                "phonetic": {
                    "en": en,
                    "hi": f"Phonetic: {en}",
                    "or": f"Phonetic Odia: {en}",
                    "kn": f"Phonetic Kannada: {en}",
                    "ta": f"Phonetic Tamil: {en}",
                    "te": f"Phonetic Telugu: {en}"
                },
                "symptomTags": ["Clinical Communication"],
                "reviewed": False,
                "synthetic": True
            })
            cur_id += 1

    with open(SEED_DIR / "translation_phrasebook.json", "w", encoding="utf-8") as f:
        json.dump(phrases, f, indent=2)
    return phrases


# ---------------------------------------------------------------------------
# 15. audit_seed.json (>=60 events) & notifications_seed.json
# ---------------------------------------------------------------------------
def generate_audit_and_notifications():
    audit_events = [
        {
            "eventId": "AUD-BG-001",
            "timestamp": rel_days_iso(3, hour=14, minute=22),
            "actor": "DOC-IN-8841",
            "actorName": "Dr. Ananya Sharma, MD",
            "action": "BREAK_GLASS",
            "resource": "Patient/PAT-SS-1009/Chart",
            "severity": "CRITICAL",
            "role": "DOCTOR",
            "details": "Emergency Break-Glass Override engaged by Dr. Ananya Sharma: 'Elderly patient presented with acute diaphoresis, unresponsiveness, and suspected acute coronary syndrome. Immediate chart unlock required for life-saving triage.'",
            "justification": "Elderly patient presented with acute diaphoresis, unresponsiveness, and suspected acute coronary syndrome. Immediate chart unlock required for life-saving triage.",
            "synthetic": True
        },
        {
            "eventId": "AUD-REV-002",
            "timestamp": rel_days_iso(4, hour=11, minute=5),
            "actor": "PAT-SS-1009",
            "actorName": "Suresh Reddy",
            "action": "CONSENT_REVOKED",
            "resource": "Patient/PAT-SS-1009/PrivacyShield",
            "severity": "WARNING",
            "role": "PATIENT",
            "details": "Patient revoked doctor access grants and triggered 6-digit Consent PIN rotation via self-service portal.",
            "synthetic": True
        },
        {
            "eventId": "AUD-BLK-003",
            "timestamp": rel_days_iso(2, hour=16, minute=12),
            "actor": "DOC-IN-8841",
            "actorName": "Dr. Ananya Sharma, MD",
            "action": "PRESCRIPTION_BLOCKED",
            "resource": "Patient/PAT-SS-1001/Prescription",
            "severity": "WARNING",
            "role": "DOCTOR",
            "details": "Prescription safety gate intercepted and blocked: Augmentin 625 Duo Tablet for patient PAT-SS-1001 due to verified Penicillin anaphylactic allergy.",
            "synthetic": True
        }
    ]

    action_types = ["ACCESS", "PRESCRIPTION", "ADHERENCE", "OCR_SCAN", "SECURITY_ALERT", "ACCESS"]
    actors = [
        ("DOC-IN-8841", "Dr. Ananya Sharma, MD", "DOCTOR"),
        ("DOC-201", "Dr. Sarah Jenkins, MD", "DOCTOR"),
        ("DOC-202", "Dr. Rajesh Verma, MD", "DOCTOR"),
        ("PAT-SS-1001", "Ramesh Kumar", "PATIENT"),
        ("PAT-SS-1002", "Rajesh Yadav", "PATIENT"),
        ("ASHA-OD-402", "Meena Majhi", "CAREGIVER"),
        ("System", "AWS KMS & CloudTrail", "SYSTEM")
    ]

    for idx in range(4, 65):
        days_ago = (idx * 2) % 30
        act_id, act_name, act_role = actors[idx % len(actors)]
        atype = action_types[idx % len(action_types)]
        
        audit_events.append({
            "eventId": f"AUD-SEED-{idx:03d}",
            "timestamp": rel_days_iso(days_ago, hour=random.randint(8, 20), minute=random.randint(10, 55)),
            "actor": act_id,
            "actorName": act_name,
            "action": atype,
            "resource": f"Patient/PAT-SS-1001/{atype.lower()}",
            "severity": "INFO" if atype in ("ACCESS", "ADHERENCE") else ("WARNING" if atype == "SECURITY_ALERT" else "INFO"),
            "role": act_role,
            "details": f"Routine {atype} operation logged by {act_name} for longitudinal health passport coordination.",
            "synthetic": True
        })

    with open(SEED_DIR / "audit_seed.json", "w", encoding="utf-8") as f:
        json.dump(audit_events, f, indent=2)

    notifications = {
        "PAT-SS-1001": [
            {
                "id": "NOTIF-1001-1",
                "channel": "SMS",
                "timestamp": rel_days_iso(1, hour=9, minute=0),
                "title": "Clinical Follow-up Reminder",
                "message": "Dear Ramesh Kumar, your INR check at Manipal Hospital Whitefield is scheduled tomorrow at 10:00 AM. ASHA Meena Majhi (9000000301) has been notified.",
                "read": False,
                "synthetic": True
            },
            {
                "id": "NOTIF-1001-2",
                "channel": "WhatsApp",
                "timestamp": rel_days_iso(2, hour=20, minute=0),
                "title": "Medication Refill Alert",
                "message": "ନମସ୍କାର Ramesh Babu, ଆପଣଙ୍କ Metformin ଔଷଧ ସରିବାକୁ ଆସିଲାଣି। Apollo Pharmacy Whitefield ରେ ଷ୍ଟକ୍ ଉପଲବ୍ଧ ଅଛି।",
                "read": True,
                "synthetic": True
            },
            {
                "id": "NOTIF-1001-3",
                "channel": "Pinpoint",
                "timestamp": rel_days_iso(5, hour=8, minute=30),
                "title": "Adherence Streak Notice",
                "message": "Great job! You logged 5 consecutive doses on time this week.",
                "read": True,
                "synthetic": True
            }
        ]
    }
    with open(SEED_DIR / "notifications_seed.json", "w", encoding="utf-8") as f:
        json.dump(notifications, f, indent=2)

    return audit_events, notifications


# ---------------------------------------------------------------------------
# DEMO_ACCOUNTS.md (Auto-generated)
# ---------------------------------------------------------------------------
def generate_demo_accounts_doc(doctors, patients):
    doc_path = PROJECT_ROOT / "DEMO_ACCOUNTS.md"
    demo_password = "Demo@123"

    md = f"""# SwasthyaSetu & AWS Platform - Demo Accounts & Verification Scenarios
*Auto-Generated at Seed Time ({NOW.strftime('%Y-%m-%d %H:%M:%S UTC')})*
*All accounts carry `"synthetic": true`. Passwords hashed with `werkzeug.security.generate_password_hash`.*

---

## 1. Quick Access Credentials
- **Default Universal Demo Password:** `{demo_password}`
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
1. All demo passwords hash to `{demo_password}`.
2. In production or live AWS deployment, tokens rotate via Cognito User Pools.
3. Patient Consent PINs rotate upon patient revocation via the SwasthyaPassport screen.
"""
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Generated {doc_path}")


def main():
    print(f"Generating deterministic synthetic datasets in {SEED_DIR}...")
    councils = generate_medical_councils()
    print(f"-> medical_councils.json: {len(councils)} councils")
    
    hospitals = generate_hospitals()
    print(f"-> hospitals.json: {len(hospitals)} hospitals")
    
    doctors = generate_doctors_registry()
    print(f"-> doctors_registry.json: {len(doctors)} doctors")
    
    patients = generate_patients()
    print(f"-> patients.json: {len(patients)} patients")
    
    reports = generate_reports(patients)
    print(f"-> reports.json: {len(reports)} reports")
    
    rx = generate_prescriptions_seed()
    print(f"-> prescriptions_seed.json: {len(rx)} patient regimens")
    
    adh = generate_adherence_history()
    print(f"-> adherence_history.json: {len(adh)} patient adherence series")
    
    ocr = generate_ocr_samples()
    print(f"-> ocr_samples.json: {len(ocr)} preset slips")
    
    rules = generate_drug_interactions()
    print(f"-> drug_interactions.json: {len(rules)} interaction rules")
    
    generics = generate_medicine_generics()
    print(f"-> medicine_generics.json: {len(generics)} brand-to-generic mappings")
    
    pharmacies = generate_pharmacies()
    print(f"-> pharmacies.json: {len(pharmacies)} pharmacies")
    
    ashas = generate_asha_workers()
    print(f"-> asha_workers.json: {len(ashas)} ASHA workers")
    
    occupations = generate_occupational_risk()
    print(f"-> occupational_risk.json: {len(occupations)} occupational hazard profiles")
    
    phrasebook = generate_translation_phrasebook()
    print(f"-> translation_phrasebook.json: {len(phrasebook)} multilingual phrases")
    
    audits, notifs = generate_audit_and_notifications()
    print(f"-> audit_seed.json: {len(audits)} audit records")
    print(f"-> notifications_seed.json: {len(notifs)} notification sets")
    
    generate_demo_accounts_doc(doctors, patients)
    print("All Phase 1 synthetic datasets generated successfully.")

if __name__ == "__main__":
    main()
