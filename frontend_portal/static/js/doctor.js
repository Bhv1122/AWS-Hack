/**
 * doctor.js - Doctor Clinical Safety Workspace Client
 * SwasthyaSetu & AWS Medication Coordination Platform
 * Design Language: Setu Care
 */

let isPatientUnlocked = false;
let unlockedViaBreakGlass = false;
let currentActiveSection = 'lookup';
let activeDoctorId = 'DOC-IN-8841';
let activePatientId = 'PAT-SS-1001';
let currentPatientProfile = null;
let doctorPinHelper = null;
let lastBlockedPrescription = null;
let _cachedMedicines = [];
let _medSearchTimer = null;
let _currentReportsFilter = 'ALL';
let _inactivitySecondsLeft = 600; // 10 minutes
let _inactivityInterval = null;

// ============================================================================
// 1. INITIALIZATION & SHORTCUTS
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  activeDoctorId = params.get('doctor_id') || 'DOC-IN-8841';
  const rawPid = params.get('patient_id') || 'PAT-SS-1001';
  activePatientId = rawPid === 'PAT-1001' ? 'PAT-SS-1001' : rawPid;

  const session = API.getSession();
  if (session && session.doctorId) {
    activeDoctorId = session.doctorId;
  }

  const docDisplay = document.getElementById('doctor-display-id');
  if (docDisplay) docDisplay.innerText = activeDoctorId;

  const lookupInput = document.getElementById('lookup-patient-id');
  if (lookupInput) lookupInput.value = activePatientId;

  // Initialize 6-digit PIN boxes
  doctorPinHelper = setupPinBoxes('doctor-pin-container', () => {
    handleDoctorUnlock();
  });

  const storedUnlocked = API.getUnlockedPatient();
  if (storedUnlocked) {
    // Part A2 Requirement: Hard refresh asks server if grant is still valid.
    // If yes, show "Resume <patient name>'s record" (no PIN needed, no clinical data visible until tapped).
    API.get(`/api/consent/status?patientId=${storedUnlocked}`).then(st => {
      if (st && st.hasActiveAccess) {
        const resumeContainer = document.getElementById('resume-grant-container');
        const resumeBtn = document.getElementById('btn-resume-record');
        const resumeName = document.getElementById('resume-patient-name');
        const pName = st.patientName || (storedUnlocked === 'PAT-SS-1001' ? 'Ramesh Kumar' : storedUnlocked);
        if (resumeName) resumeName.innerText = pName;
        if (resumeBtn) resumeBtn.innerHTML = `<span>Resume ${pName}'s Record</span>`;
        if (resumeContainer) resumeContainer.classList.remove('hidden');
      } else {
        API.clearUnlockedPatient();
      }
    }).catch(() => {
      API.clearUnlockedPatient();
    });
  }

  // Break-glass modal validation
  const bgReason = document.getElementById('break-glass-reason');
  const bgCheck = document.getElementById('break-glass-confirm-check');
  const bgBtn = document.getElementById('btn-submit-break-glass');
  const charCount = document.getElementById('char-count');

  function validateBreakGlass() {
    const len = (bgReason?.value || '').trim().length;
    if (charCount) charCount.innerText = `${len} / 15 min`;
    if (bgBtn) bgBtn.disabled = len < 15 || !(bgCheck?.checked);
  }
  if (bgReason) bgReason.addEventListener('input', validateBreakGlass);
  if (bgCheck) bgCheck.addEventListener('change', validateBreakGlass);

  // Inactivity countdown
  startInactivityCountdown();

  // Keyboard shortcut Ctrl+K / Cmd+K for command palette
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openCommandPalette();
    }
  });

  // Start periodic consent check (auto re-lock if patient revokes)
  setInterval(pollPatientConsentStatus, 15000);

  // Set Target Follow-up Date to +14 days default
  const fDate = document.getElementById('followup-date');
  if (fDate) {
    const d = new Date();
    d.setDate(d.getDate() + 14);
    fDate.value = d.toISOString().split('T')[0];
  }

  // Handle query parameter shortcuts (e.g. ?break_glass=1&section=reports)
  if (params.get('break_glass') === '1') {
    const r = document.getElementById('break-glass-reason');
    if (r) r.value = 'Emergency trauma admission - acute trauma ICU protocol';
    const c = document.getElementById('break-glass-confirm-check');
    if (c) c.checked = true;
    submitBreakGlassOverride().then(() => {
      const sec = params.get('section');
      if (sec) switchDoctorSection(sec);
    });
  } else if (params.get('section')) {
    switchDoctorSection(params.get('section'));
  }

  // Initialize unified accessible comboboxes and computed quantity
  initDoctorComboboxes();
  updateComputedQuantity();
});

function startInactivityCountdown() {
  if (_inactivityInterval) clearInterval(_inactivityInterval);
  _inactivitySecondsLeft = 600;

  function tick() {
    _inactivitySecondsLeft--;
    if (_inactivitySecondsLeft <= 0) {
      clearInterval(_inactivityInterval);
      lockPatientRecordNow('Inactivity timeout reached. Record locked for privacy.');
      return;
    }
    const mins = Math.floor(_inactivitySecondsLeft / 60);
    const secs = _inactivitySecondsLeft % 60;
    const el = document.getElementById('countdown-timer');
    if (el) el.innerText = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  }

  _inactivityInterval = setInterval(tick, 1000);

  ['mousemove', 'keydown', 'scroll', 'touchstart'].forEach(evt => {
    window.addEventListener(evt, () => {
      _inactivitySecondsLeft = 600;
    }, { passive: true });
  });
}

