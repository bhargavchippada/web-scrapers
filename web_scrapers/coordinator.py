# Version: v0.2.0
"""Coordinator — orchestrates scrapers, persistence, and optional RAG ingestion."""

from __future__ import annotations

from loguru import logger

from web_scrapers.models.base import SignalEvent
from web_scrapers.scrapers.base import BaseScraper
from web_scrapers.scrapers.news import NewsScraper
from web_scrapers.scrapers.reddit import RedditScraper


def get_all_scrapers() -> list[BaseScraper]:
    """Return all available scraper instances."""
    return [RedditScraper(), NewsScraper()]


def run_scraper(scraper: BaseScraper) -> list[SignalEvent]:
    """Run a single scraper with error isolation."""
    try:
        logger.info("Running {} scraper...", scraper.name)
        events = scraper.scrape()
        logger.info("{} scraper returned {} events", scraper.name, len(events))
        return events
    except Exception:
        logger.exception("{} scraper failed", scraper.name)
        return []


def persist_events(events: list[SignalEvent], run_id: int | None = None) -> int:
    """Persist events to the database, returning count of newly inserted (non-duplicate)."""
    if not events:
        return 0
    from web_scrapers.db.engine import get_session
    from web_scrapers.db.repository import EventRepository

    session = get_session()
    try:
        repo = EventRepository(session)
        new_count = repo.bulk_upsert(events, run_id=run_id)
        logger.info("Persisted {}/{} new events (rest were duplicates)", new_count, len(events))
        return new_count
    finally:
        session.close()


def run_all(*, persist: bool = True) -> list[SignalEvent]:
    """Run all configured scrapers and return combined events."""
    all_events: list[SignalEvent] = []
    for scraper in get_all_scrapers():
        all_events.extend(run_scraper(scraper))
    logger.info("Total events collected: {}", len(all_events))

    if persist and all_events:
        persist_events(all_events)

    return all_events


def run_single(scraper_name: str, *, persist: bool = True) -> list[SignalEvent]:
    """Run a single scraper by name."""
    scrapers = {s.name: s for s in get_all_scrapers()}
    if scraper_name not in scrapers:
        logger.error("Unknown scraper: {}. Available: {}", scraper_name, list(scrapers.keys()))
        return []
    events = run_scraper(scrapers[scraper_name])

    if persist and events:
        persist_events(events)

    return events


def run_tracked(
    scraper_name: str,
    job_id: int | None = None,
    job_name: str | None = None,
    ingest: bool = False,
) -> tuple[int, int, int]:
    """Full tracked run: scrape -> persist -> (optional) ingest.

    Returns (events_total, events_new, events_ingested).
    """
    from web_scrapers.db.engine import get_session
    from web_scrapers.db.repository import EventRepository, RunRepository

    session = get_session()
    try:
        run_repo = RunRepository(session)
        event_repo = EventRepository(session)

        run = run_repo.create_run(
            job_name=job_name or scraper_name,
            scraper=scraper_name,
            job_id=job_id,
        )

        try:
            events = run_single(scraper_name, persist=False)

            # Detect new events in a single query BEFORE upserting
            all_ids = [e.event_id for e in events]
            new_ids = event_repo.get_new_event_ids(all_ids) if all_ids else set()

            new_count = event_repo.bulk_upsert(events, run_id=run.id)

            ingested = 0
            if ingest and new_count > 0:
                import asyncio

                from web_scrapers.bridge.nexus import ingest_events

                new_events = [e for e in events if e.event_id in new_ids]
                if new_events:
                    ingested = asyncio.run(ingest_events(new_events))

            run_repo.complete_run(run, len(events), new_count, ingested)
            return len(events), new_count, ingested

        except Exception as exc:
            run_repo.complete_run(run, 0, 0, error=str(exc))
            raise
    finally:
        session.close()


async def run_all_with_ingest() -> tuple[int, int]:
    """Run all scrapers and ingest results into Nexus RAG. Returns (total, ingested)."""
    from web_scrapers.bridge.nexus import ingest_events

    events = run_all(persist=True)
    if not events:
        return 0, 0
    ingested = await ingest_events(events)
    return len(events), ingested
