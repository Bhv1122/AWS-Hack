/**
 * patient.js - Patient Mobile-First Health Portal Client
 * SwasthyaSetu & AWS Medication Coordination Platform
 * Design Language: Setu Care
 */

let activePatientId = 'PAT-SS-1001';
let patientAdherencePct = 70;
let patientStreakDays = 14;
let liveConsentPin = '482910';
let currentProfileData = null;

// ============================================================================
// 1. INITIALIZATION & DATA LOADING
// ============================================================================
document.addEventListener('DOMContentLoaded', async () => {
  const params = new URLSearchParams(window.location.search);
  const rawPid = params.get('patient_id') || 'PAT-SS-1001';
  activePatientId = rawPid === 'PAT-1001' ? 'PAT-SS-1001' : rawPid;

  const session = API.getSession();
  if (session && session.patientId) {
    activePatientId = session.patientId;
  }

  // Load Full Patient Profile
  await loadPatientProfile();

  // Load Consent Access Status (Who can see my records)
  await checkConsentAccessStatus();

  // Initial QR
  renderPassportQr();

  // Initial tab (supports ?tab=passport etc.)
  const initialTab = params.get('tab') || 'home';
  switchPatientTab(initialTab);

  // Auto-refresh consent & doses every 20s
  setInterval(() => {
    if (!document.hidden) {
      checkConsentAccessStatus();
      loadPatientProfile();
    }
  }, 20000);
});

