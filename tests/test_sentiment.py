# Version: v0.1.0
"""Tests for VADER sentiment analysis."""

from web_scrapers.analysis.sentiment import score_sentiment


class TestScoreSentiment:
    def test_positive_text(self) -> None:
        result = score_sentiment("This is amazing and wonderful!")
        assert result.compound > 0.0
        assert result.positive > 0.0

    def test_negative_text(self) -> None:
        result = score_sentiment("This is terrible and awful, absolutely horrible.")
        assert result.compound < 0.0
        assert result.negative > 0.0

    def test_neutral_text(self) -> None:
        result = score_sentiment("The meeting is at 3pm.")
        assert abs(result.compound) < 0.3

    def test_empty_string(self) -> None:
        result = score_sentiment("")
        assert result.compound == 0.0
        assert result.neutral == 0.0

    def test_social_media_text(self) -> None:
        result = score_sentiment("GME TO THE MOON 🚀🚀🚀 diamond hands!!!")
        assert result.compound > 0.0

    def test_bounds(self) -> None:
        result = score_sentiment("Extremely good and wonderful")
        assert 0.0 <= result.positive <= 1.0
        assert 0.0 <= result.negative <= 1.0
        assert 0.0 <= result.neutral <= 1.0
        assert -1.0 <= result.compound <= 1.0
