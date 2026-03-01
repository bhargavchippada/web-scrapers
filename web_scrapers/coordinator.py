# Version: v0.1.0
"""Coordinator — orchestrates all scrapers and optional RAG ingestion."""

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


def run_all() -> list[SignalEvent]:
    """Run all configured scrapers and return combined events."""
    all_events: list[SignalEvent] = []
    for scraper in get_all_scrapers():
        all_events.extend(run_scraper(scraper))
    logger.info("Total events collected: {}", len(all_events))
    return all_events


def run_single(scraper_name: str) -> list[SignalEvent]:
    """Run a single scraper by name."""
    scrapers = {s.name: s for s in get_all_scrapers()}
    if scraper_name not in scrapers:
        logger.error("Unknown scraper: {}. Available: {}", scraper_name, list(scrapers.keys()))
        return []
    return run_scraper(scrapers[scraper_name])


async def run_all_with_ingest() -> tuple[int, int]:
    """Run all scrapers and ingest results into Nexus RAG. Returns (total, ingested)."""
    from web_scrapers.bridge.nexus import ingest_events

    events = run_all()
    if not events:
        return 0, 0
    ingested = await ingest_events(events)
    return len(events), ingested
