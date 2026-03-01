# Version: v0.1.0
"""Tests for Pydantic data models."""

from datetime import UTC, datetime

import pytest

from web_scrapers.models.base import SignalEvent
from web_scrapers.models.news import NewsArticle
from web_scrapers.models.reddit import RedditPost, SentimentScore


class TestSentimentScore:
    def test_valid_scores(self) -> None:
        s = SentimentScore(positive=0.5, negative=0.2, neutral=0.3, compound=0.4)
        assert s.positive == 0.5
        assert s.compound == 0.4

    def test_compound_range(self) -> None:
        s = SentimentScore(positive=0.0, negative=1.0, neutral=0.0, compound=-1.0)
        assert s.compound == -1.0

    def test_invalid_positive_raises(self) -> None:
        with pytest.raises(ValueError):
            SentimentScore(positive=1.5, negative=0.0, neutral=0.0, compound=0.0)


class TestRedditPost:
    def test_deleted_author_coerced(self) -> None:
        post = RedditPost(
            id="t1",
            subreddit="test",
            title="Test",
            author="[deleted]",
            created_utc=datetime.now(UTC),
            url="https://reddit.com/t1",
            sentiment=SentimentScore(positive=0.0, negative=0.0, neutral=1.0, compound=0.0),
        )
        assert post.author is None

    def test_none_author_stays_none(self) -> None:
        post = RedditPost(
            id="t2",
            subreddit="test",
            title="Test",
            author=None,
            created_utc=datetime.now(UTC),
            url="https://reddit.com/t2",
            sentiment=SentimentScore(positive=0.0, negative=0.0, neutral=1.0, compound=0.0),
        )
        assert post.author is None

    def test_valid_author_preserved(self, sample_reddit_post: RedditPost) -> None:
        assert sample_reddit_post.author == "test_user"

    def test_scraped_at_auto_set(self, sample_reddit_post: RedditPost) -> None:
        assert sample_reddit_post.scraped_at is not None
        assert sample_reddit_post.scraped_at.tzinfo is not None


class TestNewsArticle:
    def test_minimal_article(self) -> None:
        a = NewsArticle(
            id="n1",
            feed_name="Test Feed",
            title="Test Article",
            link="https://example.com/1",
        )
        assert a.id == "n1"
        assert a.summary == ""
        assert a.category == ""

    def test_full_article(self) -> None:
        a = NewsArticle(
            id="n2",
            feed_name="Reuters",
            title="Markets Rally",
            summary="Stocks surged on Fed news",
            link="https://reuters.com/1",
            author="John Doe",
            published=datetime(2026, 1, 15, tzinfo=UTC),
            category="markets",
        )
        assert a.author == "John Doe"
        assert a.category == "markets"


class TestSignalEvent:
    def test_event_creation(self, sample_reddit_post: RedditPost) -> None:
        event = SignalEvent(
            source="reddit",
            event_type="post",
            payload=sample_reddit_post.model_dump(mode="json"),
            event_id="reddit:abc123",
        )
        assert event.source == "reddit"
        assert event.event_id == "reddit:abc123"
        assert event.ingested_at is not None

    def test_news_event(self) -> None:
        article = NewsArticle(
            id="n1", feed_name="Test", title="Test", link="https://example.com"
        )
        event = SignalEvent(
            source="news",
            event_type="article",
            payload=article.model_dump(mode="json"),
            event_id="news:n1",
        )
        assert event.source == "news"
        assert event.payload["feed_name"] == "Test"
