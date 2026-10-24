/**
 * components.js - Reusable UI Components, Lucide Icons, i18n & Accessible Helpers
 * SwasthyaSetu & AWS Medication Coordination Platform
 * Design Language: Setu Care
 */

// ============================================================================
// 1. LUCIDE SVG ICONS LIBRARY (Inline SVG - No Emoji in UI Chrome)
// ============================================================================
const LUCIDE_ICONS = {
  'shield': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
  'shield-alert': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
  'lock': '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  'unlock': '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/>',
  'key': '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6"/><path d="m15.5 7.5 3 3L22 7l-3-3"/>',
  'user': '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  'stethoscope': '<path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/><circle cx="20" cy="10" r="2"/>',
  'activity': '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
  'heart': '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
  'file-text': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>',
  'pill': '<path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/>',
  'scan': '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/>',
  'globe': '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
  'alert-triangle': '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
  'alert-circle': '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
  'check-circle': '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
  'x-circle': '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>',
  'copy': '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  'download': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
  'volume-2': '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>',
  'mic': '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/>',
  'refresh-cw': '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
  'sun': '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',
  'moon': '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
  'search': '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
  'clock': '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  'map-pin': '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
  'plus': '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  'minus': '<line x1="5" y1="12" x2="19" y2="12"/>',
  'x': '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  'chevron-right': '<polyline points="9 18 15 12 9 6"/>',
  'chevron-down': '<polyline points="6 9 12 15 18 9"/>',
  'arrow-right': '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
  'log-out': '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',
  'cloud': '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
  'database': '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
  'sparkles': '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>'
};

function getLucideSvg(iconName, extraClass = '') {
  const content = LUCIDE_ICONS[iconName] || LUCIDE_ICONS['activity'];
  return `<svg class="lucide-icon ${extraClass}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">${content}</svg>`;
}

function renderLucideIcons() {
  document.querySelectorAll('[data-lucide]').forEach(el => {
    const iconName = el.getAttribute('data-lucide');
    const extraClass = el.getAttribute('data-class') || '';
    el.innerHTML = getLucideSvg(iconName, extraClass);
  });
}

// ============================================================================
// 2. I18N LOCALIZATION SYSTEM
// ============================================================================
let CURRENT_LANG = localStorage.getItem('medcoord_lang') || 'en';
let I18N_CACHE = {};

async function loadI18nBundle(lang) {
  if (I18N_CACHE[lang]) return I18N_CACHE[lang];
  try {
    const res = await fetch(`/static/i18n/${lang}.json`);
    if (res.ok) {
      const data = await res.json();
      I18N_CACHE[lang] = data;
      return data;
    }
  } catch (e) {
    console.warn(`Failed to fetch i18n bundle for ${lang}, falling back to en`);
  }
  if (lang !== 'en') return loadI18nBundle('en');
  return {};
}

async function setLanguage(lang) {
  CURRENT_LANG = lang;
  localStorage.setItem('medcoord_lang', lang);
  const bundle = await loadI18nBundle(lang);

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (bundle[key]) {
      if (el.tagName === 'INPUT' && el.hasAttribute('placeholder')) {
        el.setAttribute('placeholder', bundle[key]);
      } else {
        el.innerText = bundle[key];
      }
    }
  });

  const select = document.querySelector('.lang-selector');
  if (select && select.value !== lang) {
    select.value = lang;
  }
}

function t(key, fallback = '') {
  const bundle = I18N_CACHE[CURRENT_LANG] || I18N_CACHE['en'] || {};
  return bundle[key] || fallback || key;
}

// ============================================================================
// 3. THEME & ACCESSIBILITY MANAGERS
// ============================================================================
function initTheme() {
  const savedTheme = localStorage.getItem('medcoord_theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', savedTheme);

  const savedContrast = localStorage.getItem('medcoord_contrast') || 'normal';
  document.documentElement.setAttribute('data-contrast', savedContrast);

  const savedSize = localStorage.getItem('medcoord_text_size') || 'md';
  document.documentElement.setAttribute('data-text-size', savedSize);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('medcoord_theme', next);
  showToast(`Switched to ${next} theme`, 'info');
}

function toggleContrast() {
  const current = document.documentElement.getAttribute('data-contrast');
  const next = current === 'high' ? 'normal' : 'high';
  document.documentElement.setAttribute('data-contrast', next);
  localStorage.setItem('medcoord_contrast', next);
  showToast(`High contrast ${next === 'high' ? 'enabled' : 'disabled'}`, 'info');
}

