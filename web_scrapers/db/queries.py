# Version: v0.2.0
"""High-level query helpers for common event queries."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from web_scrapers.db.engine import get_session
from web_scrapers.db.repository import EventRepository, RunRepository


def get_latest_events(source: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Get the most recent events, optionally filtered by source."""
    session = get_session()
    try:
        repo = EventRepository(session)
        rows = repo.query_events(source=source, limit=limit)
        return [
            {
                "event_id": r.event_id,
                "source": r.source,
                "event_type": r.event_type,
                "payload": r.payload,
                "scraped_at": r.scraped_at.isoformat(),
            }
            for r in rows
        ]
    finally:
        session.close()


def get_events_since(
    hours: int = 24, source: str | None = None, limit: int = 10000
) -> list[dict[str, Any]]:
    """Get events from the last N hours."""
    since = datetime.now(UTC) - timedelta(hours=hours)
    session = get_session()
    try:
        repo = EventRepository(session)
        rows = repo.query_events(source=source, since=since, limit=limit)
        return [
            {
                "event_id": r.event_id,
                "source": r.source,
                "event_type": r.event_type,
                "payload": r.payload,
                "scraped_at": r.scraped_at.isoformat(),
            }
            for r in rows
        ]
    finally:
        session.close()


def get_stats() -> dict[str, Any]:
    """Get database statistics — event counts by source and recent runs."""
    session = get_session()
    try:
        event_repo = EventRepository(session)
        run_repo = RunRepository(session)

        last_24h = datetime.now(UTC) - timedelta(hours=24)
        return {
            "total_events": event_repo.count_events(),
            "reddit_events": event_repo.count_events(source="reddit"),
            "news_events": event_repo.count_events(source="news"),
            "events_last_24h": event_repo.count_events(since=last_24h),
            "recent_runs": [
                {
                    "job_name": r.job_name,
                    "scraper": r.scraper,
                    "status": r.status.value,
                    "started_at": r.started_at.isoformat(),
                    "events_total": r.events_total,
                    "events_new": r.events_new,
                }
                for r in run_repo.get_recent_runs(limit=5)
            ],
        }
    finally:
        session.close()


def get_subreddit_summary(subreddit: str, hours: int = 24) -> dict[str, Any]:
    """Get aggregated stats for a specific subreddit."""
    since = datetime.now(UTC) - timedelta(hours=hours)
    session = get_session()
    try:
        repo = EventRepository(session)
        rows = repo.query_events(source="reddit", subreddit=subreddit, since=since, limit=10000)
        if not rows:
            return {"subreddit": subreddit, "count": 0, "avg_sentiment": None}

        sentiments = [
            r.payload.get("sentiment", {}).get("compound", 0.0) for r in rows
        ]
        return {
            "subreddit": subreddit,
            "count": len(rows),
            "avg_sentiment": round(sum(sentiments) / len(sentiments), 4),
            "max_score": max(r.payload.get("score", 0) for r in rows),
        }
    finally:
        session.close()
