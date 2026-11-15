#!/usr/bin/env python3
"""
The capstone criteria (capstone/criteria.md), three trials, each from a cold start.

    python capstone/run_capstone_eval.py --label before
    python capstone/run_capstone_eval.py --cost 10        # the 10-run cost measurement

Each trial starts its own copy of the service (python app.py on --port), sends
the fixed 58-request batch with an X-Request-Id on every request, stops the
service, and checks logs/requests.jsonl against what the client saw. Verdicts
are computed by the check functions below, not typed by hand.
"""

import argparse
import datetime as dt
import json
import math
import os
import statistics
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
import metrics  # noqa: E402
import scenarios  # noqa: E402

BASE = ["timestamp", "request_id", "route", "method", "status", "duration_ms",
        "cpu_ms", "input_bytes", "input_sha256", "outcome"]
SCORED = ["words", "tokens_scored", "model_ms", "style_ms", "cold_start"]
RESPONSE_KEYS = {"content_id", "guess", "confidence", "label", "status",
                 "model_score", "style_score", "combined_score"}
REFERENCE = ROOT / "results" / "run_2026-11-14_2109_after.json"   # unit 8, after the fix


# ── the service ──────────────────────────────────────────────────────────────

def start_service(port, out):
    env = {**os.environ, "PORT": str(port), "AI201_DEBUG": "0", "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env,
                            stdout=out, stderr=subprocess.STDOUT)
    import requests
    for _ in range(120):
        try:
            requests.get(f"http://127.0.0.1:{port}/health", timeout=1)
            return proc
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    proc.terminate()
    raise SystemExit("service didn't come up")


def stop_service(proc):
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()


# ── one trial ────────────────────────────────────────────────────────────────

def batch():
    """The fixed 58 requests, as (kind, route, body) with body None for an appeal to fill in."""
    texts = scenarios.HUMAN_TEXTS + scenarios.AI_TEXTS
    reqs = [("eval", "/submit", {"text": t, "creator_id": f"cap_eval_{i}"}) for i, t in enumerate(texts)]
    reqs += [("malformed", "/submit", b) for b in scenarios.SCENARIOS[4]["bodies"]]
    reqs += [("burst", "/submit", {"text": "Too short to judge, sent again.", "creator_id": "cap_burst"})
             for _ in range(12)]
    reqs += [("appeal_valid", "/appeal", None), ("appeal_unknown", "/appeal", None)]
    reqs += [("extra", "/submit", {"text": t, "creator_id": "cap_extra"}) for t in scenarios.AI_TEXTS[:2]]
    return reqs


def send(requests, url, route, body, rid):
    headers = {"X-Request-Id": rid}
    t0 = time.perf_counter()
    if "_raw" in body:
        r = requests.post(url + route, data=body["_raw"].encode(), timeout=120,
                          headers={**headers, "Content-Type": body["_content_type"]})
    else:
        r = requests.post(url + route, json=body, timeout=120, headers=headers)
    client_ms = (time.perf_counter() - t0) * 1000
    try:
        data = r.json()
    except ValueError:
        data = {}
    return r.status_code, data, round(client_ms, 1)


def run_trial(trial, port, label):
    import requests
    url = f"http://127.0.0.1:{port}"
    tag = uuid.uuid4().hex[:8]
    out = open(ROOT / "logs" / f"capstone_server_{label or 'run'}_{trial}.txt", "w", encoding="utf-8")
    proc = start_service(port, out)
    rows = []
    try:
        first_id = None
        for i, (kind, route, body) in enumerate(batch()):
            if kind == "appeal_valid":
                body = {"content_id": first_id or "", "reasoning": "Capstone trial: I wrote this."}
            elif kind == "appeal_unknown":
                body = {"content_id": uuid.uuid4().hex, "reasoning": "x"}
            rid = f"cap-{tag}-{i:02d}"
            status, data, client_ms = send(requests, url, route, body, rid)
            if kind == "eval" and status == 200 and first_id is None:
                first_id = data.get("content_id")
            rows.append({"i": i, "kind": kind, "route": route, "rid": rid, "status": status,
                         "client_ms": client_ms, "response": data,
                         "text": body.get("text") if isinstance(body.get("text"), str) else None})
    finally:
        stop_service(proc)
        out.close()
    entries = [e for e in metrics.read_entries() if str(e.get("request_id", "")).startswith(f"cap-{tag}-")]
    return {"trial": trial, "tag": tag, "rows": rows, "entries": entries}


