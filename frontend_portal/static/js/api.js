/**
 * api.js - Centralized HTTP, Session & Error Mapping Client
 * SwasthyaSetu & AWS Medication Coordination Platform
 * Design Language: Setu Care
 */

const ERROR_CODE_MAP = {
  'LICENSE_SUSPENDED': 'This medical council license is currently suspended.',
  'LICENSE_EXPIRED': 'Medical council license validity has expired. Renewal required.',
  'LICENSE_NOT_FOUND': 'Medical council license was not found in the national or state registry.',
  'ALREADY_REGISTERED': 'This medical license is already registered. Please sign in instead.',
  'HOSPITAL_NOT_AFFILIATED': 'Doctor is not affiliated with this hospital code.',
  'HOSPITAL_NOT_FOUND': 'Hospital code not found in the national registry.',
  'GOVID_MISMATCH': 'Government ID verification failed. Last 4 digits do not match registry records.',
  'MFA_INVALID': 'Invalid MFA verification OTP. Please enter the valid 6-digit code.',
  'PIN_RATE_LIMITED': 'Too many incorrect PIN attempts. Security cooldown active for 60 seconds.',
  'TOO_MANY_ATTEMPTS': 'Too many incorrect PIN attempts. Security cooldown active.',
  'INVALID_PIN': 'Invalid Consent PIN. Please check the current PIN with the patient.',
  'PIN_INVALID': 'Invalid Consent PIN. Please check the current PIN with the patient.',
  'CONSENT_REVOKED': 'Patient has revoked access to their health records.',
  'PATIENT_NOT_FOUND': 'Patient record not found in national registry.',
  'NOT_VERIFIED_DOCTOR': 'Doctor credentials could not be verified.',
  'SESSION_EXPIRED': 'Your session has expired. Please sign in again.',
  'UNAUTHORIZED': 'Your session has expired or requires authentication.',
  'FORBIDDEN': 'Access denied. You do not have permission for this patient record.',
  'CONTRAINDICATION_BLOCKED': 'Prescription blocked by clinical safety gatekeeper.',
  'STOCK_UNAVAILABLE': 'Medication stock is currently unavailable at this pharmacy.'
};

class ApiError extends Error {
  constructor(message, code, gate, status, rawData) {
    super(message);
    this.name = 'ApiError';
    this.code = code || 'UNKNOWN_ERROR';
    this.gate = gate;
    this.status = status;
    this.rawData = rawData;
    this.friendlyMessage = ERROR_CODE_MAP[this.code] || message;
  }
}

