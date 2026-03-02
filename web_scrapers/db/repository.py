# Version: v0.2.0
"""Repository layer — all database operations go through here."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from web_scrapers.db.models import (
    RunStatus,
    ScrapeJobRow,
    ScrapeRunRow,
    SignalEventRow,
)
from web_scrapers.models.base import SignalEvent


class EventRepository:
    """CRUD operations for signal events."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def bulk_upsert(self, events: list[SignalEvent], run_id: int | None = None) -> int:
        """Insert or refresh events via ON CONFLICT DO UPDATE.

        Updates payload and scraped_at on conflict; preserves run_id and created_at
        from the first insert. Returns the count of rows affected (inserts + updates).
        """
        if not events:
            return 0

        values = [
            {
                "event_id": e.event_id,
                "source": e.source,
                "event_type": e.event_type,
                "payload": e.payload,
                "scraped_at": e.ingested_at,
                "run_id": run_id,
            }
            for e in events
        ]

        stmt = pg_insert(SignalEventRow).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["event_id"],
            set_={
                "payload": stmt.excluded.payload,
                "scraped_at": stmt.excluded.scraped_at,
            },
        )
        result = self._session.execute(stmt)
        self._session.commit()
        return result.rowcount

    def get_by_event_id(self, event_id: str) -> SignalEventRow | None:
        """Fetch a single event by its unique event_id."""
        stmt = select(SignalEventRow).where(SignalEventRow.event_id == event_id)
        return self._session.scalar(stmt)

    def query_events(
        self,
        source: str | None = None,
        event_type: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        subreddit: str | None = None,
        feed_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[SignalEventRow]:
        """Query events with optional filters, ordered by scraped_at descending."""
        stmt = select(SignalEventRow).order_by(SignalEventRow.scraped_at.desc())

        if source:
            stmt = stmt.where(SignalEventRow.source == source)
        if event_type:
            stmt = stmt.where(SignalEventRow.event_type == event_type)
        if since:
            stmt = stmt.where(SignalEventRow.scraped_at >= since)
        if until:
            stmt = stmt.where(SignalEventRow.scraped_at <= until)
        if subreddit:
            stmt = stmt.where(SignalEventRow.payload["subreddit"].astext == subreddit)
        if feed_name:
            stmt = stmt.where(SignalEventRow.payload["feed_name"].astext == feed_name)

        stmt = stmt.limit(limit).offset(offset)
        return self._session.scalars(stmt).all()

    def count_events(
        self,
        source: str | None = None,
        since: datetime | None = None,
    ) -> int:
        """Count events with optional filters."""
        stmt = select(func.count(SignalEventRow.id))
        if source:
            stmt = stmt.where(SignalEventRow.source == source)
        if since:
            stmt = stmt.where(SignalEventRow.scraped_at >= since)
        return self._session.scalar(stmt) or 0

    def get_new_event_ids(self, event_ids: list[str]) -> set[str]:
        """Return the subset of event_ids that do NOT exist in the database."""
        if not event_ids:
            return set()
        stmt = select(SignalEventRow.event_id).where(SignalEventRow.event_id.in_(event_ids))
        existing = set(self._session.scalars(stmt).all())
        return set(event_ids) - existing


class RunRepository:
    """CRUD for scrape runs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_run(
        self,
        job_name: str,
        scraper: str,
        job_id: int | None = None,
    ) -> ScrapeRunRow:
        """Create a new scrape run record with RUNNING status."""
        run = ScrapeRunRow(
            job_id=job_id,
            job_name=job_name,
            scraper=scraper,
            status=RunStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        self._session.add(run)
        self._session.commit()
        self._session.refresh(run)
        return run

    def complete_run(
        self,
        run: ScrapeRunRow,
        events_total: int,
        events_new: int,
        events_ingested: int = 0,
        error: str | None = None,
    ) -> None:
        """Mark a run as completed or failed."""
        run.status = RunStatus.FAILED if error else RunStatus.COMPLETED
        run.finished_at = datetime.now(UTC)
        run.events_total = events_total
        run.events_new = events_new
        run.events_ingested = events_ingested
        run.error = error
        self._session.commit()

    def get_recent_runs(
        self, limit: int = 20, scraper: str | None = None
    ) -> Sequence[ScrapeRunRow]:
        """Fetch recent scrape runs, optionally filtered by scraper."""
        stmt = select(ScrapeRunRow).order_by(ScrapeRunRow.started_at.desc())
        if scraper:
            stmt = stmt.where(ScrapeRunRow.scraper == scraper)
        stmt = stmt.limit(limit)
        return self._session.scalars(stmt).all()

    def get_last_run(self, scraper: str) -> ScrapeRunRow | None:
        """Get the most recent run for a scraper."""
        stmt = (
            select(ScrapeRunRow)
            .where(ScrapeRunRow.scraper == scraper)
            .order_by(ScrapeRunRow.started_at.desc())
            .limit(1)
        )
        return self._session.scalar(stmt)


class JobRepository:
    """CRUD for scrape job definitions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self) -> Sequence[ScrapeJobRow]:
        """Fetch all jobs."""
        stmt = select(ScrapeJobRow).order_by(ScrapeJobRow.name)
        return self._session.scalars(stmt).all()

    def get_all_enabled(self) -> Sequence[ScrapeJobRow]:
        """Fetch all enabled jobs."""
        stmt = select(ScrapeJobRow).where(ScrapeJobRow.enabled.is_(True))
        return self._session.scalars(stmt).all()

    def get_by_name(self, name: str) -> ScrapeJobRow | None:
        """Fetch a job by its unique name."""
        stmt = select(ScrapeJobRow).where(ScrapeJobRow.name == name)
        return self._session.scalar(stmt)

    def upsert_job(
        self,
        name: str,
        scraper: str,
        schedule: str | None = None,
        config: dict[str, Any] | None = None,
        enabled: bool = True,
    ) -> ScrapeJobRow:
        """Create or update a job definition."""
        existing = self.get_by_name(name)
        if existing:
            existing.scraper = scraper
            existing.schedule = schedule
            existing.config = config or {}
            existing.enabled = enabled
            existing.updated_at = datetime.now(UTC)
        else:
            existing = ScrapeJobRow(
                name=name,
                scraper=scraper,
                schedule=schedule,
                config=config or {},
                enabled=enabled,
            )
            self._session.add(existing)
        self._session.commit()
        self._session.refresh(existing)
        return existing

    def set_enabled(self, name: str, *, enabled: bool) -> bool:
        """Enable or disable a job by name. Returns True if found."""
        job = self.get_by_name(name)
        if not job:
            return False
        job.enabled = enabled
        job.updated_at = datetime.now(UTC)
        self._session.commit()
        return True