# ── the five checks ──────────────────────────────────────────────────────────

def _by_rid(t):
    out = {}
    for e in t["entries"]:
        out.setdefault(e["request_id"], []).append(e)
    return out


def _accepted(t):
    by = _by_rid(t)
    return [(r, by[r["rid"]][0]) for r in t["rows"]
            if r["route"] == "/submit" and r["status"] == 200 and len(by.get(r["rid"], [])) == 1]


def check_complete(t):
    by = _by_rid(t)
    matched = sum(len(by.get(r["rid"], [])) == 1 for r in t["rows"])
    incomplete = []
    for r in t["rows"]:
        for e in by.get(r["rid"], []):
            need = BASE + (SCORED if r["route"] == "/submit" and r["status"] == 200 else [])
            missing = [k for k in need if e.get(k) is None]
            if missing:
                incomplete.append((r["kind"], r["status"], missing))
    n = len(t["rows"])
    return (f"{matched}/{n} matched, {len(incomplete)} incomplete",
            matched == n and not incomplete, incomplete)


def check_timing(t):
    by = _by_rid(t)
    pairs = [(r, by[r["rid"]][0]) for r in t["rows"] if len(by.get(r["rid"], [])) == 1]
    bounded = [isinstance(e["duration_ms"], (int, float)) and 0 <= e["duration_ms"] <= r["client_ms"]
               for r, e in pairs]
    close = [isinstance(e["duration_ms"], (int, float)) and r["client_ms"] - e["duration_ms"] <= 50
             for r, e in pairs]
    stages = [e["model_ms"] + e["style_ms"] <= e["duration_ms"] for _, e in _accepted(t)]
    n = len(t["rows"])
    frac_close = sum(close) / n
    gaps = sorted(round(r["client_ms"] - e["duration_ms"], 1) for r, e in pairs
                  if isinstance(e["duration_ms"], (int, float)))
    ok = sum(bounded) == n and frac_close >= 0.95 and all(stages)
    return (f"{sum(bounded)}/{n} bounded, {frac_close:.0%} <=50ms, stages {sum(stages)}/{len(stages)}",
            ok, {"max_gap_ms": gaps[-1] if gaps else None, "median_gap_ms": statistics.median(gaps) if gaps else None})


def check_privacy(t):
    raw = "\n".join(json.dumps(e) for e in t["entries"])
    grams = set()
    for r in t["rows"]:
        words = (r["text"] or "").split()
        grams.update(" ".join(words[i:i + 6]) for i in range(len(words) - 5))
    hits = [g for g in grams if g in raw]
    return f"{len(hits)} of {len(grams)} 6-grams found", not hits, hits[:3]


def p95(values):
    s = sorted(values)
    return s[math.ceil(0.95 * len(s)) - 1]


def check_budget(t):
    acc = [e for _, e in _accepted(t)]
    warm = [e for e in acc if e["cold_start"] is False]
    cold = [e for e in acc if e["cold_start"] is True]
    w95 = p95([e["duration_ms"] for e in warm])
    wcpu = statistics.mean(e["cpu_ms"] for e in warm)
    cold_ms = cold[0]["duration_ms"] if cold else None
    ok = w95 <= 2000 and wcpu <= 3000 and cold_ms is not None and cold_ms <= 30_000
    cold_txt = f"{cold_ms / 1000:.1f}s" if cold_ms is not None else "none"
    return (f"p95 {w95:.0f}ms, cpu {wcpu:.0f}ms, cold {cold_txt}", ok,
            {"warm_n": len(warm), "warm_p95_ms": w95, "warm_mean_cpu_ms": round(wcpu, 1),
             "warm_mean_ms": round(statistics.mean(e["duration_ms"] for e in warm), 1), "cold_ms": cold_ms})