const API = {
  // Session State Storage with Role-Namespacing (Part A2 Requirement)
  _getRoleKey() {
    const path = window.location.pathname;
    if (path.startsWith('/doctor')) return 'doctor_session';
    if (path.startsWith('/patient')) return 'patient_session';
    const params = new URLSearchParams(window.location.search);
    if (params.has('doctor_id')) return 'doctor_session';
    if (params.has('patient_id')) return 'patient_session';
    return 'doctor_session';
  },

  getSession() {
    try {
      const path = window.location.pathname;
      const key = this._getRoleKey();
      let data = sessionStorage.getItem(key);

      // Verify that doctor page gets doctor session, patient gets patient session
      if (path.startsWith('/doctor')) {
        data = sessionStorage.getItem('doctor_session') || data;
      } else if (path.startsWith('/patient')) {
        data = sessionStorage.getItem('patient_session') || data;
      }
      if (!data) {
        data = sessionStorage.getItem('medcoord_session');
      }

      if (data) {
        const parsed = JSON.parse(data);
        if (path.startsWith('/doctor') && parsed.role === 'PATIENT') {
          const docData = sessionStorage.getItem('doctor_session');
          if (docData) return JSON.parse(docData);
        } else if (path.startsWith('/patient') && parsed.role === 'DOCTOR') {
          const patData = sessionStorage.getItem('patient_session');
          if (patData) return JSON.parse(patData);
        } else {
          return parsed;
        }
      }
      
      // Fallback for direct browser URL navigation
      const params = new URLSearchParams(window.location.search);
      if (path === '/doctor' || path.startsWith('/doctor') || params.has('doctor_id')) {
        const did = params.get('doctor_id') || 'DOC-IN-8841';
        const s = { token: 'TOKEN-DOC-' + did, sessionToken: 'TOKEN-DOC-' + did, role: 'DOCTOR', doctorId: did, userId: did, name: 'Dr. Sarah Jenkins' };
        sessionStorage.setItem('doctor_session', JSON.stringify(s));
        return s;
      } else if (path === '/patient' || path.startsWith('/patient') || params.has('patient_id')) {
        const pid = params.get('patient_id') || 'PAT-SS-1001';
        const s = { token: 'TOKEN-PAT-' + pid, sessionToken: 'TOKEN-PAT-' + pid, role: 'PATIENT', patientId: pid, userId: pid, name: 'Ramesh Kumar' };
        sessionStorage.setItem('patient_session', JSON.stringify(s));
        return s;
      }
      return null;
    } catch (e) {
      return null;
    }
  },

  setSession(sessionData) {
    try {
      if (!sessionData) return;
      const role = (sessionData.role || '').toUpperCase();
      const key = role === 'DOCTOR' ? 'doctor_session' : (role === 'PATIENT' ? 'patient_session' : 'medcoord_session');
      sessionStorage.setItem(key, JSON.stringify(sessionData));
      sessionStorage.setItem('medcoord_session', JSON.stringify(sessionData));
    } catch (e) {
      console.warn('Failed to persist session to sessionStorage', e);
    }
  },

  clearSession(role) {
    try {
      const path = window.location.pathname;
      const targetRole = role || (path.startsWith('/doctor') ? 'DOCTOR' : (path.startsWith('/patient') ? 'PATIENT' : ''));
      if (targetRole === 'DOCTOR') {
        sessionStorage.removeItem('doctor_session');
        sessionStorage.removeItem('doctor_unlocked_patient');
      } else if (targetRole === 'PATIENT') {
        sessionStorage.removeItem('patient_session');
      } else {
        sessionStorage.removeItem('medcoord_session');
        sessionStorage.removeItem('doctor_session');
        sessionStorage.removeItem('patient_session');
        sessionStorage.removeItem('doctor_unlocked_patient');
      }
    } catch (e) {}
  },

  getUnlockedPatient() {
    try {
      return sessionStorage.getItem('doctor_unlocked_patient') || sessionStorage.getItem('medcoord_unlocked_patient') || null;
    } catch (e) {
      return null;
    }
  },

  setUnlockedPatient(patientId) {
    try {
      sessionStorage.setItem('doctor_unlocked_patient', patientId);
    } catch (e) {}
  },

  clearUnlockedPatient() {
    try {
      sessionStorage.removeItem('doctor_unlocked_patient');
      sessionStorage.removeItem('medcoord_unlocked_patient');
    } catch (e) {}
  },

  // Centralized Request Wrapper with 10s AbortController and Precise Status Handling
  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };

    // Attach active session role/tokens and bearer headers
    const session = this.getSession();
    if (session) {
      if (session.token || session.sessionToken) {
        defaultHeaders['Authorization'] = `Bearer ${session.token || session.sessionToken}`;
      }
      if (session.role === 'DOCTOR' && session.doctorId) {
        defaultHeaders['x-doctor-id'] = session.doctorId;
        defaultHeaders['x-user-role'] = 'DOCTOR';
      } else if (session.role === 'PATIENT' && session.patientId) {
        defaultHeaders['x-user-id'] = session.patientId;
        defaultHeaders['x-user-role'] = 'PATIENT';
      }
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {})
      }
    };

    if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
      config.body = JSON.stringify(config.body);
    } else if (config.body instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    // 10s AbortController timeout + 3s "Still working…" notification (Part A1 requirement)
    const controller = new AbortController();
    const timeoutDuration = options.timeout || 10000;
    const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);
    let workingTimer = setTimeout(() => {
      if (typeof window.showToast === 'function') {
        window.showToast('Still working…', 'info', 2500);
      }
    }, 3000);

    config.signal = controller.signal;

    try {
      const response = await fetch(url, config);
      clearTimeout(timeoutId);
      clearTimeout(workingTimer);

      // Handle 401: Only log out if genuinely SESSION_EXPIRED
      if (response.status === 401 && !url.includes('/api/auth/login')) {
        let errData = {};
        try { errData = await response.clone().json(); } catch (_) {}
        const code = errData.code || 'SESSION_EXPIRED';
        if (code === 'SESSION_EXPIRED' || code === 'UNAUTHORIZED') {
          this.clearSession();
          if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
            window.location.href = '/login?expired=1';
          }
        }
        throw new ApiError(errData.message || 'Session expired. Please sign in.', code, null, 401, errData);
      }

      // Handle 403: Re-lock privacy shield in place with clear friendly message (DO NOT logout)
      if (response.status === 403) {
        let errData = {};
        try { errData = await response.clone().json(); } catch (_) {}
        const code = errData.code || 'FORBIDDEN';
        const msg = errData.message || 'Access denied.';
        if (code === 'NO_ACTIVE_GRANT' || code === 'CONSENT_REQUIRED' || code === 'CONSENT_REVOKED') {
          if (typeof window.lockPatientRecordNow === 'function') {
            const friendly = (code === 'CONSENT_REVOKED')
              ? 'The patient removed your access.'
              : "Access expired. Enter the patient's current PIN again.";
            window.lockPatientRecordNow(friendly);
          }
        }
        throw new ApiError(msg, code, null, 403, errData);
      }

      const contentType = response.headers.get('content-type') || '';
      let data = {};
      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        try { data = JSON.parse(text); } catch (_) { data = { raw: text }; }
      }

      if (!response.ok) {
        const code = data.code || (data.status === 'ERROR' ? 'SERVER_ERROR' : null);
        const gate = data.gate || null;
        const msg = data.message || data.error || `Request failed (${response.status})`;
        throw new ApiError(msg, code, gate, response.status, data);
      }

      return data;
    } catch (err) {
      clearTimeout(timeoutId);
      clearTimeout(workingTimer);
      if (err.name === 'AbortError') {
        if (typeof window.showToast === 'function') {
          window.showToast('Taking too long, try again', 'warning', 4000);
        }
        throw new ApiError('Taking too long, try again', 'TIMEOUT', null, 408);
      }
      throw err;
    }
  },

  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  },

  post(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'POST', body });
  },

  put(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'PUT', body });
  },

  patch(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'PATCH', body });
  },

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
};

window.API = API;
window.ApiError = ApiError;
window.ERROR_CODE_MAP = ERROR_CODE_MAP;
