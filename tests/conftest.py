"""
Shared fixtures. Every test writes to its own temporary audit log, so the
committed logs/audit.jsonl is never touched by the test suite.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app as app_module  # noqa: E402
import audit  # noqa: E402
import config  # noqa: E402
import detector  # noqa: E402

AI_TEXT = (
    "Time management is an essential skill for students who want to succeed. "
    "By creating a clear schedule, students can balance their coursework and "
    "their personal responsibilities. It is important to prioritize tasks based "
    "on their deadlines. Additionally, breaking large assignments into smaller "
    "steps can help reduce stress and improve overall productivity."
)
HUMAN_TEXT = (
    "I missed the bus again. Typical! So I walked — all forty minutes of it, in "
    "the rain, past the bakery that's been 'closing down' since 2019; the smell "
    "nearly made me late on purpose. Did anyone notice? No. Mr. Hale just said "
    "(without looking up) that the quiz had started, which it had."
)


@pytest.fixture
def log_path(tmp_path, monkeypatch):
    path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(config, "LOG_DIR", tmp_path)
    monkeypatch.setattr(config, "AUDIT_LOG", path)
    return path


@pytest.fixture
def client(log_path):
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


@pytest.fixture
def fake_model(monkeypatch):
    """Replace signal one with a settable number so route tests don't need gpt2."""
    state = {"score": 0.5, "calls": 0}

    def model_signal(text):
        state["calls"] += 1
        if isinstance(state["score"], Exception):
            raise state["score"]
        return state["score"]

    monkeypatch.setattr(detector, "model_signal", model_signal)
    return state


def decisions():
    return [e for e in audit.read_entries() if "event" not in e]
