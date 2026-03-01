# Version: v0.1.0
"""Base models for all scraped data — SignalEvent envelope wraps all payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class SignalEvent(BaseModel):
    """Universal event envelope wrapping any scraped payload."""

    source: str
    event_type: str
    payload: dict[str, Any]
    event_id: str
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
