"""
Turning two numbers into one, and one number into something a person can read.

Two functions live here.

`combine_signals` is where your false-positive decision from Milestone 1
actually gets made. Everything above it — the labels, the appeal path — is
downstream of a number this function produced.

`score_to_label` is where you stop writing for a machine and start writing for
a person. A score of 0.62 means nothing to a writer.

⚠️ Your README's **Signals and Scoring** section has to name the file and
function holding your combining rule. The grader checks your code against what
you claim, so that line should read `scoring.py::combine_signals`.
"""

import math

import config


def _unit_interval(name: str, value) -> float:
    """A signal score must be a real number in [0, 1]; anything else is a bug upstream."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or math.isnan(value):
        raise ValueError(f"{name} must be a number, got {value!r}")
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")
    return float(value)


def combine_signals(model_score: float, style_score: float) -> float:
    """
    Combine two 0–1 signals into one 0–1 score. Higher means more likely AI.

    The rule, with every number in config.py:

      1. Weighted mean: WEIGHT_MODEL_SIGNAL (0.6) * model +
         WEIGHT_STYLE_SIGNAL (0.4) * style. The model signal counts for more
         because it reads the words; the style signal only sees the shape and
         is the cheaper one to fool.

      2. Disagreement shrink: when the two signals are more than
         DISAGREEMENT_GAP (0.3) apart, the mean is pulled toward 0.5 by the
         fraction of the remaining distance they've split by:

             keep = 1 - (|model - style| - GAP) / (1 - GAP)
             score = 0.5 + (mean - 0.5) * keep

         A full split (one at 0.0, the other at 1.0) lands exactly on 0.5.
         Two methods disagreeing IS uncertainty, so a single loud signal can't
         produce a high-confidence label on its own.

    Deterministic: the same two inputs always give the same output.
    """
    model = _unit_interval("model_score", model_score)
    style = _unit_interval("style_score", style_score)

    w_model, w_style = config.WEIGHT_MODEL_SIGNAL, config.WEIGHT_STYLE_SIGNAL
    score = (w_model * model + w_style * style) / (w_model + w_style)

    gap = abs(model - style)
    if gap > config.DISAGREEMENT_GAP:
        keep = 1.0 - (gap - config.DISAGREEMENT_GAP) / (1.0 - config.DISAGREEMENT_GAP)
        score = 0.5 + (score - 0.5) * keep

    return round(min(max(score, 0.0), 1.0), 4)


def score_to_label(score: float) -> tuple[str, str]:
    """
    Turn a score into a guess and the text a reader actually sees.
    ← TODO (Milestone 5)

    Returns:
        (guess, label_text) — where `guess` is a short machine-readable string
        like "ai" / "human" / "unsure", and `label_text` is the full sentence
        shown to a person.

    ⚠️ Write the label text for someone who has never heard the word
    "threshold".

        ✗ "human, 0.81 confidence"
        ✓ "We think this was probably written by a person."

    All three labels have to be **reachable**. If no score can produce one of
    them, your ranges have a gap — and Milestone 5 asks you to submit text that
    produces each one, which is how you'd find out.

    The hardest one to write is "unsure". It has to admit uncertainty without
    sounding like an accusation, because the person reading it may well have
    written every word themselves. Your breakout asks your group what they'd
    think if they got it on their own work. That question is the whole
    milestone.
    """
    # TODO: replace this — thresholds are in config.py
    if score >= config.AI_THRESHOLD:
        return "ai", "PLACEHOLDER — write the high-confidence AI label."
    if score <= config.HUMAN_THRESHOLD:
        return "human", "PLACEHOLDER — write the high-confidence human label."
    return "unsure", "PLACEHOLDER — write the unsure label."


def label_ranges() -> list[tuple[str, str]]:
    """
    The score range each label covers. Your README needs these beside the
    label text — given to you so the numbers can't drift apart from config.py.
    """
    return [
        ("high-confidence human", f"0.00 – {config.HUMAN_THRESHOLD:.2f}"),
        ("unsure", f"{config.HUMAN_THRESHOLD:.2f} – {config.AI_THRESHOLD:.2f}"),
        ("high-confidence AI", f"{config.AI_THRESHOLD:.2f} – 1.00"),
    ]
