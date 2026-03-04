# Version: v0.1.0
"""Web content models — structured output from universal web scraping."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class ScrapedContent(BaseModel):
    """Structured content extracted from any web page.

    Uses trafilatura for intelligent text extraction with metadata.
    """

    url: str
    title: str | None = None
    author: str | None = None
    date: datetime | None = None
    text: str
    description: str | None = None
    sitename: str | None = None
    categories: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    comments: str | None = None
    license: str | None = None
    raw_html: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def word_count(self) -> int:
        """Return approximate word count of extracted text."""
        return len(self.text.split()) if self.text else 0

    @property
    def has_metadata(self) -> bool:
        """Return True if metadata was extracted."""
        return bool(self.title or self.author or self.date)


class ScrapeResult(BaseModel):
    """Result of a scrape operation with status information."""

    success: bool
    url: str
    content: ScrapedContent | None = None
    error: str | None = None
    duration_ms: float = 0.0
