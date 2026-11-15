"""
The request log. Capstone, Shape A.

One JSON line per HTTP request to /submit or /appeal, written to
`logs/requests.jsonl`. That includes requests that were refused or
rate-limited. `logs/audit.jsonl` says what was *decided*. This file says what
each request *cost*: how long it took, how much CPU it used, and for a scored
submission, where the time went.

Every entry:
    timestamp      UTC, millisecond precision
    request_id     the caller's X-Request-Id header if it's sane, else a new
                   one; echoed back in the response header either way
    route, method, status
    duration_ms    wall time from the start of the request to the response
    cpu_ms         process CPU time over the same span (all threads, so it
                   can exceed duration_ms when torch uses several cores)
    input_bytes    size of the request body
    input_sha256   first 16 hex digits of the body's SHA-256. This identifies
                   an input without storing it: the log never holds the
                   writer's text
    outcome        the guess, the appeal status, or the error code

An accepted /submit also carries, from app.py::submit:
    words, tokens_scored, model_ms, style_ms, cold_start
"""

import hashlib
import json
import re
import threading
import time
import uuid
from datetime import datetime, timezone

from flask import g, request

import config

ROUTES = {"/submit", "/appeal"}
_ID_OK = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_lock = threading.Lock()


def start():
    """Before the request: start both clocks."""
    g.metrics_t0 = time.perf_counter()
    g.metrics_cpu0 = time.process_time()


def note(**fields):
    """A handler adds its own fields (stage timings) to this request's entry."""
    g.setdefault("metrics_extra", {}).update(fields)


def _request_id() -> str:
    if "metrics_id" not in g:
        given = request.headers.get("X-Request-Id", "")
        g.metrics_id = given if _ID_OK.match(given) else uuid.uuid4().hex
    return g.metrics_id


def finish(response):
    """After the request: write one line and echo the request id."""
    if request.path not in ROUTES:
        return response
    rid = _request_id()
    response.headers["X-Request-Id"] = rid

    t0, cpu0 = g.get("metrics_t0"), g.get("metrics_cpu0")
    try:
        body = request.get_data(cache=True)
    except Exception:  # noqa: BLE001 — body over MAX_CONTENT_LENGTH can't be read again
        body = None
    data = response.get_json(silent=True) if response.is_json else None
    data = data if isinstance(data, dict) else {}

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "request_id": rid,
        "route": request.path,
        "method": request.method,
        "status": response.status_code,
        "duration_ms": round((time.perf_counter() - t0) * 1000, 1) if t0 is not None else None,
        "cpu_ms": round((time.process_time() - cpu0) * 1000, 1) if cpu0 is not None else None,
        "input_bytes": len(body) if body is not None else request.content_length,
        "input_sha256": hashlib.sha256(body).hexdigest()[:16] if body is not None else "unreadable",
        "outcome": data.get("guess") or data.get("error") or data.get("status") or str(response.status_code),
        **g.get("metrics_extra", {}),
    }
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    with _lock, config.REQUEST_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return response


def read_entries() -> list[dict]:
    if not config.REQUEST_LOG.exists():
        return []
    out = []
    for line in config.REQUEST_LOG.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
