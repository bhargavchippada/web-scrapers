# Version: v0.4.0
"""Database layer — persistent storage for scraped events, runs, and jobs."""

from web_scrapers.db.engine import get_session
from web_scrapers.db.models import Base, ScrapeJobRow, ScrapeRunRow, SignalEventRow
from web_scrapers.db.queries import (
    get_events_since,
    get_latest_events,
    get_stats,
    get_subreddit_summary,
)
from web_scrapers.db.repository import EventRepository, JobRepository, RunRepository

__all__ = [
    # ORM models
    "Base",
    "ScrapeJobRow",
    "ScrapeRunRow",
    "SignalEventRow",
    # Session factory
    "get_session",
    # Repositories
    "EventRepository",
    "JobRepository",
    "RunRepository",
    # Query helpers
    "get_events_since",
    "get_latest_events",
    "get_stats",
    "get_subreddit_summary",
]
