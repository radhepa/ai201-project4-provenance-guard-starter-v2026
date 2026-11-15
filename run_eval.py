#!/usr/bin/env python3
"""
Run your five criteria three times each.  <- UNIT 8, MILESTONE 3

    python app.py                              # in one terminal
    python run_eval.py --label before          # in another
    python run_eval.py --label after

The attack set tests what staff thought to test. This tests what *you* thought
to test, and the two rarely overlap much. Both count.

Fill in `scenarios.py` first — that's where you say what each criterion needs
run against it. A criterion about false positives needs your own writing. One
about label coverage needs inputs across the score range.

!! Three trials, and **your first signal runs a model, so identical input can
score differently twice.** That's exactly why repeats matter here.

This does the sending and the recording. It does not decide whether a trial
passed — that depends on the criterion you wrote, so the Verdict column comes
back blank.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import config

# Windows consoles often run a codepage that can't print every character in
# this file's help text. Without this, `--help` ends in a UnicodeEncodeError
# traceback instead of the help — which is a miserable first thing to hit.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):  # not a normal text stream
        pass


DEFAULT_URL = f"http://{config.HOST}:{config.PORT}"


def bodies_for(scenario):
    """
    The request bodies one scenario sends.

    A "texts" scenario gets a creator_id made up for it. A "bodies" scenario is
    sent exactly as written, which is how a bad-input criterion says things a
    string can't — no `text` field, a null, something enormous.
    """
    if scenario.get("bodies"):
        return list(scenario["bodies"])
    return [
        {"text": text, "creator_id": f"eval_{scenario['name'][:12]}_{i}"}
        for i, text in enumerate(scenario["texts"], 1)
    ]


def post_body(requests, url, body, timeout):
    """Send one body: raw bytes when it says `_raw`, JSON otherwise."""
    if "_raw" in body:
        return requests.post(f"{url}/submit", data=body["_raw"].encode("utf-8"),
                             headers={"Content-Type": body["_content_type"]}, timeout=timeout)
    return requests.post(f"{url}/submit", json=body, timeout=timeout)


def log_entries(requests, url):
    return requests.get(f"{url}/log", timeout=30).json()["entries"]


def run_appeals(requests, url, results, scenario, trial, timeout):
    """
    Criterion 4: appeal every content_id that came back, then some made-up
    ones, and check what the audit log recorded for each.
    """
    import uuid

    for i, row in enumerate(results, 1):
        reason = f"run_eval trial {trial}: I wrote piece {i} myself."
        row["appeal_reason"] = reason
        response = requests.post(f"{url}/appeal", json={"content_id": row.get("content_id") or "",
                                                        "reasoning": reason}, timeout=timeout)
        row["appeal_status"] = response.status_code
        row["appeal_returned_status"] = response.json().get("status")
    for _ in range(scenario.get("unknown_appeals", 0)):
        fake = uuid.uuid4().hex
        response = requests.post(f"{url}/appeal", json={"content_id": fake, "reasoning": "x"},
                                 timeout=timeout)
        results.append({"unknown": True, "content_id": fake, "appeal_status": response.status_code,
                        "appeal_returned_status": response.json().get("status"), "sent": "(appeal only)"})

    entries = log_entries(requests, url)
    for row in results:
        appeals = [e for e in entries if e.get("event") == "appeal"
                   and e.get("content_id") == row.get("content_id")]
        row["appeal_entries"] = len(appeals)
        if not row.get("unknown"):
            row["reason_logged"] = bool(appeals) and appeals[0].get("reasoning") == row["appeal_reason"]


def describe(body):
    """A short, readable note of what was sent — for the report."""
    if "_raw" in body:
        return f"raw {body['_content_type']}: {body['_raw'][:60]!r}"
    if set(body) == {"text", "creator_id"} and isinstance(body.get("text"), str):
        text = body["text"]
        return text[:70] if text else "(empty text)"
    return json.dumps(body)[:120]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--label", default="")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--pause", type=float, default=65.0,
                        help="seconds between trials, so one trial's malformed requests "
                             "(counted per address) don't eat the next trial's rate limit")
    args = parser.parse_args()

    try:
        import requests
    except ImportError:
        print("The `requests` package isn't installed.\n"
              "Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    try:
        import scenarios
    except ImportError:
        print("No scenarios.py found. Milestone 3 starts by filling it in.",
              file=sys.stderr)
        sys.exit(1)

    problems = scenarios.validate()
    if problems:
        print("scenarios.py has problems:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    try:
        requests.get(f"{args.url}/health", timeout=5)
    except Exception:  # noqa: BLE001
        print(f"Nothing answering at {args.url}. Start it:  python app.py",
              file=sys.stderr)
        sys.exit(1)

    if args.trials < 3:
        print(f"!! {args.trials} trial(s). The submission asks for three.\n")

    import time

    # Trials on the outside: trial 1 runs every scenario, then trial 2, ... so
    # a criterion that needs two scenarios (the score gap) reads one trial.
    rows = [{"scenario": s, "trials": []} for s in scenarios.SCENARIOS]
    for trial in range(1, args.trials + 1):
        if trial > 1 and args.pause:
            print(f"\n(pausing {args.pause:.0f}s so the per-minute limit resets)")
            time.sleep(args.pause)
        print(f"\n=== trial {trial} ===")
        for row in rows:
            scenario = row["scenario"]
            decisions_before = sum("event" not in e for e in log_entries(requests, args.url))
            results = []
            for i, body in enumerate(bodies_for(scenario), 1):
                preview = describe(body)
                try:
                    response = post_body(requests, args.url, body, args.timeout)
                    try:
                        payload = response.json() if response.content else {}
                    except ValueError:
                        payload = {"error": None, "_not_json": response.text[:200]}
                    results.append({
                        "status": response.status_code,
                        "content_id": payload.get("content_id"),
                        "guess": payload.get("guess"),
                        "confidence": payload.get("confidence"),
                        "model_score": payload.get("model_score"),
                        "style_score": payload.get("style_score"),
                        "label": payload.get("label"),
                        "error": payload.get("error"),
                        "sent": preview,
                    })
                except Exception as exc:  # noqa: BLE001
                    results.append({"status": None, "error": f"{type(exc).__name__}: {exc}",
                                    "sent": preview})
            if scenario.get("appeal"):
                run_appeals(requests, args.url, results, scenario, trial, args.timeout)
            added = sum("event" not in e for e in log_entries(requests, args.url)) - decisions_before
            for result in results:
                result["decisions_added"] = added

            row["trials"].append(results)
            guesses = [r.get("guess") or str(r.get("status")) for r in results]
            print(f"  {scenario['name']}: {', '.join(guesses)}")

        by_name = {row["scenario"]["name"]: row["trials"][-1] for row in rows}
        for row in rows:
            check = row["scenario"].get("check")
            row.setdefault("cells", []).append(check(by_name) if check else ("", None))
            print(f"  -> criterion {row['scenario'].get('criterion')}: {row['cells'][-1][0]}")

    write_report(rows, args)


def write_report(rows, args):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = args.trials
    headers = " | ".join(f"Run {i}" for i in range(1, n + 1))
    divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        "- Produced by: `run_eval.py::main`",
        "- Service: `app.py::submit` · scoring: `scoring.py::combine_signals`",
        f"- {n} trials per criterion · {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Fill in Target from `criteria.md`, and Run and Verdict from the output",
        "underneath. Whether a trial passed depends on the criterion you wrote.",
        "",
        f"| Criterion | Target | {headers} | Verdict |",
        f"|---|---|{divider}|---|",
    ]

    for row in rows:
        scenario = row["scenario"]
        number = scenario.get("criterion")
        name = scenario["name"]
        cells = row.get("cells") or [("", None)] * n
        decided = [passed for _, passed in cells]
        verdict = ("" if None in decided else "**MET**" if all(decided) else "**MISSED**")
        lines.append(f"| {name} | {scenario.get('target', '')} | "
                     f"{' | '.join(c for c, _ in cells)} | {verdict} |")

    lines += ["", "---", "", "## What actually came back", "",
              "Real output. Paste the relevant parts into your README — the rubric",
              "asks for the actual JSON, not a description of it.", ""]

    for row in rows:
        scenario = row["scenario"]
        lines += [f"### {scenario['name']}", ""]
        for trial_number, results in enumerate(row["trials"], 1):
            lines += [f"**Trial {trial_number}**", "", "```json",
                      json.dumps(results, indent=2), "```", ""]

    path.write_text("\n".join(lines), encoding="utf-8")
    raw = path.with_suffix(".json")
    raw.write_text(json.dumps([{"scenario": r["scenario"]["name"], "cells": r.get("cells"),
                                "trials": r["trials"]} for r in rows], indent=2), encoding="utf-8")
    print(f"\nWrote {path.relative_to(config.ROOT)} and {raw.name}")
    print("Commit it. It's the evidence the test actually happened.")


if __name__ == "__main__":
    main()