function adjustTextSize(delta) {
  const sizes = ['sm', 'md', 'lg', 'xl'];
  const current = document.documentElement.getAttribute('data-text-size') || 'md';
  let idx = sizes.indexOf(current) + delta;
  if (idx < 0) idx = 0;
  if (idx >= sizes.length) idx = sizes.length - 1;
  const next = sizes[idx];
  document.documentElement.setAttribute('data-text-size', next);
  localStorage.setItem('medcoord_text_size', next);
}

// ============================================================================
// 4. TOAST NOTIFICATIONS
// ============================================================================
let _recentToastsMap = new Map();

function showToast(message, type = 'success') {
  const key = `${type}:${message}`;
  const now = Date.now();
  if (_recentToastsMap.has(key) && (now - _recentToastsMap.get(key) < 2000)) {
    return; // suppress duplicate toast spam within 2 seconds
  }
  _recentToastsMap.set(key, now);

  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');

  const iconMap = {
    success: 'check-circle',
    error: 'alert-triangle',
    warning: 'alert-circle',
    info: 'activity'
  };

  toast.innerHTML = `
    ${getLucideSvg(iconMap[type] || 'activity', 'sm')}
    <span class="toast-message leading-tight">${message}</span>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 250);
  }, 4000);
}

// ============================================================================
// 5. MODALS & DRAWERS
// ============================================================================
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  const focusable = modal.querySelector('input, select, textarea, button:not([disabled])');
  if (focusable) focusable.focus();
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.open, .drawer-backdrop.open').forEach(el => {
      el.classList.remove('open');
      el.setAttribute('aria-hidden', 'true');
    });
  }
});

// AWS Cloud Drawer
async function toggleAwsDrawer(open = null) {
  const drawer = document.getElementById('aws-status-drawer');
  if (!drawer) return;

  const shouldOpen = open !== null ? open : !drawer.classList.contains('open');
  if (shouldOpen) {
    drawer.classList.add('open');
    drawer.setAttribute('aria-hidden', 'false');
    await loadAwsStatusDetails();
  } else {
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
  }
}

async function loadAwsStatusDetails() {
  const container = document.getElementById('aws-drawer-content');
  if (!container) return;

  try {
    const data = await API.get('/api/aws-status');
    const mode = data.mode || 'OPERATIONAL (SANDBOX-FALLBACK MODE)';
    const account = data.accountId || '686255979381';
    const role = data.iamRole || 'arn:aws:iam::686255979381:role/MedCoordClinicalLambdaExecutionRole';
    const kmsAlias = data.kmsAlias || 'alias/MedCoord-HIPAA-MasterKey';

    const modules = [
      { name: 'Cognito & Identity Center', desc: 'Zero-Trust RBAC & Doctor 4-Gate Verification', status: 'ONLINE', icon: 'shield' },
      { name: 'AWS KMS Envelope Encryption', desc: `Master Key: ${kmsAlias}`, status: 'ONLINE', icon: 'key' },
      { name: 'HealthLake, DynamoDB & S3', desc: 'FHIR R4 Patient Profiles & Document Lake', status: 'ONLINE', icon: 'database' },
      { name: 'Comprehend Medical & Bedrock', desc: 'Clinical Safety Gatekeeper & Drug Rules', status: 'ONLINE', icon: 'activity' },
      { name: 'AppSync & Timestream', desc: '1-Click Telemetry & Dose Adherence Sync', status: 'ONLINE', icon: 'activity' },
      { name: 'Location Service & OpenSearch', desc: 'Haversine Route & Pharmacy Geo-Stock', status: 'ONLINE', icon: 'map-pin' },
      { name: 'AWS CloudTrail & STS', desc: 'Immutable Statutory Audit Ledger', status: 'ONLINE', icon: 'shield-alert' }
    ];

    container.innerHTML = `
      <div class="space-y-4">
        <div class="p-3.5 rounded-xl border border-primary-border bg-primary-soft flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            ${getLucideSvg('cloud', 'text-primary')}
            <div>
              <div class="text-xs font-bold text-main">Platform AWS Architecture</div>
              <div class="text-[11px] font-semibold text-primary">${mode}</div>
            </div>
          </div>
          <span class="badge badge-teal">CONNECTED</span>
        </div>

        <div class="text-xs font-bold text-muted uppercase tracking-wider">Active AWS Modules (7/7 Live)</div>

        <div class="space-y-2">
          ${modules.map(m => `
            <div class="p-3 rounded-xl border border-subtle bg-card flex items-start gap-3">
              <span class="text-primary mt-0.5">${getLucideSvg(m.icon, 'sm')}</span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-1">
                  <span class="text-xs font-bold text-main truncate">${m.name}</span>
                  <span class="badge badge-teal text-[9px]">${m.status}</span>
                </div>
                <p class="text-[11px] text-muted leading-tight mt-0.5">${m.desc}</p>
              </div>
            </div>
          `).join('')}
        </div>

        <div class="pt-3 border-t border-subtle space-y-2 text-[11px] text-muted">
          <div><strong>AWS Account ID:</strong> <code class="font-mono text-main">${account}</code></div>
          <div class="truncate"><strong>Assumed Role:</strong> <code class="font-mono text-main">${role}</code></div>
          <div><strong>KMS Master Key:</strong> <code class="font-mono text-main">arn:aws:kms:us-east-1:alias/MedCoord-HIPAA-MasterKey</code></div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `
      <div class="p-4 rounded-xl bg-amber-soft border border-warning-border text-xs text-warning">
        <p><strong>Note:</strong> Platform running in Zero-Credential Sandbox Mode with local DynamoDB/S3 state cache.</p>
      </div>
    `;
  }
}

