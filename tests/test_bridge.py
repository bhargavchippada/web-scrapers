# Version: v0.2.0
"""Tests for the Nexus RAG ingestion bridge."""

from __future__ import annotations

import asyncio
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

from web_scrapers.bridge.nexus import PROJECT_ID, SCOPE, ingest_events
from web_scrapers.models.base import SignalEvent


def _make_event(event_id: str = "test:1") -> SignalEvent:
    return SignalEvent(
        source="test", event_type="test", payload={"key": "value"}, event_id=event_id
    )


class TestIngestEvents:
    @patch("web_scrapers.bridge.nexus._ensure_nexus_importable", return_value=False)
    def test_returns_zero_when_nexus_unavailable(self, mock_ensure: MagicMock) -> None:
        result = asyncio.run(ingest_events([_make_event()]))
        assert result == 0

    @patch("web_scrapers.bridge.nexus._ensure_nexus_importable", return_value=True)
    def test_ingest_calls_nexus_tools(self, _mock_ensure: MagicMock) -> None:
        mock_ingest = AsyncMock(return_value={"status": "ok"})
        nexus_mod = ModuleType("nexus")
        tools_mod = ModuleType("nexus.tools")
        tools_mod.ingest_document = mock_ingest

        with patch.dict(
            sys.modules,
            {
                "nexus": nexus_mod,
                "nexus.tools": tools_mod,
            },
        ):
            events = [_make_event("a"), _make_event("b")]
            result = asyncio.run(ingest_events(events))

        assert result == 2
        assert mock_ingest.await_count == 2
        assert mock_ingest.await_args_list[0].kwargs["project_id"] == PROJECT_ID
        assert mock_ingest.await_args_list[0].kwargs["scope"] == SCOPE
        assert mock_ingest.await_args_list[0].kwargs["source_identifier"] == "a"
        assert mock_ingest.await_args_list[1].kwargs["source_identifier"] == "b"

    @patch("web_scrapers.bridge.nexus._ensure_nexus_importable", return_value=True)
    def test_returns_zero_when_nexus_import_fails(self, _mock_ensure: MagicMock) -> None:
        nexus_mod = ModuleType("nexus")
        with patch.dict(sys.modules, {"nexus": nexus_mod}, clear=False):
            sys.modules.pop("nexus.tools", None)
            result = asyncio.run(ingest_events([_make_event()]))

        assert result == 0

    def test_project_id_and_scope(self) -> None:
        assert PROJECT_ID == "WEB_SCRAPERS"
        assert SCOPE == "WEB_RESEARCH"
