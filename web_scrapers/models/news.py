# Version: v0.1.0
"""News article model for RSS/Atom feed items."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    """A single news article parsed from an RSS/Atom feed."""

    id: str
    feed_name: str
    title: str
    summary: str = ""
    link: str
    author: str | None = None
    published: datetime | None = None
    category: str = ""
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
