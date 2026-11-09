#!/usr/bin/env python3
"""
Provenance Guard — the web service.

    python app.py

Then, in another terminal:

    curl -X POST http://127.0.0.1:5000/ping \
      -H "Content-Type: application/json" \
      -d '{"message": "hello"}'

That's the example route. It works right now, before you've written anything.
**Leave it alone** — it's your control. When something breaks later, check that
`/ping` still answers: if it does, the problem is in your handler; if it
doesn't, it's the service itself.

Routes:

    POST /ping        the worked example. Already works. Don't edit it
    POST /submit      score a piece of text and label it
    POST /appeal      a writer disputes a decision; moves it to under_review
    GET  /log         the audit log. Already works
    GET  /health      is the service up, and is the model loaded
"""

import uuid

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

import audit
import config

app = Flask(__name__)


# ── Rate limiting — UNIT 8 ────────────────────────────────────────────────────
# Off until you turn it on. In unit 8, Milestone 1:
#
#   1. Set RATE_LIMITING_ENABLED = True in config.py (or AI201_RATE_LIMITS=1)
#   2. Choose your numbers there
#   3. Uncomment the @limiter.limit(...) line on /submit below
#
# The order doesn't matter. While limiting is off, that decorator is a no-op
# that quietly does nothing, so uncommenting it early costs you nothing — but
# it also means no 429 until you've done step 1.
#
# The storage backend is preconfigured, which stops Flask-Limiter printing a
# warning on every start. In-memory is right for one laptop and wrong for
# anything real — a restart forgets every count.

class _LimiterOff:
    """
    Stands in for the real limiter while rate limiting is off.

    It makes @limiter.limit(...) a decorator that returns the route
    untouched, so uncommenting the line before you flip the setting is
    harmless instead of a crash on startup.
    """

    def limit(self, *args, **kwargs):
        return lambda view: view


limiter = _LimiterOff()
if config.RATE_LIMITING_ENABLED:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    def rate_limit_key():
        """
        Who a request counts against.

        Falling back to the caller's address is the easy version. Unit 8's
        stretch asks about per-creator limits instead — and the difference
        matters: one script can look like a thousand callers, and one household
        can look like one.
        """
        payload = request.get_json(silent=True)
        # A body that parses as JSON but isn't an object — a bare list or
        # string — has no .get. Without this guard the key function raises
        # BEFORE the route runs, and a malformed request becomes a 500 that
        # looks like your handler crashed when your handler never ran.
        if not isinstance(payload, dict):
            return get_remote_address()
        creator = payload.get("creator_id")
        return creator if isinstance(creator, str) and creator.strip() else get_remote_address()

    limiter = Limiter(
        key_func=rate_limit_key,
        app=app,
        storage_uri=config.RATE_LIMIT_STORAGE,
        default_limits=[],
    )

    @app.errorhandler(429)
    def rate_limited(exc):
        """
        A rejected request still leaves a trace.

        ⚠️ An attack that shows up only as an absence is one you'll never find.
        """
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            payload = {}
        audit.log_rejection(
            creator_id=payload.get("creator_id", "unknown"),
            reason="rate_limited",
            limit=str(exc.description),
        )
        return jsonify({
            "error": "rate_limited",
            "message": "Too many submissions. Try again shortly.",
            "limit": str(exc.description),
        }), 429


# ── The worked example. Already works. Don't edit. ────────────────────────────

@app.post("/ping")
def ping():
    """
    Everything a route needs, in six lines.

    JSON arrives as a dict. You pull things out of it. You return a dict and
    the framework turns it into a response. That's the whole idea.
    """
    payload = request.get_json(silent=True) or {}
    return jsonify({
        "ok": True,
        "you_sent": payload.get("message"),
        "service": "provenance-guard",
    })


@app.get("/health")
def health():
    """Is the service up, and has the model been downloaded yet?"""
    import detector

    loaded = detector._model is not None
    return jsonify({
        "ok": True,
        "detector_model": config.DETECTOR_MODEL,
        "detector_loaded": loaded,
        "rate_limiting": config.RATE_LIMITING_ENABLED,
        "log_entries": len(audit.read_entries()),
    })


# ── Request validation ────────────────────────────────────────────────────────

class BadRequest(Exception):
    """A request we refuse. Carries the HTTP status and a machine-readable code."""

    def __init__(self, status: int, error: str, message: str, **extra):
        super().__init__(message)
        self.status, self.error, self.message, self.extra = status, error, message, extra


