"""Signal two: each measure, its edge cases, and the CLI."""

import subprocess
import sys

import pytest

import stylometry
from conftest import AI_TEXT, HUMAN_TEXT, ROOT


class TestSentenceLengthSpread:
    def test_equal_sentences_have_no_spread(self):
        assert stylometry.sentence_length_spread("One two three. Four five six. Seven eight nine.") == 0.0

    def test_mixed_lengths_spread_more(self):
        even = "The cat sat down. The dog ran off. The bird flew up."
        lumpy = "Stop. The dog ran off down the long road past the old mill and the river. Why?"
        assert stylometry.sentence_length_spread(lumpy) > stylometry.sentence_length_spread(even)

    @pytest.mark.parametrize("text", ["", "   ", "Just one sentence here", "One sentence only."])
    def test_fewer_than_two_sentences_is_zero_not_a_crash(self, text):
        assert stylometry.sentence_length_spread(text) == 0.0


class TestTypeTokenRatio:
    def test_empty_text_is_zero(self):
        assert stylometry.type_token_ratio("") == 0.0
        assert stylometry.type_token_ratio("!!! ...") == 0.0

    def test_all_unique_short_text_is_one(self):
        assert stylometry.type_token_ratio("every word here differs") == 1.0

    def test_repetition_lowers_it(self):
        assert stylometry.type_token_ratio("the the the the") == 0.25

    def test_short_text_safe_and_in_range(self):
        for text in ["a", "a b", "word " * 3, AI_TEXT, HUMAN_TEXT * 5]:
            assert 0.0 <= stylometry.type_token_ratio(text) <= 1.0

    def test_moving_window_removes_most_of_the_length_effect(self):
        # Plain TTR on repeated text falls with length; MATTR stays put.
        once = stylometry.type_token_ratio(HUMAN_TEXT)
        five_times = stylometry.type_token_ratio(" ".join([HUMAN_TEXT] * 5))
        assert abs(once - five_times) < 0.1


class TestPunctuationDensity:
    def test_no_words_is_zero(self):
        assert stylometry.punctuation_density("") == 0.0

    def test_full_stops_and_commas_dont_count(self):
        assert stylometry.punctuation_density("Apples, pears, plums. Figs, dates.") == 0.0

    def test_expressive_marks_count(self):
        # ; ! ? and an em dash: 4 marks over 7 words
        assert stylometry.punctuation_density("Wait; stop! Why? I said — no more.") == pytest.approx(4 / 7, abs=1e-4)

    def test_apostrophes_inside_words_dont_count(self):
        assert stylometry.punctuation_density("I don't think Mary's cat can't swim.") == 0.0


class TestStyleSignal:
    @pytest.mark.parametrize("text", ["", "x", "One sentence only.", AI_TEXT, HUMAN_TEXT, "?!;" * 100])
    def test_always_between_zero_and_one(self, text):
        assert 0.0 <= stylometry.style_signal(text) <= 1.0

    def test_deterministic(self):
        assert stylometry.style_signal(AI_TEXT) == stylometry.style_signal(AI_TEXT)

    def test_direction_assistant_prose_scores_more_ai_than_lumpy_human(self):
        assert stylometry.style_signal(AI_TEXT) > stylometry.style_signal(HUMAN_TEXT)

    def test_measure_scores_are_each_normalised(self):
        scores = stylometry.measure_scores(HUMAN_TEXT)
        assert set(scores) == {"sentence_length_spread", "type_token_ratio", "punctuation_density"}
        assert all(0.0 <= v <= 1.0 for v in scores.values())

    def test_one_sentence_spread_is_neutral_not_ai(self):
        assert stylometry.measure_scores("A single sentence of ordinary words.")["sentence_length_spread"] == 0.5


def test_cli_runs_on_given_text():
    result = subprocess.run(
        [sys.executable, "stylometry.py", "some writing here. And a bit more!"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "style_signal" in result.stdout
