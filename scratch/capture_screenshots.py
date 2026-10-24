"""
Comprehensive screenshot capture for SwasthyaSetu & AWS Platform.
Captures responsive layouts (360, 768, 1280, 1440) and every key clinical module.
"""
import subprocess
import os
import time

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = r"D:\AWS\docs\screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGETS = [
    # Responsive Login Steppers
    ("login_1440.png", "http://127.0.0.1:5000/login", 1440, 900),
    ("login_1280.png", "http://127.0.0.1:5000/login", 1280, 800),
    ("login_768.png", "http://127.0.0.1:5000/login", 768, 1024),
    ("login_360.png", "http://127.0.0.1:5000/login", 360, 800),

    # Doctor Privacy Shield (Locked)
    ("doctor_locked_1440.png", "http://127.0.0.1:5000/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001", 1440, 900),
    ("doctor_locked_1280.png", "http://127.0.0.1:5000/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001", 1280, 800),
    ("doctor_locked_768.png", "http://127.0.0.1:5000/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001", 768, 1024),

    # Doctor Clinical Modules (Unlocked)
    ("doctor_unlocked_overview_1280.png", "http://127.0.0.1:5000/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001&unlocked=1&section=overview", 1280, 850),
    ("doctor_reports_trends_1280.png", "http://127.0.0.1:5000/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001&unlocked=1&section=reports", 1280, 850),
    ("doctor_prescriptions_1280.png", "http://127.0.0.1:5000/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001&unlocked=1&section=prescriptions", 1280, 850),
    ("doctor_translator_1280.png", "http://127.0.0.1:5000/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001&unlocked=1&section=translator", 1280, 850),
    ("doctor_scanner_1280.png", "http://127.0.0.1:5000/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001&unlocked=1&section=ocr", 1280, 850),
    ("doctor_work_risk_1280.png", "http://127.0.0.1:5000/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001&unlocked=1&section=workrisk", 1280, 850),

    # Patient Mobile Workspace (360px)
    ("patient_home_360.png", "http://127.0.0.1:5000/patient?patient_id=PAT-SS-1001&tab=home", 360, 800),
    ("patient_medicines_360.png", "http://127.0.0.1:5000/patient?patient_id=PAT-SS-1001&tab=medicines", 360, 800),
    ("patient_reports_360.png", "http://127.0.0.1:5000/patient?patient_id=PAT-SS-1001&tab=reports", 360, 800),
    ("patient_passport_360.png", "http://127.0.0.1:5000/patient?patient_id=PAT-SS-1001&tab=passport", 360, 800),
    ("patient_pharmacy_360.png", "http://127.0.0.1:5000/patient?patient_id=PAT-SS-1001&tab=pharmacy", 360, 800),
    ("patient_alerts_360.png", "http://127.0.0.1:5000/patient?patient_id=PAT-SS-1001&tab=alerts", 360, 800),

    # Patient Responsive Views
    ("patient_home_768.png", "http://127.0.0.1:5000/patient?patient_id=PAT-SS-1001", 768, 1024),
    ("patient_home_1280.png", "http://127.0.0.1:5000/patient?patient_id=PAT-SS-1001", 1280, 800),
    ("patient_home_1440.png", "http://127.0.0.1:5000/patient?patient_id=PAT-SS-1001", 1440, 900),

    # Compliance & Architecture
    ("audit_stream_1280.png", "http://127.0.0.1:5000/audit", 1280, 850),
    ("pharmacy_locator_1280.png", "http://127.0.0.1:5000/pharmacy?patient_id=PAT-SS-1001", 1280, 850),
    ("platform_hub_1280.png", "http://127.0.0.1:5000/", 1280, 850)
]

print(f"Capturing {len(TARGETS)} screenshots into {OUTPUT_DIR}...")
for fname, url, width, height in TARGETS:
    out_path = os.path.join(OUTPUT_DIR, fname)
    args = [
        CHROME_PATH,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        f"--window-size={width},{height}",
        f"--screenshot={out_path}",
        url
    ]
    res = subprocess.run(args, capture_output=True)
    if os.path.exists(out_path):
        size = os.path.getsize(out_path)
        print(f"  [OK] {fname} ({width}x{height}) -> {size} bytes")
    else:
        print(f"  [FAIL] {fname} ({width}x{height})")

print("All screenshots captured successfully.")
