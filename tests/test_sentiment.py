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

    def test_unicode_emoji_text(self) -> None:
        result = score_sentiment("🚀🌙💎🙌 bullish af!!!")
        # VADER doesn't score emoji, but should not crash
        assert -1.0 <= result.compound <= 1.0

    def test_all_numbers(self) -> None:
        result = score_sentiment("123 456 789 000")
        assert result.compound == 0.0

    def test_very_long_text(self) -> None:
        text = "This is great! " * 500
        result = score_sentiment(text)
        assert result.compound > 0.0

    def test_mixed_sentiment(self) -> None:
        result = score_sentiment("Good news and bad news today")
        # Mixed sentiment — compound could go either way
        assert -1.0 <= result.compound <= 1.0

    def test_financial_jargon(self) -> None:
        result = score_sentiment("Massive short squeeze incoming, bears are dead")
        # VADER may not perfectly parse financial jargon but should not crash
        assert -1.0 <= result.compound <= 1.0