def check_unchanged(t):
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    ref30 = next(s for s in ref if s["scenario"].startswith("3."))["trials"][0]
    evals = [r for r in t["rows"] if r["kind"] == "eval"]
    same = sum(r["response"].get("guess") == x["guess"] and r["response"].get("combined_score") == x["confidence"]
               for r, x in zip(evals, ref30))
    keys_ok = all(set(r["response"]) == RESPONSE_KEYS for r in evals if r["status"] == 200)
    return f"{same}/30 identical, keys {'same' if keys_ok else 'CHANGED'}", same == 30 and keys_ok, None


CRITERIA = [
    ("1. Every request leaves one complete entry", "58/58 matched, 0 incomplete", check_complete),
    ("2. Timings trustworthy", "100% bounded, >=95% <=50ms, stages 100%", check_timing),
    ("3. No writer text in the log", "0 6-grams found", check_privacy),
    ("4. Latency and CPU budget", "warm p95 <=2000ms, cpu <=3000ms, cold <=30s", check_budget),
    ("5. Decisions unchanged", "30/30 identical, same 8 keys", check_unchanged),
]


# ── the 10-run cost measurement ──────────────────────────────────────────────

def run_cost(n, port, label):
    import requests
    url = f"http://127.0.0.1:{port}"
    texts = scenarios.HUMAN_TEXTS[:n // 2] + scenarios.AI_TEXTS[:n - n // 2]
    tag = uuid.uuid4().hex[:8]
    out = open(ROOT / "logs" / f"capstone_server_cost_{label or 'run'}.txt", "w", encoding="utf-8")
    proc = start_service(port, out)
    try:
        # one throwaway submission so the 10 measured runs are all warm; it's logged as the cold start
        send(requests, url, "/submit", {"text": scenarios.AI_TEXTS[-1], "creator_id": "cap_cost_warmup"},
             f"cost-{tag}-warm")
        for i, text in enumerate(texts):
            send(requests, url, "/submit", {"text": text, "creator_id": f"cap_cost_{i}"}, f"cost-{tag}-{i:02d}")
    finally:
        stop_service(proc)
        out.close()
    entries = {e["request_id"]: e for e in metrics.read_entries()
               if str(e.get("request_id", "")).startswith(f"cost-{tag}-")}
    runs = [entries[f"cost-{tag}-{i:02d}"] for i in range(len(texts))]
    cold = entries[f"cost-{tag}-warm"]

    cpu = [e["cpu_ms"] for e in runs]
    wall = [e["duration_ms"] for e in runs]
    tok = [e["tokens_scored"] for e in runs]
    lines = [f"# Capstone cost — {n} runs", "",
             "- Produced by: `capstone/run_capstone_eval.py::run_cost`, from `logs/requests.jsonl`",
             f"- {dt.datetime.now():%Y-%m-%d %H:%M} · request ids `cost-{tag}-*` · machine: "
             f"{os.cpu_count()} logical CPUs, CPU-only torch", "",
             "| Run | tokens | duration_ms | cpu_ms | model_ms | style_ms | guess |",
             "|---|---|---|---|---|---|---|"]
    for i, e in enumerate(runs, 1):
        lines.append(f"| {i} | {e['tokens_scored']} | {e['duration_ms']} | {e['cpu_ms']} | "
                     f"{e['model_ms']} | {e['style_ms']} | {e['outcome']} |")
    total_cpu, total_wall = sum(cpu) / 1000, sum(wall) / 1000
    mean_cpu, mean_wall, mean_tok = total_cpu / n, total_wall / n, sum(tok) / n
    lines += ["",
              f"Cold start (model load, not one of the {n}): duration {cold['duration_ms']} ms, "
              f"cpu {cold['cpu_ms']} ms.", "",
              "```",
              f"total CPU   = {' + '.join(f'{c / 1000:.3f}' for c in cpu)} = {total_cpu:.3f} CPU-s",
              f"per run     = {total_cpu:.3f} / {n} = {mean_cpu:.3f} CPU-s   (wall {mean_wall:.3f} s, {mean_tok:.0f} tokens)",
              f"100 a day   = 100 x {mean_cpu:.3f} = {100 * mean_cpu:.1f} CPU-s = {100 * mean_cpu / 60:.2f} CPU-min of compute",
              f"            + 1 cold start a day ({cold['cpu_ms'] / 1000:.1f} CPU-s) = {100 * mean_cpu + cold['cpu_ms'] / 1000:.1f} CPU-s",
              f"tokens/day  = 100 x {mean_tok:.0f} = {100 * mean_tok:.0f} tokens through gpt2",
              "API spend   = $0 (gpt2 runs locally; no hosted API is called)",
              "```"]
    path = config.RESULTS_DIR / f"capstone_cost_{dt.datetime.now():%Y-%m-%d_%H%M}{'_' + label if label else ''}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote {path.relative_to(ROOT)}")


