# Version: v0.1.0
"""Tests for the News/RSS scraper (mocked HTTP — no network calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from web_scrapers.scrapers.news import NewsScraper, _entry_id, _parse_entry


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
        mock_client.get.side_effect = Exception("Connection refused")
        mock_client_cls.return_value = mock_client

        scraper = NewsScraper()
        events = scraper.scrape()
        assert events == []