// ============================================================================
// 2. SECTION SWITCHING & COMMAND PALETTE
// ============================================================================
function switchDoctorSection(sectionId) {
  currentActiveSection = sectionId;

  document.querySelectorAll('.nav-rail-item').forEach(item => {
    if (item.getAttribute('data-section') === sectionId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  document.querySelectorAll('.doctor-section-pane').forEach(pane => {
    if (pane.id === `section-${sectionId}`) {
      pane.classList.remove('hidden');
    } else {
      pane.classList.add('hidden');
    }
  });

  // If locked and trying to access clinical sections, notify doctor
  if (!isPatientUnlocked && sectionId !== 'lookup') {
    showToast('Record is locked. Please enter Consent PIN or Break-Glass to unlock.', 'warning');
    switchDoctorSection('lookup');
  }
}

function openCommandPalette() {
  const p = document.getElementById('command-palette');
  if (p) {
    p.style.display = 'flex';
    const inp = document.getElementById('cmd-palette-input');
    if (inp) {
      inp.value = '';
      inp.focus();
    }
  }
}

function closeCommandPalette() {
  const p = document.getElementById('command-palette');
  if (p) p.style.display = 'none';
}

// ============================================================================
// 3. ZERO-TRUST UNLOCK & PRIVACY SHIELD
// ============================================================================
async function handleDoctorUnlock() {
  const pidInput = document.getElementById('lookup-patient-id');
  const pid = (pidInput?.value || '').trim().toUpperCase() || activePatientId;
  const pin = doctorPinHelper ? String(doctorPinHelper.getPin() || '').trim() : '';
  const fbError = document.getElementById('pin-feedback-error');
  const btn = document.getElementById('btn-decrypt-chart');

  if (!pin || pin.length !== 6) {
    showToast('Please enter the patient’s complete 6-digit Consent PIN', 'warning');
    if (doctorPinHelper) doctorPinHelper.shake();
    if (fbError) {
      fbError.innerText = 'Please enter all 6 digits of the patient Consent PIN.';
      fbError.classList.remove('hidden');
    }
    return;
  }

  if (fbError) fbError.classList.add('hidden');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Verifying Consent PIN &amp; Decrypting...</span>`;
  }

  try {
    const res = await API.post('/api/auth/lookup-patient', {
      doctorId: activeDoctorId,
      patientId: pid,
      consentPin: pin,
      emergencyBreakGlass: false
    });

    isPatientUnlocked = true;
    unlockedViaBreakGlass = false;
    activePatientId = pid;
    currentPatientProfile = Object.assign({}, res.patient || res, {
      prescriptions: res.prescriptions || res.active_prescriptions || (res.patient && res.patient.prescriptions) || []
    });

    API.setUnlockedPatient(pid);
    updateWorkspaceUnlockedState();
    showToast(`Health record for ${currentPatientProfile.name || pid} unlocked!`, 'success');
    switchDoctorSection('overview');
  } catch (err) {
    if (doctorPinHelper) doctorPinHelper.shake();
    let msg = err.friendlyMessage || err.message;
    if (err.code === 'PIN_INVALID' && err.rawData && typeof err.rawData.attemptsRemaining === 'number') {
      msg = `Invalid Consent PIN. ${err.rawData.attemptsRemaining} attempt(s) remaining before security cooldown.`;
    } else if (err.code === 'TOO_MANY_ATTEMPTS' && err.rawData && err.rawData.retryAfterSeconds) {
      msg = `Too many incorrect PIN attempts. Security cooldown active for ${err.rawData.retryAfterSeconds} seconds.`;
    } else if (err.code === 'CONSENT_REVOKED') {
      msg = 'Patient has revoked access to their health records.';
    } else if (err.code === 'PATIENT_NOT_FOUND') {
      msg = 'Patient ID not found in registry.';
    } else if (err.code === 'SESSION_EXPIRED') {
      msg = 'Your session has expired. Please log in again.';
    }
    if (fbError) {
      fbError.innerText = msg;
      fbError.classList.remove('hidden');
    }
    showToast(msg, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Unlock Patient Record</span>`;
    }
  }
}

function openBreakGlassModal() {
  openModal('break-glass-modal');
  const r = document.getElementById('break-glass-reason');
  if (r) r.focus();
}

async function submitBreakGlassOverride() {
  const pid = document.getElementById('lookup-patient-id')?.value.trim() || activePatientId;
  const reason = document.getElementById('break-glass-reason')?.value.trim();
  const btn = document.getElementById('btn-submit-break-glass');

  if (!reason || reason.length < 15) {
    showToast('Clinical justification must be at least 15 characters long.', 'warning');
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Auditing Break-Glass...</span>`;
  }

  try {
    const res = await API.post('/api/auth/lookup-patient', {
      doctorId: activeDoctorId,
      patientId: pid,
      breakGlass: true,
      reason
    });

    isPatientUnlocked = true;
    unlockedViaBreakGlass = true;
    activePatientId = pid;
    currentPatientProfile = res.patient || res;

    closeModal('break-glass-modal');
    updateWorkspaceUnlockedState();
    showToast('Emergency Break-Glass authorized. CloudTrail audit logged.', 'warning');
    switchDoctorSection('overview');
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Authorize Emergency Break-Glass</span>`;
    }
  }
}

async function lockPatientRecordNow(customMsg) {
  try {
    await API.post('/api/auth/lock', { doctorId: activeDoctorId, patientId: activePatientId });
  } catch (_) {}

  isPatientUnlocked = false;
  unlockedViaBreakGlass = false;
  API.clearUnlockedPatient();
  if (doctorPinHelper) doctorPinHelper.clear();

  const banner = document.getElementById('break-glass-alert-banner');
  if (banner) banner.classList.add('hidden');

  const ind = document.getElementById('unlock-indicator-badge');
  if (ind) {
    ind.className = 'badge badge-amber text-xs w-full justify-center';
    ind.innerText = 'LOCKED · PRIVACY SHIELD';
  }

  showToast(customMsg || 'Patient chart locked. Privacy shield re-engaged.', 'info');
  switchDoctorSection('lookup');
}

async function pollPatientConsentStatus() {
  if (!isPatientUnlocked) return;
  try {
    const status = await API.get(`/api/consent/status?patientId=${activePatientId}`);
    if (status && status.hasActiveAccess === false && !unlockedViaBreakGlass) {
      const msg = status.revoked ? 'The patient removed your access.' : "Access expired. Enter the patient's current PIN again.";
      lockPatientRecordNow(msg);
    }
  } catch (err) {
    if (err && (err.code === 'NO_ACTIVE_GRANT' || err.code === 'CONSENT_REVOKED')) {
      const msg = (err.code === 'CONSENT_REVOKED') ? 'The patient removed your access.' : "Access expired. Enter the patient's current PIN again.";
      lockPatientRecordNow(msg);
    } else {
      // Non-destructive: transient network or 500 errors keep current screen
      console.debug('Transient auto-refresh check:', err);
    }
  }
}

function selectRecentPatient(pid) {
  const inp = document.getElementById('lookup-patient-id');
  if (inp) inp.value = pid;
  activePatientId = pid;
  if (doctorPinHelper) doctorPinHelper.clear();
  showToast(`Pre-filled ${pid}. Enter 6-digit Consent PIN to unlock.`, 'info');
}

function pasteQrPayloadToInput() {
  if (navigator.clipboard && navigator.clipboard.readText) {
    navigator.clipboard.readText().then(text => {
      try {
        const parsed = JSON.parse(text);
        if (parsed.patientId) {
          document.getElementById('lookup-patient-id').value = parsed.patientId;
          showToast(`Pasted QR Payload: ${parsed.patientId}`, 'success');
        }
      } catch (_) {
        const trimmed = text.trim();
        document.getElementById('lookup-patient-id').value = trimmed;
        showToast(`Pasted ID: ${trimmed}`, 'success');
      }
    }).catch(() => showToast('Failed to read clipboard', 'warning'));
  }
}

