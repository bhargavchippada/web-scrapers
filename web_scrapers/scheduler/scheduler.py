# Version: v0.2.0
"""APScheduler-based daemon for scheduled scraping jobs."""

from __future__ import annotations

import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from web_scrapers.coordinator import run_tracked
from web_scrapers.db.engine import get_session
from web_scrapers.db.repository import JobRepository


def _execute_job(job_id: int, job_name: str, scraper: str, ingest: bool = False) -> None:
    """Callback for APScheduler — runs a single tracked scrape."""
    logger.info("Scheduler executing job: {} (scraper={})", job_name, scraper)
    try:
        total, new, ingested = run_tracked(scraper, job_id=job_id, job_name=job_name, ingest=ingest)
        logger.info(
            "Job {} complete: {} total, {} new, {} ingested",
            job_name,
            total,
            new,
            ingested,
        )
    except Exception:
        logger.exception("Job {} failed", job_name)


def build_scheduler(ingest: bool = False) -> BlockingScheduler:
    """Build scheduler from DB job definitions."""
    scheduler = BlockingScheduler()

    session = get_session()
    try:
        repo = JobRepository(session)
        jobs = repo.get_all_enabled()

        for job in jobs:
            if not job.schedule:
                logger.warning("Job {} has no schedule, skipping", job.name)
                continue

            trigger = CronTrigger.from_crontab(job.schedule)
            scheduler.add_job(
                _execute_job,
                trigger=trigger,
                args=[job.id, job.name, job.scraper, ingest],
                id=f"scrape_{job.name}",
                name=f"Scrape: {job.name}",
                replace_existing=True,
            )
            logger.info("Registered job: {} [{}]", job.name, job.schedule)
    finally:
        session.close()

    if not scheduler.get_jobs():
        logger.warning("No scheduled jobs found. Daemon will idle.")

    return scheduler


def run_daemon(ingest: bool = False) -> None:
    """Start the blocking scheduler daemon."""
    logger.info("Starting web-scrapers daemon...")
    scheduler = build_scheduler(ingest=ingest)

    def _shutdown(signum, _frame):
        logger.info("Received signal {}, shutting down...", signum)
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    scheduler.start()
