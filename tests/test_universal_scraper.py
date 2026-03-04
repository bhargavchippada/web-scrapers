# Version: v0.1.0
"""Tests for the universal web scraper."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from web_scrapers.scrapers.universal import (
    UniversalScraper,
    _generate_event_id,
    _parse_categories,
    _parse_date,
    _parse_tags,
    scrape_url,
    scrape_urls,
)


class TestHelperFunctions:
    """Tests for module-level helper functions."""

    def test_generate_event_id_stable(self) -> None:
        """Event IDs should be stable for the same URL."""
        url = "https://example.com/article/123"
        id1 = _generate_event_id(url)
        id2 = _generate_event_id(url)
        assert id1 == id2
        assert len(id1) == 16  # Truncated to 16 chars

    def test_generate_event_id_different_urls(self) -> None:
        """Different URLs should produce different IDs."""
        id1 = _generate_event_id("https://example.com/a")
        id2 = _generate_event_id("https://example.com/b")
        assert id1 != id2

    def test_parse_date_valid(self) -> None:
        """Valid date string should be parsed."""
        result = _parse_date("2026-01-15")
        assert result == datetime(2026, 1, 15, tzinfo=UTC)

    def test_parse_date_none(self) -> None:
        """None input should return None."""
        assert _parse_date(None) is None

    def test_parse_date_invalid(self) -> None:
        """Invalid date string should return None."""
        assert _parse_date("not-a-date") is None

    def test_parse_tags_valid(self) -> None:
        """Comma-separated tags should be split."""
        result = _parse_tags("finance, stocks, investing")
        assert result == ["finance", "stocks", "investing"]

    def test_parse_tags_none(self) -> None:
        """None input should return empty list."""
        assert _parse_tags(None) == []

    def test_parse_tags_empty(self) -> None:
        """Empty string should return empty list."""
        assert _parse_tags("") == []

    def test_parse_categories_valid(self) -> None:
        """Comma-separated categories should be split."""
        result = _parse_categories("business, markets")
        assert result == ["business", "markets"]

    def test_parse_categories_none(self) -> None:
        """None input should return empty list."""
        assert _parse_categories(None) == []


class TestUniversalScraper:
    """Tests for UniversalScraper class."""

    def test_name_property(self) -> None:
        """Scraper name should be 'universal'."""
        scraper = UniversalScraper()
        assert scraper.name == "universal"

    def test_init_defaults(self) -> None:
        """Default initialization values."""
        scraper = UniversalScraper()
        assert scraper.urls == []
        assert scraper.include_comments is False
        assert scraper.include_tables is True
        assert scraper.output_format == "text"

    def test_init_with_urls(self) -> None:
        """Initialize with URLs list."""
        urls = ["https://example.com/a", "https://example.com/b"]
        scraper = UniversalScraper(urls=urls)
        assert scraper.urls == urls

    @patch("web_scrapers.scrapers.universal.trafilatura")
    def test_extract_success(self, mock_trafilatura: MagicMock) -> None:
        """Successful extraction returns ScrapeResult with content."""
        mock_trafilatura.fetch_url.return_value = "<html>test</html>"
        mock_trafilatura.extract.return_value = "Article content here"

        mock_metadata = MagicMock()
        mock_metadata.title = "Test Article"
        mock_metadata.author = "Test Author"
        mock_metadata.date = "2026-01-15"
        mock_metadata.description = "Test description"
        mock_metadata.sitename = "Example"
        mock_metadata.categories = "business"
        mock_metadata.tags = "finance, stocks"
        mock_metadata.license = "CC-BY"
        mock_metadata.url = "https://example.com/article"
        mock_metadata.hostname = "example.com"
        mock_metadata.pagetype = "article"
        mock_trafilatura.extract_metadata.return_value = mock_metadata

        scraper = UniversalScraper()
        result = scraper.extract("https://example.com/article")

        assert result.success is True
        assert result.content is not None
        assert result.content.title == "Test Article"
        assert result.content.text == "Article content here"
        assert result.error is None

    @patch("web_scrapers.scrapers.universal.trafilatura")
    def test_extract_fetch_failure(self, mock_trafilatura: MagicMock) -> None:
        """Failed fetch returns ScrapeResult with error."""
        mock_trafilatura.fetch_url.return_value = None

        scraper = UniversalScraper()
        result = scraper.extract("https://example.com/notfound")

        assert result.success is False
        assert result.content is None
        assert "Failed to fetch" in result.error

    @patch("web_scrapers.scrapers.universal.trafilatura")
    def test_extract_no_content(self, mock_trafilatura: MagicMock) -> None:
        """No content extracted returns ScrapeResult with error."""
        mock_trafilatura.fetch_url.return_value = "<html>empty</html>"
        mock_trafilatura.extract.return_value = None

        scraper = UniversalScraper()
        result = scraper.extract("https://example.com/empty")

        assert result.success is False
        assert "No content extracted" in result.error

    @patch("web_scrapers.scrapers.universal.trafilatura")
    def test_extract_with_raw_html(self, mock_trafilatura: MagicMock) -> None:
        """Extract from pre-fetched HTML."""
        mock_trafilatura.extract.return_value = "Article content"
        mock_trafilatura.extract_metadata.return_value = None

        scraper = UniversalScraper()
        result = scraper.extract("https://example.com", raw_html="<html>test</html>")

        assert result.success is True
        mock_trafilatura.fetch_url.assert_not_called()

    def test_scrape_no_urls(self) -> None:
        """Scrape with no URLs returns empty list."""
        scraper = UniversalScraper()
        events = scraper.scrape()
        assert events == []

    @patch("web_scrapers.scrapers.universal.trafilatura")
    def test_scrape_with_urls(self, mock_trafilatura: MagicMock) -> None:
        """Scrape multiple URLs returns SignalEvents."""
        mock_trafilatura.fetch_url.return_value = "<html>test</html>"
        mock_trafilatura.extract.return_value = "Content"
        mock_trafilatura.extract_metadata.return_value = None

        scraper = UniversalScraper(urls=["https://a.com", "https://b.com"])
        events = scraper.scrape()

        assert len(events) == 2
        assert all(e.source == "web" for e in events)
        assert all(e.event_type == "article" for e in events)

    @patch("web_scrapers.scrapers.universal.trafilatura")
    def test_health_check_success(self, mock_trafilatura: MagicMock) -> None:
        """Health check passes when extraction succeeds."""
        mock_trafilatura.fetch_url.return_value = "<html>test</html>"
        mock_trafilatura.extract.return_value = "Content"
        mock_trafilatura.extract_metadata.return_value = None

        scraper = UniversalScraper()
        assert scraper.health_check() is True

    @patch("web_scrapers.scrapers.universal.trafilatura")
    def test_health_check_failure(self, mock_trafilatura: MagicMock) -> None:
        """Health check fails when extraction fails."""
        mock_trafilatura.fetch_url.return_value = None

        scraper = UniversalScraper()
        assert scraper.health_check() is False


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    @patch("web_scrapers.scrapers.universal.trafilatura")
    def test_scrape_url(self, mock_trafilatura: MagicMock) -> None:
        """scrape_url convenience function works."""
        mock_trafilatura.fetch_url.return_value = "<html>test</html>"
        mock_trafilatura.extract.return_value = "Content"
        mock_trafilatura.extract_metadata.return_value = None

        result = scrape_url("https://example.com")
        assert result.success is True

    @patch("web_scrapers.scrapers.universal.trafilatura")
    def test_scrape_urls(self, mock_trafilatura: MagicMock) -> None:
        """scrape_urls convenience function works."""
        mock_trafilatura.fetch_url.return_value = "<html>test</html>"
        mock_trafilatura.extract.return_value = "Content"
        mock_trafilatura.extract_metadata.return_value = None

        results = scrape_urls(["https://a.com", "https://b.com"])
        assert len(results) == 2
        assert all(r.success for r in results)


class TestPublicAPIImport:
    """Tests for public API imports from root module."""

    def test_import_universal_scraper(self) -> None:
        """UniversalScraper should be importable from root."""
        from web_scrapers import UniversalScraper

        assert UniversalScraper is not None

    def test_import_scrape_url(self) -> None:
        """scrape_url should be importable from root."""
        from web_scrapers import scrape_url

        assert callable(scrape_url)

    def test_import_scrape_urls(self) -> None:
        """scrape_urls should be importable from root."""
        from web_scrapers import scrape_urls

        assert callable(scrape_urls)