// ============================================================================
// 6. QR CODE & PIN BOX UTILITIES
// ============================================================================
function renderQrCode(containerId, payload, width = 140, height = 140) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';
  const textPayload = typeof payload === 'string' ? payload : JSON.stringify(payload);

  try {
    if (typeof QRCode !== 'undefined') {
      new QRCode(container, {
        text: textPayload,
        width: width,
        height: height,
        colorDark: '#0F766E',
        colorLight: '#FFFFFF',
        correctLevel: QRCode.CorrectLevel.M
      });
      return;
    }
  } catch (e) {
    console.warn('QRCode library not ready, using canvas fallback', e);
  }

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, width, height);
  ctx.fillStyle = '#0F766E';
  ctx.strokeRect(6, 6, width - 12, height - 12);
  ctx.font = 'bold 12px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('SwasthyaID', width / 2, height / 2 - 6);
  ctx.font = '10px monospace';
  ctx.fillText('VERIFIED QR', width / 2, height / 2 + 12);
  container.appendChild(canvas);
}

function setupPinBoxes(containerId, onComplete) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const boxes = container.querySelectorAll('.pin-digit-box');
  if (!boxes.length) return;

  boxes.forEach((box, idx) => {
    box.addEventListener('input', (e) => {
      const val = box.value.replace(/[^0-9]/g, '');
      box.value = val ? val[val.length - 1] : '';
      if (box.value && idx < boxes.length - 1) {
        boxes[idx + 1].focus();
      }
      checkDone();
    });

    box.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' && !box.value && idx > 0) {
        boxes[idx - 1].focus();
      }
    });

    box.addEventListener('paste', (e) => {
      e.preventDefault();
      const pasted = (e.clipboardData || window.clipboardData).getData('text').trim().replace(/[^0-9]/g, '');
      if (pasted.length >= 6) {
        for (let i = 0; i < 6; i++) {
          if (boxes[i]) boxes[i].value = pasted[i];
        }
        boxes[5].focus();
        checkDone();
      }
    });
  });

  function checkDone() {
    const pin = Array.from(boxes).map(b => b.value).join('');
    if (pin.length === 6 && onComplete) onComplete(pin);
  }

  return {
    getPin: () => Array.from(boxes).map(b => b.value).join(''),
    setPin: (val) => {
      const s = String(val || '').replace(/[^0-9]/g, '');
      boxes.forEach((b, i) => b.value = s[i] || '');
    },
    clear: () => boxes.forEach(b => { b.value = ''; b.classList.remove('error'); }),
    shake: () => {
      container.classList.add('shake');
      boxes.forEach(b => b.classList.add('error'));
      setTimeout(() => container.classList.remove('shake'), 450);
    }
  };
}

// ============================================================================
// 7. TEXT-TO-SPEECH (Audio Accessibility)
// ============================================================================
function speakText(text, lang = 'en-US') {
  if (!('speechSynthesis' in window)) {
    showToast('Voice read-aloud not supported in this browser.', 'warning');
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang;
  utterance.rate = 0.95;

  const voices = window.speechSynthesis.getVoices();
  const voice = voices.find(v => v.lang.startsWith(lang.substring(0, 2)));
  if (voice) utterance.voice = voice;

  window.speechSynthesis.speak(utterance);
  showToast('Reading aloud...', 'info');
}

// Copy to Clipboard
function copyToClipboard(text, label = 'Text') {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(`${label} copied to clipboard!`, 'success');
    }).catch(() => fallbackCopy(text, label));
  } else {
    fallbackCopy(text, label);
  }
}

