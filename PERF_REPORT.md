# Performance & Timing Profiling Report (Part A1 Baseline)

**Platform:** SwasthyaSetu & AWS Medication Coordination Platform (`D:\AWS`)  
**Environment:** Python 3.14 (Flask threaded backend on port 5000, Windows x64)  
**Timestamp:** 2026-10-24 08:12:00 UTC  
**Target Goal:** Unlock ≤ 1.5 s, Modify/Discontinue ≤ 1.5 s (Sandbox & Expired AWS Credentials)

---

## 1. Baseline Measurements (Before Code Fixes)

We instrumented the Flask request lifecycle with before/after-request high-resolution performance timers (`time.perf_counter()`), attached `X-Response-Time-Ms` response headers, and added per-substep timers across AWS client operations, local state read/write, KMS cryptography, and CSV indexing.

We executed the full four-step clinical flow:
1. **Doctor Login** (`POST /api/auth/login-doctor`, DOC-IN-8841, MFA 654321)
2. **Patient Lookup & Unlock** (`POST /api/auth/lookup-patient`, PAT-SS-1001 with current PIN)
3. **Patient Profile & History** (`GET /api/profile?patientId=PAT-SS-1001`)
4. **Modify Prescription** (`PUT /api/prescriptions`, dosage adjust)

### Measured Round-Trip Numbers:
| Step | Endpoint | Status | Round-Trip Elapsed | Target | Meets Target? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Doctor Login** | `POST /api/auth/login-doctor` | 200 OK | **373.54 ms** | ≤ 1,500 ms |  PASS |
| **2. Patient Lookup (PIN)** | `POST /api/auth/lookup-patient` | 200 OK | **26,237.68 ms (26.24 s)** | ≤ 1,500 ms |  **CRITICAL FAIL** |
| **3. Patient Profile** | `GET /api/profile?patientId=PAT-SS-1001` | 200 OK | **467.29 ms** | ≤ 1,500 ms |  PASS |
| **4. Modify Prescription** | `PUT /api/prescriptions` | **400 BAD REQ** | **715.11 ms** | ≤ 1,500 ms |  **FAIL (ERROR)** |
| **TOTAL FLOW TIME** | Full Clinical Journey | — | **27,793.62 ms (27.8 s)** | ≤ 6,000 ms |  **CRITICAL FAIL** |

---

## 2. Slowest Substeps Breakdown (Root Cause Attribution)

Direct profiling of the internal execution path during `lookup_patient_by_doctor` revealed the following exact bottlenecks:

| Rank | Substep Component | Measured Latency | Root Cause |
| :--- | :--- | :--- | :--- |
| **1** | **Live AWS Network Probing (DynamoDB / STS / KMS)** | **15,000 – 30,000 ms** | Live `boto3.client` / `boto3.resource` calls were constructed without timeouts (`connect_timeout=2`, `read_timeout=3`). When AWS credentials expire (or on EC2 metadata probing `169.254.169.254`), boto3 performs default multi-attempt exponential backoff retries, blocking the request thread synchronously for up to 30 seconds before falling back to local state. |
| **2** | **Synchronous Medicine CSV Dataset Load** | **11,011.03 ms** | `get_doctor_patient_view()` invoked `load_medicine_catalog()` synchronously inside the request. Parsing and indexing all 253,973 rows of `A_Z_medicines_dataset_of_India.csv` (30.6 MB) on the main request thread consumed 11.01 seconds. |
| **3** | **Synchronous `local_state.json` Full-Disk Rewrites** | **168.98 ms per write** (× 4–5 writes = **~800 ms**) | Every audit event, PIN rate-limit check, and session grant executed `json.dumps()` and a full-file disk write with Windows retry sleeps (`time.sleep(0.04)`), causing I/O stalls and write-lock contention. |
| **4** | **`check_aws_integration_status()` Polling on Request Path** | **2,500 – 5,000 ms** | Invoking `/aws/status` or rendering pages executed live AWS API queries (`list_tables`, `head_bucket`, `describe_key`) on every request instead of answering from an in-memory cached circuit breaker under 50 ms. |
| **5** | **Modify Prescription Request Misrouting (HTTP 400)** | **715.11 ms** | `api_prescriptions_root()` checked `action in ("MODIFY", "MODIFIED")` and `new_dosage in body`. The frontend passed `action="MODIFY_DOSAGE"` and `dosage="100mg"`. As a result, the request fell through to `api_doctor_prescribe()` (new prescription pipeline), causing an HTTP 400 / 401 error. |

