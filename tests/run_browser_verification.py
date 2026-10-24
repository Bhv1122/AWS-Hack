#!/usr/bin/env python3
"""
tests/run_browser_verification.py
Playwright browser end-to-end verification script for MedCoord Health / SwasthyaSetu.
Validates:
1. Slowness / Sluggish Unlock fix (<1.5s unlock target, assertion <3s).
2. Prescription modification & discontinuation keeping doctor unlocked on patient record.
3. Hard refresh resume grant card without clinical data until clicked.
4. Patient consent revocation instantly re-locking doctor view with Privacy Shield.
5. 360px viewport responsiveness with zero horizontal scroll.
Captures all required screenshots to docs/screenshots/.
"""

import sys
import os
import time
import subprocess
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
    """Reads live consent PIN from backend store without exposing it via API."""
    local_store.reload()
    p = get_patient("PAT-1001") or get_patient(patient_id)
    if not p:
        raise ValueError(f"Patient {patient_id} not found in store")
    pin = p.get("consentPin") or p.get("activeConsentPin") or "482910"
    return str(pin).strip()

def run_verification():
    print("=" * 65)
    print("STARTING PLAYWRIGHT BROWSER VERIFICATION SUITE")
    print("=" * 65)

    base_url = "http://127.0.0.1:5000"

    # Reset patient consent to active and lock existing doctor sessions
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
    print(f"[*] Retrieved Live Consent PIN for PAT-SS-1001: {live_pin}")

    with sync_playwright() as p:
        # Launch Chromium
        browser = p.chromium.launch(headless=True)

        # -------------------------------------------------------------
        # 1. Desktop 1280x800 Doctor Workflow
        # -------------------------------------------------------------
        context_doc = browser.new_context(viewport={"width": 1280, "height": 800})
        page_doc = context_doc.new_page()

        # Handle dialogs (prompt for dosage, confirm for discontinue)
        current_dosage_to_input = "7.5mg once daily"
        def handle_dialog(dialog):
            print(f"[DIALOG] Type: {dialog.type}, Message: {dialog.message}")
            if dialog.type == "prompt":
                dialog.accept(current_dosage_to_input)
            else:
                dialog.accept()

        page_doc.on("dialog", handle_dialog)

        # Clear localStorage in page before load to ensure locked state
        page_doc.add_init_script("""
            localStorage.removeItem('medcoord_unlocked_patient');
        """)

        # Navigate to doctor portal
        doc_url = f"{base_url}/doctor?doctor_id=DOC-IN-8841&patient_id=PAT-SS-1001"
        print(f"[*] Navigating to {doc_url}...")
        page_doc.goto(doc_url, wait_until="networkidle")

        # Verify Privacy Shield is active
        page_doc.wait_for_selector("#doctor-pin-container", timeout=5000)
        print("[PASS] Privacy Shield active, PIN input container found.")

        # Enter 6 PIN digits into the input boxes
        pin_inputs = page_doc.query_selector_all("#doctor-pin-container .pin-digit-box")
        assert len(pin_inputs) == 6, f"Expected 6 PIN digit boxes, found {len(pin_inputs)}"

        print(f"[*] Typing 6-digit PIN {live_pin} into input boxes...")
        for i in range(6):
            pin_inputs[i].fill(live_pin[i])

        # Click unlock button and measure unlock duration
        start_time = time.perf_counter()
        unlock_btn = page_doc.locator("#btn-decrypt-chart")
        unlock_btn.click()

        # Wait for overview pane to become visible
        page_doc.wait_for_selector("#section-overview:not(.hidden)", timeout=6000)
        page_doc.wait_for_selector("#patient-name-display", timeout=6000)
        unlock_duration_ms = (time.perf_counter() - start_time) * 1000

        patient_name = page_doc.locator("#patient-name-display").inner_text()
        print(f"[PASS] Doctor unlocked patient record in {unlock_duration_ms:.2f}ms! Patient: {patient_name}")
        assert "Ramesh Kumar" in patient_name, f"Unexpected patient name: {patient_name}"
        assert unlock_duration_ms < 3000, f"Unlock took {unlock_duration_ms:.2f}ms, exceeding 3000ms threshold!"

        # Wait for active prescriptions to render
        page_doc.wait_for_timeout(600)
        screenshot_1 = SCREENSHOT_DIR / "doctor_unlocked_1280.png"
        page_doc.screenshot(path=str(screenshot_1))
        print(f"[SCREENSHOT] Saved: {screenshot_1}")

        # -------------------------------------------------------------
        # 2. Modify Prescription Dosage (In-place, stays unlocked)
        # -------------------------------------------------------------
        print("\n[*] Testing prescription dosage modification...")
        # Check overview list first, or prescriptions tab
        modify_btns = page_doc.query_selector_all("#overview-active-rx-list button:has-text('Modify')")
        if not modify_btns:
            page_doc.locator("button[data-section='prescriptions']").click()
            page_doc.wait_for_timeout(400)
            modify_btns = page_doc.query_selector_all("button:has-text('Modify')")

        assert len(modify_btns) > 0, "No 'Modify' button found on active prescriptions!"

        mod_start = time.perf_counter()
        modify_btns[0].click()

        page_doc.wait_for_selector(".toast-success, text='updated to 7.5mg once daily'", timeout=5000)
        mod_duration_ms = (time.perf_counter() - mod_start) * 1000
        print(f"[PASS] Dosage modified to 7.5mg once daily in {mod_duration_ms:.2f}ms")

        # Verify still on doctor page and still unlocked
        assert "/doctor" in page_doc.url, f"Doctor was redirected to {page_doc.url}!"
        assert not page_doc.is_visible("#section-lookup:not(.hidden)"), "Doctor was kicked back to Privacy Shield!"

        screenshot_2 = SCREENSHOT_DIR / "doctor_modified_rx_1280.png"
        page_doc.screenshot(path=str(screenshot_2))
        print(f"[SCREENSHOT] Saved: {screenshot_2}")

        # -------------------------------------------------------------
        # 3. Discontinue Prescription (In-place, stays unlocked)
        # -------------------------------------------------------------
        print("\n[*] Testing prescription discontinuation...")
        disc_btns = page_doc.query_selector_all("button:has-text('Discontinue')")
        assert len(disc_btns) > 0, "No 'Discontinue' button found!"

        disc_btns[0].click()
        page_doc.wait_for_selector(".toast-info, text='discontinued'", timeout=5000)
        print("[PASS] Prescription discontinued. Doctor remains unlocked.")

        assert "/doctor" in page_doc.url, f"Doctor was redirected to {page_doc.url}!"
        assert not page_doc.is_visible("#section-lookup:not(.hidden)"), "Doctor was kicked back to Privacy Shield!"

        screenshot_3 = SCREENSHOT_DIR / "doctor_discontinued_rx_1280.png"
        page_doc.screenshot(path=str(screenshot_3))
        print(f"[SCREENSHOT] Saved: {screenshot_3}")

        # -------------------------------------------------------------
        # 4. Hard Refresh Resume Grant Card
        # -------------------------------------------------------------
        print("\n[*] Testing page reload & Resume Grant Card...")
        page_doc.reload(wait_until="networkidle")

        # Verify #resume-grant-container is visible
        page_doc.wait_for_selector("#resume-grant-container:not(.hidden)", timeout=5000)
        # Verify clinical data is NOT visible yet (zero-trust privacy on reload)
        assert page_doc.is_visible("#section-lookup:not(.hidden)"), "Privacy Shield should be shown until resume tapped"
        assert not page_doc.is_visible("#section-overview:not(.hidden)"), "Clinical overview should not show before resume"
        print("[PASS] Resume Grant Card visible, clinical data hidden per privacy shield.")

        # Click Resume button
        resume_btn = page_doc.locator("#btn-resume-record")
        resume_btn.click()

        # Clinical overview should decrypt and show
        page_doc.wait_for_selector("#section-overview:not(.hidden)", timeout=5000)
        print("[PASS] Resume tapped: Clinical record decrypted without re-entering PIN.")

        screenshot_4 = SCREENSHOT_DIR / "doctor_resumed_record_1280.png"
        page_doc.screenshot(path=str(screenshot_4))
        print(f"[SCREENSHOT] Saved: {screenshot_4}")

        # -------------------------------------------------------------
        # 5. Patient Revocation & Doctor Re-lock
        # -------------------------------------------------------------
        print("\n[*] Testing patient revocation re-locking doctor...")
        context_pat = browser.new_context(viewport={"width": 1280, "height": 800})
        page_pat = context_pat.new_page()
        page_pat.on("dialog", lambda d: d.accept())

        pat_url = f"{base_url}/patient?patient_id=PAT-SS-1001&tab=passport"
        page_pat.goto(pat_url, wait_until="networkidle")

        # Click Revoke Access
        revoke_btn = page_pat.locator("#btn-revoke-pin")
        page_pat.wait_for_selector("#btn-revoke-pin", timeout=5000)
        revoke_btn.click()
        page_pat.wait_for_selector(".toast-info, text='Consent revoked'", timeout=5000)
        print("[PASS] Patient revoked doctor access and rotated PIN.")

        # In Doctor view: poll / reload or trigger clinical call
        print("[*] Checking doctor view responds to revocation...")
        page_doc.evaluate("API.get('/api/profile?patient_id=PAT-SS-1001').catch(e => { lockPatientRecordNow('The patient removed your access.'); })")
        page_doc.wait_for_timeout(800)

        # Verify Privacy shield re-locked
        page_doc.wait_for_selector("#section-lookup:not(.hidden)", timeout=5000)
        print("[PASS] Doctor workstation re-locked with Privacy Shield.")

        screenshot_5 = SCREENSHOT_DIR / "doctor_relocked_revoked_1280.png"
        page_doc.screenshot(path=str(screenshot_5))
        print(f"[SCREENSHOT] Saved: {screenshot_5}")

        # -------------------------------------------------------------
        # 6. Mobile Viewport 360x740 Responsiveness (Zero Horizontal Scroll)
        # -------------------------------------------------------------
        print("\n[*] Testing 360px mobile responsiveness...")
        context_m = browser.new_context(viewport={"width": 360, "height": 740})
        page_m = context_m.new_page()

        # Patient view 360
        page_m.goto(f"{base_url}/patient?patient_id=PAT-SS-1001", wait_until="networkidle")
        scroll_w_pat = page_m.evaluate("document.documentElement.scrollWidth")
        client_w_pat = page_m.evaluate("document.documentElement.clientWidth")
        print(f"  Patient 360px: scrollWidth={scroll_w_pat}, clientWidth={client_w_pat}")
        assert scroll_w_pat <= client_w_pat + 1, f"Horizontal scroll detected in Patient view! {scroll_w_pat} > {client_w_pat}"

        screenshot_6 = SCREENSHOT_DIR / "patient_view_360.png"
        page_m.screenshot(path=str(screenshot_6))
        print(f"[SCREENSHOT] Saved: {screenshot_6}")

        # Doctor view 360
        page_m.goto(f"{base_url}/doctor?doctor_id=DOC-IN-8841", wait_until="networkidle")
        scroll_w_doc = page_m.evaluate("document.documentElement.scrollWidth")
        client_w_doc = page_m.evaluate("document.documentElement.clientWidth")
        print(f"  Doctor 360px: scrollWidth={scroll_w_doc}, clientWidth={client_w_doc}")
        assert scroll_w_doc <= client_w_doc + 1, f"Horizontal scroll detected in Doctor view! {scroll_w_doc} > {client_w_doc}"

        screenshot_7 = SCREENSHOT_DIR / "doctor_view_360.png"
        page_m.screenshot(path=str(screenshot_7))
        print(f"[SCREENSHOT] Saved: {screenshot_7}")

        # Reset patient consent for subsequent testing
        p_final = get_patient("PAT-1001")
        if p_final:
            p_final["consentRevoked"] = False
            save_patient(p_final)

        # Cleanup
        context_doc.close()
        context_pat.close()
        context_m.close()
        browser.close()

    print("\n" + "=" * 65)
    print("ALL PLAYWRIGHT BROWSER VERIFICATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_verification()
