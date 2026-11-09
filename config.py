"""
Settings for Provenance Guard.

Everything you're likely to change lives here, at the top, on purpose.

You'll edit the thresholds in Milestone 5 and the rate limits in unit 8.
"""

import os
from pathlib import Path

ROOT = Path(__file__).parent


# ─── The service ─────────────────────────────────────────────────────────────

# `127.0.0.1` is loopback — only your own machine can reach it, which is what
# you want all through units 7 and 8. A host somewhere else has to accept
# traffic from outside the box, and that means `0.0.0.0`. Setting the env var
# is how you get it; the default keeps your local `curl` commands unchanged.
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))

# Flask's debug mode gives anyone who can reach the service an interactive
# Python prompt inside your process. Fine on loopback, a gift to strangers
# anywhere else — so it turns itself off the moment HOST isn't loopback.
DEBUG = os.getenv("AI201_DEBUG", "1") == "1" and HOST in ("127.0.0.1", "localhost")


# ─── The local model ─────────────────────────────────────────────────────────
# Your first signal runs a language model ON YOUR OWN MACHINE. No account, no
# key, no card. It downloads about 550 MB the first time — do that before
# class, not during it.
#
# What it measures: how *predictable* your text is to a language model. Text a
# model finds easy to predict tends to be text a model wrote.
#
# The first call is the slow one — ten to twenty seconds while the model loads,
# longer on an older laptop. After that it stays in memory and a submission
# takes a second or two. That cost is part of what you're learning: this is
# what running a model inline in a request actually looks like.

DETECTOR_MODEL = os.getenv("AI201_DETECTOR_MODEL", "gpt2")

# Longer text gives a steadier reading but takes longer. 400 tokens is roughly
# 300 words, which is enough for the signal to mean something.
DETECTOR_MAX_TOKENS = 400


# ─── Scoring (Milestone 4) ───────────────────────────────────────────────────
# How much each signal counts toward the combined score.
#
# ⚠️ These are placeholders. Milestone 4 asks you to write your combining rule
# down BEFORE you code it, and to put the numbers in your README. Whatever you
# decide, it goes here.

# My rule (scoring.py::combine_signals), written down before coding it:
#
#   1. Weighted mean: 0.6 * model + 0.4 * style. The model signal gets more
#      weight because it reads the words; the style signal only sees shape and
#      is the cheaper one to fool.
#   2. Disagreement shrink: if the two signals are more than
#      DISAGREEMENT_GAP apart, the mean is pulled toward 0.5 (unsure) in
#      proportion to how far past the gap they are. At a full 1.0 split the
#      result is exactly 0.5. Two methods disagreeing IS uncertainty, and I'd
#      rather say "unsure" than accuse on one signal alone.

WEIGHT_MODEL_SIGNAL = 0.6
WEIGHT_STYLE_SIGNAL = 0.4
DISAGREEMENT_GAP = 0.3


# ─── The style signal (stylometry.py) ───────────────────────────────────────
# Each measure is mapped onto 0-1 AI-likeness linearly between
# (ai_end, human_end), clamped. The ends were read off the calibration split
# only (eval_data/calibration_*.json, `python eval_data/calibrate.py`), never
# off the evaluation set. Calibration means, human vs AI:
#
#   sentence-length CV      human 0.58   AI 0.25   -> low spread = AI
#   MATTR (window 50)       human 0.78   AI 0.87   -> HIGH variety = AI
#   expressive punct/word   human 0.075  AI 0.000  -> no punctuation = AI
#
# MATTR came out the opposite way to what I assumed going in: generated prose
# avoids repeating words inside a 50-word window, while human narrative
# repeats pronouns and names. So its scale runs high = AI.

STYLE_SPREAD_RANGE = (0.25, 0.60)   # (ai_end, human_end)
STYLE_TTR_RANGE = (0.87, 0.75)      # (ai_end, human_end) — flipped, see above
STYLE_PUNCT_RANGE = (0.00, 0.06)    # (ai_end, human_end)
STYLE_WEIGHTS = {
    "sentence_length_spread": 1.0,
    "type_token_ratio": 1.0,
    "punctuation_density": 1.0,
}


# ─── Thresholds (Milestone 5) ────────────────────────────────────────────────
# Where one label becomes another. Scores run 0.0 (confidently human) to 1.0
# (confidently AI).
#
#   score <  HUMAN_THRESHOLD                 -> high-confidence human
#   HUMAN_THRESHOLD <= score <= AI_THRESHOLD -> unsure
#   score >  AI_THRESHOLD                    -> high-confidence AI
#
# Both boundaries fall into "unsure" on purpose: a score sitting exactly on a
# line is the least certain score there is.
#
# ⚠️ This is where your false-positive decision from Milestone 1 actually gets
# made. Widening the unsure band means fewer wrong accusations and more AI text
# getting through. There is no setting that avoids the trade — only settings
# that decide who pays for it.

# Conservative on purpose: an AI label needs a combined score above 0.75,
# well clear of a coin flip, and the unsure band is 0.40 wide. Missing some AI
# text costs the site a little; accusing a real writer costs that person a lot.
HUMAN_THRESHOLD = 0.35
AI_THRESHOLD = 0.75

# ⚠️ One thing that catches people out in Milestone 5. A weighted average can
# only land between its two inputs — so while `style_signal` is still the stub
# returning 0.5, the combined score can never leave 0.25–0.75 no matter what
# the model signal says, and the human label needs a model score below 0.20 to
# be reachable at all.
#
# If a label you can't reach is the problem, the fix is upstream of the
# thresholds: a style signal that actually varies. `scoring.label_ranges()`
# prints the bands; the reachable range is a different question.


# ─── Input limits (POST /submit and /appeal) ────────────────────────────────
# Over MAX_TEXT_CHARS is refused with 413 rather than silently truncated; the
# detector reads only the first DETECTOR_MAX_TOKENS anyway, so a 1 MB body is
# all cost and no signal. Under MIN_TEXT_WORDS there's too little text for
# either signal to mean anything, so it's refused with 422 instead of labelled.

MAX_TEXT_CHARS = 20_000
MIN_TEXT_WORDS = 20
MAX_CREATOR_ID_CHARS = 128
MAX_APPEAL_REASON_CHARS = 5_000


# ─── Rate limiting (UNIT 8) ──────────────────────────────────────────────────
# Off in unit 7. You turn it on and choose the numbers in unit 8, Milestone 1.
#
# Think about two people: a real writer submitting their own work a few times
# an hour, and a script sending a thousand variations to map your thresholds.
# Your README has to say why your numbers and not others.

RATE_LIMITING_ENABLED = os.getenv("AI201_RATE_LIMITS", "0") == "1"

RATE_LIMIT_PER_MINUTE = 10
RATE_LIMIT_PER_DAY = 200

# Flask-Limiter warns loudly without this. In-memory is right for one laptop
# and wrong for anything real — a restart forgets every count, and two copies
# of the service wouldn't share limits.
RATE_LIMIT_STORAGE = "memory://"


# ─── Paths ───────────────────────────────────────────────────────────────────

LOG_DIR = ROOT / "logs"
AUDIT_LOG = LOG_DIR / "audit.jsonl"
RESULTS_DIR = ROOT / "results"