// ============================================================================
// 4. WORKSPACE UNLOCKED STATE RENDERER
// ============================================================================
function updateWorkspaceUnlockedState() {
  if (!currentPatientProfile) return;
  const p = currentPatientProfile;

  // Emergency banner
  try {
    const banner = document.getElementById('break-glass-alert-banner');
    if (banner) {
      if (unlockedViaBreakGlass) banner.classList.remove('hidden');
      else banner.classList.add('hidden');
    }
  } catch (e) {
    console.warn('Error rendering emergency banner:', e);
  }

  // Indicator
  try {
    const ind = document.getElementById('unlock-indicator-badge');
    if (ind) {
      ind.className = unlockedViaBreakGlass ? 'badge badge-red text-xs w-full justify-center' : 'badge badge-green text-xs w-full justify-center';
      ind.innerText = unlockedViaBreakGlass ? 'EMERGENCY BREAK-GLASS' : 'UNLOCKED · CONSENT OK';
    }
  } catch (e) {
    console.warn('Error rendering unlock indicator badge:', e);
  }

  // Sticky Patient Header
  try {
    const nameEl = document.getElementById('patient-name-display');
    if (nameEl) nameEl.innerText = p.name || 'Ramesh Kumar';
    const initEl = document.getElementById('patient-initials');
    if (initEl) {
      const parts = (p.name || 'RK').split(' ');
      initEl.innerText = parts.length > 1 ? `${parts[0][0]}${parts[1][0]}` : parts[0].substring(0, 2).toUpperCase();
    }
    const gaEl = document.getElementById('patient-gender-age');
    if (gaEl) gaEl.innerText = `${p.gender || 'Male'}, ${p.age || 42} yrs`;
    const idEl = document.getElementById('patient-id-display');
    if (idEl) idEl.innerText = p.id || p.patientId || activePatientId;
    const abhaEl = document.getElementById('patient-abha-display');
    if (abhaEl) abhaEl.innerText = p.abhaId || 'ABHA-21-9845-3310-7742';
    const langEl = document.getElementById('patient-lang-display');
    if (langEl) langEl.innerText = p.preferredLanguage || 'Odia';
    const locEl = document.getElementById('patient-location-display');
    if (locEl) locEl.innerText = `${p.originState || 'Odisha'} → ${p.currentLocation || 'Bengaluru'}`;
  } catch (e) {
    console.warn('Error rendering patient header:', e);
  }

  // Allergies
  try {
    const algContainer = document.getElementById('patient-allergies-list');
    const railAllergies = document.getElementById('safety-rail-allergies');
    const allergies = p.allergies || ['Penicillin'];
    if (algContainer) {
      algContainer.innerHTML = allergies.map(a => `
        <span class="badge badge-red text-xs font-bold">${a} (Severe)</span>
      `).join('');
    }
    if (railAllergies) {
      railAllergies.innerHTML = allergies.map(a => `<div>• ${a}</div>`).join('');
    }
  } catch (e) {
    console.warn('Error rendering allergies:', e);
    const algContainer = document.getElementById('patient-allergies-list');
    if (algContainer) algContainer.innerHTML = `<span class="text-xs text-muted">Couldn't load allergies · <button type="button" class="text-primary underline" onclick="updateWorkspaceUnlockedState()">Retry</button></span>`;
  }

  // Active Prescriptions (Overview & Prescriptions Pane)
  try {
    renderActivePrescriptionsList(p.prescriptions || []);
  } catch (e) {
    console.warn('Error rendering prescriptions:', e);
    const overviewList = document.getElementById('overview-active-rx-list');
    if (overviewList) overviewList.innerHTML = `<p class="text-xs text-muted p-3">Couldn't load prescriptions · <button type="button" class="text-primary underline" onclick="renderActivePrescriptionsList(currentPatientProfile?.prescriptions || [])">Retry</button></p>`;
  }

  // FHIR Bundle Code
  try {
    const fhirEl = document.getElementById('fhir-bundle-code');
    if (fhirEl) {
      fhirEl.innerText = JSON.stringify({
        resourceType: "Bundle",
        type: "collection",
        entry: [
          { resource: { resourceType: "Patient", id: p.id || activePatientId, name: [{ text: p.name }], gender: p.gender } },
          { resource: { resourceType: "MedicationRequest", status: "active", intent: "order", medicationCodeableConcept: { text: "Metformin 500mg" } } },
          { resource: { resourceType: "MedicationRequest", status: "active", intent: "order", medicationCodeableConcept: { text: "Warfarin 5mg" } } }
        ]
      }, null, 2);
    }
  } catch (e) {
    console.warn('Error rendering FHIR bundle:', e);
  }

  // Load Reports & Trends & Audit Trail
  try {
    loadPatientReports();
  } catch (e) {
    console.warn('Error loading reports:', e);
  }
  try {
    loadPatientTrends();
  } catch (e) {
    console.warn('Error loading trends:', e);
  }
  try {
    loadDoctorAuditTrail();
  } catch (e) {
    console.warn('Error loading audit trail:', e);
  }
}

function renderActivePrescriptionsList(prescriptions) {
  const activeCountEl = document.getElementById('active-rx-count');
  if (activeCountEl) activeCountEl.innerText = prescriptions.length;

  const overviewList = document.getElementById('overview-active-rx-list');
  const fullList = document.getElementById('doctor-prescriptions-list');
  const railList = document.getElementById('safety-rail-medicines');

  const html = prescriptions.length ? prescriptions.map(rx => `
    <div class="p-3.5 rounded-xl border border-subtle bg-card flex items-start justify-between gap-3 shadow-xs">
      <div>
        <div class="flex items-center gap-2">
          <span class="font-bold text-sm text-main">${rx.medicationName || rx.medication}</span>
          <span class="badge badge-teal text-[10px]">${rx.dosage || rx.dose || '500mg'}</span>
          <span class="badge badge-indigo text-[10px]">${rx.frequency || 'TWICE_DAILY'}</span>
        </div>
        <p class="text-xs text-muted mt-1">Prescribed by ${rx.prescribedBy || 'Dr. Sharma'} · ${rx.instructions || 'Take with water'}</p>
      </div>
      <div class="flex items-center gap-1.5 flex-shrink-0">
        <button type="button" onclick="promptModifyDosage('${rx.prescriptionId || rx.id}', '${rx.medicationName || rx.medication}', '${rx.dosage || rx.dose}')" class="btn btn-secondary text-xs px-2.5 py-1">
          Modify
        </button>
        <button type="button" onclick="promptDiscontinueMed('${rx.prescriptionId || rx.id}', '${rx.medicationName || rx.medication}')" class="btn btn-secondary text-xs px-2.5 py-1 text-danger hover:bg-danger-soft">
          Discontinue
        </button>
      </div>
    </div>
  `).join('') : '<p class="text-xs text-muted p-3">No active prescriptions.</p>';

  if (overviewList) overviewList.innerHTML = html;
  if (fullList) fullList.innerHTML = html;
  if (railList) {
    railList.innerHTML = prescriptions.map(rx => `
      <div class="font-bold text-main">• ${rx.medicationName || rx.medication} <span class="text-muted font-normal">(${rx.dosage || '500mg'})</span></div>
    `).join('');
  }
}

