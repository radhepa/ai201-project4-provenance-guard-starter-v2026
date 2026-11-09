"""
Signal two: the style signal.

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures, each turned into a 0-1 AI-likeness score and averaged:

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures ───────────────────────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies: the coefficient of variation (standard
    deviation / mean) of words per sentence.

    Returns a float >= 0. **Higher means more human** — human writing puts a
    three-word sentence next to a forty-word one; generated prose marches in
    step. Dividing by the mean makes long and short texts comparable.

    Fewer than two sentences has no spread to measure and returns 0.0;
    `style_signal` treats that case as "no evidence" rather than as AI.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    return round(statistics.stdev(lengths) / mean, 4)


def type_token_ratio(text: str, window: int = 50) -> float:
    """
    Vocabulary variety, short-text safe: the moving-average type-token ratio
    (MATTR) — unique words over total words inside every run of `window`
    words, averaged.

    Returns a float in [0, 1]. **Higher means more varied vocabulary** — and,
    on my calibration data, more AI-like: generated prose avoids repeating a
    word inside a 50-word window, while human narrative repeats pronouns and
    names. That's the opposite of what I assumed before measuring.

    Plain TTR falls as text gets longer (common words repeat), so a 60-word
    and a 600-word text aren't comparable on it. A fixed window removes most
    of that length effect. Text shorter than the window falls back to plain
    TTR over all of it; no words at all returns 0.0.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    if len(tokens) <= window:
        return round(len(set(tokens)) / len(tokens), 4)
    ratios = [len(set(tokens[i:i + window])) / window
              for i in range(len(tokens) - window + 1)]
    return round(statistics.mean(ratios), 4)


# Expressive punctuation: the marks that vary most between writers. Full stops
# and commas are left out on purpose — every writer uses them, and generated
# prose uses commas heavily ("such as X, Y, and Z").
_EXPRESSIVE = re.compile(r"[;:!?()\"“”‘—–…]|--| - |(?<!\w)'|'(?!\w)")


def punctuation_density(text: str) -> float:
    """
    Expressive punctuation per word: semicolons, colons, dashes, brackets,
    quotation marks, question and exclamation marks, ellipses.

    Returns a float >= 0. **Higher means more human** in my reading: generated
    prose leans on full stops and commas and rarely reaches for a semicolon,
    a dash or a quotation. Apostrophes inside words (don't, Mary's) aren't
    counted.
    """
    n = len(words(text))
    if n == 0:
        return 0.0
    return round(len(_EXPRESSIVE.findall(text)) / n, 4)


# ── Combining them ───────────────────────────────────────────────────────────

def _scale(value: float, ai_end: float, human_end: float) -> float:
    """Map a measure onto 0-1 AI-likeness: 1.0 at ai_end, 0.0 at human_end, clamped."""
    score = (human_end - value) / (human_end - ai_end)
    return min(max(score, 0.0), 1.0)


def measure_scores(text: str) -> dict:
    """
    Each measure as a 0-1 AI-likeness score (higher = more AI-like).

    `_scale` maps each raw measure between its (ai_end, human_end) pair from
    config.py: spread and punctuation run "higher = more human", MATTR runs
    "higher = more AI". The pairs were set from the calibration split only
    (eval_data/calibration_*.json), never from the evaluation set.
    """
    import config

    spread = (_scale(sentence_length_spread(text), *config.STYLE_SPREAD_RANGE)
              if len(sentences(text)) >= 2 else 0.5)  # one sentence: no evidence
    return {
        "sentence_length_spread": round(spread, 4),
        "type_token_ratio": round(_scale(type_token_ratio(text), *config.STYLE_TTR_RANGE), 4),
        "punctuation_density": round(_scale(punctuation_density(text), *config.STYLE_PUNCT_RANGE), 4),
    }


def style_signal(text: str) -> float:
    """
    The style signal as a 0-1 score. **Higher means more likely AI.**

    The weighted mean of the three flipped, scaled measures, with weights
    from config.STYLE_WEIGHTS. Same direction as `detector.model_signal`.
    """
    import config

    scores = measure_scores(text)
    total = sum(config.STYLE_WEIGHTS.values())
    value = sum(config.STYLE_WEIGHTS[k] * scores[k] for k in scores) / total
    return round(min(max(value, 0.0), 1.0), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
    print(f"per-measure AI-likeness  {measure_scores(text)}")
