# Version: v0.3.1
"""Bridge for ingesting scraped signal events into Nexus RAG (Memgraph + pgvector)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from loguru import logger

from web_scrapers.models.base import SignalEvent

# Add mcp-nexus-rag to path for direct import
_NEXUS_PATH = Path(__file__).resolve().parents[3] / "mcp-nexus-rag"

PROJECT_ID = "WEB_SCRAPERS"
SCOPE = "WEB_RESEARCH"


def _ensure_nexus_importable() -> bool:
    """Add mcp-nexus-rag to sys.path if available."""
    if not _NEXUS_PATH.exists():
        logger.warning("mcp-nexus-rag not found at {}", _NEXUS_PATH)
        return False
    nexus_str = str(_NEXUS_PATH)
    if nexus_str not in sys.path:
        sys.path.insert(0, nexus_str)
    return True


async def ingest_events(events: list[SignalEvent]) -> int:
    """Ingest signal events into Nexus RAG using unified ingest_document.

    Uses `ingest_document` which ingests to both graph (Memgraph) and vector (pgvector)
    backends in a single call. This is the preferred approach per CLAUDE.md.

    Returns count of successfully ingested events.
    """
    if not _ensure_nexus_importable():
        logger.error("Cannot ingest — mcp-nexus-rag not available")
        return 0

    try:
        from nexus.tools import ingest_document
    except ImportError:
        logger.exception("Cannot ingest — failed to import nexus.tools.ingest_document")
        return 0

    ingested = 0
    for event in events:
        text = json.dumps(event.model_dump(mode="json"), indent=2)
        source_id = event.event_id

        try:
            await ingest_document(
                text=text,
                project_id=PROJECT_ID,
                scope=SCOPE,
                source_identifier=source_id,
            )
            ingested += 1
        except Exception:
            logger.exception("Failed to ingest event {}", event.event_id)

    logger.info("Ingested {}/{} events into Nexus RAG", ingested, len(events))
    return ingested
