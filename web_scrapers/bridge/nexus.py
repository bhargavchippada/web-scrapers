# Version: v0.1.0
"""Bridge for ingesting scraped signal events into Nexus RAG (Neo4j + Qdrant)."""

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
    """Ingest signal events into Nexus RAG. Returns count of successfully ingested events."""
    if not _ensure_nexus_importable():
        logger.error("Cannot ingest — mcp-nexus-rag not available")
        return 0

    from nexus.tools import ingest_graph_document, ingest_vector_document

    ingested = 0
    for event in events:
        text = json.dumps(event.model_dump(mode="json"), indent=2)
        source_id = f"{event.source}:{event.event_id}"

        try:
            await ingest_graph_document(
                text=text,
                project_id=PROJECT_ID,
                scope=SCOPE,
                source_identifier=source_id,
            )
            await ingest_vector_document(
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
