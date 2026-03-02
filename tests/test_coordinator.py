# Version: v0.2.0
"""Tests for the scraper coordinator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from web_scrapers.coordinator import (
    get_all_scrapers,
    run_all,
    run_scraper,
    run_single,
    run_tracked,
)
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
        mock_event = SignalEvent(source="test", event_type="test", payload={}, event_id="t:1")
        mock_scraper.scrape.return_value = [mock_event]
        events = run_scraper(mock_scraper)
        assert len(events) == 1

    @patch("web_scrapers.coordinator.persist_events", return_value=1)
    @patch("web_scrapers.coordinator.get_all_scrapers")
    def test_run_all(self, mock_get: MagicMock, mock_persist: MagicMock) -> None:
        mock_scraper = MagicMock()
        mock_scraper.name = "mock"
        mock_event = SignalEvent(source="mock", event_type="test", payload={}, event_id="m:1")
        mock_scraper.scrape.return_value = [mock_event]
        mock_get.return_value = [mock_scraper]

        events = run_all()
        assert len(events) == 1
        mock_persist.assert_called_once()

    @patch("web_scrapers.coordinator.persist_events", return_value=0)
    @patch("web_scrapers.coordinator.get_all_scrapers")
    def test_run_all_no_persist(self, mock_get: MagicMock, mock_persist: MagicMock) -> None:
        mock_scraper = MagicMock()
        mock_scraper.name = "mock"
        mock_event = SignalEvent(source="mock", event_type="test", payload={}, event_id="m:1")
        mock_scraper.scrape.return_value = [mock_event]
        mock_get.return_value = [mock_scraper]

        events = run_all(persist=False)
        assert len(events) == 1
        mock_persist.assert_not_called()

    @patch("web_scrapers.coordinator.persist_events", return_value=0)
    @patch("web_scrapers.coordinator.get_all_scrapers")
    def test_run_single_unknown(self, mock_get: MagicMock, mock_persist: MagicMock) -> None:
        mock_scraper = MagicMock()
        mock_scraper.name = "reddit"
        mock_get.return_value = [mock_scraper]

        events = run_single("nonexistent")
        assert events == []

    @patch("web_scrapers.coordinator.persist_events", return_value=1)
    @patch("web_scrapers.coordinator.get_all_scrapers")
    def test_run_single_known(self, mock_get: MagicMock, mock_persist: MagicMock) -> None:
        mock_scraper = MagicMock()
        mock_scraper.name = "reddit"
        mock_event = SignalEvent(source="reddit", event_type="post", payload={}, event_id="r:1")
        mock_scraper.scrape.return_value = [mock_event]
        mock_get.return_value = [mock_scraper]

        events = run_single("reddit")
        assert len(events) == 1
        mock_persist.assert_called_once()


class TestRunTracked:
    @patch("web_scrapers.coordinator.run_single")
    @patch("web_scrapers.db.repository.RunRepository")
    @patch("web_scrapers.db.repository.EventRepository")
    @patch("web_scrapers.db.engine.get_session")
    def test_run_tracked_success(
        self,
        mock_get_session: MagicMock,
        mock_event_cls: MagicMock,
        mock_run_cls: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        mock_event = SignalEvent(source="reddit", event_type="post", payload={}, event_id="r:1")
        mock_run.return_value = [mock_event]
        mock_get_session.return_value = MagicMock()

        mock_run_repo = mock_run_cls.return_value
        mock_event_repo = mock_event_cls.return_value
        mock_run_obj = MagicMock()
        mock_run_obj.id = 42
        mock_run_repo.create_run.return_value = mock_run_obj
        mock_event_repo.get_new_event_ids.return_value = {"r:1"}
        mock_event_repo.bulk_upsert.return_value = 1

        total, new, ingested = run_tracked("reddit", job_name="test-job")

        assert total == 1
        assert new == 1
        assert ingested == 0
        mock_run_repo.complete_run.assert_called_once_with(mock_run_obj, 1, 1, 0)

    @patch("web_scrapers.coordinator.run_single")
    @patch("web_scrapers.db.repository.RunRepository")
    @patch("web_scrapers.db.repository.EventRepository")
    @patch("web_scrapers.db.engine.get_session")
    def test_run_tracked_failure(
        self,
        mock_get_session: MagicMock,
        mock_event_cls: MagicMock,
        mock_run_cls: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        mock_run.side_effect = RuntimeError("scrape failed")
        mock_get_session.return_value = MagicMock()

        mock_run_repo = mock_run_cls.return_value
        mock_run_obj = MagicMock()
        mock_run_obj.id = 99
        mock_run_repo.create_run.return_value = mock_run_obj

        with pytest.raises(RuntimeError, match="scrape failed"):
            run_tracked("reddit")

        mock_run_repo.complete_run.assert_called_once()
        call_args = mock_run_repo.complete_run.call_args
        assert "scrape failed" in str(call_args)

    @patch("web_scrapers.coordinator.run_single")
    @patch("web_scrapers.db.repository.RunRepository")
    @patch("web_scrapers.db.repository.EventRepository")
    @patch("web_scrapers.db.engine.get_session")
    def test_run_tracked_dedup(
        self,
        mock_get_session: MagicMock,
        mock_event_cls: MagicMock,
        mock_run_cls: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        """When all events are duplicates, new_count=0 and no ingestion."""
        mock_event = SignalEvent(source="reddit", event_type="post", payload={}, event_id="r:dup")
        mock_run.return_value = [mock_event]
        mock_get_session.return_value = MagicMock()

        mock_run_repo = mock_run_cls.return_value
        mock_event_repo = mock_event_cls.return_value
        mock_run_obj = MagicMock()
        mock_run_obj.id = 1
        mock_run_repo.create_run.return_value = mock_run_obj
        mock_event_repo.get_new_event_ids.return_value = set()
        mock_event_repo.bulk_upsert.return_value = 0

        total, new, ingested = run_tracked("reddit", ingest=True)

        assert total == 1
        assert new == 0
        assert ingested == 0
