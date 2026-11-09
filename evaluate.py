#!/usr/bin/env python3
"""
Measure the five criteria in criteria.md against the LIVE service, three trials.

    python app.py              # in one terminal
    python evaluate.py         # in another

Every request is a real HTTP call to the running service with the real gpt2
detector. The targets below are copied from criteria.md, which was committed
before this script was ever run; they are not tuned here.

Writes results/eval_<stamp>.json (every response) and results/eval_<stamp>.md
(the verdict table).
"""

import argparse
import datetime as dt
import json
import statistics
import sys
import uuid
from pathlib import Path

import requests

import config
import scoring

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

DATA = config.ROOT / "eval_data"

# Targets, verbatim from criteria.md.
TARGET_MAX_FALSE_POSITIVES = 1      # criterion 1: at most 1 of 20
TARGET_MIN_GAP = 0.20               # criterion 2
TARGET_LABELS = {"human", "unsure", "ai"}   # criterion 3(b)
TARGET_APPEALS_OK = 5               # criterion 4
TARGET_UNKNOWN_404 = 3
TARGET_BAD_INPUT = 12               # criterion 5


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def decision_count(url):
    entries = requests.get(f"{url}/log", timeout=30).json()["entries"]
    return sum("event" not in e for e in entries), entries


def submit(url, text, creator_id, timeout):
    response = requests.post(f"{url}/submit", json={"text": text, "creator_id": creator_id},
                             timeout=timeout)
    return response.status_code, response.json()


