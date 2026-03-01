# Version: v0.2.0
"""Database layer — persistent storage for scraped events, runs, and jobs."""

from web_scrapers.db.engine import get_session
from web_scrapers.db.models import Base, ScrapeJobRow, ScrapeRunRow, SignalEventRow

__all__ = [
    "Base",
    "ScrapeJobRow",
    "ScrapeRunRow",
    "SignalEventRow",
    "get_session",
]