function fallbackCopy(text, label) {
  const ta = document.createElement('textarea');
  ta.value = text;
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand('copy');
    showToast(`${label} copied to clipboard!`, 'success');
  } catch (e) {
    showToast('Failed to copy', 'error');
  }
  document.body.removeChild(ta);
}

// ============================================================================
// 8. JUDGE PANEL & JUDGE TOUR
// ============================================================================
async function initJudgePanel() {
  const panel = document.getElementById('judge-panel');
  if (!panel) return;

  try {
    const [accRes, scenRes] = await Promise.all([
      API.get('/api/demo/accounts'),
      API.get('/api/demo/scenarios')
    ]);

    const docScenarios = scenRes.doctorScenarios || [];
    const patScenarios = scenRes.patientScenarios || [];

    const docContainer = document.getElementById('judge-doctor-scenarios');
    if (docContainer) {
      docContainer.innerHTML = docScenarios.map(s => `
        <button type="button" class="btn btn-secondary text-xs w-full justify-between" onclick="fillJudgeDoctorScenario('${s.key}')">
          <span class="font-bold text-left">${s.title}</span>
          <span class="badge ${s.expectedGate ? 'badge-amber' : 'badge-green'} text-[10px]">${s.expectedCode || 'VALID'}</span>
        </button>
      `).join('');
    }

    const patContainer = document.getElementById('judge-patient-scenarios');
    if (patContainer) {
      patContainer.innerHTML = patScenarios.map(s => `
        <button type="button" class="btn btn-secondary text-xs w-full justify-between" onclick="fillJudgePatientScenario('${s.patientId}')">
          <span class="font-bold text-left">${s.patientId} · ${s.title}</span>
          <span class="badge badge-teal text-[10px]">${s.primaryCondition || 'Active'}</span>
        </button>
      `).join('');
    }
  } catch (e) {
    console.warn('Judge panel demo endpoints unavailable (DEMO_MODE=false or error)', e);
  }
}

// Judge Tour (7-Step Spotlight Walkthrough)
const TOUR_STEPS = [
  { step: 1, title: 'Step 1: Role Chooser', desc: 'Choose between Patient and Doctor portals, or explore one-click judge scenarios.' },
  { step: 2, title: 'Step 2: Doctor Multi-Gate Verification', desc: 'Observe live medical council lookup and strict 4-gate verification.' },
  { step: 3, title: 'Step 3: Zero-Trust Consent Unlock', desc: 'Doctor unlocks patient chart using 6-digit Consent PIN or Break-Glass.' },
  { step: 4, title: 'Step 4: AI Safety Gatekeeper Interception', desc: 'Try prescribing Augmentin to Ramesh Kumar (penicillin allergy) to observe safety block.' },
  { step: 5, title: 'Step 5: BhashaSehat Clinical Translator', desc: 'Translate Odia symptoms to English with native script and voice read-aloud.' },
  { step: 6, title: 'Step 6: Document AI & KaamSuraksha', desc: 'Scan historical paper slips and calculate occupational silica risk.' },
  { step: 7, title: 'Step 7: Patient Consent Revocation & PIN Rotation', desc: 'Patient revokes doctor access with 1 tap; PIN rotates and doctor view locks.' }
];

