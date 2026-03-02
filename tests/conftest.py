# Version: v0.2.0
"""Shared test fixtures for web-scrapers."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from web_scrapers.models.reddit import RedditComment, RedditPost, SentimentScore


@pytest.fixture
def sample_sentiment() -> SentimentScore:
    return SentimentScore(positive=0.3, negative=0.1, neutral=0.6, compound=0.5)


@pytest.fixture
def sample_reddit_post(sample_sentiment: SentimentScore) -> RedditPost:
    return RedditPost(
        id="abc123",
        subreddit="wallstreetbets",
        title="GME to the moon",
        selftext="Diamond hands forever",
        author="test_user",
        score=500,
        upvote_ratio=0.85,
        num_comments=120,
        created_utc=datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC),
        url="https://reddit.com/r/wallstreetbets/abc123",
        flair="YOLO",
        sentiment=sample_sentiment,
    )


@pytest.fixture
def mock_reddit_submission() -> MagicMock:
    """Create a mock praw Submission object."""
    sub = MagicMock()
    sub.id = "xyz789"
    sub.title = "SPY puts printing"
    sub.selftext = "Bought puts at open, printing hard"
    author = MagicMock()
    author.name = "trader_joe"
    sub.author = author
    sub.score = 200
    sub.upvote_ratio = 0.92
    sub.num_comments = 45
    sub.created_utc = 1737000000.0
    sub.permalink = "/r/options/comments/xyz789/spy_puts_printing/"
    sub.link_flair_text = "Gain"
    sub.subreddit = MagicMock()
    sub.subreddit.display_name = "options"
    return sub


@pytest.fixture
def mock_reddit_comment() -> MagicMock:
    """Create a mock praw Comment object."""
    comment = MagicMock()
    comment.id = "cmt123"
    comment.body = "This is bullish AF!"
    author = MagicMock()
    author.name = "comment_user"
    comment.author = author
    comment.score = 50
    comment.created_utc = 1737001000.0
    comment.parent_id = "t3_xyz789"  # t3_ prefix indicates parent is a post
    comment.permalink = "/r/options/comments/xyz789/spy_puts_printing/cmt123/"
    return comment


@pytest.fixture
def sample_reddit_comment(sample_sentiment: SentimentScore) -> RedditComment:
    return RedditComment(
        id="cmt456",
        post_id="xyz789",
        subreddit="options",
        body="Great DD, I'm in!",
        author="commenter",
        score=25,
        created_utc=datetime(2026, 1, 15, 12, 30, 0, tzinfo=UTC),
        parent_id="t3_xyz789",
        is_top_level=True,
        depth=0,
        permalink="https://reddit.com/r/options/comments/xyz789/test/cmt456/",
        sentiment=sample_sentiment,
    )


@pytest.fixture
def sample_rss_xml() -> str:
    """Minimal RSS 2.0 feed XML for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Financial News</title>
    <link>https://example.com</link>
    <description>Test feed</description>
    <item>
      <title>Markets rally on Fed decision</title>
      <link>https://example.com/article/1</link>
      <description>Stocks surged after the Federal Reserve announced rate cuts.</description>
      <pubDate>Mon, 15 Jan 2026 12:00:00 GMT</pubDate>
      <guid>https://example.com/article/1</guid>
    </item>
    <item>
      <title>Oil prices drop sharply</title>
      <link>https://example.com/article/2</link>
      <description>Crude oil fell 5% on oversupply fears.</description>
      <pubDate>Mon, 15 Jan 2026 14:00:00 GMT</pubDate>
      <guid>https://example.com/article/2</guid>
    </item>
  </channel>
</rss>"""
