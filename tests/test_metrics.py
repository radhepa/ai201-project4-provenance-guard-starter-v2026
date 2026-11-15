"""The capstone request log: one complete line per request, never the text."""

import json

import config
import metrics
from conftest import HUMAN_TEXT

BASE = ["timestamp", "request_id", "route", "method", "status", "duration_ms",
        "cpu_ms", "input_bytes", "input_sha256", "outcome"]
SCORED = ["words", "model_ms", "style_ms", "cold_start"]


def test_accepted_and_refused_each_leave_one_complete_line(client, fake_model):
    ok = client.post("/submit", json={"text": HUMAN_TEXT, "creator_id": "m1"},
                     headers={"X-Request-Id": "req-ok"})
    bad = client.post("/submit", json={"creator_id": "m1"}, headers={"X-Request-Id": "req-bad"})
    assert ok.headers["X-Request-Id"] == "req-ok"
    entries = {e["request_id"]: e for e in metrics.read_entries()}
    assert set(entries) == {"req-ok", "req-bad"}
    for e in entries.values():
        assert all(e.get(k) is not None for k in BASE), e
    assert all(entries["req-ok"].get(k) is not None for k in SCORED)
    assert entries["req-ok"]["outcome"] == ok.get_json()["guess"]
    assert entries["req-bad"]["status"] == 400 and entries["req-bad"]["outcome"] == "missing_field"


def test_log_never_holds_the_text(client, fake_model):
    client.post("/submit", json={"text": HUMAN_TEXT, "creator_id": "m2"})
    raw = config.REQUEST_LOG.read_text(encoding="utf-8")
    assert "forty minutes" not in raw and "m2" not in raw


def test_unsafe_request_id_is_replaced(client, fake_model):
    r = client.post("/submit", json={"creator_id": "m3"}, headers={"X-Request-Id": "a b\"}"})
    assert r.headers["X-Request-Id"] != "a b\"}"
    assert json.loads(config.REQUEST_LOG.read_text(encoding="utf-8"))["request_id"] == r.headers["X-Request-Id"]


def test_other_routes_are_not_logged(client):
    client.post("/ping", json={"message": "hi"})
    assert metrics.read_entries() == []