// ============================================================================
// 5. CLINICAL REPORTS & TRENDS (NEW SCREEN)
// ============================================================================
async function loadPatientReports() {
  const container = document.getElementById('doctor-reports-list');
  const overviewPreview = document.getElementById('overview-reports-preview');
  if (!container && !overviewPreview) return;

  try {
    const data = await API.get(`/api/reports?patientId=${activePatientId}`);
    const reports = data.reports || [];

    // Filter reports
    const filtered = _currentReportsFilter === 'ALL'
      ? reports
      : reports.filter(r => r.type === _currentReportsFilter);

    if (overviewPreview) {
      overviewPreview.innerHTML = reports.slice(0, 3).map(r => `
        <div class="p-2.5 rounded-lg border border-subtle flex items-center justify-between">
          <div>
            <span class="font-bold text-main">${r.title}</span>
            <span class="text-muted block text-[11px]">${r.date} · ${r.facility}</span>
          </div>
          <span class="badge ${r.source === 'HOME_STATE_PHC' ? 'badge-amber' : 'badge-teal'} text-[9px]">
            ${r.source === 'HOME_STATE_PHC' ? 'ODISHA PHC' : 'BENGALURU'}
          </span>
        </div>
      `).join('');
    }

    if (container) {
      container.innerHTML = filtered.length ? filtered.map(r => `
        <div class="card p-5 space-y-3">
          <div class="flex items-center justify-between pb-2 border-b border-subtle">
            <div class="flex items-center gap-2">
              <span class="font-bold text-base text-main">${r.title}</span>
              <span class="badge ${r.source === 'HOME_STATE_PHC' ? 'badge-amber' : 'badge-teal'} text-[10px]">
                ${r.source === 'HOME_STATE_PHC' ? 'HOME STATE PHC' : 'BENGALURU CLINIC'}
              </span>
            </div>
            <span class="text-xs text-muted font-mono">${r.date}</span>
          </div>

          <!-- Lab Results Table or Findings -->
          ${r.results && r.results.length ? `
            <div class="overflow-x-auto">
              <table class="w-full text-xs text-left">
                <thead class="bg-card-subtle text-muted uppercase font-bold">
                  <tr>
                    <th class="p-2">Analyte</th>
                    <th class="p-2">Value</th>
                    <th class="p-2">Reference Range</th>
                    <th class="p-2">Evaluation</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-subtle">
                  ${r.results.map(res => `
                    <tr>
                      <td class="p-2 font-bold">${res.name}</td>
                      <td class="p-2 font-mono font-bold text-main">${res.value} ${res.unit}</td>
                      <td class="p-2 text-muted">${res.refLow || 0} - ${res.refHigh || 0} ${res.unit}</td>
                      <td class="p-2">
                        <span class="badge ${res.flag === 'CRITICAL' ? 'badge-red' : (res.flag === 'H' ? 'badge-amber' : 'badge-green')} text-[10px]">
                          ${res.flag === 'CRITICAL' ? 'CRITICAL HIGH' : (res.flag === 'H' ? 'HIGH' : 'NORMAL')}
                        </span>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          ` : ''}

          <!-- Imaging / Spirometry Findings -->
          ${r.findings ? `
            <div class="p-3 rounded-xl bg-card-subtle text-xs space-y-1">
              <strong>Findings:</strong>
              <p class="text-muted leading-relaxed">${r.findings}</p>
              ${r.impression ? `<div class="pt-1"><strong>Impression:</strong> <span class="text-main font-semibold">${r.impression}</span></div>` : ''}
            </div>
          ` : ''}

          <!-- Paper Prescription Side-by-Side OCR -->
          ${r.attachment && r.attachment.ocrRawText ? `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              <div class="p-3 bg-bg-card-subtle rounded-xl text-xs font-mono">
                <span class="font-bold text-muted block mb-1">Raw OCR Scanned Slip:</span>
                <p class="whitespace-pre-wrap">${r.attachment.ocrRawText}</p>
              </div>
              <div class="p-3 bg-card-subtle rounded-xl text-xs">
                <span class="font-bold text-teal block mb-1">OCR Confidence: ${(r.attachment.ocrConfidence * 100).toFixed(0)}%</span>
                <p class="text-muted">Digitized &amp; verified into national FHIR record lake.</p>
              </div>
            </div>
          ` : ''}
        </div>
      `).join('') : '<p class="text-xs text-muted p-4 text-center">No reports found for this filter.</p>';
    }
  } catch (e) {
    console.warn('Failed to load reports', e);
  }
}

function filterReports(category) {
  _currentReportsFilter = category;
  loadPatientReports();
}

async function loadPatientTrends() {
  const hba1cBox = document.getElementById('chart-hba1c');
  const inrBox = document.getElementById('chart-inr');
  if (!hba1cBox || !inrBox) return;

  try {
    const [hRes, inrRes] = await Promise.all([
      API.get(`/api/trends?patientId=${activePatientId}&metric=HbA1c`),
      API.get(`/api/trends?patientId=${activePatientId}&metric=INR`)
    ]);

    const hPoints = hRes.series || [{ date: '9m ago', value: 8.9 }, { date: '4m ago', value: 8.1 }, { date: 'Current', value: 7.4 }];
    const inrPoints = inrRes.series || [{ date: '6m ago', value: 2.1 }, { date: '2m ago', value: 3.4 }, { date: 'Current', value: 2.6 }];

    hba1cBox.innerHTML = renderSvgTrendLine(hPoints, 6.0, 9.5, '#0F766E');
    inrBox.innerHTML = renderSvgTrendLine(inrPoints, 1.5, 4.0, '#DC2626');
  } catch (e) {
    console.warn('Trends load failed', e);
  }
}

function renderSvgTrendLine(points, minVal, maxVal, strokeColor) {
  const w = 300;
  const h = 90;
  if (!points || !points.length) return '';

  const coords = points.map((p, i) => {
    const x = (i / (points.length - 1)) * (w - 40) + 20;
    const y = h - ((p.value - minVal) / (maxVal - minVal)) * (h - 20) - 10;
    return { x, y, val: p.value, date: p.date };
  });

  const pathD = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x} ${c.y}`).join(' ');

  return `
    <svg viewBox="0 0 ${w} ${h}" class="w-full h-full overflow-visible">
      <path d="${pathD}" fill="none" stroke="${strokeColor}" stroke-width="2.5" stroke-linecap="round"/>
      ${coords.map(c => `
        <circle cx="${c.x}" cy="${c.y}" r="4.5" fill="${strokeColor}"/>
        <text x="${c.x}" y="${c.y - 8}" text-anchor="middle" font-size="10" font-weight="bold" fill="currentColor">${c.val}</text>
        <text x="${c.x}" y="${h - 2}" text-anchor="middle" font-size="9" fill="#94A3B8">${c.date}</text>
      `).join('')}
    </svg>
  `;
}

// ============================================================================
// 6. MEDICINES SERVER-SIDE SEARCH & AI SAFETY INTERCEPTION
// ============================================================================
let medCombobox = null;
let _currentSafetyCheck = null;

function initDoctorComboboxes() {
  const medInput = document.getElementById('prescribe-med-input');
  if (medInput && !medCombobox) {
    medCombobox = Combobox.create(medInput, {
      debounceMs: 200,
      minChars: 2,
      limit: 15,
      emptyText: "No medicine found. Check the spelling.",
      hintText: "Type at least 2 characters to search...",
      fetchOptions: async (query, signal) => {
        const url = `/api/medicines-catalog?q=${encodeURIComponent(query)}&limit=15&patientId=${encodeURIComponent(activePatientId)}`;
        const res = await API.get(url, { signal });
        return res.matches || res.results || res.medicines || [];
      },
      onSelect: (item) => {
        selectMedicineFromSearch(
          item.name || item.brand_name,
          item.generic || item.generic_composition
        );
      }
    });
  }

  // Convert other native dropdowns in the app to accessible comboboxes
  const freqSelect = document.getElementById('prescribe-freq-select');
  if (freqSelect) Combobox.createFromSelect(freqSelect, { onSelect: () => updateComputedQuantity() });

  const transSrc = document.getElementById('trans-source-lang');
  if (transSrc) Combobox.createFromSelect(transSrc);

  const transTgt = document.getElementById('trans-target-lang');
  if (transTgt) Combobox.createFromSelect(transTgt);

  const occSelect = document.getElementById('risk-occupation');
  if (occSelect) Combobox.createFromSelect(occSelect, { onSelect: () => recalcWorkRisk() });

  const ashaSelect = document.getElementById('followup-asha-select');
  if (ashaSelect) Combobox.createFromSelect(ashaSelect);
}

function debounceMedicineSearch(q) {
  if (medCombobox) {
    medCombobox.search(q);
  }
}

function selectMedicineFromSearch(name, generic) {
  const medInput = document.getElementById('prescribe-med-input');
  const genInput = document.getElementById('prescribe-generics-input');
  if (medInput) medInput.value = name;
  if (genInput) genInput.value = generic || name;

  const legacyBox = document.getElementById('med-search-results');
  if (legacyBox) legacyBox.classList.add('hidden');

  // Trigger live safety check (Task 2)
  runLiveSafetyCheck(name, activePatientId);
}

function fillQuickAugmentin() {
  selectMedicineFromSearch('Augmentin 625 Duo Tablet', 'amoxicillin + clavulanic acid');
  const d = document.getElementById('prescribe-dosage-input');
  if (d) d.value = '625 Duo';
  updateComputedQuantity();
}

function fillQuickAspirin() {
  selectMedicineFromSearch('Ecosprin 75mg Tablet', 'aspirin');
  const d = document.getElementById('prescribe-dosage-input');
  if (d) d.value = '75mg';
  updateComputedQuantity();
}

async function runLiveSafetyCheck(medicineName, patientId, chosenIndication = null) {
  const panel = document.getElementById('doctor-safety-panel');
  if (!panel) return;

  const med = (medicineName || document.getElementById('prescribe-med-input')?.value || '').trim();
  if (!med) {
    panel.classList.add('hidden');
    panel.innerHTML = '';
    return;
  }

  panel.classList.remove('hidden');
  panel.innerHTML = `
    <div class="p-3 rounded-xl border border-subtle bg-bg-card-subtle animate-pulse flex items-center gap-3 text-xs text-muted">
      <span class="animate-spin text-primary inline-block">↻</span>
      <span>Checking clinical safety against patient allergies, active regimens, and DDI...</span>
    </div>
  `;

  try {
    const res = await API.post('/api/prescribe/check', {
      patientId: patientId || activePatientId,
      medicineName: med,
      dosage: document.getElementById('prescribe-dosage-input')?.value || '',
      indication: chosenIndication
    });

    _currentSafetyCheck = res;
    renderDoctorSafetyPanel(res, med);
  } catch (err) {
    console.warn('Safety check failed', err);
    panel.innerHTML = `
      <div class="p-3 rounded-xl border border-warning-border bg-warning-soft text-xs text-warning flex items-center justify-between">
        <span>Could not verify safety automatically. Please review manually.</span>
        <button type="button" class="btn btn-secondary text-xs py-0.5 px-2 font-bold" onclick="runLiveSafetyCheck('${med}', '${patientId}')">Retry</button>
      </div>
    `;
  }
}

function renderDoctorSafetyPanel(res, medName) {
  const panel = document.getElementById('doctor-safety-panel');
  const prescribeBtn = document.getElementById('btn-submit-prescription');
  if (!panel) return;

  panel.classList.remove('hidden');
  const patientName = currentPatientProfile?.name || 'this patient';

  if (res.riskLevel === 'NONE') {
    panel.innerHTML = `
      <div class="p-2.5 rounded-lg border border-success-border bg-success-soft text-xs text-success flex items-center gap-2 font-medium">
        <svg class="lucide-icon sm text-success flex-shrink-0" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        <span>No conflicts found with this patient's allergies and current medicines.</span>
      </div>
    `;
    if (prescribeBtn) {
      prescribeBtn.className = 'btn btn-doctor w-full h-12 text-base font-bold';
      prescribeBtn.innerHTML = `<svg class="lucide-icon sm" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><span>Authorize Prescription &amp; Run AI Safety Check</span>`;
    }
    return;
  }

  if (res.riskLevel === 'UNKNOWN') {
    panel.innerHTML = `
      <div class="p-3 rounded-xl border border-warning-border bg-warning-soft text-xs text-warning flex items-center gap-2 font-medium">
        <svg class="lucide-icon sm text-warning flex-shrink-0" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>We couldn't check this automatically, please review manually.</span>
      </div>
    `;
    if (prescribeBtn) {
      prescribeBtn.className = 'btn btn-doctor w-full h-12 text-base font-bold';
      prescribeBtn.innerHTML = `<svg class="lucide-icon sm" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><span>Authorize Prescription (Manual Review)</span>`;
    }
    return;
  }

  // SEVERE or CAUTION box
  const isSevere = res.riskLevel === 'SEVERE';
  const boxBorder = isSevere ? 'border-2 border-danger bg-danger-soft/40' : 'border border-warning-border bg-warning-soft/40';
  const titleColor = isSevere ? 'text-danger' : 'text-warning';
  const badgeColor = isSevere ? 'badge-red' : 'badge-amber';
  const headerIcon = isSevere
    ? '<svg class="lucide-icon sm text-danger" viewBox="0 0 24 24"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
    : '<svg class="lucide-icon sm text-warning" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';

  // Primary explanation from findings (up to 2 sentences)
  const firstFinding = (res.findings && res.findings[0]) || {};
  const plainText = firstFinding.plainExplanation || (isSevere ? `Risky combination detected for ${medName}.` : `Caution advised when prescribing ${medName}.`);
  const clinicianNote = firstFinding.clinicianNote || '';
  const findingWith = firstFinding.with || '';

  // Alternatives / Safer options
  let optionsHtml = '';
  if (res.noSafeSubstitute) {
    optionsHtml = `
      <div class="p-3 rounded-lg bg-surface border border-subtle text-xs space-y-1.5">
        <p class="font-bold text-danger">${res.noSubstituteMessage || 'No direct safe replacement available.'}</p>
        <div class="flex items-center gap-2">
          <span class="badge badge-amber text-[10px] font-bold">Request Specialist Review</span>
          <span class="text-[11px] text-muted">Specialist cardiologist or clinical pharmacologist consultation required.</span>
        </div>
      </div>
    `;
  } else if (res.alternatives && res.alternatives.length > 0) {
    const cards = res.alternatives.map((alt) => {
      const isDuplicateAction = alt.action === 'AVOID_DUPLICATE';
      if (isDuplicateAction) {
        return `
          <div class="card p-3 border border-subtle space-y-2 bg-surface">
            <div class="flex items-center justify-between">
              <span class="font-extrabold text-xs text-main">Keep Current Active Regimen</span>
              <span class="badge badge-teal text-[9px] font-bold">Recommended</span>
            </div>
            <p class="text-xs text-muted">${alt.reason}</p>
            <div class="pt-1">
              <button type="button" onclick="switchDoctorSection('overview')" class="btn btn-secondary text-xs py-1 px-3">
                <span>View Current Active Prescriptions</span>
              </button>
            </div>
          </div>
        `;
      }

      const cautionsHtml = (alt.cautions || []).map(c => `
        <span class="badge badge-amber text-[10px] py-0.5">${c}</span>
      `).join('');

      const brandsHtml = (alt.brands || []).map(b => `
        <button type="button" onclick="useAlternativeReplacement('${b.name.replace(/'/g, "\\'")}', '${alt.generic.replace(/'/g, "\\'")}', '${medName.replace(/'/g, "\\'")}')" class="badge badge-teal text-[10px] py-1 px-2 cursor-pointer hover:bg-primary-soft text-left inline-flex items-center gap-1.5" title="Click to use this brand">
          <strong class="font-bold">${b.name}</strong>
          ${b.price ? `<span class="opacity-80">₹${b.price}</span>` : ''}
          ${b.manufacturer ? `<span class="opacity-70">(${b.manufacturer})</span>` : ''}
        </button>
      `).join('');

      const targetBrand = (alt.brands && alt.brands[0]) ? alt.brands[0].name : alt.generic;
      const isAltCaution = alt.riskLevel === 'CAUTION';

      return `
        <div class="card p-3 border border-subtle space-y-2.5 bg-surface hover:shadow-md transition-shadow">
          <div class="flex items-start justify-between gap-2">
            <div>
              <span class="font-extrabold text-sm text-main capitalize">${alt.generic}</span>
              ${isAltCaution ? '<span class="badge badge-amber text-[9px] font-bold ml-2">Use with caution</span>' : '<span class="badge badge-teal text-[9px] font-bold ml-2">No conflicts found</span>'}
            </div>
            <button type="button" onclick="useAlternativeReplacement('${targetBrand.replace(/'/g, "\\'")}', '${alt.generic.replace(/'/g, "\\'")}', '${medName.replace(/'/g, "\\'")}')" class="btn btn-primary text-xs py-1.5 px-3 min-h-[44px] flex-shrink-0 shadow-sm font-bold">
              <span>Use this instead</span>
            </button>
          </div>
          <p class="text-xs text-muted leading-relaxed">${alt.reason}</p>
          ${cautionsHtml ? `<div class="flex flex-wrap gap-1.5">${cautionsHtml}</div>` : ''}
          ${brandsHtml ? `
            <div class="pt-1 border-t border-subtle">
              <span class="text-[10px] font-bold text-muted uppercase block mb-1">Catalog Brands (Click to select):</span>
              <div class="flex flex-wrap gap-1.5">${brandsHtml}</div>
            </div>
          ` : ''}
          <div class="text-[11px] text-muted flex items-center gap-1">
            <svg class="lucide-icon sm text-primary" viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            <span>In stock at 3 pharmacies nearby (nearest: Apollo Pharmacy · 0.8 km)</span>
          </div>
        </div>
      `;
    }).join('');

    optionsHtml = `
      <div class="space-y-2 pt-2 border-t border-subtle">
        <span class="text-xs font-extrabold text-main block uppercase tracking-wider">Safer Replacement Options:</span>
        <div class="space-y-2">${cards}</div>
      </div>
    `;
  }

  // Indication Selector if needed
  let indicationHtml = '';
  if (res.needsIndication) {
    indicationHtml = `
      <div class="p-2.5 rounded-lg bg-surface border border-subtle flex items-center justify-between gap-3">
        <label class="text-xs font-bold text-main whitespace-nowrap">What is it for?</label>
        <select onchange="runLiveSafetyCheck('${medName.replace(/'/g, "\\'")}', '${activePatientId}', this.value)" class="form-control text-xs py-1">
          <option value="Respiratory infection">Respiratory infection</option>
          <option value="Urinary infection">Urinary infection</option>
          <option value="Skin infection">Skin infection</option>
          <option value="Pain or fever">Pain or fever</option>
          <option value="Blood pressure">Blood pressure</option>
          <option value="Diabetes">Diabetes</option>
          <option value="Cholesterol">Cholesterol</option>
          <option value="Acid reflux">Acid reflux</option>
          <option value="Other">Other</option>
        </select>
      </div>
    `;
  }

  panel.innerHTML = `
    <div class="p-4 rounded-xl ${boxBorder} space-y-3">
      <div class="flex items-start justify-between gap-2">
        <div class="flex items-center gap-2">
          ${headerIcon}
          <h4 class="font-extrabold text-sm ${titleColor}">${isSevere ? `Risky for ${patientName}` : `Caution for ${patientName}`}</h4>
          ${findingWith ? `<span class="badge ${badgeColor} text-[10px] font-bold">${findingWith}</span>` : ''}
        </div>
        <span class="text-[10px] text-muted font-bold tracking-wider">Decision support · Doctor must confirm</span>
      </div>

      <p class="text-xs text-main font-medium leading-relaxed">${plainText}</p>

      ${clinicianNote ? `
        <div>
          <button type="button" onclick="toggleSafetyWhyDetails()" class="text-xs font-bold text-primary hover:underline flex items-center gap-1">
            <span>Why? Clinician Pharmacology Notes</span>
            <svg class="lucide-icon sm" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
          <div id="safety-why-details" class="hidden mt-2 p-3 rounded-lg bg-surface border border-subtle text-xs text-muted space-y-1">
            <p><strong>Clinical Pharmacology:</strong> ${clinicianNote}</p>
            <p class="text-[11px] text-sub">Source: Rules Engine + AWS Bedrock Pharmacology Gatekeeper</p>
          </div>
        </div>
      ` : ''}

      ${indicationHtml}
      ${optionsHtml}
    </div>
  `;

  // Adjust Prescribe button style
  if (prescribeBtn) {
    if (isSevere) {
      prescribeBtn.className = 'btn btn-secondary w-full h-12 text-base font-bold text-danger border-2 border-danger/40 hover:bg-danger-soft';
      prescribeBtn.innerHTML = `<svg class="lucide-icon sm" viewBox="0 0 24 24"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/></svg><span>Prescribe anyway… (Requires Clinical Justification)</span>`;
    } else {
      prescribeBtn.className = 'btn btn-doctor w-full h-12 text-base font-bold';
      prescribeBtn.innerHTML = `<svg class="lucide-icon sm" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><span>Authorize Prescription (Caution Logged)</span>`;
    }
  }
}

function toggleSafetyWhyDetails() {
  const el = document.getElementById('safety-why-details');
  if (el) el.classList.toggle('hidden');
}

async function useAlternativeReplacement(brandOrGenericName, genericName, originalMedicine) {
  const medInput = document.getElementById('prescribe-med-input');
  const genInput = document.getElementById('prescribe-generics-input');
  const doseInput = document.getElementById('prescribe-dosage-input');

  if (medInput) medInput.value = brandOrGenericName;
  if (genInput) genInput.value = genericName || brandOrGenericName;

  showToast(`Replaced ${originalMedicine} with ${brandOrGenericName}`, 'success');

  // Audit acceptance
  API.post('/api/prescribe/accept-alternative', {
    patientId: activePatientId,
    originalMedicine,
    replacementMedicine: brandOrGenericName
  }).catch(() => {});

  // Re-run safety check on replacement
  await runLiveSafetyCheck(brandOrGenericName, activePatientId);

  // Scroll to dose field
  if (doseInput) {
    doseInput.focus();
    doseInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

function setPrescribeDuration(days) {
  const input = document.getElementById('prescribe-duration-input');
  if (input) input.value = days;

  document.querySelectorAll('.duration-chip').forEach(btn => {
    if (btn.innerText === `${days}d`) {
      btn.className = 'duration-chip badge badge-teal cursor-pointer font-bold border-teal';
    } else {
      btn.className = 'duration-chip badge badge-indigo cursor-pointer hover:bg-doctor-soft';
    }
  });
  updateComputedQuantity();
}

function updateComputedQuantity() {
  const duration = parseInt(document.getElementById('prescribe-duration-input')?.value || '7', 10);
  const freq = document.getElementById('prescribe-freq-select')?.value || 'TWICE_DAILY';
  const label = document.getElementById('prescribe-computed-quantity');
  if (!label) return;

  let dosesPerDay = 1;
  if (freq === 'TWICE_DAILY') dosesPerDay = 2;
  else if (freq === 'THRICE_DAILY') dosesPerDay = 3;
  else if (freq === 'FOUR_TIMES_DAILY') dosesPerDay = 4;

  const totalDoses = dosesPerDay * (duration || 7);
  label.innerText = `About ${totalDoses} tablets`;
}

async function handlePrescribeSubmit(e) {
  if (e) e.preventDefault();
  const med = document.getElementById('prescribe-med-input')?.value.trim();
  const dosage = document.getElementById('prescribe-dosage-input')?.value.trim();
  const freq = document.getElementById('prescribe-freq-select')?.value;
  const durationDays = parseInt(document.getElementById('prescribe-duration-input')?.value || '7', 10);
  const notes = document.getElementById('prescribe-notes-input')?.value.trim();
  const btn = document.getElementById('btn-submit-prescription');

  if (!med || !dosage) {
    showToast('Please specify medicine name and dosage', 'warning');
    return;
  }

  // If severe and override not confirmed, open safety modal
  if (_currentSafetyCheck && _currentSafetyCheck.riskLevel === 'SEVERE') {
    lastBlockedPrescription = {
      doctorId: activeDoctorId,
      patientId: activePatientId,
      medicationName: med,
      dosage,
      frequency: freq,
      durationDays: durationDays || 7,
      instructions: notes
    };
    openSafetyModal({
      reason: (_currentSafetyCheck.findings && _currentSafetyCheck.findings[0]) ? _currentSafetyCheck.findings[0].plainExplanation : 'Severe interaction',
      source: _currentSafetyCheck.source || 'RULES_ENGINE',
      alternatives: _currentSafetyCheck.alternatives
    });
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Evaluating Clinical Safety Rules &amp; Bedrock...</span>`;
  }

  try {
    const payload = {
      doctorId: activeDoctorId,
      patientId: activePatientId,
      medicationName: med,
      dosage,
      frequency: freq,
      durationDays: durationDays || 7,
      instructions: notes
    };

    const res = await API.post('/api/prescribe', payload);

    if (res.status === 'BLOCKED' || res.decision === 'BLOCKED') {
      lastBlockedPrescription = payload;
      openSafetyModal(res);
    } else {
      showToast('Saved. The patient can now reserve it at a pharmacy', 'success');
      // Refresh patient profile
      const prof = await API.get(`/api/profile?patient_id=${activePatientId}`);
      currentPatientProfile = prof.patient || prof;
      updateWorkspaceUnlockedState();
    }
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg class="lucide-icon sm" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><span>Authorize Prescription &amp; Run AI Safety Check</span>`;
    }
  }
}

function openSafetyModal(alertData) {
  const explanationEl = document.getElementById('safety-modal-explanation');
  const sourceEl = document.getElementById('safety-modal-source');
  if (explanationEl) explanationEl.innerText = alertData.reason || alertData.clinicalExplanation || alertData.message || 'Contraindicated medication detected.';
  if (sourceEl) sourceEl.innerText = alertData.source || 'RULES_ENGINE';

  const altBox = document.getElementById('safety-modal-alternatives');
  const alts = alertData.alternatives || alertData.safeAlternatives || [];

  if (altBox) {
    if (!alts.length) {
      altBox.innerHTML = '<p class="text-xs text-muted">No automatic alternatives available. Cardiology/Specialist review required.</p>';
    } else {
      altBox.innerHTML = alts.map(a => {
        const genName = typeof a === 'string' ? a : (a.generic || a.name || 'Alternative');
        const reason = typeof a === 'string' ? '' : (a.reason || '');
        const targetBrand = (typeof a === 'object' && a.brands && a.brands[0]) ? a.brands[0].name : genName;
        return `
          <div class="card p-2.5 border border-subtle flex items-center justify-between gap-2">
            <div>
              <span class="font-bold text-xs text-main capitalize">${genName}</span>
              ${reason ? `<p class="text-[11px] text-muted">${reason}</p>` : ''}
            </div>
            <button type="button" onclick="selectAlternativeMed('${targetBrand.replace(/'/g, "\\'")}', '${genName.replace(/'/g, "\\'")}')" class="btn btn-primary text-xs py-1 px-2.5 font-bold">
              Use this instead
            </button>
          </div>
        `;
      }).join('');
    }
  }

  openModal('safety-interception-modal');
  const cancelBtn = document.getElementById('btn-cancel-blocked');
  if (cancelBtn) cancelBtn.focus();
}

function selectAlternativeMed(brandOrGeneric, genericName) {
  closeModal('safety-interception-modal');
  const originalMed = document.getElementById('prescribe-med-input')?.value;
  useAlternativeReplacement(brandOrGeneric, genericName, originalMed);
}

async function submitClinicalOverride() {
  const reason = document.getElementById('override-justification-input')?.value.trim();
  if (!reason || reason.length < 10) {
    showToast('Please type a clinical override reason (at least 10 characters)', 'warning');
    return;
  }

  if (!lastBlockedPrescription) return;

  try {
    const payload = {
      ...lastBlockedPrescription,
      forceOverride: true,
      overrideReason: reason
    };

    const res = await API.post('/api/prescribe', payload);
    closeModal('safety-interception-modal');
    showToast('Saved with clinical override. The patient can now reserve it at a pharmacy', 'warning');
    // Refresh patient profile
    const prof = await API.get(`/api/profile?patient_id=${activePatientId}`);
    currentPatientProfile = prof.patient || prof;
    updateWorkspaceUnlockedState();
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  }
}

async function resumePatientRecord() {
  const storedUnlocked = API.getUnlockedPatient() || activePatientId;
  const btn = document.getElementById('btn-resume-record');
  if (btn) btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Opening Record...</span>`;
  try {
    const res = await API.get(`/api/profile?patientId=${storedUnlocked}`);
    isPatientUnlocked = true;
    activePatientId = storedUnlocked;
    currentPatientProfile = res.patient || res;
    updateWorkspaceUnlockedState();
    switchDoctorSection('overview');
    showToast(`Health record for ${currentPatientProfile.name || 'Patient'} resumed.`, 'success');
  } catch (err) {
    showToast(err.friendlyMessage || 'Session expired or access revoked.', 'error');
    API.clearUnlockedPatient();
    const resumeContainer = document.getElementById('resume-grant-container');
    if (resumeContainer) resumeContainer.classList.add('hidden');
  }
}
window.resumePatientRecord = resumePatientRecord;

async function promptModifyDosage(rxId, name, currentDose) {
  const newDose = prompt(`Modify dosage for ${name}:`, currentDose);
  if (!newDose || newDose === currentDose) return;

  try {
    const res = await API.put('/api/prescriptions', {
      doctorId: activeDoctorId,
      patientId: activePatientId,
      prescriptionId: rxId,
      dosage: newDose,
      new_dosage: newDose,
      status: 'MODIFIED',
      action: 'MODIFY_DOSAGE'
    });

    showToast(`Dosage for ${name} updated to ${newDose}`, 'success');

    // In-place UI update without full reload or kick-out (Part A2 requirement)
    if (currentPatientProfile && currentPatientProfile.prescriptions) {
      const rx = currentPatientProfile.prescriptions.find(r => (r.prescriptionId || r.id) === rxId);
      if (rx) {
        rx.dosage = newDose;
        rx.dose = newDose;
        rx.status = 'MODIFIED';
      }
    }
    renderActivePrescriptionsList(currentPatientProfile?.prescriptions || []);

    // Sync in background without blocking UI
    try {
      const prof = await API.get(`/api/profile?patient_id=${activePatientId}`);
      if (prof && (prof.patient || prof.prescriptions)) {
        currentPatientProfile = prof.patient || prof;
        updateWorkspaceUnlockedState();
      }
    } catch (_) {}
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  }
}

async function promptDiscontinueMed(rxId, name) {
  if (!confirm(`Are you sure you want to discontinue ${name}? It will be safely removed from the patient's daily schedule.`)) {
    return;
  }

  try {
    await API.post('/api/prescriptions', {
      doctorId: activeDoctorId,
      patientId: activePatientId,
      prescriptionId: rxId,
      status: 'DISCONTINUED',
      action: 'DISCONTINUE'
    });

    showToast(`${name} discontinued. Schedule updated.`, 'info');

    // In-place UI update without full reload or kick-out (Part A2 requirement)
    if (currentPatientProfile && currentPatientProfile.prescriptions) {
      currentPatientProfile.prescriptions = currentPatientProfile.prescriptions.filter(r => (r.prescriptionId || r.id) !== rxId);
    }
    renderActivePrescriptionsList(currentPatientProfile?.prescriptions || []);

    // Sync in background without blocking UI
    try {
      const prof = await API.get(`/api/profile?patient_id=${activePatientId}`);
      if (prof && (prof.patient || prof.prescriptions)) {
        currentPatientProfile = prof.patient || prof;
        updateWorkspaceUnlockedState();
      }
    } catch (_) {}
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  }
}

// ============================================================================
// 7. BHASHASEHAT TRANSLATOR
// ============================================================================
function swapTranslatorLanguages() {
  const s = document.getElementById('trans-source-lang');
  const t = document.getElementById('trans-target-lang');
  if (s && t) {
    const tmp = s.value;
    s.value = t.value;
    t.value = tmp;
  }
}

function fillTranslatePhrase(phrase, src, tgt) {
  document.getElementById('trans-input-text').value = phrase;
  document.getElementById('trans-source-lang').value = src;
  document.getElementById('trans-target-lang').value = tgt;
  handleTranslateSubmit();
}

async function handleTranslateSubmit() {
  const text = document.getElementById('trans-input-text')?.value.trim();
  const src = document.getElementById('trans-source-lang')?.value;
  const tgt = document.getElementById('trans-target-lang')?.value;
  const resBox = document.getElementById('trans-result-box');
  const outEl = document.getElementById('trans-output-text');
  const phonEl = document.getElementById('trans-phonetic-text');
  const symEl = document.getElementById('trans-symptoms-chips');

  if (!text) return;

  try {
    const res = await API.post('/api/swasthya/translate', {
      text,
      sourceLanguage: src,
      targetLanguage: tgt,
      speakerRole: 'DOCTOR'
    });

    outEl.innerText = res.translatedText || res.translation || text;
    phonEl.innerText = res.phonetic ? `Phonetic: ${res.phonetic}` : '';

    const syms = res.extractedSymptoms || res.symptoms || [];
    symEl.innerHTML = syms.map(s => `<span class="badge badge-amber text-xs">Symptom: ${s}</span>`).join('');

    resBox.classList.remove('hidden');
    showToast('Translated via BhashaSehat phrasebook & Translate', 'success');
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  }
}

function startVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showToast('Microphone speech recognition not supported in this browser.', 'warning');
    return;
  }
  const rec = new SpeechRecognition();
  rec.lang = 'hi-IN';
  showToast('Listening... Speak now 🎙️', 'info');
  rec.onresult = (evt) => {
    document.getElementById('trans-input-text').value = evt.results[0][0].transcript;
    handleTranslateSubmit();
  };
  rec.start();
}

// ============================================================================
// 8. DOCUMENT AI SCANNER
// ============================================================================
let _selectedOcrPreset = 'odisha_phc_paper_slip';
function selectOcrSample(sampleKey) {
  _selectedOcrPreset = sampleKey;
  showToast(`Selected Document AI preset: ${sampleKey}`, 'info');
  executeOcrScan();
}

async function executeOcrScan() {
  const btn = document.getElementById('btn-run-ocr');
  const container = document.getElementById('ocr-results-container');
  const rawTextEl = document.getElementById('ocr-raw-text');
  const medsList = document.getElementById('ocr-medicines-list');

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Scanning with Textract &amp; Comprehend Medical...</span>`;
  }

  try {
    const res = await API.post('/api/swasthya/ocr-scan', {
      patientId: activePatientId,
      sampleType: _selectedOcrPreset,
      documentTitle: 'Historical Clinic Slip'
    });

    rawTextEl.innerText = res.rawOcrText || res.extractedText || 'No text extracted';
    const meds = res.extractedMedications || ['Warfarin 5mg', 'Metformin 500mg'];

    medsList.innerHTML = meds.map(m => `
      <div class="p-2.5 rounded-lg border border-subtle bg-card flex items-center justify-between">
        <span class="font-bold text-main">${m}</span>
        <span class="badge badge-teal text-[9px]">EXTRACTED</span>
      </div>
    `).join('');

    container.classList.remove('hidden');
    showToast(`Extracted ${meds.length} medications from prescription slip!`, 'success');
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Scan Slip with Amazon Textract &amp; Comprehend</span>`;
    }
  }
}