---

## 3. Targeted Fix Plan (Part A1 & A2 Implementation)

1. **AWS Client Singleton & Per-Service Circuit Breaker:**
   - Configure `boto3` clients with `botocore.config.Config(connect_timeout=2, read_timeout=3, retries={"max_attempts": 1})`.
   - Set environment variables: `AWS_EC2_METADATA_DISABLED=true`, `AWS_METADATA_SERVICE_TIMEOUT=1`, `AWS_METADATA_SERVICE_NUM_ATTEMPTS=1`.
   - Implement an in-memory Circuit Breaker: upon any network error or expired token, immediately route to the sandbox for 5 minutes with zero network delays.
   - Cache `/api/aws-status` in memory; answer in < 50 ms.
2. **Asynchronous Background CSV Loading:**
   - Pre-load and index `A_Z_medicines_dataset_of_India.csv` once at server startup in a background daemon thread. Never parse CSV inside an HTTP request.
3. **In-Memory Thread-Safe State & Fire-and-Forget Auditing:**
   - Keep `local_state.json` in memory behind a `threading.RLock`.
   - Offload CloudTrail audit writes and non-blocking telemetry to background fire-and-forget worker tasks with 1-second timeouts.
4. **Prescription Endpoint Alignment:**
   - Accept `action="MODIFY_DOSAGE"` and `dosage` or `new_dosage`.
   - Take `doctorId` from verified session.
   - Return 200 with updated prescription without reloads or AI pipeline stalls.

---

## 4. Post-Optimization Measurements (Measured in Live Runtime)

Following implementation of the low-latency boto3 configuration, per-service circuit breaker, background CSV indexing, and write-behind `LocalStateStore`, we re-measured the full four-step clinical flow:

### Measured Round-Trip Numbers:
| Step | Endpoint | Status | Baseline Latency | Post-Optimization Latency | Target | Meets Target? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Doctor Login** | `POST /api/auth/login-doctor` | 200 OK | 373.54 ms | **75.56 ms** (server: 1.05 ms) | ≤ 1,500 ms |  **PASS** |
| **2. Patient Lookup (PIN)** | `POST /api/auth/lookup-patient` | 200 OK | 26,237.68 ms | **1,442.31 ms** (server: 1,357.41 ms) | ≤ 1,500 ms |  **PASS (18x faster)** |
| **3. Patient Profile** | `GET /api/profile?patientId=PAT-SS-1001` | 200 OK | 467.29 ms | **81.06 ms** (server: 3.02 ms) | ≤ 1,500 ms |  **PASS** |
| **4. Modify Prescription** | `PUT /api/prescriptions` | 200 OK | 715.11 ms (400 ERR) | **700.94 ms** (server: 633.23 ms) | ≤ 1,500 ms |  **PASS (Fixed & 200 OK)** |
| **TOTAL FLOW TIME** | Full Clinical Journey | 200 OK | 27,793.62 ms | **2,299.87 ms** | ≤ 6,000 ms |  **PASS (12x faster overall)** |

### Health Check Performance:
- `/api/aws-status`: **33.14 ms** (Target: < 50 ms) — **PASS**
- Pill Label: `"Sandbox mode (AWS credentials expired)"` in calm info state (not an error).

---

## 5. Summary of Files Changed for Optimization
1. `backend_lambdas/aws_core.py`:
   - Configured `BOTO_CONFIG = Config(connect_timeout=2, read_timeout=3, retries={"max_attempts": 1})`.
   - Set environment defaults `AWS_EC2_METADATA_DISABLED=true`, `AWS_METADATA_SERVICE_TIMEOUT=1`.
   - Implemented `AWSCircuitBreaker` with 300s cooldown trip.
   - Background daemon thread for `load_medicine_catalog()` CSV parsing.
   - Refactored `LocalStateStore` with `threading.RLock()` and asynchronous write-behind disk persistence.
   - Updated `get_prescription` and `update_prescription` to normalize `PAT-SS-1001` composite keys.
2. `backend_lambdas/prescription_ai_engine.py`:
   - Updated `modify_prescription_dosage` and `discontinue_prescription` to normalize `patient_id` and search fallback catalog.
3. `frontend_portal/app.py`:
   - Added `api_prescriptions_root` accepting PUT and POST for MODIFY/DISCONTINUE.
   - Validated active doctor consent grants and returned HTTP 200 with updated prescription details.
   - Fast cached response on `/api/aws-status` in < 50 ms.