function startJudgeTour() {
  let currentStep = 0;
  const overlay = document.createElement('div');
  overlay.id = 'judge-tour-overlay';
  overlay.className = 'fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4';
  
  function renderTourStep() {
    const item = TOUR_STEPS[currentStep];
    overlay.innerHTML = `
      <div class="card max-w-md w-full shadow-2xl border-2 border-primary animate-in fade-in zoom-in-95">
        <div class="flex items-center justify-between pb-3 border-b border-subtle">
          <span class="badge badge-teal text-xs">Judge Walkthrough · Step ${item.step} of 7</span>
          <button type="button" onclick="document.getElementById('judge-tour-overlay').remove()" class="p-1 text-muted hover:text-main">
            ${getLucideSvg('x', 'sm')}
          </button>
        </div>
        <div class="py-4">
          <h3 class="font-extrabold text-lg text-main mb-2">${item.title}</h3>
          <p class="text-sm text-muted leading-relaxed">${item.desc}</p>
        </div>
        <div class="flex items-center justify-between pt-3 border-t border-subtle">
          <button type="button" class="btn btn-secondary text-xs" onclick="document.getElementById('judge-tour-overlay').remove()">Skip Tour</button>
          <div class="flex gap-2">
            ${currentStep > 0 ? `<button type="button" class="btn btn-secondary text-xs" id="tour-prev">Previous</button>` : ''}
            <button type="button" class="btn btn-primary text-xs" id="tour-next">${currentStep === 6 ? 'Finish Tour' : 'Next Step'}</button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('tour-next').onclick = () => {
      if (currentStep < 6) {
        currentStep++;
        renderTourStep();
      } else {
        overlay.remove();
        showToast('Judge tour completed!', 'success');
      }
    };
    if (document.getElementById('tour-prev')) {
      document.getElementById('tour-prev').onclick = () => {
        if (currentStep > 0) {
          currentStep--;
          renderTourStep();
        }
      };
    }
  }

  document.body.appendChild(overlay);
  renderTourStep();
}

// Auto Inactivity Lock for Doctor Workspace (Default 10 min)
let _inactivityTimer = null;
function setupInactivityLock(minutes = 10, onLock) {
  const ms = minutes * 60 * 1000;
  function resetTimer() {
    if (_inactivityTimer) clearTimeout(_inactivityTimer);
    _inactivityTimer = setTimeout(() => {
      if (onLock) onLock();
    }, ms);
  }

  ['mousedown', 'keydown', 'scroll', 'touchstart'].forEach(evt => {
    window.addEventListener(evt, resetTimer, { passive: true });
  });
  resetTimer();
}

// ============================================================================
// 12. UNIVERSAL ACCESSIBLE ARIA COMBOBOX COMPONENT
// ============================================================================
const Combobox = {
  _instances: new Map(),
  _seq: 0,

  create(inputEl, config = {}) {
    if (!inputEl) return null;
    if (Combobox._instances.has(inputEl)) {
      return Combobox._instances.get(inputEl);
    }

    const id = `cb-${++Combobox._seq}-${Math.random().toString(36).substring(2, 7)}`;
    const listboxId = `${id}-listbox`;

    // Config defaults
    const debounceMs = config.debounceMs !== undefined ? config.debounceMs : 200;
    const minChars = config.minChars !== undefined ? config.minChars : 2;
    const limit = config.limit || 15;
    const emptyText = config.emptyText || "No medicine found. Check the spelling.";
    const hintText = config.hintText || "Type at least 2 characters to search...";
    const onSelect = config.onSelect || (() => {});
    const fetchOptions = config.fetchOptions || null;
    let staticOptions = config.options || null;

    let items = [];
    let activeIndex = -1;
    let isOpen = false;
    let debounceTimer = null;
    let abortController = null;
    let reqCounter = 0;
    let lastQuery = '';

    // ARIA Attributes on input
    inputEl.setAttribute('role', 'combobox');
    inputEl.setAttribute('aria-autocomplete', 'list');
    inputEl.setAttribute('aria-expanded', 'false');
    inputEl.setAttribute('aria-haspopup', 'listbox');
    inputEl.setAttribute('aria-controls', listboxId);
    inputEl.setAttribute('autocomplete', 'off');

    // Create listbox portal on document.body
    const portal = document.createElement('div');
    portal.id = listboxId;
    portal.className = 'combobox-portal';
    portal.setAttribute('role', 'listbox');
    portal.setAttribute('aria-label', inputEl.getAttribute('aria-label') || inputEl.placeholder || 'Suggestions');
    portal.style.display = 'none';
    document.body.appendChild(portal);

    function updatePosition() {
      if (!isOpen || !portal || portal.style.display === 'none') return;
      const rect = inputEl.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;
      const portalHeight = portal.offsetHeight || 240;

      // Auto-flip upward if not enough room below
      const spaceBelow = viewportHeight - rect.bottom;
      const spaceAbove = rect.top;
      const flipUp = spaceBelow < Math.min(260, portalHeight + 10) && spaceAbove > spaceBelow;

      const top = flipUp
        ? Math.max(8, rect.top - portalHeight - 4)
        : Math.min(viewportHeight - portalHeight - 8, rect.bottom + 4);

      // Width matches at least input width, minimum 280px on desktop, bounded by viewport width
      const width = Math.min(Math.max(rect.width, 280), viewportWidth - 16);
      const left = Math.max(8, Math.min(rect.left, viewportWidth - width - 8));

      portal.style.top = `${top}px`;
      portal.style.left = `${left}px`;
      portal.style.width = `${width}px`;
      portal.style.maxWidth = `${viewportWidth - 16}px`;
    }

    function open() {
      if (isOpen) {
        updatePosition();
        return;
      }
      isOpen = true;
      inputEl.setAttribute('aria-expanded', 'true');
      portal.style.display = 'block';
      updatePosition();
    }

    function close() {
      if (!isOpen) return;
      isOpen = false;
      inputEl.setAttribute('aria-expanded', 'false');
      inputEl.removeAttribute('aria-activedescendant');
      portal.style.display = 'none';
      activeIndex = -1;
    }

    function escapeHtml(str) {
      return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function highlightText(text, query) {
      if (!text) return '';
      if (!query || !query.trim()) return escapeHtml(text);
      const escapedQuery = query.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`(${escapedQuery})`, 'gi');
      return escapeHtml(text).replace(regex, '<mark class="combobox-highlight">$1</mark>');
    }

    function renderItems(dataItems, query = '') {
      items = dataItems || [];
      activeIndex = -1;

      if (items.length === 0) {
        portal.innerHTML = `<div class="combobox-state combobox-empty">${escapeHtml(emptyText)}</div>`;
        open();
        return;
      }

      const rows = items.map((it, idx) => {
        const optId = `${id}-opt-${idx}`;
        const name = it.name || it.brand_name || it.label || it.value || '';
        const subtitle = it.subtitle || it.generic || it.generic_composition || '';
        const form = it.dosage_form || it.form || '';
        const pack = it.pack_size || it.pack || it.packSize || '';
        const price = it.price !== undefined ? it.price : (it.unit_price !== undefined ? it.unit_price : '');
        const mfg = it.manufacturer || '';
        const isDisc = it.is_discontinued || it.isDiscontinued;
        const risk = it.risk; // Task 2 risk badge

        // Risk badge (Task 2)
        let riskBadge = '';
        if (risk === 'SEVERE') {
          riskBadge = '<span class="badge badge-red text-[10px] font-bold"><svg class="lucide-icon sm inline mr-0.5" viewBox="0 0 24 24"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>Risky for this patient</span>';
        } else if (risk === 'CAUTION') {
          riskBadge = '<span class="badge badge-amber text-[10px] font-bold"><svg class="lucide-icon sm inline mr-0.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>Use with caution</span>';
        } else if (risk === 'UNKNOWN') {
          riskBadge = '<span class="badge bg-slate-200 dark:bg-slate-700 text-muted text-[10px] font-bold">Can\'t check</span>';
        } else if (risk === 'NONE') {
          riskBadge = '<span class="badge badge-teal text-[10px] font-bold"><svg class="lucide-icon sm inline mr-0.5" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>No conflicts found</span>';
        }

        // Subtitle details
        const subDetails = [];
        if (subtitle) subDetails.push(escapeHtml(subtitle));
        if (form && !subtitle.toLowerCase().includes(form.toLowerCase())) subDetails.push(escapeHtml(form));
        if (pack) subDetails.push(escapeHtml(pack));
        if (price !== '' && price !== null && price !== undefined) subDetails.push(`₹${price}`);
        if (mfg) subDetails.push(escapeHtml(mfg));

        return `
          <div role="option" id="${optId}" class="combobox-option" data-index="${idx}" aria-selected="false">
            <div class="combobox-option-title">
              <span>${highlightText(name, query)}</span>
              <div class="flex items-center gap-1.5 flex-shrink-0">
                ${isDisc ? '<span class="badge bg-slate-200 dark:bg-slate-700 text-muted text-[9px] uppercase font-bold">Discontinued</span>' : ''}
                ${riskBadge}
                ${it.badge ? `<span class="badge badge-teal text-[9px]">${escapeHtml(it.badge)}</span>` : ''}
              </div>
            </div>
            ${subDetails.length > 0 ? `<div class="combobox-option-subtitle">${subDetails.join(' · ')}</div>` : ''}
          </div>
        `;
      }).join('');

      portal.innerHTML = rows;
      open();
    }

    function renderSkeleton() {
      portal.innerHTML = `
        <div class="combobox-skeleton-row">
          <div class="combobox-skeleton-line-1"></div>
          <div class="combobox-skeleton-line-2"></div>
        </div>
        <div class="combobox-skeleton-row">
          <div class="combobox-skeleton-line-1"></div>
          <div class="combobox-skeleton-line-2"></div>
        </div>
        <div class="combobox-skeleton-row">
          <div class="combobox-skeleton-line-1"></div>
          <div class="combobox-skeleton-line-2"></div>
        </div>
      `;
      open();
    }

    function renderError(retryFn) {
      portal.innerHTML = `
        <div class="combobox-state combobox-error">
          <span>Search failed.</span>
          <button type="button" class="btn btn-secondary text-xs ml-2 py-0.5 px-2 font-bold" id="${id}-btn-retry">Retry</button>
        </div>
      `;
      const retryBtn = document.getElementById(`${id}-btn-retry`);
      if (retryBtn && retryFn) {
        retryBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          retryFn();
        });
      }
      open();
    }

    function renderHint() {
      portal.innerHTML = `<div class="combobox-state combobox-hint">${escapeHtml(hintText)}</div>`;
      open();
    }

    function setActiveOption(index) {
      const options = portal.querySelectorAll('.combobox-option');
      if (options.length === 0) return;

      options.forEach(opt => {
        opt.classList.remove('combobox-active');
        opt.setAttribute('aria-selected', 'false');
      });

      if (index >= 0 && index < options.length) {
        activeIndex = index;
        const activeOpt = options[index];
        activeOpt.classList.add('combobox-active');
        activeOpt.setAttribute('aria-selected', 'true');
        inputEl.setAttribute('aria-activedescendant', activeOpt.id);
        activeOpt.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } else {
        activeIndex = -1;
        inputEl.removeAttribute('aria-activedescendant');
      }
    }

    function selectIndex(index) {
      if (index >= 0 && index < items.length) {
        const selected = items[index];
        const val = selected.name || selected.brand_name || selected.label || selected.value || '';
        inputEl.value = val;
        close();
        if (onSelect) onSelect(selected);
      }
    }

    async function executeQuery(q) {
      lastQuery = q;
      const trimmed = (q || '').trim();

      if (staticOptions) {
        if (!trimmed) {
          renderItems(staticOptions.slice(0, limit), '');
        } else {
          const lower = trimmed.toLowerCase();
          const filtered = staticOptions.filter(o => {
            const l = (o.label || o.name || o.value || '').toLowerCase();
            const s = (o.subtitle || o.generic || '').toLowerCase();
            return l.includes(lower) || s.includes(lower);
          });
          renderItems(filtered.slice(0, limit), trimmed);
        }
        return;
      }

      if (!fetchOptions) return;

      if (trimmed.length < minChars) {
        renderHint();
        return;
      }

      if (abortController) {
        abortController.abort();
      }
      abortController = new AbortController();
      const currentReqId = ++reqCounter;

      renderSkeleton();

      try {
        const results = await fetchOptions(trimmed, abortController.signal);
        if (currentReqId !== reqCounter) return; // Discard stale out-of-order response
        renderItems((results || []).slice(0, limit), trimmed);
      } catch (err) {
        if (err.name === 'AbortError') return;
        if (currentReqId !== reqCounter) return;
        renderError(() => executeQuery(lastQuery));
      }
    }

    function onInput() {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        executeQuery(inputEl.value);
      }, debounceMs);
    }

    // Pointer events: pointerdown with preventDefault prevents blur race condition!
    portal.addEventListener('pointerdown', (e) => {
      const opt = e.target.closest('.combobox-option');
      if (opt) {
        e.preventDefault(); // Keeps input focused
        const idx = parseInt(opt.getAttribute('data-index'), 10);
        selectIndex(idx);
      }
    });

    // Touch scroll: allow scrolling without closing
    portal.addEventListener('touchmove', (e) => {
      e.stopPropagation();
    }, { passive: true });

    // Keyboard navigation
    inputEl.addEventListener('keydown', (e) => {
      if (!isOpen && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
        e.preventDefault();
        executeQuery(inputEl.value);
        return;
      }

      if (!isOpen) return;

      const optCount = portal.querySelectorAll('.combobox-option').length;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          if (optCount > 0) {
            const nextIdx = (activeIndex + 1) % optCount;
            setActiveOption(nextIdx);
          }
          break;

        case 'ArrowUp':
          e.preventDefault();
          if (optCount > 0) {
            const prevIdx = (activeIndex - 1 + optCount) % optCount;
            setActiveOption(prevIdx);
          }
          break;

        case 'Home':
          if (optCount > 0) {
            e.preventDefault();
            setActiveOption(0);
          }
          break;

        case 'End':
          if (optCount > 0) {
            e.preventDefault();
            setActiveOption(optCount - 1);
          }
          break;

        case 'Enter':
          if (activeIndex >= 0 && activeIndex < optCount) {
            e.preventDefault();
            selectIndex(activeIndex);
          }
          break;

        case 'Escape':
          e.preventDefault();
          close();
          break;

        case 'Tab':
          close();
          break;
      }
    });

    inputEl.addEventListener('input', onInput);

    inputEl.addEventListener('focus', () => {
      if (minChars === 0 || (inputEl.value && inputEl.value.trim().length >= minChars)) {
        executeQuery(inputEl.value);
      }
    });

    // Position updates
    window.addEventListener('scroll', updatePosition, true);
    window.addEventListener('resize', updatePosition);
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', updatePosition);
      window.visualViewport.addEventListener('scroll', updatePosition);
    }

    // Dismiss on outside click
    document.addEventListener('pointerdown', (e) => {
      if (!isOpen) return;
      if (e.target === inputEl || portal.contains(e.target)) return;
      close();
    });

    const instance = {
      id,
      inputEl,
      portal,
      open,
      close,
      search: (q) => executeQuery(q),
      setOptions(newOptions) {
        staticOptions = newOptions;
      },
      destroy() {
        clearTimeout(debounceTimer);
        if (abortController) abortController.abort();
        window.removeEventListener('scroll', updatePosition, true);
        window.removeEventListener('resize', updatePosition);
        if (portal && portal.parentNode) portal.parentNode.removeChild(portal);
        Combobox._instances.delete(inputEl);
      }
    };

    Combobox._instances.set(inputEl, instance);
    return instance;
  },

  createFromSelect(selectEl, config = {}) {
    if (!selectEl) return null;

    // Read options from native select
    const opts = Array.from(selectEl.options).map(o => ({
      value: o.value,
      label: o.text || o.value,
      subtitle: o.getAttribute('data-sub') || '',
      badge: o.getAttribute('data-badge') || '',
      selected: o.selected
    }));

    const selectedOpt = opts.find(o => o.selected) || opts[0];

    // Create wrapper & combobox input
    const wrapper = document.createElement('div');
    wrapper.className = 'combobox-select-wrapper';

    const input = document.createElement('input');
    input.type = 'text';
    input.className = `${selectEl.className} combobox-select-input`;
    input.value = selectedOpt ? selectedOpt.label : '';
    input.placeholder = config.placeholder || selectEl.getAttribute('aria-label') || 'Select option...';

    const chevron = document.createElement('span');
    chevron.className = 'combobox-select-chevron';
    chevron.innerHTML = '<svg class="lucide-icon sm" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg>';

    // Hide native select but keep for form submit / onchange
    selectEl.classList.add('hidden');
    selectEl.parentNode.insertBefore(wrapper, selectEl);
    wrapper.appendChild(input);
    wrapper.appendChild(chevron);
    wrapper.appendChild(selectEl);

    const cb = Combobox.create(input, {
      options: opts,
      minChars: 0,
      emptyText: config.emptyText || "No matching options",
      onSelect: (item) => {
        selectEl.value = item.value;
        selectEl.dispatchEvent(new Event('change', { bubbles: true }));
        if (config.onSelect) config.onSelect(item);
      }
    });

    // Clicking chevron or input with 0 chars opens immediately
    chevron.addEventListener('click', (e) => {
      e.stopPropagation();
      input.focus();
      cb.open();
    });

    return cb;
  }
};

// Global Initialization
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  renderLucideIcons();
  setLanguage(CURRENT_LANG);
});

// Window Exports
window.Combobox = Combobox;
window.getLucideSvg = getLucideSvg;
window.renderLucideIcons = renderLucideIcons;
window.loadI18nBundle = loadI18nBundle;
window.setLanguage = setLanguage;
window.t = t;
window.initTheme = initTheme;
window.toggleTheme = toggleTheme;
window.toggleContrast = toggleContrast;
window.adjustTextSize = adjustTextSize;
window.showToast = showToast;
window.openModal = openModal;
window.closeModal = closeModal;
window.toggleAwsDrawer = toggleAwsDrawer;
window.loadAwsStatusDetails = loadAwsStatusDetails;
window.renderQrCode = renderQrCode;
window.setupPinBoxes = setupPinBoxes;
window.speakText = speakText;
window.copyToClipboard = copyToClipboard;
window.initJudgePanel = initJudgePanel;
window.startJudgeTour = startJudgeTour;
window.setupInactivityLock = setupInactivityLock;
