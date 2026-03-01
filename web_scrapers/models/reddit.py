# Version: v0.1.0
"""Reddit post models with sentiment scoring."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class SentimentScore(BaseModel):
    """VADER sentiment analysis result."""

    positive: float = Field(ge=0.0, le=1.0)
    negative: float = Field(ge=0.0, le=1.0)
    neutral: float = Field(ge=0.0, le=1.0)
    compound: float = Field(ge=-1.0, le=1.0)


class RedditPost(BaseModel):
    """A single Reddit post with metadata and sentiment."""

    id: str
    subreddit: str
    title: str
    selftext: str = ""
    author: str | None = None
    score: int = 0
    upvote_ratio: float = Field(ge=0.0, le=1.0, default=0.0)
    num_comments: int = 0
    created_utc: datetime
    url: str
    flair: str | None = None
    sentiment: SentimentScore
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("author", mode="before")
    @classmethod
    def coerce_deleted_author(cls, v: object) -> str | None:
        if v is None or str(v) == "[deleted]":
            return None
        return str(v)
