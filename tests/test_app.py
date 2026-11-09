"""
The routes, with signal one mocked so these run in a second without gpt2.
The real-detector runs live in test_end_to_end.py.
"""

import pytest

import audit
import config
import detector
import scoring
import stylometry
from conftest import AI_TEXT, HUMAN_TEXT, decisions

RESPONSE_FIELDS = {"content_id", "guess", "confidence", "label", "status",
                   "model_score", "style_score", "combined_score"}
LOG_FIELDS = {"timestamp", "content_id", "creator_id", "guess", "model_score",
              "style_score", "combined_score", "label", "status"}


def submit(client, text=AI_TEXT, creator_id="writer_1"):
    return client.post("/submit", json={"text": text, "creator_id": creator_id})


# ── The control routes ────────────────────────────────────────────────────────

def test_ping_still_answers(client):
    response = client.post("/ping", json={"message": "hello"})
    assert response.status_code == 200
    assert response.get_json() == {"ok": True, "you_sent": "hello", "service": "provenance-guard"}


def test_health_and_log(client, fake_model):
    assert client.get("/health").get_json()["ok"] is True
    submit(client)
    body = client.get("/log?limit=5").get_json()
    assert body["count"] == 1 and body["entries"][0]["creator_id"] == "writer_1"


# ── POST /submit ──────────────────────────────────────────────────────────────

