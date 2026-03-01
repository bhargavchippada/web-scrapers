# Version: v0.1.0
"""Tests for the Reddit scraper (mocked — no API calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from web_scrapers.scrapers.reddit import (
    _ALLOWED_SORTS,
    RedditScraper,
    _parse_submission,
)


class TestParseSubmission:
    def test_parses_submission(self, mock_reddit_submission: MagicMock) -> None:
        post = _parse_submission(mock_reddit_submission, "options")
        assert post.id == "xyz789"
        assert post.subreddit == "options"
        assert post.title == "SPY puts printing"
        assert post.author == "trader_joe"
        assert post.score == 200
        assert post.sentiment is not None
        assert post.sentiment.compound != 0.0

    def test_deleted_author(self, mock_reddit_submission: MagicMock) -> None:
        mock_reddit_submission.author = None
        post = _parse_submission(mock_reddit_submission, "options")
        assert post.author is None


class TestRedditScraper:
    def test_name(self) -> None:
        scraper = RedditScraper()
        assert scraper.name == "reddit"

    @patch("web_scrapers.scrapers.reddit.get_subreddit_targets")
    def test_scrape_empty_targets(self, mock_targets: MagicMock) -> None:
        mock_targets.return_value = []
        scraper = RedditScraper()
        events = scraper.scrape()
        assert events == []

    @patch("web_scrapers.scrapers.reddit.get_subreddit_targets")
    def test_scrape_with_targets(
        self,
        mock_targets: MagicMock,
        mock_reddit_submission: MagicMock,
    ) -> None:
        mock_targets.return_value = [
            {"name": "options", "sort": "new", "limit": 5},
        ]
        mock_client = MagicMock()
        mock_subreddit = MagicMock()
        mock_subreddit.new.return_value = [mock_reddit_submission]
        mock_client.subreddit.return_value = mock_subreddit

        scraper = RedditScraper(client=mock_client)
        events = scraper.scrape()

        assert len(events) == 1
        assert events[0].source == "reddit"
        assert events[0].event_type == "post"
        assert events[0].event_id == "reddit:xyz789"

    @patch("web_scrapers.scrapers.reddit.get_subreddit_targets")
    def test_scrape_handles_error(
        self,
        mock_targets: MagicMock,
    ) -> None:
        mock_targets.return_value = [
            {"name": "badsubreddit", "sort": "new", "limit": 5},
        ]
        mock_client = MagicMock()
        mock_client.subreddit.side_effect = Exception("API error")

        scraper = RedditScraper(client=mock_client)
        events = scraper.scrape()
        assert events == []


class TestRedditScraperEdgeCases:
    def test_invalid_sort_rejected(self) -> None:
        mock_client = MagicMock()
        mock_client.subreddit.return_value = MagicMock()
        scraper = RedditScraper(client=mock_client)
        with pytest.raises(ValueError, match="Invalid sort method"):
            scraper._scrape_subreddit(mock_client, "test", "malicious_method", 10)

    def test_allowed_sorts_whitelist(self) -> None:
        assert "new" in _ALLOWED_SORTS
        assert "hot" in _ALLOWED_SORTS
        assert "top" in _ALLOWED_SORTS
        assert "rising" in _ALLOWED_SORTS
        assert "controversial" in _ALLOWED_SORTS
        assert "delete" not in _ALLOWED_SORTS

    @patch("web_scrapers.scrapers.reddit.get_subreddit_targets")
    def test_scrape_continues_on_subreddit_error(
        self,
        mock_targets: MagicMock,
        mock_reddit_submission: MagicMock,
    ) -> None:
        """If one subreddit fails, others still get scraped."""
        mock_targets.return_value = [
            {"name": "bad_sub", "sort": "new", "limit": 5},
            {"name": "good_sub", "sort": "new", "limit": 5},
        ]
        mock_client = MagicMock()
        bad_sub = MagicMock()
        bad_sub.new.side_effect = Exception("Private subreddit")
        good_sub = MagicMock()
        good_sub.new.return_value = [mock_reddit_submission]

        def route_subreddit(name: str) -> MagicMock:
            return bad_sub if name == "bad_sub" else good_sub

        mock_client.subreddit.side_effect = route_subreddit

        scraper = RedditScraper(client=mock_client)
        events = scraper.scrape()
        # Only good_sub produced events
        assert len(events) == 1

    @patch("web_scrapers.scrapers.reddit.get_subreddit_targets")
    def test_scrape_submission_parse_error_continues(
        self,
        mock_targets: MagicMock,
    ) -> None:
        """If one submission fails to parse, others still get processed."""
        mock_targets.return_value = [
            {"name": "test_sub", "sort": "new", "limit": 5},
        ]
        good_sub = MagicMock()
        good_sub.id = "good1"
        good_sub.title = "Good post"
        good_sub.selftext = "Content"
        author = MagicMock()
        author.name = "user"
        good_sub.author = author
        good_sub.score = 10
        good_sub.upvote_ratio = 0.9
        good_sub.num_comments = 5
        good_sub.created_utc = 1737000000.0
        good_sub.permalink = "/r/test/good1/"
        good_sub.link_flair_text = None

        bad_sub = MagicMock()
        bad_sub.id = "bad1"
        bad_sub.title = None  # Will cause error
        bad_sub.selftext = None
        bad_sub.author = None
        bad_sub.score = None  # Invalid
        bad_sub.upvote_ratio = "invalid"
        bad_sub.num_comments = None
        bad_sub.created_utc = "not_a_timestamp"
        bad_sub.permalink = "/r/test/bad1/"
        bad_sub.link_flair_text = None

        mock_client = MagicMock()
        mock_subreddit = MagicMock()
        mock_subreddit.new.return_value = [bad_sub, good_sub]
        mock_client.subreddit.return_value = mock_subreddit

        scraper = RedditScraper(client=mock_client)
        events = scraper.scrape()
        # bad_sub fails but good_sub succeeds
        assert len(events) == 1
        assert events[0].event_id == "reddit:good1"

    def test_parse_empty_selftext(self, mock_reddit_submission: MagicMock) -> None:
        mock_reddit_submission.selftext = ""
        post = _parse_submission(mock_reddit_submission, "test")
        assert post.selftext == ""

    def test_parse_none_flair(self, mock_reddit_submission: MagicMock) -> None:
        mock_reddit_submission.link_flair_text = None
        post = _parse_submission(mock_reddit_submission, "test")
        assert post.flair is None

    def test_health_check_returns_bool(self) -> None:
        mock_client = MagicMock()
        mock_sub = MagicMock()
        mock_sub.display_name = "test"
        mock_client.subreddit.return_value = mock_sub
        scraper = RedditScraper(client=mock_client)
        assert scraper.health_check() is True

    def test_health_check_failure(self) -> None:
        mock_client = MagicMock()
        mock_client.subreddit.side_effect = Exception("Auth failed")
        scraper = RedditScraper(client=mock_client)
        assert scraper.health_check() is False