def _json_object() -> dict:
    """The request body as a dict, or a BadRequest saying why not."""
    if not request.is_json:
        raise BadRequest(415, "unsupported_media_type",
                         "Send JSON with the header Content-Type: application/json.")
    payload = request.get_json(silent=True)
    if payload is None:
        raise BadRequest(400, "invalid_json", "The request body isn't valid JSON.")
    if not isinstance(payload, dict):
        raise BadRequest(400, "invalid_body",
                         "The JSON body must be an object, like {\"text\": \"...\"}.")
    return payload


def _required_string(payload: dict, field: str, max_chars: int) -> str:
    """A field that must be a non-blank string no longer than max_chars."""
    if field not in payload or payload[field] is None:
        raise BadRequest(400, "missing_field", f"'{field}' is required.", field=field)
    value = payload[field]
    if not isinstance(value, str):
        raise BadRequest(400, "invalid_type", f"'{field}' must be a string.", field=field)
    if not value.strip():
        raise BadRequest(400, "empty_field", f"'{field}' can't be empty.", field=field)
    if len(value) > max_chars:
        raise BadRequest(413, "field_too_long",
                         f"'{field}' is {len(value)} characters; the limit is {max_chars}.",
                         field=field, limit=max_chars)
    return value


def _refuse(exc: BadRequest, payload=None):
    """Answer a refused request and leave a trace of it in the audit log."""
    creator = payload.get("creator_id") if isinstance(payload, dict) else None
    audit.log_rejection(
        creator_id=creator if isinstance(creator, str) and creator.strip() else "unknown",
        reason=exc.error,
        route=request.path,
        http_status=exc.status,
        **exc.extra,
    )
    return jsonify({"error": exc.error, "message": exc.message, **exc.extra}), exc.status


# The whole body, before Flask parses it. Bigger than any text we'd accept, so
# the in-route MAX_TEXT_CHARS check is the one callers normally meet.
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024


@app.errorhandler(413)
def body_too_large(exc):
    return _refuse(BadRequest(413, "body_too_large",
                              "The request body is too large.",
                              limit_bytes=app.config["MAX_CONTENT_LENGTH"]))


# ── POST /submit ──────────────────────────────────────────────────────────────

@app.post("/submit")
# @limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute;{config.RATE_LIMIT_PER_DAY}/day")
def submit():
    """
    Take a piece of text, decide about it, log the decision, answer.

    Expects JSON:  {"text": "...", "creator_id": "..."}

    Returns 200 with:
        content_id      unique id for this decision; /appeal needs it
        guess           the classification: "ai", "human" or "unsure"
        confidence      the combined score, 0.0 (confidently human) to 1.0
                        (confidently AI) — same number as combined_score
        label           the sentence a reader sees
        status          "decided"
        model_score     signal one (detector.model_signal), 0–1, higher = AI
        style_score     signal two (stylometry.style_signal), 0–1, higher = AI
        combined_score  scoring.combine_signals(model_score, style_score)

    Refuses with a JSON {"error": ..., "message": ...} body and logs the
    refusal: 415 not JSON, 400 malformed/missing/blank/wrong-type fields,
    413 text too long, 422 text too short to score, 503 detector unavailable,
    500 an unexpected scoring failure.
    """
    import detector
    import scoring
    import stylometry

    payload = None
    try:
        payload = _json_object()
        text = _required_string(payload, "text", config.MAX_TEXT_CHARS)
        creator_id = _required_string(payload, "creator_id", config.MAX_CREATOR_ID_CHARS)
        if len(stylometry.words(text)) < config.MIN_TEXT_WORDS:
            raise BadRequest(422, "text_too_short",
                             f"Send at least {config.MIN_TEXT_WORDS} words — "
                             f"there isn't enough text to judge.",
                             min_words=config.MIN_TEXT_WORDS)

        try:
            model_score = detector.model_signal(text)
        except detector.DetectorUnavailable:
            raise BadRequest(503, "detector_unavailable",
                             "The detector model isn't available right now. "
                             "Nothing was decided; try again later.")
        except ValueError as exc:  # too few tokens for the model to score
            raise BadRequest(422, "text_too_short", str(exc))

        style_score = round(stylometry.style_signal(text), 4)
        combined = round(scoring.combine_signals(model_score, style_score), 4)
        guess, label = scoring.score_to_label(combined)
    except BadRequest as exc:
        return _refuse(exc, payload)
    except HTTPException:
        raise  # e.g. 413 body too large: its own handler answers
    except Exception as exc:  # noqa: BLE001 — a crash must still answer in JSON and leave a trace
        app.logger.exception("scoring failed")
        return _refuse(BadRequest(500, "scoring_failed",
                                  "Something went wrong scoring this text. Nothing was decided.",
                                  detail=type(exc).__name__), payload)

    content_id = uuid.uuid4().hex
    audit.log_decision(
        content_id=content_id,
        creator_id=creator_id,
        guess=guess,
        model_score=model_score,
        style_score=style_score,
        combined_score=combined,
        label=label,
        status="decided",
    )
    return jsonify({
        "content_id": content_id,
        "guess": guess,
        "confidence": combined,
        "label": label,
        "status": "decided",
        "model_score": model_score,
        "style_score": style_score,
        "combined_score": combined,
    })


