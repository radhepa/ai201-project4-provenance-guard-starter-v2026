"""The combining rule and the label mapping, including every boundary."""

import itertools

import pytest

import config
import scoring

GUESSES = {"human", "unsure", "ai"}


class TestCombineSignals:
    @pytest.mark.parametrize("m,s", [(0, 0), (1, 1), (0, 1), (1, 0), (0.5, 0.5), (0.9, 0.2), (0.33, 0.71)])
    def test_in_unit_interval_and_deterministic(self, m, s):
        first = scoring.combine_signals(m, s)
        assert 0.0 <= first <= 1.0
        assert scoring.combine_signals(m, s) == first

    def test_agreement_extremes(self):
        assert scoring.combine_signals(0.0, 0.0) == 0.0
        assert scoring.combine_signals(1.0, 1.0) == 1.0

    def test_weighted_mean_when_signals_agree(self):
        m, s = 0.8, 0.7  # gap 0.1, under DISAGREEMENT_GAP
        expected = (config.WEIGHT_MODEL_SIGNAL * m + config.WEIGHT_STYLE_SIGNAL * s) / (
            config.WEIGHT_MODEL_SIGNAL + config.WEIGHT_STYLE_SIGNAL)
        assert scoring.combine_signals(m, s) == pytest.approx(expected, abs=1e-4)

    def test_uses_both_signals(self):
        assert scoring.combine_signals(0.8, 0.6) != scoring.combine_signals(0.8, 0.7)
        assert scoring.combine_signals(0.6, 0.8) != scoring.combine_signals(0.7, 0.8)

    def test_full_disagreement_is_exactly_unsure_middle(self):
        assert scoring.combine_signals(1.0, 0.0) == 0.5
        assert scoring.combine_signals(0.0, 1.0) == 0.5

    def test_disagreement_pulls_toward_half(self):
        m, s = 0.95, 0.3
        plain_mean = 0.6 * m + 0.4 * s
        combined = scoring.combine_signals(m, s)
        assert 0.5 < combined < plain_mean

    def test_one_loud_signal_alone_never_reaches_ai(self):
        assert scoring.score_to_label(scoring.combine_signals(1.0, 0.0))[0] == "unsure"
        assert scoring.score_to_label(scoring.combine_signals(1.0, 0.5))[0] == "unsure"

    @pytest.mark.parametrize("bad", [-0.01, 1.01, float("nan"), None, "0.5", True])
    def test_rejects_invalid_inputs(self, bad):
        with pytest.raises(ValueError):
            scoring.combine_signals(bad, 0.5)
        with pytest.raises(ValueError):
            scoring.combine_signals(0.5, bad)


class TestScoreToLabel:
    def test_extremes(self):
        assert scoring.score_to_label(0.0)[0] == "human"
        assert scoring.score_to_label(1.0)[0] == "ai"

    def test_middle_is_unsure(self):
        assert scoring.score_to_label(0.5)[0] == "unsure"
        assert scoring.score_to_label(0.49)[0] == "unsure"
        assert scoring.score_to_label(0.51)[0] == "unsure"

    def test_exact_boundaries_belong_to_unsure(self):
        assert scoring.score_to_label(config.HUMAN_THRESHOLD)[0] == "unsure"
        assert scoring.score_to_label(config.AI_THRESHOLD)[0] == "unsure"

    def test_adjacent_to_boundaries(self):
        eps = 1e-4
        assert scoring.score_to_label(config.HUMAN_THRESHOLD - eps)[0] == "human"
        assert scoring.score_to_label(config.HUMAN_THRESHOLD + eps)[0] == "unsure"
        assert scoring.score_to_label(config.AI_THRESHOLD - eps)[0] == "unsure"
        assert scoring.score_to_label(config.AI_THRESHOLD + eps)[0] == "ai"

    def test_sweep_has_no_gaps_or_overlaps(self):
        """Criterion 3(a): every score in a 0.0001 sweep gets one label, changing only at thresholds."""
        previous = None
        changes = []
        for i in range(10_001):
            score = i / 10_000
            guess, text = scoring.score_to_label(score)
            assert guess in GUESSES and text
            if previous is not None and guess != previous:
                changes.append(score)
            previous = guess
        assert changes == [config.HUMAN_THRESHOLD, round(config.AI_THRESHOLD + 1e-4, 4)]

    def test_labels_are_full_distinct_sentences(self):
        texts = {scoring.score_to_label(x)[1] for x in (0.0, 0.5, 1.0)}
        assert len(texts) == 3
        for text in texts:
            assert text[0].isupper() and text.endswith(".") and len(text.split()) >= 8
            assert "threshold" not in text.lower()

    def test_ai_threshold_is_conservative(self):
        assert config.AI_THRESHOLD >= 0.7
        assert config.AI_THRESHOLD - config.HUMAN_THRESHOLD >= 0.3

    @pytest.mark.parametrize("bad", [-0.1, 1.1, float("nan"), None])
    def test_rejects_out_of_range(self, bad):
        with pytest.raises(ValueError):
            scoring.score_to_label(bad)


def test_ai_label_requires_both_signals_above_half():
    """The AI label says 'two separate checks both pointed that way'. Check it's true."""
    grid = [i / 100 for i in range(101)]
    for m, s in itertools.product(grid, grid):
        if scoring.score_to_label(scoring.combine_signals(m, s))[0] == "ai":
            assert m > 0.5 and s > 0.5, (m, s)


def test_label_ranges_match_config():
    ranges = dict(scoring.label_ranges())
    assert set(ranges) == {"high-confidence human", "unsure", "high-confidence AI"}
    assert f"{config.HUMAN_THRESHOLD:.2f}" in ranges["unsure"]
    assert f"{config.AI_THRESHOLD:.2f}" in ranges["unsure"]
