# Version: v0.1.0
"""VADER sentiment analysis — tuned for social media text."""

from __future__ import annotations

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from web_scrapers.models.reddit import SentimentScore

_analyzer = SentimentIntensityAnalyzer()


def score_sentiment(text: str) -> SentimentScore:
    """Score text sentiment using VADER. Returns positive/negative/neutral/compound."""
    scores = _analyzer.polarity_scores(text)
    return SentimentScore(
        positive=scores["pos"],
        negative=scores["neg"],
        neutral=scores["neu"],
        compound=scores["compound"],
    )