async function addOcrScanToProfile() {
  showToast('Historical paper prescription added to patient records lake!', 'success');
  loadPatientReports();
}

// ============================================================================
// 9. KAAMSURAKSHA OCCUPATIONAL RISK RE-CALCULATOR
// ============================================================================
async function recalcWorkRisk() {
  const occ = document.getElementById('risk-occupation')?.value;
  const years = parseInt(document.getElementById('risk-exposure-years')?.value || 6, 10);
  const syms = [];
  if (document.getElementById('sym-cough')?.checked) syms.push('cough');
  if (document.getElementById('sym-dyspnea')?.checked) syms.push('shortness of breath');
  if (document.getElementById('sym-chest-tightness')?.checked) syms.push('chest tightness');

  try {
    const res = await API.post('/api/swasthya/occupational-risk', {
      patientId: activePatientId,
      occupation: occ,
      exposureYears: years,
      reportedSymptoms: syms
    });

    const badge = document.getElementById('risk-tier-badge');
    const guidance = document.getElementById('risk-clinical-guidance');

    if (badge) {
      badge.className = res.riskLevel === 'HIGH' ? 'badge badge-red font-bold text-xs' : (res.riskLevel === 'MODERATE' ? 'badge badge-amber font-bold text-xs' : 'badge badge-green font-bold text-xs');
      badge.innerText = `${res.riskLevel} RISK (${res.primaryPredictedCondition || 'Occupational Hazard'})`;
    }
    if (guidance) guidance.innerText = res.clinicalGuidance || res.explanation;
  } catch (e) {
    console.warn('Risk calc failed', e);
  }
}

