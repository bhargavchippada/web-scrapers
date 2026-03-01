# Version: v0.1.0
"""Tests for the Reddit scraper (mocked — no API calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from web_scrapers.scrapers.reddit import RedditScraper, _parse_submission


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