# ── report ───────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--label", default="")
    p.add_argument("--port", type=int, default=5001)
    p.add_argument("--cost", type=int, default=0, help="run the N-submission cost measurement instead")
    args = p.parse_args()
    (ROOT / "logs").mkdir(exist_ok=True)
    if args.cost:
        return run_cost(args.cost, args.port, args.label)

    trials = []
    for n in range(1, args.trials + 1):
        print(f"=== trial {n} ===", flush=True)
        t = run_trial(n, args.port, args.label)
        t["cells"] = []
        for name, _, check in CRITERIA:
            cell, ok, detail = check(t)
            t["cells"].append({"criterion": name, "cell": cell, "met": ok, "detail": detail})
            print(f"  {name}: {cell} -> {'MET' if ok else 'MISSED'}", flush=True)
        trials.append(t)

    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    path = config.RESULTS_DIR / f"capstone_run_{stamp}{'_' + args.label if args.label else ''}.md"
    lines = [f"# Capstone run log{' — ' + args.label if args.label else ''}", "",
             "- Produced by: `capstone/run_capstone_eval.py::main`",
             f"- {len(trials)} trials, each from a cold start · {dt.datetime.now():%Y-%m-%d %H:%M}", "",
             "| Criterion | Target | " + " | ".join(f"Run {t['trial']}" for t in trials) + " | Verdict |",
             "|---|---|" + "---|" * len(trials) + "---|"]
    for i, (name, target, _) in enumerate(CRITERIA):
        cells = [t["cells"][i] for t in trials]
        verdict = "**MET**" if all(c["met"] for c in cells) else "**MISSED**"
        lines.append(f"| {name} | {target} | " + " | ".join(c["cell"] for c in cells) + f" | {verdict} |")
    lines += ["", "## Details per trial", ""]
    for t in trials:
        lines += [f"### Trial {t['trial']} (request ids `cap-{t['tag']}-*`)", "", "```json",
                  json.dumps([{"criterion": c["criterion"], "detail": c["detail"]} for c in t["cells"]], indent=2),
                  "```", "", "Status codes: " + " ".join(str(r["status"]) for r in t["rows"]), ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    path.with_suffix(".json").write_text(json.dumps(trials, indent=2, default=str), encoding="utf-8")
    print("\n" + "\n".join(lines[5:5 + 2 + len(CRITERIA)]))
    print(f"\nWrote {path.relative_to(ROOT)} and .json")


if __name__ == "__main__":
    main()
