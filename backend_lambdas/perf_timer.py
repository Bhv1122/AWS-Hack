"""
perf_timer.py - Performance timing instrumentation
Provides per-step timers and global slowest-step tracking for A1 profiling.
"""

import time
import threading
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

try:
    from flask import has_request_context, g
except ImportError:
    has_request_context = lambda: False
    g = None

_PERF_LOCK = threading.RLock()
_SLOWEST_STEPS: List[Dict[str, Any]] = []
_REQUEST_HISTORY: List[Dict[str, Any]] = []

@contextmanager
def timed_step(step_name: str, details: Optional[str] = None):
    t0 = time.perf_counter()
    try:
        yield
    finally:
        t1 = time.perf_counter()
        elapsed_ms = round((t1 - t0) * 1000, 2)
        rec = {
            "step": step_name,
            "elapsed_ms": elapsed_ms,
            "details": details or "",
            "timestamp": time.time()
        }
        if has_request_context() and g is not None:
            if not hasattr(g, "request_steps"):
                g.request_steps = []
            g.request_steps.append(rec)
        with _PERF_LOCK:
            _SLOWEST_STEPS.append(rec)
            _SLOWEST_STEPS.sort(key=lambda x: x["elapsed_ms"], reverse=True)
            if len(_SLOWEST_STEPS) > 100:
                _SLOWEST_STEPS.pop()

def record_request_perf(method: str, path: str, status_code: int, duration_ms: float, steps: List[Dict[str, Any]]):
    with _PERF_LOCK:
        _REQUEST_HISTORY.append({
            "method": method,
            "path": path,
            "status": status_code,
            "duration_ms": round(duration_ms, 2),
            "steps": steps,
            "timestamp": time.time()
        })
        if len(_REQUEST_HISTORY) > 100:
            _REQUEST_HISTORY.pop(0)

def get_slowest_steps(limit: int = 10) -> List[Dict[str, Any]]:
    with _PERF_LOCK:
        return list(_SLOWEST_STEPS[:limit])

def get_request_history(limit: int = 20) -> List[Dict[str, Any]]:
    with _PERF_LOCK:
        return list(_REQUEST_HISTORY[-limit:])

def clear_perf_metrics():
    with _PERF_LOCK:
        _SLOWEST_STEPS.clear()
        _REQUEST_HISTORY.clear()