class TestSubmit:
    def test_success_shape(self, client, fake_model):
        fake_model["score"] = 0.9
        response = submit(client)
        assert response.status_code == 200
        body = response.get_json()
        assert RESPONSE_FIELDS <= set(body)
        assert body["status"] == "decided"
        assert body["model_score"] == 0.9
        assert body["style_score"] == stylometry.style_signal(AI_TEXT)
        assert body["confidence"] == body["combined_score"] == scoring.combine_signals(0.9, body["style_score"])
        assert (body["guess"], body["label"]) == scoring.score_to_label(body["combined_score"])

    def test_content_ids_are_unique(self, client, fake_model):
        ids = {submit(client).get_json()["content_id"] for _ in range(20)}
        assert len(ids) == 20

    def test_every_submission_is_logged_with_all_fields(self, client, fake_model):
        body = submit(client).get_json()
        [entry] = decisions()
        assert LOG_FIELDS <= set(entry)
        assert entry["content_id"] == body["content_id"]
        assert entry["model_score"] == body["model_score"]
        assert entry["style_score"] == body["style_score"]
        assert entry["combined_score"] == body["combined_score"]
        assert entry["label"] == body["label"] and entry["status"] == "decided"

    def test_full_pipeline_ai(self, client, fake_model):
        fake_model["score"] = 0.95
        assert submit(client, AI_TEXT).get_json()["guess"] == "ai"

    def test_full_pipeline_human(self, client, fake_model):
        fake_model["score"] = 0.10
        assert submit(client, HUMAN_TEXT).get_json()["guess"] == "human"

    def test_full_pipeline_split_signals_land_unsure(self, client, fake_model):
        fake_model["score"] = 0.95  # model says AI, style of HUMAN_TEXT says human
        assert submit(client, HUMAN_TEXT).get_json()["guess"] == "unsure"

    def test_text_at_the_size_limit_is_accepted(self, client, fake_model):
        text = ("word " * (config.MAX_TEXT_CHARS // 5))[:config.MAX_TEXT_CHARS]
        assert submit(client, text).status_code == 200


# ── Bad input (criterion 5) ───────────────────────────────────────────────────

BAD_JSON_BODIES = [
    ([1, 2], 400, "invalid_body"),
    ("just a string", 400, "invalid_body"),
    ({"creator_id": "x"}, 400, "missing_field"),
    ({"text": "", "creator_id": "x"}, 400, "empty_field"),
    ({"text": "   \n\t ", "creator_id": "x"}, 400, "empty_field"),
    ({"text": None, "creator_id": "x"}, 400, "missing_field"),
    ({"text": 42, "creator_id": "x"}, 400, "invalid_type"),
    ({"text": ["a", "list"], "creator_id": "x"}, 400, "invalid_type"),
    ({"text": AI_TEXT}, 400, "missing_field"),
    ({"text": AI_TEXT, "creator_id": ""}, 400, "empty_field"),
    ({"text": AI_TEXT, "creator_id": 7}, 400, "invalid_type"),
    ({"text": AI_TEXT, "creator_id": "c" * (config.MAX_CREATOR_ID_CHARS + 1)}, 413, "field_too_long"),
    ({"text": "x" * (config.MAX_TEXT_CHARS + 1), "creator_id": "x"}, 413, "field_too_long"),
    ({"text": "Far too short to judge.", "creator_id": "x"}, 422, "text_too_short"),
]


class TestBadInput:
    @pytest.mark.parametrize("body,status,error", BAD_JSON_BODIES)
    def test_refused_with_json_error_and_no_decision(self, client, fake_model, body, status, error):
        response = client.post("/submit", json=body)
        assert response.status_code == status
        assert response.get_json()["error"] == error
        assert decisions() == []
        assert fake_model["calls"] == 0  # refused before the model ran
        [rejection] = audit.read_entries()
        assert rejection["event"] == "rejected" and rejection["reason"] == error

    def test_invalid_json(self, client, fake_model):
        response = client.post("/submit", data="{not json", content_type="application/json")
        assert response.status_code == 400 and response.get_json()["error"] == "invalid_json"

    def test_wrong_content_type(self, client, fake_model):
        response = client.post("/submit", data="text=hello", content_type="application/x-www-form-urlencoded")
        assert response.status_code == 415 and response.get_json()["error"] == "unsupported_media_type"

    def test_no_body_at_all(self, client, fake_model):
        response = client.post("/submit")
        assert response.status_code == 415

    def test_enormous_body(self, client, fake_model):
        response = client.post("/submit", data="x" * 400_000, content_type="application/json")
        assert response.status_code == 413 and response.get_json()["error"] == "body_too_large"
        assert decisions() == []


class TestModelErrors:
    def test_detector_unavailable_is_503(self, client, fake_model):
        fake_model["score"] = detector.DetectorUnavailable("no weights")
        response = submit(client)
        assert response.status_code == 503
        assert response.get_json()["error"] == "detector_unavailable"
        assert decisions() == []

    def test_too_few_tokens_is_422(self, client, fake_model):
        fake_model["score"] = ValueError("Text is too short to score")
        assert submit(client).status_code == 422

    def test_unexpected_crash_is_json_500_and_logged(self, client, fake_model):
        fake_model["score"] = RuntimeError("CUDA fell over")
        response = submit(client)
        assert response.status_code == 500
        assert response.get_json()["error"] == "scoring_failed"
        assert audit.read_entries()[-1]["reason"] == "scoring_failed"

    def test_out_of_range_model_score_is_caught(self, client, fake_model):
        fake_model["score"] = 1.7
        assert submit(client).status_code == 500
        assert decisions() == []


# ── POST /appeal (criterion 4) ────────────────────────────────────────────────

class TestAppeal:
    def test_appeal_moves_to_under_review_and_logs(self, client, fake_model):
        fake_model["score"] = 0.95
        original = submit(client).get_json()
        response = client.post("/appeal", json={"content_id": original["content_id"],
                                                "reasoning": "I wrote this myself."})
        assert response.status_code == 200
        body = response.get_json()
        assert body["status"] == "under_review"
        assert body["content_id"] == original["content_id"]
        assert body["original_decision"]["guess"] == original["guess"]

        history = audit.entries_for(original["content_id"])
        assert [e.get("event") for e in history] == [None, "appeal"]
        appeal_entry = history[1]
        assert appeal_entry["reasoning"] == "I wrote this myself."
        assert appeal_entry["status"] == "under_review"
        assert appeal_entry["creator_id"] == "writer_1"
        for field in ("guess", "model_score", "style_score", "combined_score", "label"):
            assert appeal_entry[field] == original[field]
        assert history[0]["status"] == "decided"  # the original is never overwritten

    def test_reason_is_accepted_as_alias(self, client, fake_model):
        cid = submit(client).get_json()["content_id"]
        response = client.post("/appeal", json={"content_id": cid, "reason": "Mine."})
        assert response.status_code == 200
        assert audit.entries_for(cid)[-1]["reasoning"] == "Mine."

    def test_unknown_id_is_404_and_adds_no_appeal(self, client, fake_model):
        response = client.post("/appeal", json={"content_id": "does-not-exist", "reasoning": "x"})
        assert response.status_code == 404
        assert response.get_json()["error"] == "unknown_content_id"
        assert not any(e.get("event") == "appeal" for e in audit.read_entries())

    def test_repeat_appeal_is_409_and_logged(self, client, fake_model):
        cid = submit(client).get_json()["content_id"]
        assert client.post("/appeal", json={"content_id": cid, "reasoning": "one"}).status_code == 200
        second = client.post("/appeal", json={"content_id": cid, "reasoning": "two"})
        assert second.status_code == 409
        assert second.get_json()["error"] == "already_under_review"
        history = audit.entries_for(cid)
        assert sum(e.get("event") == "appeal" for e in history) == 1
        assert history[-1]["event"] == "rejected" and history[-1]["reason"] == "already_under_review"

    @pytest.mark.parametrize("body,status", [
        ({}, 400),
        ({"content_id": "abc"}, 400),
        ({"reasoning": "x"}, 400),
        ({"content_id": "", "reasoning": "x"}, 400),
        ({"content_id": 5, "reasoning": "x"}, 400),
        ({"content_id": "abc", "reasoning": "   "}, 400),
        ([1], 400),
    ])
    def test_bad_appeal_bodies(self, client, fake_model, body, status):
        response = client.post("/appeal", json=body)
        assert response.status_code == status
        assert "error" in response.get_json()

    def test_appeal_reason_too_long(self, client, fake_model):
        cid = submit(client).get_json()["content_id"]
        response = client.post("/appeal", json={"content_id": cid,
                                                "reasoning": "r" * (config.MAX_APPEAL_REASON_CHARS + 1)})
        assert response.status_code == 413

    def test_appeal_wrong_content_type(self, client, fake_model):
        assert client.post("/appeal", data="content_id=x").status_code == 415