@app.post("/appeal")
def appeal():
    """
    A writer says we got it wrong.

    Expects JSON:  {"content_id": "...", "reasoning": "..."}
    ("reason" is accepted as another name for "reasoning".)

    Returns 200 with the content_id, status "under_review", a confirmation
    message and the original decision. The appeal is appended to the audit
    log beside the original decision, with its reason, the original guess,
    both signal scores, the combined score and the label.

    Repeat-appeal policy: one appeal per content_id. Once an item is
    under_review, another appeal gets 409 and is logged as a rejection
    (reason "already_under_review") — refused, but never silently dropped.

    Refuses with JSON: 415 not JSON, 400 malformed/missing/blank/wrong-type
    fields, 413 reason too long, 404 unknown content_id, 409 repeat appeal.
    """
    payload = None
    try:
        payload = _json_object()
        content_id = _required_string(payload, "content_id", 64)
        if "reasoning" not in payload and "reason" in payload:
            payload = {**payload, "reasoning": payload["reason"]}
        reasoning = _required_string(payload, "reasoning", config.MAX_APPEAL_REASON_CHARS)

        history = audit.entries_for(content_id)
        decision = next((e for e in history if "event" not in e), None)
        if decision is None:
            raise BadRequest(404, "unknown_content_id",
                             "We have no decision with that content_id. Check it "
                             "matches the one /submit returned.",
                             content_id=content_id)
        payload = {**payload, "creator_id": decision["creator_id"]}
        # shortcut: check-then-append isn't atomic across threads; two appeals
        # racing within milliseconds could both land. Fine for one laptop.
        if any(e.get("event") == "appeal" for e in history):
            raise BadRequest(409, "already_under_review",
                             "This item has already been appealed and is waiting "
                             "for a person to review it.",
                             content_id=content_id, current_status="under_review")
    except BadRequest as exc:
        return _refuse(exc, payload)

    entry = audit.log_appeal(
        content_id=content_id,
        creator_id=decision["creator_id"],
        reasoning=reasoning,
        guess=decision.get("guess"),
        model_score=decision.get("model_score"),
        style_score=decision.get("style_score"),
        combined_score=decision.get("combined_score"),
        label=decision.get("label"),
    )
    return jsonify({
        "content_id": content_id,
        "status": "under_review",
        "message": "Thanks. Your appeal is recorded and a person will review "
                   "this decision. The automatic label stays on hold until then.",
        "appealed_at": entry["timestamp"],
        "original_decision": {
            "guess": decision.get("guess"),
            "confidence": decision.get("combined_score"),
            "label": decision.get("label"),
            "decided_at": decision.get("timestamp"),
        },
    })


# ── Already works ─────────────────────────────────────────────────────────────

@app.get("/log")
def get_log():
    """
    The audit log, most recent last.

        curl "http://127.0.0.1:5000/log?limit=10"

    You need this in unit 8 to paste entries into your README, and you need it
    now to see whether your logging is actually working.
    """
    limit = request.args.get("limit", type=int)
    entries = audit.read_entries(limit=limit)
    return jsonify({"count": len(entries), "entries": entries})


def main():
    print(f"Provenance Guard on http://{config.HOST}:{config.PORT}")
    print(f"  detector model:  {config.DETECTOR_MODEL}")
    print(f"  rate limiting:   {'ON' if config.RATE_LIMITING_ENABLED else 'off (unit 8)'}")
    print(f"  audit log:       {config.AUDIT_LOG}")
    print()
    print("Check it's alive:")
    print(f'  curl -X POST http://{config.HOST}:{config.PORT}/ping \\')
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{\"message\": \"hello\"}'")
    print()
    # debug=True hands out an interactive debugger, so it's local-only — see config.py
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == "__main__":
    main()
