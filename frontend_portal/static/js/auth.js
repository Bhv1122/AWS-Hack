/**
 * auth.js - Authentication & Multi-Gate Verification Client
 * SwasthyaSetu & AWS Medication Coordination Platform
 * Design Language: Setu Care
 */

let currentPatientStep = 1;
let _createdPatientId = null;
let _createdDoctorId = null;
let _licenseDebounceTimer = null;
let _hospitalDebounceTimer = null;

// ============================================================================
// 1. ROLE & TAB NAVIGATION
// ============================================================================
function switchGatewayRole(role) {
  const patientCard = document.getElementById('role-card-patient');
  const doctorCard = document.getElementById('role-card-doctor');
  const patientSection = document.getElementById('patient-gateway-section');
  const doctorSection = document.getElementById('doctor-gateway-section');

  if (role === 'patient') {
    if (patientCard) {
      patientCard.classList.add('border-primary', 'bg-primary-soft');
      patientCard.classList.remove('border-subtle', 'bg-card');
    }
    if (doctorCard) {
      doctorCard.classList.remove('border-doctor', 'bg-doctor-soft');
      doctorCard.classList.add('border-subtle', 'bg-card');
    }
    if (patientSection) patientSection.classList.remove('hidden');
    if (doctorSection) doctorSection.classList.add('hidden');
  } else {
    if (doctorCard) {
      doctorCard.classList.add('border-doctor', 'bg-doctor-soft');
      doctorCard.classList.remove('border-subtle', 'bg-card');
    }
    if (patientCard) {
      patientCard.classList.remove('border-primary', 'bg-primary-soft');
      patientCard.classList.add('border-subtle', 'bg-card');
    }
    if (doctorSection) doctorSection.classList.remove('hidden');
    if (patientSection) patientSection.classList.add('hidden');
  }
}

function switchAuthTab(role, tab) {
  const loginForm = document.getElementById(`${role}-signin-form`);
  const registerForm = document.getElementById(`${role}-register-form`);
  const loginTab = document.getElementById(`${role}-tab-login`);
  const registerTab = document.getElementById(`${role}-tab-register`);
  const accentClass = role === 'doctor' ? 'text-doctor' : 'text-primary';
  const borderClass = role === 'doctor' ? 'border-doctor' : 'border-primary';

  if (tab === 'login') {
    if (loginForm) loginForm.classList.remove('hidden');
    if (registerForm) registerForm.classList.add('hidden');
    if (loginTab) {
      loginTab.classList.add('font-extrabold', accentClass, borderClass);
      loginTab.classList.remove('text-muted', 'font-semibold', 'border-transparent');
    }
    if (registerTab) {
      registerTab.classList.remove('font-extrabold', accentClass, borderClass);
      registerTab.classList.add('text-muted', 'font-semibold', 'border-transparent');
    }
  } else {
    if (loginForm) loginForm.classList.add('hidden');
    if (registerForm) registerForm.classList.remove('hidden');
    if (registerTab) {
      registerTab.classList.add('font-extrabold', accentClass, borderClass);
      registerTab.classList.remove('text-muted', 'font-semibold', 'border-transparent');
    }
    if (loginTab) {
      loginTab.classList.remove('font-extrabold', accentClass, borderClass);
      loginTab.classList.add('text-muted', 'font-semibold', 'border-transparent');
    }
  }
}

// ============================================================================
// 2. PATIENT 4-STEP WIZARD & REGISTRATION
// ============================================================================
function goToPatientStep(step) {
  if (step < 1 || step > 4) return;
  currentPatientStep = step;

  for (let i = 1; i <= 4; i++) {
    const pane = document.getElementById(`patient-step-${i}`);
    if (pane) {
      if (i === step) pane.classList.remove('hidden');
      else pane.classList.add('hidden');
    }
  }

  const progressBar = document.getElementById('patient-wizard-progress');
  if (progressBar) progressBar.style.width = `${(step / 4) * 100}%`;

  const titles = [
    'Step 1 of 4: Personal Info',
    'Step 2 of 4: Location & Language',
    'Step 3 of 4: Occupation & Health',
    'Step 4 of 4: Security Password'
  ];
  const stepLabel = document.getElementById('patient-step-indicator');
  if (stepLabel) stepLabel.innerText = titles[step - 1];
}

