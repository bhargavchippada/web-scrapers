# Version: v0.2.0
"""Tests for the News/RSS scraper (mocked HTTP — no network calls)."""

from __future__ import annotations

from time import struct_time
from unittest.mock import MagicMock, patch

import httpx

from web_scrapers.scrapers.news import (
    NewsScraper,
    _entry_id,
    _parse_entry,
    _parse_published,
)


class TestEntryId:
    def test_generates_deterministic_id(self) -> None:
        entry = MagicMock()
        entry.id = "https://example.com/article/1"
        entry.link = "https://example.com/article/1"
        id1 = _entry_id(entry, "Test Feed")
        id2 = _entry_id(entry, "Test Feed")
        assert id1 == id2
        assert len(id1) == 16

    def test_fallback_to_title(self) -> None:
        entry = MagicMock(spec=[])
        entry.id = ""
        entry.link = ""
        entry.title = "Some Title"
        # Need to handle getattr fallback
        id1 = _entry_id(entry, "Feed")
        assert len(id1) == 16


class TestParseEntry:
    def test_parses_feed_entry(self) -> None:
        entry = MagicMock()
        entry.id = "https://example.com/1"
        entry.title = "Markets rally"
        entry.summary = "Stocks surged"
        entry.link = "https://example.com/1"
        entry.author = "Jane"
        entry.published_parsed = None
        article = _parse_entry(entry, "Test Feed", "markets")
        assert article.title == "Markets rally"
        assert article.feed_name == "Test Feed"
        assert article.category == "markets"


class TestNewsScraper:
    def test_name(self) -> None:
        scraper = NewsScraper()
        assert scraper.name == "news"

    @patch("web_scrapers.scrapers.news.get_feed_targets")
    def test_scrape_empty_targets(self, mock_targets: MagicMock) -> None:
        mock_targets.return_value = []
        scraper = NewsScraper()
        events = scraper.scrape()
        assert events == []

    @patch("web_scrapers.scrapers.news.httpx.Client")
    @patch("web_scrapers.scrapers.news.get_feed_targets")
    def test_scrape_with_feed(
        self,
        mock_targets: MagicMock,
        mock_client_cls: MagicMock,
        sample_rss_xml: str,
    ) -> None:
        mock_targets.return_value = [
            {"name": "Test Feed", "url": "https://example.com/rss", "category": "markets"},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = sample_rss_xml
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        scraper = NewsScraper()
        events = scraper.scrape()

        assert len(events) == 2
        assert events[0].source == "news"
        assert events[0].event_type == "article"
        assert "Markets rally" in events[0].payload["title"]

    @patch("web_scrapers.scrapers.news.httpx.Client")
    @patch("web_scrapers.scrapers.news.get_feed_targets")
    def test_scrape_handles_http_error(
        self,
        mock_targets: MagicMock,
        mock_client_cls: MagicMock,
    ) -> None:
        mock_targets.return_value = [
            {"name": "Bad Feed", "url": "https://bad.example.com/rss", "category": "test"},
        ]
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client_cls.return_value = mock_client

        scraper = NewsScraper()
        events = scraper.scrape()
        assert events == []


class TestParsePublished:
    def test_valid_struct_time(self) -> None:
        st = struct_time((2026, 1, 15, 12, 0, 0, 2, 15, 0))
        entry = MagicMock()
        entry.published_parsed = st
        result = _parse_published(entry)
        assert result is not None
        assert result.year == 2026

    def test_none_published_parsed(self) -> None:
        entry = MagicMock()
        entry.published_parsed = None
        assert _parse_published(entry) is None

    def test_missing_attribute(self) -> None:
        entry = MagicMock(spec=[])
        assert _parse_published(entry) is None

    def test_non_struct_time_value(self) -> None:
        entry = MagicMock()
        entry.published_parsed = "not a struct time"
        assert _parse_published(entry) is None


class TestEntryIdEdgeCases:
    def test_different_feeds_different_ids(self) -> None:
        entry = MagicMock()
        entry.id = "https://example.com/1"
        id1 = _entry_id(entry, "Feed A")
        id2 = _entry_id(entry, "Feed B")
        # Same entry ID → same hash (feed name not used when id exists)
        assert id1 == id2

    def test_empty_id_and_link_uses_title(self) -> None:
        entry = MagicMock()
        entry.id = ""
        entry.link = ""
        entry.title = "Breaking News"
        id1 = _entry_id(entry, "Feed A")
        id2 = _entry_id(entry, "Feed B")
        # Different feed names → different hashes in fallback
        assert id1 != id2


class TestNewsScraperEdgeCases:
    @patch("web_scrapers.scrapers.news.httpx.Client")
    @patch("web_scrapers.scrapers.news.get_feed_targets")
    def test_scrape_empty_rss_feed(
        self,
        mock_targets: MagicMock,
        mock_client_cls: MagicMock,
    ) -> None:
        """Feed with no items returns empty events list."""
        mock_targets.return_value = [
            {"name": "Empty Feed", "url": "https://example.com/rss", "category": "test"},
        ]
        empty_rss = """<?xml version="1.0"?>
        <rss version="2.0"><channel><title>Empty</title></channel></rss>"""
        mock_resp = MagicMock()
        mock_resp.text = empty_rss
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        scraper = NewsScraper()
        events = scraper.scrape()
        assert events == []

    @patch("web_scrapers.scrapers.news.httpx.Client")
    @patch("web_scrapers.scrapers.news.get_feed_targets")
    def test_scrape_multiple_feeds(
        self,
        mock_targets: MagicMock,
        mock_client_cls: MagicMock,
        sample_rss_xml: str,
    ) -> None:
        """Multiple feeds are scraped sequentially."""
        mock_targets.return_value = [
            {"name": "Feed A", "url": "https://a.com/rss", "category": "a"},
            {"name": "Feed B", "url": "https://b.com/rss", "category": "b"},
        ]
        mock_resp = MagicMock()
        mock_resp.text = sample_rss_xml
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        scraper = NewsScraper()
        events = scraper.scrape()
        # 2 items per feed × 2 feeds
        assert len(events) == 4

    @patch("web_scrapers.scrapers.news.get_feed_targets")
    def test_health_check_no_targets(self, mock_targets: MagicMock) -> None:
        mock_targets.return_value = []
        scraper = NewsScraper()
        assert scraper.health_check() is False

    @patch("web_scrapers.scrapers.news.httpx.Client")
    @patch("web_scrapers.scrapers.news.get_feed_targets")
    def test_health_check_handles_request_error(
        self,
        mock_targets: MagicMock,
        mock_client_cls: MagicMock,
    ) -> None:
        mock_targets.return_value = [{"name": "Feed", "url": "https://example.com/rss"}]
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.ConnectError("DNS fail")
        mock_client_cls.return_value = mock_client

        scraper = NewsScraper()
        assert scraper.health_check() is False