// ============================================================================
// 2. TAB NAVIGATION SWITCHER
// ============================================================================
function switchPatientTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.getAttribute('data-tab') === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  document.querySelectorAll('.patient-tab-pane').forEach(pane => {
    if (pane.id === `tab-${tabId}`) {
      pane.classList.remove('hidden');
    } else {
      pane.classList.add('hidden');
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (tabId === 'passport') {
    renderPassportQr();
    loadPatientAuditTimeline();
  } else if (tabId === 'pharmacy') {
    loadPharmaciesList('Warfarin');
  } else if (tabId === 'reports') {
    loadPatientReports();
  } else if (tabId === 'alerts') {
    loadPatientAlerts();
  }
}

// ============================================================================
// 3. PROFILE & DOCTOR ACCESS STATUS
// ============================================================================
async function loadPatientProfile() {
  try {
    const data = await API.get(`/api/profile?patient_id=${activePatientId}`);
    currentProfileData = data.patient || data;
    const p = currentProfileData;

    // Greeting
    const nameEl = document.getElementById('home-patient-name');
    if (nameEl) nameEl.innerText = p.name || 'Ramesh Kumar';

    // Passport
    const pidEl = document.getElementById('passport-id-val');
    if (pidEl) pidEl.innerText = p.id || activePatientId;
    const abhaEl = document.getElementById('passport-abha-val');
    if (abhaEl) abhaEl.innerText = p.abhaId || 'ABHA-21-9845-3310-7742';

    // Live PIN
    if (p.consent && p.consent.pin) {
      liveConsentPin = p.consent.pin;
    }
    const pinEl = document.getElementById('passport-live-pin');
    if (pinEl) pinEl.innerText = liveConsentPin;

    // Render Medicines tab
    renderMedicinesTab(p.prescriptions || []);
  } catch (e) {
    console.warn('Profile fetch failed', e);
  }
}

async function checkConsentAccessStatus() {
  const statusEl = document.getElementById('consent-access-status-text');
  if (!statusEl) return;

  try {
    const data = await API.get(`/api/consent/status?patientId=${activePatientId}`);
    if (data.activeGrant) {
      statusEl.innerHTML = `Your doctor can see your records: <strong class="text-teal">Yes (${data.doctorInitials || 'Doctor'} via ${data.method || 'PIN'})</strong>`;
    } else {
      statusEl.innerHTML = `Your doctor can see your records: <strong class="text-muted">No (Private)</strong>`;
    }
  } catch (_) {
    statusEl.innerHTML = `Your doctor can see your records: <strong class="text-muted">No (Private)</strong>`;
  }
}

function renderPassportQr() {
  const qrContainer = document.getElementById('patient-passport-qr');
  if (!qrContainer) return;
  const payload = JSON.stringify({
    patientId: activePatientId,
    abhaId: currentProfileData?.abhaId || 'ABHA-21-9845-3310-7742',
    name: currentProfileData?.name || 'Ramesh Kumar',
    synthetic: true
  });
  renderQrCode('patient-passport-qr', payload, 140, 140);
}

// ============================================================================
// 4. DOSE ADHERENCE & 1-CLICK TELEMETRY
// ============================================================================
async function markDoseTaken(rxId, medName, slot) {
  const btn = document.getElementById(`btn-take-${rxId}`);
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Confirming Dose...</span>`;
  }

  try {
    const res = await API.post('/api/adherence', {
      patient_id: activePatientId,
      prescription_id: rxId,
      status: 'TAKEN',
      scheduled_slot: slot || 'Morning 08:00'
    });

    if (btn) {
      btn.className = 'btn btn-secondary w-full text-xs font-bold text-success opacity-90 cursor-default';
      btn.innerHTML = `✓ Taken at ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }

    patientStreakDays += 1;
    patientAdherencePct = Math.min(100, patientAdherencePct + 5);

    const sEl = document.getElementById('home-streak-days');
    if (sEl) sEl.innerText = patientStreakDays;

    const pEl = document.getElementById('home-adherence-pct');
    if (pEl) pEl.innerText = `${patientAdherencePct}%`;

    showToast(`Dose of ${medName} marked taken! Adherence streak updated.`, 'success');
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Mark Taken</span>`;
    }
  }
}

function simulateMissedDose() {
  patientStreakDays = 0;
  patientAdherencePct = Math.max(40, patientAdherencePct - 15);
  const sEl = document.getElementById('home-streak-days');
  if (sEl) sEl.innerText = '0';
  const pEl = document.getElementById('home-adherence-pct');
  if (pEl) pEl.innerText = `${patientAdherencePct}%`;
  showToast('Simulated missed dose. Caregiver alert dispatched to Sunita Kumar.', 'warning');
}

function readAloudGreeting() {
  const name = currentProfileData?.name || 'Ramesh';
  speakText(`Namaste ${name}. You have taken one of your scheduled doses today. Your next dose of Warfarin is scheduled for tonight at eight PM.`, 'en-US');
}

// ============================================================================
// 5. MEDICINES TAB & EXPORT SCHEDULE PDF
// ============================================================================
function renderMedicinesTab(prescriptions) {
  const container = document.getElementById('patient-medicines-list');
  if (!container) return;

  const defaultMeds = [
    { medicationName: 'Warfarin', dosage: '5mg', instructions: 'Take 1 tablet after food at night. Do not miss doses.', status: 'ACTIVE' },
    { medicationName: 'Metformin', dosage: '500mg', instructions: 'Take with breakfast in the morning.', status: 'ACTIVE' },
    { medicationName: 'Atorvastatin', dosage: '20mg', instructions: 'Take at bedtime for cholesterol.', status: 'ACTIVE' }
  ];

  const list = prescriptions && prescriptions.length ? prescriptions : defaultMeds;

  container.innerHTML = list.map(m => {
    const isRisky = m.hasConflict || m.isRisky || m.risk === 'SEVERE' || m.risk === 'CAUTION' || m.riskBadge === 'RISKY';
    const cautionBadgeHtml = isRisky ? `
      <div class="p-2.5 rounded-lg border border-warning-border bg-warning-soft text-xs text-warning-ink flex items-center justify-between gap-2">
        <div class="flex items-center gap-1.5 font-bold">
          <svg class="lucide-icon sm text-warning flex-shrink-0" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <span>Ask your doctor about this medicine; it may not suit your allergy</span>
        </div>
        <button type="button" onclick="speakText('Ask your doctor about this medicine; it may not suit your allergy', 'en-US')" class="btn-read-aloud text-xs whitespace-nowrap">
          Read aloud
        </button>
      </div>
    ` : '';

    return `
      <div class="card p-4 space-y-2 border border-subtle">
        <div class="flex items-center justify-between pb-2 border-b border-subtle">
          <div class="flex items-center gap-2">
            <span class="font-extrabold text-base text-main">${m.medicationName || m.medication}</span>
            <span class="badge badge-teal text-xs">${m.dosage || '500mg'}</span>
          </div>
          <span class="badge badge-green text-[10px]">ACTIVE</span>
        </div>
        ${cautionBadgeHtml}
        <p class="text-xs text-muted leading-relaxed">${m.instructions || 'Take as advised by your doctor.'}</p>
        <div class="flex items-center justify-between pt-1 text-xs">
          <span class="text-muted">Doctor: ${m.prescribedBy || 'Dr. Sharma'}</span>
          <button type="button" onclick="speakText('${m.medicationName || m.medication}. Dosage ${m.dosage}. ${m.instructions}', 'en-US')" class="btn-read-aloud">
            Read aloud 🔊
          </button>
        </div>
      </div>
    `;
  }).join('');
}

function exportSchedulePdf() {
  showToast('Generating personalized bilingual Medication Schedule PDF...', 'info');
  setTimeout(() => {
    window.open(`/api/export-pdf?patient_id=${activePatientId}`, '_blank');
  }, 400);
}

// ============================================================================
// 6. REVOKE DOCTOR ACCESS & PIN ROTATION
// ============================================================================
async function promptRevokeConsent() {
  if (!confirm('Are you sure you want to revoke doctor access? Any doctor currently viewing your health record will be locked out immediately, and a new Consent PIN will be generated.')) {
    return;
  }

  const btn = document.getElementById('btn-revoke-pin');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Revoking Doctor Access &amp; Rotating PIN...</span>`;
  }

  try {
    const res = await API.post('/api/auth/revoke-consent', {
      patientId: activePatientId
    });

    const newPin = res.newConsentPin || res.consentPin;
    if (newPin) {
      liveConsentPin = newPin;
      const pinEl = document.getElementById('passport-live-pin');
      if (pinEl) {
        pinEl.classList.add('pin-card-flip');
        pinEl.innerText = newPin;
      }
    }

    await checkConsentAccessStatus();
    loadPatientAuditTimeline();
    showToast('Doctor access revoked! Your live Consent PIN has been rotated.', 'success');
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Revoke Doctor Access &amp; Rotate PIN</span>`;
    }
  }
}

// ============================================================================
// 7. REPORTS TAB & PAPER SCANNING
// ============================================================================
async function loadPatientReports() {
  const container = document.getElementById('patient-reports-list');
  if (!container) return;

  try {
    const data = await API.get(`/api/reports?patientId=${activePatientId}`);
    const reports = data.reports || [];

    container.innerHTML = reports.length ? reports.map(r => `
      <div class="card p-4 space-y-2 border border-subtle">
        <div class="flex items-center justify-between pb-2 border-b border-subtle">
          <div>
            <h4 class="font-extrabold text-sm text-main">${r.title}</h4>
            <span class="text-[11px] text-muted">${r.date} · ${r.facility}</span>
          </div>
          <span class="badge ${r.source === 'HOME_STATE_PHC' ? 'badge-amber' : 'badge-teal'} text-[9px]">
            ${r.source === 'HOME_STATE_PHC' ? 'ODISHA PHC' : 'BENGALURU'}
          </span>
        </div>
        <p class="text-xs text-muted leading-relaxed">${r.findings || r.impression || 'Test completed and verified by clinic doctor.'}</p>
        <button type="button" onclick="speakText('${r.title}. ${r.findings || r.impression || 'Normal'}', 'en-US')" class="btn-read-aloud">
          Read aloud 🔊
        </button>
      </div>
    `).join('') : '<p class="text-xs text-muted p-4 text-center">No reports found.</p>';
  } catch (e) {
    console.warn('Reports load failed', e);
  }
}

function openPatientScanSlipModal() {
  showToast('Opening Document AI camera scanner...', 'info');
}

function openPatientWorkCheckModal() {
  showToast('Opening KaamSuraksha work health check...', 'info');
}

// ============================================================================
// 8. PHARMACIES FINDER & STOCK RESERVATION
// ============================================================================
async function loadPharmaciesList(query = 'Warfarin') {
  const container = document.getElementById('patient-pharmacies-list');
  if (!container) return;

  try {
    const data = await API.get(`/api/pharmacies/locate?q=${encodeURIComponent(query)}&patient_id=${activePatientId}`);
    const pharmacies = data.pharmacies || data.alternativePharmacies || [];

    container.innerHTML = pharmacies.slice(0, 5).map(ph => `
      <div class="card p-4 space-y-3 border border-subtle">
        <div class="flex items-start justify-between">
          <div>
            <h4 class="font-extrabold text-sm text-main">${ph.name}</h4>
            <p class="text-xs text-muted">${ph.address || 'Whitefield, Bengaluru'}</p>
            <span class="text-[11px] font-bold text-primary mt-1 block">
              📍 ${(ph.distanceKm || ph.distance_km || 1.2).toFixed(1)} km away (${ph.driveTimeFormatted || '5 mins'})
            </span>
          </div>
          <span class="badge ${ph.stockStatus === 'IN_STOCK' || ph.isInStock ? 'badge-green' : 'badge-amber'} text-[10px]">
            ${ph.stockStatus === 'IN_STOCK' || ph.isInStock ? 'IN STOCK' : 'LOW STOCK'}
          </span>
        </div>
        <button type="button" onclick="reserveMedication('${ph.pharmacyId || ph.id || 'PHARM-403'}', '${ph.name.replace(/'/g, "\\'")}', '${query}')" class="btn btn-primary w-full text-xs font-bold">
          Reserve at Counter &amp; Get Pickup Code
        </button>
      </div>
    `).join('');
  } catch (e) {
    console.warn('Pharmacy locate failed', e);
  }
}

async function reserveMedication(pharmId, pharmName, medName) {
  try {
    const res = await API.post('/api/pharmacies/reserve', {
      patient_id: activePatientId,
      prescription_id: 'RX-WAR-1001',
      pharmacy_id: pharmId
    });

    const code = res.pickupCode || 'PICKUP-78DD-0FB9';
    document.getElementById('voucher-pharm-name').innerText = pharmName;
    document.getElementById('voucher-med-name').innerText = `${medName} (5mg) · 30 Days Stock`;
    document.getElementById('voucher-pickup-code').innerText = code;

    openModal('voucher-modal');
    showToast(`Stock reserved at ${pharmName}! Code: ${code}`, 'success');
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  }
}

// ============================================================================
// 9. AUDIT TIMELINE & CARE ALERTS FEED
// ============================================================================
async function loadPatientAuditTimeline() {
  const container = document.getElementById('patient-audit-timeline');
  if (!container) return;

  try {
    const data = await API.get(`/api/audit?patientId=${activePatientId}`);
    const events = data.events || data.audit_logs || [];

    container.innerHTML = events.length ? events.map(ev => {
      const isBreakGlass = ev.action && ev.action.includes('BREAK_GLASS');
      return `
        <div class="p-3 rounded-xl border ${isBreakGlass ? 'border-danger bg-danger-soft' : 'border-subtle bg-card-subtle'} text-xs space-y-1">
          <div class="flex items-center justify-between">
            <span class="font-extrabold ${isBreakGlass ? 'text-danger' : 'text-main'}">${ev.action || 'ACCESS'}</span>
            <span class="text-muted font-mono text-[10px]">${ev.timestamp || 'Recent'}</span>
          </div>
          <p class="${isBreakGlass ? 'text-danger font-semibold' : 'text-muted'}">${ev.details || ev.resource || 'Health record view'}</p>
          ${isBreakGlass && ev.justification ? `<p class="text-danger font-mono text-[11px]">Reason: "${ev.justification}"</p>` : ''}
        </div>
      `;
    }).join('') : '<p class="text-xs text-muted p-2">No past accesses.</p>';
  } catch (e) {
    console.warn('Audit fetch failed', e);
  }
}

async function loadPatientAlerts() {
  const container = document.getElementById('patient-alerts-feed');
  if (!container) return;

  try {
    const data = await API.get(`/api/swasthya/alerts?patientId=${activePatientId}`);
    const alerts = data.alerts || [
      { channel: 'SMS', text: 'Namaste Ramesh, your follow-up is scheduled with Dr. Sharma for Nov 20.', time: '2 hours ago' },
      { channel: 'WHATSAPP', text: 'Daily Reminder: Please take your Warfarin tablet after food.', time: 'Yesterday' }
    ];

    container.innerHTML = alerts.map(a => `
      <div class="p-3.5 rounded-xl border border-subtle bg-card flex items-start gap-3 text-xs shadow-xs">
        <div class="w-8 h-8 rounded-lg bg-teal-soft text-teal flex items-center justify-center font-bold flex-shrink-0">
          💬
        </div>
        <div class="flex-1">
          <div class="flex items-center justify-between pb-1">
            <span class="badge badge-teal text-[9px]">${a.channel || 'SMS'}</span>
            <span class="text-[10px] text-muted">${a.time || 'Today'}</span>
          </div>
          <p class="text-main leading-relaxed">${a.text || a.message}</p>
        </div>
      </div>
    `).join('');
  } catch (e) {
    console.warn('Alerts fetch failed', e);
  }
}

// Window Exports
window.switchPatientTab = switchPatientTab;
window.markDoseTaken = markDoseTaken;
window.simulateMissedDose = simulateMissedDose;
window.readAloudGreeting = readAloudGreeting;
window.exportSchedulePdf = exportSchedulePdf;
window.promptRevokeConsent = promptRevokeConsent;
window.openPatientScanSlipModal = openPatientScanSlipModal;
window.openPatientWorkCheckModal = openPatientWorkCheckModal;
window.loadPharmaciesList = loadPharmaciesList;
window.reserveMedication = reserveMedication;
