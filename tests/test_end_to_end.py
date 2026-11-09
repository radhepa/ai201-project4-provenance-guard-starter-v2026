"""
Real end-to-end runs with the actual gpt2 detector — no mocks.

Skipped automatically if the model hasn't been downloaded (run
`python detector.py` once). Uses the calibration split only; the evaluation
split is scored by evaluate.py against the live service.
"""

import json
from pathlib import Path

import pytest

import audit
import detector
from conftest import decisions

DATA = Path(__file__).resolve().parent.parent / "eval_data"

try:
    detector._load()
    HAVE_MODEL = True
except detector.DetectorUnavailable:
    HAVE_MODEL = False

pytestmark = pytest.mark.skipif(not HAVE_MODEL, reason="gpt2 not downloaded; run python detector.py")


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_model_signal_is_normalised_and_deterministic():
    text = load("calibration_ai.json")[0]["text"]
    first = detector.model_signal(text)
    assert 0.0 <= first <= 1.0
    assert detector.model_signal(text) == first


def test_model_is_loaded_once_and_reused(client):
    model_before = detector._model
    text = load("calibration_ai.json")[1]["text"]
    for _ in range(3):
        assert client.post("/submit", json={"text": text, "creator_id": "e2e"}).status_code == 200
    assert detector._model is model_before


def test_real_submit_then_appeal(client):
    text = load("calibration_ai.json")[2]["text"]
    response = client.post("/submit", json={"text": text, "creator_id": "e2e_writer"})
    assert response.status_code == 200
    body = response.get_json()
    for key in ("model_score", "style_score", "combined_score", "confidence"):
        assert 0.0 <= body[key] <= 1.0
    appeal = client.post("/appeal", json={"content_id": body["content_id"], "reasoning": "real run"})
    assert appeal.status_code == 200 and appeal.get_json()["status"] == "under_review"
    assert [e.get("event") for e in audit.entries_for(body["content_id"])] == [None, "appeal"]


def test_calibration_ai_scores_above_calibration_human(client):
    """Signal sanity on the calibration split: AI text should score higher on average."""
    def mean_score(samples):
        scores = [client.post("/submit", json={"text": s["text"], "creator_id": "e2e"}).get_json()["combined_score"]
                  for s in samples]
        return sum(scores) / len(scores)

    assert mean_score(load("calibration_ai.json")) > mean_score(load("calibration_human.json")[:8])
    assert len(decisions()) == 5 + 8