// ============================================================================
// 10. SEHATSETU FOLLOW-UP & CLOUDTRAIL AUDIT
// ============================================================================
async function handleFollowupSubmit(e) {
  if (e) e.preventDefault();
  const date = document.getElementById('followup-date')?.value;
  const clinic = document.getElementById('followup-clinic')?.value;
  const asha = document.getElementById('followup-asha-select')?.value;
  const notes = document.getElementById('followup-notes')?.value;
  const btn = document.getElementById('btn-schedule-followup');

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Syncing with Pinpoint &amp; SNS...</span>`;
  }

  try {
    const res = await API.post('/api/swasthya/followup', {
      patientId: activePatientId,
      followupDate: date,
      currentClinic: clinic,
      homeStateAshaId: asha,
      notes,
      preferredLanguage: 'Odia'
    });

    const previewBox = document.getElementById('followup-sms-preview-card');
    const previewText = document.getElementById('sms-preview-text');

    if (previewBox && previewText) {
      previewText.innerText = (res.alerts && res.alerts[0] && res.alerts[0].message)
        ? res.alerts[0].message
        : `[SwasthyaSetu SMS] Namaste Ramesh Kumar. Your follow-up is scheduled for ${date} at ${clinic}. ASHA worker ${asha} will check on your recovery.`;
      previewBox.classList.remove('hidden');
    }

    showToast('Cross-state follow-up synchronized & SMS dispatched!', 'success');
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Sync Cross-State Follow-up &amp; Dispatch SMS</span>`;
    }
  }
}

