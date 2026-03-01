# Version: v0.1.0
"""Tests for the scraper coordinator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from web_scrapers.coordinator import get_all_scrapers, run_all, run_scraper, run_single
from web_scrapers.models.base import SignalEvent


class TestCoordinator:
    def test_get_all_scrapers(self) -> None:
        scrapers = get_all_scrapers()
        names = [s.name for s in scrapers]
        assert "reddit" in names
        assert "news" in names

    def test_run_scraper_catches_errors(self) -> None:
        mock_scraper = MagicMock()
        mock_scraper.name = "broken"
        mock_scraper.scrape.side_effect = Exception("boom")
        events = run_scraper(mock_scraper)
        assert events == []

    def test_run_scraper_returns_events(self) -> None:
        mock_scraper = MagicMock()
        mock_scraper.name = "test"
        mock_event = SignalEvent(
            source="test", event_type="test", payload={}, event_id="t:1"
        )
        mock_scraper.scrape.return_value = [mock_event]
        events = run_scraper(mock_scraper)
        assert len(events) == 1

    @patch("web_scrapers.coordinator.get_all_scrapers")
    def test_run_all(self, mock_get: MagicMock) -> None:
        mock_scraper = MagicMock()
        mock_scraper.name = "mock"
        mock_event = SignalEvent(
            source="mock", event_type="test", payload={}, event_id="m:1"
        )
        mock_scraper.scrape.return_value = [mock_event]
        mock_get.return_value = [mock_scraper]

        events = run_all()
        assert len(events) == 1

    @patch("web_scrapers.coordinator.get_all_scrapers")
    def test_run_single_unknown(self, mock_get: MagicMock) -> None:
        mock_scraper = MagicMock()
        mock_scraper.name = "reddit"
        mock_get.return_value = [mock_scraper]

        events = run_single("nonexistent")
        assert events == []

    @patch("web_scrapers.coordinator.get_all_scrapers")
    def test_run_single_known(self, mock_get: MagicMock) -> None:
        mock_scraper = MagicMock()
        mock_scraper.name = "reddit"
        mock_event = SignalEvent(
            source="reddit", event_type="post", payload={}, event_id="r:1"
        )
        mock_scraper.scrape.return_value = [mock_event]
        mock_get.return_value = [mock_scraper]

        events = run_single("reddit")
        assert len(events) == 1
