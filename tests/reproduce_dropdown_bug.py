#!/usr/bin/env python3
"""
tests/reproduce_dropdown_bug.py
Step 1 of Task 1:
Reproduce the medicine search dropdown bug BEFORE any code fixes.
Log in / unlock PAT-SS-1001 as doctor DOC-IN-8841.
Open Add medicine (Prescriptions section), type "aug",
and capture screenshots at 1280px and 360px.
"""

import sys
import os
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SCREENSHOT_DIR = ROOT_DIR / "docs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

from backend_lambdas.aws_core import get_patient, save_patient, local_store
from backend_lambdas.auth_security_engine import lock_doctor_session

def get_live_pin(patient_id="PAT-SS-1001"):
    local_store.reload()
    p = get_patient("PAT-1001") or get_patient(patient_id)
    if not p:
        raise ValueError(f"Patient {patient_id} not found in store")
    pin = p.get("consentPin") or p.get("activeConsentPin") or "482910"
    return str(pin).strip()

def unlock_page(page, live_pin):
    # Check if already unlocked on server
    is_already_unlocked = page.evaluate("""() => {
        const ov = document.getElementById('section-overview');
        return ov && !ov.classList.contains('hidden');
    }""")
    if is_already_unlocked:
        print("  -> Page is already unlocked!")
        page.evaluate("isPatientUnlocked = true;")
        return

    # Wait for either the resume container or the pin container to become visible
    page.wait_for_selector("#resume-grant-container:not(.hidden), #doctor-pin-container", timeout=6000)
    if page.is_visible("#resume-grant-container:not(.hidden)"):
        print("  -> Found Resume Grant button, clicking...")
        page.locator("#btn-resume-record").click()
    else:
        print("  -> Entering 6-digit PIN...")
        pin_inputs = page.query_selector_all("#doctor-pin-container .pin-digit-box")
        for i in range(6):
            pin_inputs[i].fill(live_pin[i])
    page.wait_for_selector("#section-overview:not(.hidden)", timeout=8000)
    page.evaluate("isPatientUnlocked = true;")

def run_reproduce():
    print("=" * 65)
    print("TASK 1 STEP 1: REPRODUCING MEDICINE DROPDOWN BUG")
    print("=" * 65)

    base_url = "http://127.0.0.1:5000"

    # Reset patient consent
    p_obj = get_patient("PAT-1001")
    if p_obj:
        p_obj["consentRevoked"] = False
        save_patient(p_obj)

    lock_doctor_session("DOC-IN-8841", "PAT-1001")
    lock_doctor_session("DOC-201", "PAT-1001")
    lock_doctor_session("DOC-IN-8841", "PAT-SS-1001")
    lock_doctor_session("DOC-201", "PAT-SS-1001")
    local_store.reload()

    live_pin = get_live_pin("PAT-SS-1001")
    print(f"[*] Live PIN for PAT-SS-1001: {live_pin}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # -------------------------------------------------------------
        # Part A: Desktop 1280x800
        # -------------------------------------------------------------
        context_1280 = browser.new_context(viewport={"width": 1280, "height": 800})
        page_1280 = context_1280.new_page()

        page_1280.add_init_script("localStorage.removeItem('medcoord_unlocked_patient');")
        doc_url = f"{base_url}/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001"
        page_1280.goto(doc_url, wait_until="networkidle")

        unlock_page(page_1280, live_pin)
        print("[*] Unlocked doctor workspace at 1280px.")

        # Switch to Prescriptions section
        page_1280.evaluate("switchDoctorSection('prescriptions')")
        page_1280.wait_for_selector("#section-prescriptions:not(.hidden)", timeout=5000)

        # Type 'aug' in search
        med_input = page_1280.locator("#prescribe-med-input")
        med_input.click()
        med_input.fill("")
        med_input.type("aug", delay=100)

        # Wait for results box
        page_1280.wait_for_selector("#med-search-results:not(.hidden)", timeout=6000)
        page_1280.wait_for_timeout(600)

        shot_1280 = SCREENSHOT_DIR / "dropdown_reproduce_1280.png"
        page_1280.screenshot(path=str(shot_1280))
        print(f"[SCREENSHOT] Saved 1280px reproduction: {shot_1280}")

        # -------------------------------------------------------------
        # Part B: Mobile 360x740
        # -------------------------------------------------------------
        context_360 = browser.new_context(viewport={"width": 360, "height": 740})
        page_360 = context_360.new_page()

        page_360.goto(doc_url, wait_until="networkidle")
        unlock_page(page_360, live_pin)
        print("[*] Unlocked doctor workspace at 360px.")

        # Switch to Prescriptions section via evaluate
        page_360.evaluate("switchDoctorSection('prescriptions')")
        page_360.wait_for_selector("#section-prescriptions:not(.hidden)", timeout=5000)

        # Scroll to input
        med_input_360 = page_360.locator("#prescribe-med-input")
        med_input_360.scroll_into_view_if_needed()
        med_input_360.click()
        med_input_360.fill("")
        med_input_360.type("aug", delay=100)

        page_360.wait_for_selector("#med-search-results:not(.hidden)", timeout=6000)
        page_360.wait_for_timeout(600)

        shot_360 = SCREENSHOT_DIR / "dropdown_reproduce_360.png"
        page_360.screenshot(path=str(shot_360))
        print(f"[SCREENSHOT] Saved 360px reproduction: {shot_360}")

        # Capture inspect details
        details_1280 = page_1280.evaluate("""() => {
            const input = document.getElementById('prescribe-med-input');
            const res = document.getElementById('med-search-results');
            const inRect = input.getBoundingClientRect();
            const resRect = res.getBoundingClientRect();
            return {
                inputRect: inRect,
                resultsRect: resRect,
                resultsContent: res.innerHTML,
                resultsParentClass: res.parentElement.className
            };
        }""")
        print("[*] 1280px Dropdown DOM details:", details_1280)

        details_360 = page_360.evaluate("""() => {
            const input = document.getElementById('prescribe-med-input');
            const res = document.getElementById('med-search-results');
            const inRect = input.getBoundingClientRect();
            const resRect = res.getBoundingClientRect();
            return {
                inputRect: inRect,
                resultsRect: resRect,
                resultsContent: res.innerHTML,
                resultsParentClass: res.parentElement.className
            };
        }""")
        print("[*] 360px Dropdown DOM details:", details_360)

        context_1280.close()
        context_360.close()
        browser.close()

    print("\n" + "=" * 65)
    print("STEP 1 REPRODUCTION COMPLETE!")
    print("=" * 65)

if __name__ == "__main__":
    run_reproduce()
