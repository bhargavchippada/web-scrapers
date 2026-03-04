# Version: v0.4.0
"""Tests for db/queries.py — high-level query helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest


class TestGetLatestEvents:
    def test_returns_events_as_dicts(self) -> None:
        mock_session = MagicMock()
        mock_row = MagicMock()
        mock_row.event_id = "reddit:abc123"
        mock_row.source = "reddit"
        mock_row.event_type = "post"
        mock_row.payload = {"title": "Test Post"}
        mock_row.scraped_at = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)

        with (
            patch("web_scrapers.db.queries.get_session", return_value=mock_session),
            patch(
                "web_scrapers.db.queries.EventRepository.query_events",
                return_value=[mock_row],
            ),
        ):
            from web_scrapers.db.queries import get_latest_events

            result = get_latest_events(source="reddit", limit=10)

        assert len(result) == 1
        assert result[0]["event_id"] == "reddit:abc123"
        assert result[0]["source"] == "reddit"
        assert result[0]["payload"] == {"title": "Test Post"}
        assert "scraped_at" in result[0]

    def test_returns_empty_list_when_no_events(self) -> None:
        mock_session = MagicMock()

        with (
            patch("web_scrapers.db.queries.get_session", return_value=mock_session),
            patch(
                "web_scrapers.db.queries.EventRepository.query_events",
                return_value=[],
            ),
        ):
            from web_scrapers.db.queries import get_latest_events

            result = get_latest_events()

        assert result == []

    def test_closes_session(self) -> None:
        mock_session = MagicMock()

        with (
            patch("web_scrapers.db.queries.get_session", return_value=mock_session),
            patch(
                "web_scrapers.db.queries.EventRepository.query_events",
                return_value=[],
            ),
        ):
            from web_scrapers.db.queries import get_latest_events

            get_latest_events()

        mock_session.close.assert_called_once()


class TestGetEventsSince:
    def test_filters_by_hours(self) -> None:
        mock_session = MagicMock()
        mock_row = MagicMock()
        mock_row.event_id = "news:xyz"
        mock_row.source = "news"
        mock_row.event_type = "article"
        mock_row.payload = {"title": "Breaking News"}
        mock_row.scraped_at = datetime(2026, 3, 1, 10, 0, tzinfo=UTC)

        with (
            patch("web_scrapers.db.queries.get_session", return_value=mock_session),
            patch(
                "web_scrapers.db.queries.EventRepository.query_events",
                return_value=[mock_row],
            ) as mock_query,
        ):
            from web_scrapers.db.queries import get_events_since

            result = get_events_since(hours=24, source="news", limit=100)

        assert len(result) == 1
        assert result[0]["source"] == "news"
        # Verify query_events was called with since parameter
        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args.kwargs
        assert "since" in call_kwargs
        assert call_kwargs["source"] == "news"
        assert call_kwargs["limit"] == 100


class TestGetStats:
    def test_returns_stats_dict(self) -> None:
        mock_session = MagicMock()
        mock_run = MagicMock()
        mock_run.job_name = "reddit-financial"
        mock_run.scraper = "reddit"
        mock_run.status = MagicMock(value="completed")
        mock_run.started_at = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
        mock_run.events_total = 100
        mock_run.events_new = 25

        with (
            patch("web_scrapers.db.queries.get_session", return_value=mock_session),
            patch(
                "web_scrapers.db.queries.EventRepository.count_events",
                side_effect=[500, 300, 200, 50],  # total, reddit, news, last_24h
            ),
            patch(
                "web_scrapers.db.queries.RunRepository.get_recent_runs",
                return_value=[mock_run],
            ),
        ):
            from web_scrapers.db.queries import get_stats

            result = get_stats()

        assert result["total_events"] == 500
        assert result["reddit_events"] == 300
        assert result["news_events"] == 200
        assert result["events_last_24h"] == 50
        assert len(result["recent_runs"]) == 1
        assert result["recent_runs"][0]["job_name"] == "reddit-financial"


class TestGetSubredditSummary:
    def test_returns_summary_with_sentiment(self) -> None:
        mock_session = MagicMock()
        mock_row1 = MagicMock()
        mock_row1.payload = {"sentiment": {"compound": 0.5}, "score": 100}
        mock_row2 = MagicMock()
        mock_row2.payload = {"sentiment": {"compound": -0.2}, "score": 50}

        with (
            patch("web_scrapers.db.queries.get_session", return_value=mock_session),
            patch(
                "web_scrapers.db.queries.EventRepository.query_events",
                return_value=[mock_row1, mock_row2],
            ),
        ):
            from web_scrapers.db.queries import get_subreddit_summary

            result = get_subreddit_summary("wallstreetbets", hours=24)

        assert result["subreddit"] == "wallstreetbets"
        assert result["count"] == 2
        assert result["avg_sentiment"] == pytest.approx(0.15, abs=0.01)
        assert result["max_score"] == 100

    def test_returns_empty_summary_when_no_events(self) -> None:
        mock_session = MagicMock()

        with (
            patch("web_scrapers.db.queries.get_session", return_value=mock_session),
            patch(
                "web_scrapers.db.queries.EventRepository.query_events",
                return_value=[],
            ),
        ):
            from web_scrapers.db.queries import get_subreddit_summary

            result = get_subreddit_summary("emptysubreddit")

        assert result["subreddit"] == "emptysubreddit"
        assert result["count"] == 0
        assert result["avg_sentiment"] is None


class TestPublicAPIImports:
    """Test that the public API exports work correctly."""

    def test_imports_from_root_module(self) -> None:
        from web_scrapers import (
            BaseScraper,
            NewsArticle,
            NewsScraper,
            RedditComment,
            RedditPost,
            RedditScraper,
            SentimentScore,
            Settings,
            SignalEvent,
            __version__,
            get_settings,
            score_sentiment,
        )

        assert __version__ == "0.5.0"
        assert Settings is not None
        assert get_settings is not None
        assert score_sentiment is not None
        assert BaseScraper is not None
        assert RedditScraper is not None
        assert NewsScraper is not None
        assert SignalEvent is not None
        assert RedditPost is not None
        assert RedditComment is not None
        assert NewsArticle is not None
        assert SentimentScore is not None

    def test_get_settings_returns_default(self) -> None:
        from web_scrapers import get_settings, settings

        result = get_settings()
        assert result is settings

    def test_get_settings_with_overrides(self) -> None:
        from web_scrapers import get_settings

        result = get_settings(database_url="postgresql://test:test@localhost/test")
        assert result.database_url == "postgresql://test:test@localhost/test"


class TestDbModuleExports:
    """Test that db module exports query helpers."""

    def test_db_module_exports(self) -> None:
        from web_scrapers.db import (
            EventRepository,
            JobRepository,
            RunRepository,
            get_events_since,
            get_latest_events,
            get_stats,
            get_subreddit_summary,
        )

        assert EventRepository is not None
        assert JobRepository is not None
        assert RunRepository is not None
        assert get_events_since is not None
        assert get_latest_events is not None
        assert get_stats is not None
        assert get_subreddit_summary is not None