async function handlePatientRegister(e) {
  if (e) e.preventDefault();
  const name = document.getElementById('reg-pat-name')?.value.trim();
  const age = document.getElementById('reg-pat-age')?.value.trim();
  const gender = document.getElementById('reg-pat-gender')?.value;
  const phone = document.getElementById('reg-pat-phone')?.value.trim();
  const origin = document.getElementById('reg-pat-origin')?.value.trim();
  const city = document.getElementById('reg-pat-city')?.value.trim();
  const lang = document.getElementById('reg-pat-lang')?.value;
  const occupation = document.getElementById('reg-pat-occupation')?.value.trim();
  const exposureYears = document.getElementById('reg-pat-exposure')?.value || 5;
  const allergies = document.getElementById('reg-pat-allergies')?.value.split(',').map(s => s.trim()).filter(Boolean);
  const password = document.getElementById('reg-pat-password')?.value || 'Demo@123';

  const btn = document.getElementById('patient-register-btn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Generating SwasthyaID...</span>`;
  }

  try {
    const res = await API.post('/api/auth/register-patient', {
      fullName: name,
      age: parseInt(age, 10),
      gender,
      mobileNumber: phone,
      originState: origin,
      currentCity: city,
      preferredLanguage: lang,
      occupation,
      exposureYears: parseInt(exposureYears, 10),
      allergies,
      password
    });

    _createdPatientId = res.patientId;
    API.setSession({
      role: 'PATIENT',
      patientId: res.patientId,
      name: res.name || name,
      token: res.sessionToken || res.token,
      consentPin: res.consentPin
    });

    // Populate Success Modal
    document.getElementById('ready-pat-id').innerText = res.patientId;
    document.getElementById('ready-pat-name').innerText = res.name || name;
    document.getElementById('ready-pat-abha').innerText = res.abhaId || 'ABHA-GENERATED-SAFE';
    document.getElementById('ready-pat-pin').innerText = res.consentPin || '------';

    renderQrCode('ready-pat-qr', res.qrPayload || res.patientId, 110, 110);
    openModal('patient-success-modal');
    showToast('SwasthyaID and Passport successfully generated!', 'success');
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Generate SwasthyaID &amp; Passport</span>`;
    }
  }
}

function proceedToPatientPortal() {
  if (_createdPatientId) {
    window.location.href = `/patient?patient_id=${_createdPatientId}`;
  } else {
    window.location.href = '/patient';
  }
}

async function handlePatientLogin(e) {
  if (e) e.preventDefault();
  const ident = document.getElementById('patient-login-id')?.value.trim();
  const pwd = document.getElementById('patient-login-password')?.value.trim();
  const btn = document.getElementById('patient-signin-btn');

  if (!ident || !pwd) {
    showToast('Please enter Patient ID and password', 'warning');
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Authenticating...</span>`;
  }

  try {
    const res = await API.post('/api/auth/login-patient', { identifier: ident, password: pwd });
    const pid = res.patientId || ident;
    API.setSession({
      role: 'PATIENT',
      patientId: pid,
      name: res.name || 'Patient',
      token: res.sessionToken || res.token,
      consentPin: res.consentPin
    });

    showToast(`Welcome back, ${res.name || pid}!`, 'success');
    setTimeout(() => {
      window.location.href = `/patient?patient_id=${pid}`;
    }, 400);
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Sign In &amp; Open SwasthyaID Portal</span>`;
    }
  }
}

// ============================================================================
// 3. DOCTOR 4-GATE VERIFICATION & REGISTRATION
// ============================================================================
function debounceLookupLicense(val) {
  clearTimeout(_licenseDebounceTimer);
  const fb = document.getElementById('license-feedback');
  const gateEl = document.getElementById('doc-gate-1');
  const statusEl = document.getElementById('gate-1-status');
  if (!val || val.trim().length < 5) {
    if (fb) fb.classList.add('hidden');
    if (gateEl) gateEl.className = 'gate-step active';
    if (statusEl) statusEl.innerText = '';
    return;
  }

  _licenseDebounceTimer = setTimeout(async () => {
    try {
      const data = await API.get(`/api/registry/license/${encodeURIComponent(val.trim())}`);
      fb.classList.remove('hidden');
      if (data.found && data.status === 'ACTIVE') {
        fb.className = 'text-xs font-semibold p-2.5 rounded-lg border bg-teal-soft text-teal border-teal-border';
        fb.innerHTML = `✓ Active · ${data.council} · ${data.maskedName || 'Verified Practitioner'}`;
        gateEl.className = 'gate-step completed';
        statusEl.innerText = 'VERIFIED';
        statusEl.className = 'text-[11px] font-bold text-teal';
      } else if (data.found && data.status === 'SUSPENDED') {
        fb.className = 'text-xs font-semibold p-2.5 rounded-lg border bg-danger-soft text-danger border-danger-border';
        fb.innerHTML = `✕ Licence Suspended by ${data.council}. Registration blocked.`;
        gateEl.className = 'gate-step failed';
        statusEl.innerText = 'SUSPENDED';
        statusEl.className = 'text-[11px] font-bold text-danger';
      } else if (data.found && data.status === 'EXPIRED') {
        fb.className = 'text-xs font-semibold p-2.5 rounded-lg border bg-danger-soft text-danger border-danger-border';
        fb.innerHTML = `✕ Licence Expired (${data.council}). Renewal required.`;
        gateEl.className = 'gate-step failed';
        statusEl.innerText = 'EXPIRED';
        statusEl.className = 'text-[11px] font-bold text-danger';
      } else {
        fb.className = 'text-xs font-semibold p-2.5 rounded-lg border bg-danger-soft text-danger border-danger-border';
        fb.innerHTML = `✕ Licence number not found in Medical Councils Registry.`;
        gateEl.className = 'gate-step failed';
        statusEl.innerText = 'NOT FOUND';
        statusEl.className = 'text-[11px] font-bold text-danger';
      }
    } catch (e) {
      console.warn('License lookup check failed', e);
    }
  }, 350);
}

function debounceLookupHospital(code) {
  clearTimeout(_hospitalDebounceTimer);
  const fb = document.getElementById('hospital-feedback');
  const gateEl = document.getElementById('doc-gate-2');
  const statusEl = document.getElementById('gate-2-status');
  if (!code || code.trim().length < 4) {
    if (fb) fb.classList.add('hidden');
    if (gateEl) gateEl.className = 'gate-step';
    if (statusEl) statusEl.innerText = '';
    return;
  }

  _hospitalDebounceTimer = setTimeout(async () => {
    try {
      const data = await API.get(`/api/registry/hospital/${encodeURIComponent(code.trim())}`);
      fb.classList.remove('hidden');
      if (data.valid) {
        fb.className = 'text-xs font-semibold p-2.5 rounded-lg border bg-teal-soft text-teal border-teal-border';
        fb.innerHTML = `✓ ${data.name} (${data.city}, ${data.state})`;
        gateEl.className = 'gate-step completed';
        statusEl.innerText = 'AFFILIATED';
        statusEl.className = 'text-[11px] font-bold text-teal';
      } else {
        fb.className = 'text-xs font-semibold p-2.5 rounded-lg border bg-danger-soft text-danger border-danger-border';
        fb.innerHTML = `✕ Hospital code not recognized in national directory.`;
        gateEl.className = 'gate-step failed';
        statusEl.innerText = 'INVALID';
        statusEl.className = 'text-[11px] font-bold text-danger';
      }
    } catch (e) {
      console.warn('Hospital lookup failed', e);
    }
  }, 350);
}

async function handleDoctorRegister(e) {
  if (e) e.preventDefault();
  // Clear previous gate error badges
  [1, 2, 3, 4].forEach(g => {
    const el = document.getElementById(`doc-gate-${g}`);
    if (el) el.classList.remove('failed');
    const fb = document.getElementById(`gate-${g}-feedback`);
    if (fb) fb.classList.add('hidden');
  });

  const licenseNumber = document.getElementById('reg-doc-license')?.value.trim();
  const hospitalCode = document.getElementById('reg-doc-hosp')?.value.trim();
  const name = document.getElementById('reg-doc-name')?.value.trim();
  const degree = document.getElementById('reg-doc-degree')?.value.trim();
  const specialty = document.getElementById('reg-doc-specialty')?.value.trim();
  const govIdProof = document.getElementById('reg-doc-govid')?.value.trim();
  const mfaOtp = document.getElementById('reg-doc-mfa')?.value.trim();
  const password = 'Demo@123';

  const btn = document.getElementById('doctor-register-btn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Executing 4-Gate National Verification...</span>`;
  }

  try {
    const res = await API.post('/api/auth/register-doctor', {
      licenseNumber,
      hospitalCode,
      name,
      degree,
      specialty,
      govIdProof,
      mfaOtp,
      password
    });

    _createdDoctorId = res.doctorId;
    API.setSession({
      role: 'DOCTOR',
      doctorId: res.doctorId,
      name: res.name || name,
      token: res.sessionToken || res.token,
      kmsSessionToken: res.kmsSessionToken
    });

    // Mark all 4 gates completed
    [1, 2, 3, 4].forEach(g => {
      const el = document.getElementById(`doc-gate-${g}`);
      if (el) el.className = 'gate-step completed';
    });

    document.getElementById('ready-doc-id').innerText = res.doctorId;
    document.getElementById('ready-doc-name').innerText = res.name || name;
    document.getElementById('ready-doc-license').innerText = `${res.licenseNumber || licenseNumber} (Verified)`;
    document.getElementById('ready-doc-token').innerText = res.kmsSessionToken || 'KMS:MASTER-KEY:VERIFIED';

    renderQrCode('ready-doc-qr', res.doctorBadge || res.doctorId, 110, 110);
    openModal('doctor-success-modal');
    showToast(`Doctor verified & issued ${res.doctorId}`, 'success');
  } catch (err) {
    const gate = err.gate || 1;
    const gateEl = document.getElementById(`doc-gate-${gate}`);
    if (gateEl) {
      gateEl.className = 'gate-step failed';
      gateEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    const fb = document.getElementById(`gate-${gate}-feedback`) || document.getElementById('license-feedback');
    if (fb) {
      fb.classList.remove('hidden');
      fb.className = 'text-xs font-semibold p-2.5 rounded-lg border bg-danger-soft text-danger border-danger-border mt-2';
      fb.innerHTML = `✕ <strong>Gate ${gate} Verification Failed:</strong> ${err.friendlyMessage || err.message}`;
    }
    showToast(`Gate ${gate} failed: ${err.friendlyMessage || err.message}`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Submit 4-Gate Verification &amp; Issue Credential</span>`;
    }
  }
}

function proceedToDoctorPortal() {
  if (_createdDoctorId) {
    window.location.href = `/doctor?doctor_id=${_createdDoctorId}&patient_id=PAT-SS-1001`;
  } else {
    window.location.href = '/doctor';
  }
}

async function handleDoctorLogin(e) {
  if (e) e.preventDefault();
  const ident = document.getElementById('doctor-login-id')?.value.trim();
  const pwd = document.getElementById('doctor-login-password')?.value.trim();
  const mfa = document.getElementById('doctor-login-mfa')?.value.trim();
  const btn = document.getElementById('doctor-signin-btn');

  if (!ident || !pwd || !mfa) {
    showToast('Please enter Doctor ID, password, and MFA code (654321)', 'warning');
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">↻</span><span>Verifying MFA...</span>`;
  }

  try {
    const res = await API.post('/api/auth/login-doctor', { identifier: ident, password: pwd, mfa_otp: mfa });
    const did = res.doctorId || ident;
    API.setSession({
      role: 'DOCTOR',
      doctorId: did,
      name: res.name || 'Dr. Sharma',
      token: res.sessionToken || res.token,
      kmsSessionToken: res.kmsSessionToken
    });

    showToast(`Practitioner session verified: ${res.name || did}!`, 'success');
    setTimeout(() => {
      window.location.href = `/doctor?doctor_id=${did}&patient_id=PAT-SS-1001`;
    }, 400);
  } catch (err) {
    showToast(err.friendlyMessage || err.message, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Verify MFA &amp; Enter Clinical Workspace</span>`;
    }
  }
}

// ============================================================================
// 4. JUDGE DEMO PRESETS (Doctor Valid & Negative Scenarios, Patient Scenarios)
// ============================================================================
function fillDoctorScenario(scenarioKey) {
  switchGatewayRole('doctor');
  switchAuthTab('doctor', 'register');

  const lic = document.getElementById('reg-doc-license');
  const hosp = document.getElementById('reg-doc-hosp');
  const name = document.getElementById('reg-doc-name');
  const deg = document.getElementById('reg-doc-degree');
  const spec = document.getElementById('reg-doc-specialty');
  const govid = document.getElementById('reg-doc-govid');
  const otp = document.getElementById('reg-doc-mfa');

  if (scenarioKey === 'VALID_KARNATAKA') {
    // Dr. Rajeshwar Rao (unregistered)
    if (lic) lic.value = 'KMC-2021-44120';
    if (hosp) hosp.value = 'HOSP-BLR-990';
    if (name) name.value = 'Dr. Rajeshwar Rao';
    if (deg) deg.value = 'MBBS, MD';
    if (spec) spec.value = 'Cardiology';
    if (govid) govid.value = '4412';
    if (otp) otp.value = '654321';
    showToast('Loaded Scenario: Valid Karnataka Cardiologist (KMC-2021-44120)', 'info');
  } else if (scenarioKey === 'VALID_ODISHA') {
    if (lic) lic.value = 'NMC-IND-55201';
    if (hosp) hosp.value = 'AIIMS-BBSR-101';
    if (name) name.value = 'Dr. Manoj Mohapatra';
    if (deg) deg.value = 'MBBS, MD';
    if (spec) spec.value = 'Pulmonology';
    if (govid) govid.value = '5520';
    if (otp) otp.value = '654321';
    showToast('Loaded Scenario: Valid Odisha Pulmonologist (NMC-IND-55201)', 'info');
  } else if (scenarioKey === 'SUSPENDED') {
    if (lic) lic.value = 'KMC-2016-10233';
    if (hosp) hosp.value = 'HOSP-BLR-990';
    if (name) name.value = 'Dr. Vikram Patel';
    if (deg) deg.value = 'MBBS';
    if (spec) spec.value = 'General Medicine';
    if (govid) govid.value = '1023';
    if (otp) otp.value = '654321';
    showToast('Loaded Scenario: Suspended Licence (Gate 1 Failure expected)', 'warning');
  } else if (scenarioKey === 'EXPIRED') {
    if (lic) lic.value = 'TNMC-2011-45110';
    if (hosp) hosp.value = 'HOSP-BLR-990';
    if (name) name.value = 'Dr. Sundaram Iyer';
    if (deg) deg.value = 'MBBS, DNB';
    if (spec) spec.value = 'Cardiology';
    if (govid) govid.value = '4511';
    if (otp) otp.value = '654321';
    showToast('Loaded Scenario: Expired Licence (Gate 1 Failure expected)', 'warning');
  } else if (scenarioKey === 'NOT_FOUND') {
    if (lic) lic.value = 'KMC-2024-00000';
    if (hosp) hosp.value = 'HOSP-BLR-990';
    if (name) name.value = 'Dr. Fictional Persona';
    if (deg) deg.value = 'MBBS';
    if (spec) spec.value = 'Paediatrics';
    if (govid) govid.value = '0000';
    if (otp) otp.value = '654321';
    showToast('Loaded Scenario: Licence Not In Registry (Gate 1 Failure)', 'warning');
  } else if (scenarioKey === 'WRONG_HOSPITAL') {
    if (lic) lic.value = 'KMC-2018-55120';
    if (hosp) hosp.value = 'HOSP-BLR-990'; // Not affiliated with HOSP-BLR-990
    if (name) name.value = 'Dr. Sunita Deshmukh';
    if (deg) deg.value = 'MBBS, MS';
    if (spec) spec.value = 'Obstetrics & Gynaecology';
    if (govid) govid.value = '5512';
    if (otp) otp.value = '654321';
    showToast('Loaded Scenario: Hospital Not Affiliated (Gate 2 Failure expected)', 'warning');
  } else if (scenarioKey === 'WRONG_GOVID') {
    if (lic) lic.value = 'KMC-2020-77341';
    if (hosp) hosp.value = 'HOSP-BLR-990';
    if (name) name.value = 'Dr. Deepak Hegde';
    if (deg) deg.value = 'MBBS, MD';
    if (spec) spec.value = 'Pulmonology';
    if (govid) govid.value = '9999'; // Real is 7734
    if (otp) otp.value = '654321';
    showToast('Loaded Scenario: Govt ID Mismatch (Gate 3 Failure expected)', 'warning');
  } else if (scenarioKey === 'WRONG_OTP') {
    if (lic) lic.value = 'KMC-2021-44120';
    if (hosp) hosp.value = 'HOSP-BLR-990';
    if (name) name.value = 'Dr. Rajeshwar Rao';
    if (deg) deg.value = 'MBBS, MD';
    if (spec) spec.value = 'Cardiology';
    if (govid) govid.value = '4412';
    if (otp) otp.value = '111111'; // Wrong OTP
    showToast('Loaded Scenario: Invalid MFA OTP (Gate 4 Failure expected)', 'warning');
  }

  if (lic && lic.value) debounceLookupLicense(lic.value);
  if (hosp && hosp.value) debounceLookupHospital(hosp.value);
}

function fillPatientScenario(patientId) {
  switchGatewayRole('patient');
  switchAuthTab('patient', 'login');
  const idEl = document.getElementById('patient-login-id');
  const pwdEl = document.getElementById('patient-login-password');
  if (idEl) idEl.value = patientId;
  if (pwdEl) pwdEl.value = 'Demo@123';
  showToast(`Loaded Patient Scenario: ${patientId}. Click Sign In to open.`, 'info');
}

// Window Exports
window.switchGatewayRole = switchGatewayRole;
window.switchAuthTab = switchAuthTab;
window.goToPatientStep = goToPatientStep;
window.handlePatientRegister = handlePatientRegister;
window.proceedToPatientPortal = proceedToPatientPortal;
window.handlePatientLogin = handlePatientLogin;
window.debounceLookupLicense = debounceLookupLicense;
window.debounceLookupHospital = debounceLookupHospital;
window.handleDoctorRegister = handleDoctorRegister;
window.proceedToDoctorPortal = proceedToDoctorPortal;
window.handleDoctorLogin = handleDoctorLogin;
window.fillDoctorScenario = fillDoctorScenario;
window.fillPatientScenario = fillPatientScenario;