def bad_requests():
    """The 12 malformed requests named in criterion 5: (name, kwargs for requests.post)."""
    ok_text = load("ai_samples.json")[0]["text"]
    js = {"Content-Type": "application/json"}
    return [
        ("non-JSON body", {"data": "{this is not json", "headers": js}),
        ("wrong content type", {"data": "text=hello&creator_id=x",
                                "headers": {"Content-Type": "application/x-www-form-urlencoded"}}),
        ("JSON list, not object", {"json": ["text", "creator_id"]}),
        ("missing text", {"json": {"creator_id": "eval_bad"}}),
        ("empty text", {"json": {"text": "", "creator_id": "eval_bad"}}),
        ("whitespace-only text", {"json": {"text": "  \n\t  ", "creator_id": "eval_bad"}}),
        ("non-string text", {"json": {"text": 12345, "creator_id": "eval_bad"}}),
        ("missing creator_id", {"json": {"text": ok_text}}),
        ("empty creator_id", {"json": {"text": ok_text, "creator_id": ""}}),
        ("non-string creator_id", {"json": {"text": ok_text, "creator_id": ["x"]}}),
        ("text over size limit", {"json": {"text": "word " * (config.MAX_TEXT_CHARS // 5 + 1),
                                           "creator_id": "eval_bad"}}),
        ("text too short to score", {"json": {"text": "Too short to judge.", "creator_id": "eval_bad"}}),
    ]


def sweep_ok():
    """Criterion 3(a): no gaps or overlaps in a 0.0001 sweep, changes only at thresholds."""
    previous, changes = None, []
    for i in range(10_001):
        guess, _ = scoring.score_to_label(i / 10_000)
        if previous is not None and guess != previous:
            changes.append(i / 10_000)
        previous = guess
    return changes == [config.HUMAN_THRESHOLD, round(config.AI_THRESHOLD + 1e-4, 4)], changes


def run_trial(trial, url, timeout):
    human = load("human_samples.json")
    ai = load("ai_samples.json")
    rows = []
    for sample, truth in [(s, "human") for s in human] + [(s, "ai") for s in ai]:
        status, body = submit(url, sample["text"], f"eval_t{trial}_{sample['id']}", timeout)
        rows.append({"id": sample["id"], "truth": truth, "plain": sample.get("plain"),
                     "status": status, **{k: body.get(k) for k in (
                         "content_id", "guess", "confidence", "model_score", "style_score", "label")}})
    human_rows = [r for r in rows if r["truth"] == "human"]
    ai_rows = [r for r in rows if r["truth"] == "ai"]

    false_positives = [r["id"] for r in human_rows if r["guess"] == "ai"]
    gap = (statistics.mean(r["confidence"] for r in ai_rows)
           - statistics.mean(r["confidence"] for r in human_rows))
    labels_seen = {r["guess"] for r in rows}
    sweep_pass, sweep_changes = sweep_ok()

    # Criterion 4 — appeals on five fresh submissions, then three unknown ids.
    appeal_rows = []
    for sample in human[:5]:
        _, body = submit(url, sample["text"], f"eval_appeal_t{trial}_{sample['id']}", timeout)
        reason = f"evaluate.py trial {trial}: I wrote {sample['id']} myself."
        response = requests.post(f"{url}/appeal", json={"content_id": body["content_id"],
                                                        "reasoning": reason}, timeout=timeout)
        appeal_rows.append({"content_id": body["content_id"], "reason": reason,
                            "status": response.status_code,
                            "returned_status": response.json().get("status")})
    unknown_rows = []
    for _ in range(3):
        fake = uuid.uuid4().hex
        response = requests.post(f"{url}/appeal", json={"content_id": fake, "reasoning": "x"},
                                 timeout=timeout)
        unknown_rows.append({"content_id": fake, "status": response.status_code})
    _, entries = decision_count(url)
    for row in appeal_rows:
        appeals = [e for e in entries if e.get("content_id") == row["content_id"]
                   and e.get("event") == "appeal"]
        row["appeal_entries"] = len(appeals)
        row["reason_logged"] = bool(appeals) and appeals[0].get("reasoning") == row["reason"]
    for row in unknown_rows:
        row["appeal_entries"] = sum(e.get("content_id") == row["content_id"]
                                    and e.get("event") == "appeal" for e in entries)
    appeals_ok = sum(r["status"] == 200 and r["returned_status"] == "under_review"
                     and r["appeal_entries"] == 1 and r["reason_logged"] for r in appeal_rows)
    unknown_ok = sum(r["status"] == 404 and r["appeal_entries"] == 0 for r in unknown_rows)

    # Criterion 5 — twelve malformed requests.
    before, _ = decision_count(url)
    bad_rows = []
    for name, kwargs in bad_requests():
        response = requests.post(f"{url}/submit", timeout=timeout, **kwargs)
        try:
            error = response.json().get("error")
        except ValueError:
            error = None
        bad_rows.append({"request": name, "status": response.status_code, "error": error})
    after, _ = decision_count(url)
    bad_ok = sum(400 <= r["status"] < 500 and bool(r["error"]) for r in bad_rows)

    return {
        "trial": trial,
        "c1": {"false_positives": false_positives, "count": len(false_positives),
               "pass": len(false_positives) <= TARGET_MAX_FALSE_POSITIVES},
        "c2": {"mean_ai": round(statistics.mean(r["confidence"] for r in ai_rows), 4),
               "mean_human": round(statistics.mean(r["confidence"] for r in human_rows), 4),
               "gap": round(gap, 4), "pass": gap >= TARGET_MIN_GAP},
        "c3": {"labels_seen": sorted(labels_seen), "sweep_pass": sweep_pass,
               "sweep_changes": sweep_changes,
               "pass": sweep_pass and labels_seen == TARGET_LABELS},
        "c4": {"appeals_ok": appeals_ok, "unknown_ok": unknown_ok,
               "appeals": appeal_rows, "unknown": unknown_rows,
               "pass": appeals_ok == TARGET_APPEALS_OK and unknown_ok == TARGET_UNKNOWN_404},
        "c5": {"refused_cleanly": bad_ok, "new_decisions": after - before, "requests": bad_rows,
               "pass": bad_ok == TARGET_BAD_INPUT and after == before},
        "submissions": rows,
    }


def write_report(trials, stamp):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    json_path = config.RESULTS_DIR / f"eval_{stamp}.json"
    json_path.write_text(json.dumps(trials, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def cell(t, key):
        c = t[key]
        return {
            "c1": lambda: f"{c['count']} of 20",
            "c2": lambda: f"{c['gap']:.3f}",
            "c3": lambda: f"{len(c['labels_seen'])} of 3, sweep {'ok' if c['sweep_pass'] else 'GAP'}",
            "c4": lambda: f"{c['appeals_ok']}/5 + {c['unknown_ok']}/3",
            "c5": lambda: f"{c['refused_cleanly']}/12, {c['new_decisions']} decisions",
        }[key]()

    names = {
        "c1": ("1. False positives on known-human text", "<= 1 of 20 labelled AI"),
        "c2": ("2. Score separation (mean AI - mean human)", ">= 0.20"),
        "c3": ("3. Label coverage, no gaps/overlaps", "3 of 3 labels; 0 gaps"),
        "c4": ("4. Appeal path", "5/5 valid + 3/3 unknown -> 404"),
        "c5": ("5. Bad input refused cleanly", "12/12 4xx, 0 decisions"),
    }
    lines = [f"# Evaluation — {stamp}", "",
             "- Produced by: `evaluate.py::main` against the live service (`app.py`), real gpt2",
             "- Targets from `criteria.md` (committed before the first run)",
             f"- Raw responses: `{json_path.relative_to(config.ROOT).as_posix()}`", "",
             "| Criterion | Target | " + " | ".join(f"Run {t['trial']}" for t in trials) + " | Verdict |",
             "|---|---|" + "---|" * len(trials) + "---|"]
    for key, (name, target) in names.items():
        verdict = "PASS" if all(t[key]["pass"] for t in trials) else "FAIL"
        lines.append(f"| {name} | {target} | " + " | ".join(cell(t, key) for t in trials)
                     + f" | **{verdict}** |")

    lines += ["", "## Per-passage scores (trial 1)", "",
              "| id | truth | plain | model | style | combined | guess |", "|---|---|---|---|---|---|---|"]
    for r in trials[0]["submissions"]:
        lines.append(f"| {r['id']} | {r['truth']} | {'yes' if r['plain'] else ''} | {r['model_score']} "
                     f"| {r['style_score']} | {r['confidence']} | {r['guess']} |")
    md_path = config.RESULTS_DIR / f"eval_{stamp}.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path, json_path


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=f"http://{config.HOST}:{config.PORT}")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    try:
        requests.get(f"{args.url}/health", timeout=5)
    except requests.RequestException:
        sys.exit(f"Nothing answering at {args.url}. Start it:  python app.py")

    trials = []
    for trial in range(1, args.trials + 1):
        print(f"trial {trial}…", flush=True)
        result = run_trial(trial, args.url, args.timeout)
        trials.append(result)
        print("  " + "  ".join(f"{k}={'PASS' if result[k]['pass'] else 'FAIL'}"
                               for k in ("c1", "c2", "c3", "c4", "c5")))

    md_path, json_path = write_report(trials, dt.datetime.now().strftime("%Y-%m-%d_%H%M"))
    print(f"\nWrote {md_path.relative_to(config.ROOT)} and {json_path.relative_to(config.ROOT)}")
    print(md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
