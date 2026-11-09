#!/usr/bin/env python3
"""
Print raw style measures and the model signal on the CALIBRATION split only.

    python eval_data/calibrate.py

This is what the STYLE_*_RANGE constants in config.py were read off. It never
touches the evaluation set (human_samples.json / ai_samples.json).
"""

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import detector  # noqa: E402
import scoring  # noqa: E402
import stylometry  # noqa: E402

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def row(sample):
    text = sample["text"]
    m = detector.model_signal(text)
    s = stylometry.style_signal(text)
    return {
        "id": sample["id"],
        "plain": sample.get("plain"),
        "spread": stylometry.sentence_length_spread(text),
        "mattr": stylometry.type_token_ratio(text),
        "punct": stylometry.punctuation_density(text),
        "model": m,
        "style": s,
        "combined": round(scoring.combine_signals(m, s), 4),
    }


def summary(name, rows):
    print(f"\n{name}  (n={len(rows)})")
    for key in ("spread", "mattr", "punct", "model", "style", "combined"):
        vals = [r[key] for r in rows]
        print(f"  {key:9} mean {statistics.mean(vals):.3f}  "
              f"min {min(vals):.3f}  max {max(vals):.3f}")


def main():
    human = [row(s) for s in load("calibration_human.json")]
    ai = [row(s) for s in load("calibration_ai.json")]
    for r in human + ai:
        print(json.dumps(r))
    summary("calibration human", human)
    summary("calibration AI", ai)


if __name__ == "__main__":
    main()