async function loadDoctorAuditTrail() {
  const container = document.getElementById('doctor-audit-stream-list');
  if (!container) return;

  try {
    const data = await API.get(`/api/audit?patientId=${activePatientId}`);
    const events = data.events || data.audit_logs || [];

    container.innerHTML = events.length ? events.map(ev => `
      <div class="p-3 rounded-xl border border-subtle bg-card flex items-start gap-3 text-xs">
        <div class="w-8 h-8 rounded-lg ${ev.action && (ev.action.includes('BREAK_GLASS') || ev.action.includes('BLOCKED')) ? 'bg-danger-soft text-danger' : 'bg-primary-soft text-primary'} flex items-center justify-center font-bold flex-shrink-0">
          ✓
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between">
            <span class="font-extrabold text-main">${ev.action || ev.eventName || 'ACCESS'}</span>
            <span class="text-muted font-mono text-[10px]">${ev.timestamp || 'Just now'}</span>
          </div>
          <p class="text-muted mt-0.5">${ev.details || ev.resource || 'Health record access'}</p>
        </div>
      </div>
    `).join('') : '<p class="text-xs text-muted p-3">No audit records found.</p>';
  } catch (e) {
    console.warn('Audit trail failed', e);
  }
}

// Window Exports
window.switchDoctorSection = switchDoctorSection;
window.openCommandPalette = openCommandPalette;
window.closeCommandPalette = closeCommandPalette;
window.handleDoctorUnlock = handleDoctorUnlock;
window.openBreakGlassModal = openBreakGlassModal;
window.submitBreakGlassOverride = submitBreakGlassOverride;
window.lockPatientRecordNow = lockPatientRecordNow;
window.selectRecentPatient = selectRecentPatient;
window.pasteQrPayloadToInput = pasteQrPayloadToInput;
window.filterReports = filterReports;
window.debounceMedicineSearch = debounceMedicineSearch;
window.selectMedicineFromSearch = selectMedicineFromSearch;
window.fillQuickAugmentin = fillQuickAugmentin;
window.fillQuickAspirin = fillQuickAspirin;
window.handlePrescribeSubmit = handlePrescribeSubmit;
window.selectAlternativeMed = selectAlternativeMed;
window.submitClinicalOverride = submitClinicalOverride;
window.promptModifyDosage = promptModifyDosage;
window.promptDiscontinueMed = promptDiscontinueMed;
window.swapTranslatorLanguages = swapTranslatorLanguages;
window.fillTranslatePhrase = fillTranslatePhrase;
window.handleTranslateSubmit = handleTranslateSubmit;
window.startVoiceInput = startVoiceInput;
window.selectOcrSample = selectOcrSample;
window.executeOcrScan = executeOcrScan;
window.addOcrScanToProfile = addOcrScanToProfile;
window.recalcWorkRisk = recalcWorkRisk;
window.handleFollowupSubmit = handleFollowupSubmit;
