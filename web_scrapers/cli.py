# Version: v0.2.0
"""CLI entry point for web-scrapers."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime

import typer
from loguru import logger

from web_scrapers.config import settings

app = typer.Typer(help="Web Scrapers — Financial intelligence gathering toolkit")
scrape_app = typer.Typer(help="Run individual scrapers")
db_app = typer.Typer(help="Database management commands")
jobs_app = typer.Typer(help="Scraping job management")
app.add_typer(scrape_app, name="scrape")
app.add_typer(db_app, name="db")
app.add_typer(jobs_app, name="jobs")


def _setup_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.scraper_log_level)


# ─── Scrape commands ────────────────────────────────────────────────────


@scrape_app.command("reddit")
def scrape_reddit(
    output_json: bool = typer.Option(False, "--json", help="Output events as JSON"),
    no_persist: bool = typer.Option(False, "--no-persist", help="Skip database persistence"),
) -> None:
    """Scrape Reddit posts from configured subreddits."""
    _setup_logging()
    from web_scrapers.coordinator import run_single

    events = run_single("reddit", persist=not no_persist)
    if output_json:
        for ev in events:
            typer.echo(ev.model_dump_json())
    else:
        typer.echo(f"Collected {len(events)} Reddit events")


@scrape_app.command("news")
def scrape_news(
    output_json: bool = typer.Option(False, "--json", help="Output events as JSON"),
    no_persist: bool = typer.Option(False, "--no-persist", help="Skip database persistence"),
) -> None:
    """Scrape news articles from configured RSS feeds."""
    _setup_logging()
    from web_scrapers.coordinator import run_single

    events = run_single("news", persist=not no_persist)
    if output_json:
        for ev in events:
            typer.echo(ev.model_dump_json())
    else:
        typer.echo(f"Collected {len(events)} news events")


@app.command("run-all")
def run_all_cmd(
    ingest: bool = typer.Option(False, "--ingest", help="Ingest events into Nexus RAG"),
    output_json: bool = typer.Option(False, "--json", help="Output events as JSON"),
    no_persist: bool = typer.Option(False, "--no-persist", help="Skip database persistence"),
) -> None:
    """Run all configured scrapers."""
    _setup_logging()

    if ingest:
        from web_scrapers.coordinator import run_all_with_ingest

        total, ingested = asyncio.run(run_all_with_ingest())
        typer.echo(f"Collected {total} events, ingested {ingested} into Nexus RAG")
    else:
        from web_scrapers.coordinator import run_all

        events = run_all(persist=not no_persist)
        if output_json:
            for ev in events:
                typer.echo(ev.model_dump_json())
        else:
            typer.echo(f"Collected {len(events)} total events")


@app.command("health")
def health() -> None:
    """Check connectivity to all data sources and database."""
    _setup_logging()
    from web_scrapers.scrapers import NewsScraper, RedditScraper

    scrapers = [RedditScraper(), NewsScraper()]
    all_ok = True
    for s in scrapers:
        ok = s.health_check()
        status = "OK" if ok else "FAIL"
        typer.echo(f"  {s.name}: {status}")
        if not ok:
            all_ok = False

    # DB health check
    try:
        from sqlalchemy import text as sa_text

        from web_scrapers.db.engine import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(sa_text("SELECT 1"))
        typer.echo("  database: OK")
    except Exception:
        typer.echo("  database: FAIL")
        all_ok = False

    raise typer.Exit(code=0 if all_ok else 1)


# ─── Database commands ──────────────────────────────────────────────────


@db_app.command("init")
def db_init() -> None:
    """Initialize database schema and run migrations."""
    _setup_logging()
    import subprocess

    from web_scrapers.db.engine import ensure_schema

    ensure_schema()
    result = subprocess.run(
        ["poetry", "run", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        typer.echo("Database initialized successfully")
    else:
        typer.echo(f"Migration failed: {result.stderr}", err=True)
        raise typer.Exit(code=1)


@db_app.command("seed-jobs")
def db_seed_jobs() -> None:
    """Load job definitions from config/jobs.yaml into the database."""
    _setup_logging()
    from web_scrapers.config import get_job_definitions
    from web_scrapers.db.engine import get_session
    from web_scrapers.db.repository import JobRepository

    definitions = get_job_definitions()
    if not definitions:
        typer.echo("No job definitions found in config/jobs.yaml")
        return

    session = get_session()
    try:
        repo = JobRepository(session)
        for job_def in definitions:
            repo.upsert_job(
                name=job_def["name"],
                scraper=job_def["scraper"],
                schedule=job_def.get("schedule"),
                config=job_def.get("config", {}),
                enabled=job_def.get("enabled", True),
            )
            typer.echo(f"  Seeded job: {job_def['name']}")
    finally:
        session.close()

    typer.echo(f"Seeded {len(definitions)} jobs")


@db_app.command("stats")
def db_stats() -> None:
    """Show database statistics."""
    _setup_logging()
    from web_scrapers.db.queries import get_stats

    stats = get_stats()
    typer.echo("Database Statistics:")
    typer.echo(f"  Total events:    {stats['total_events']}")
    typer.echo(f"  Reddit events:   {stats['reddit_events']}")
    typer.echo(f"  News events:     {stats['news_events']}")
    typer.echo(f"  Last 24h:        {stats['events_last_24h']}")

    if stats["recent_runs"]:
        typer.echo("\nRecent Runs:")
        for run in stats["recent_runs"]:
            typer.echo(
                f"  {run['started_at']} | {run['job_name']:20s} | "
                f"{run['status']:10s} | +{run['events_new']} new"
            )


@db_app.command("query")
def db_query(
    source: str | None = typer.Option(None, help="Filter by source (reddit, news)"),
    subreddit: str | None = typer.Option(None, help="Filter by subreddit"),
    feed_name: str | None = typer.Option(None, "--feed", help="Filter by feed name"),
    since: str | None = typer.Option(None, help="Events since (ISO datetime or YYYY-MM-DD)"),
    until: str | None = typer.Option(None, help="Events until (ISO datetime or YYYY-MM-DD)"),
    limit: int = typer.Option(50, help="Maximum results"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Query stored events with filters."""
    _setup_logging()
    from web_scrapers.db.engine import get_session
    from web_scrapers.db.repository import EventRepository

    since_dt = datetime.fromisoformat(since) if since else None
    until_dt = datetime.fromisoformat(until) if until else None

    session = get_session()
    try:
        repo = EventRepository(session)
        rows = repo.query_events(
            source=source,
            since=since_dt,
            until=until_dt,
            subreddit=subreddit,
            feed_name=feed_name,
            limit=limit,
        )

        if output_json:
            for r in rows:
                typer.echo(
                    json.dumps(
                        {
                            "event_id": r.event_id,
                            "source": r.source,
                            "event_type": r.event_type,
                            "payload": r.payload,
                            "scraped_at": r.scraped_at.isoformat(),
                        }
                    )
                )
        else:
            typer.echo(f"Found {len(rows)} events:")
            for r in rows:
                title = r.payload.get("title", r.payload.get("feed_name", ""))
                typer.echo(
                    f"  [{r.source}] {r.scraped_at:%Y-%m-%d %H:%M} | "
                    f"{r.event_id} | {title[:60]}"
                )
    finally:
        session.close()


# ─── Jobs commands ──────────────────────────────────────────────────────


@jobs_app.command("list")
def jobs_list() -> None:
    """Show all configured scraping jobs."""
    _setup_logging()
    from web_scrapers.db.engine import get_session
    from web_scrapers.db.repository import JobRepository, RunRepository

    session = get_session()
    try:
        job_repo = JobRepository(session)
        run_repo = RunRepository(session)
        jobs = job_repo.get_all()

        if not jobs:
            typer.echo("No jobs configured. Run `db seed-jobs` first.")
            return

        typer.echo(f"{'Name':25s} {'Scraper':10s} {'Schedule':20s} {'Enabled':8s} {'Last Run':25s}")
        typer.echo("-" * 90)
        for job in jobs:
            last_run = run_repo.get_last_run(job.scraper)
            last_run_str = last_run.started_at.strftime("%Y-%m-%d %H:%M") if last_run else "never"
            enabled_str = "yes" if job.enabled else "no"
            typer.echo(
                f"{job.name:25s} {job.scraper:10s} {(job.schedule or 'manual'):20s} "
                f"{enabled_str:8s} {last_run_str:25s}"
            )
    finally:
        session.close()


@jobs_app.command("run")
def jobs_run(
    name: str = typer.Argument(help="Job name to run"),
    ingest: bool = typer.Option(False, "--ingest", help="Also ingest into Nexus RAG"),
) -> None:
    """Manually trigger a specific scraping job."""
    _setup_logging()
    from web_scrapers.db.engine import get_session
    from web_scrapers.db.repository import JobRepository

    session = get_session()
    try:
        job_repo = JobRepository(session)
        job = job_repo.get_by_name(name)
        if not job:
            typer.echo(f"Job '{name}' not found")
            raise typer.Exit(code=1)
    finally:
        session.close()

    from web_scrapers.coordinator import run_tracked

    total, new, ingested = run_tracked(
        job.scraper, job_id=job.id, job_name=job.name, ingest=ingest
    )
    typer.echo(f"Job '{name}' complete: {total} scraped, {new} new, {ingested} ingested")


@jobs_app.command("enable")
def jobs_enable(name: str = typer.Argument(help="Job name to enable")) -> None:
    """Enable a disabled scraping job."""
    _setup_logging()
    from web_scrapers.db.engine import get_session
    from web_scrapers.db.repository import JobRepository

    session = get_session()
    try:
        repo = JobRepository(session)
        if repo.set_enabled(name, enabled=True):
            typer.echo(f"Job '{name}' enabled")
        else:
            typer.echo(f"Job '{name}' not found")
            raise typer.Exit(code=1)
    finally:
        session.close()


@jobs_app.command("disable")
def jobs_disable(name: str = typer.Argument(help="Job name to disable")) -> None:
    """Disable a scraping job."""
    _setup_logging()
    from web_scrapers.db.engine import get_session
    from web_scrapers.db.repository import JobRepository

    session = get_session()
    try:
        repo = JobRepository(session)
        if repo.set_enabled(name, enabled=False):
            typer.echo(f"Job '{name}' disabled")
        else:
            typer.echo(f"Job '{name}' not found")
            raise typer.Exit(code=1)
    finally:
        session.close()


@jobs_app.command("history")
def jobs_history(
    limit: int = typer.Option(20, help="Number of runs to show"),
    scraper: str | None = typer.Option(None, help="Filter by scraper name"),
) -> None:
    """Show recent scraping run history."""
    _setup_logging()
    from web_scrapers.db.engine import get_session
    from web_scrapers.db.repository import RunRepository

    session = get_session()
    try:
        repo = RunRepository(session)
        runs = repo.get_recent_runs(limit=limit, scraper=scraper)

        if not runs:
            typer.echo("No runs recorded yet.")
            return

        typer.echo(
            f"{'Started At':20s} {'Job':20s} {'Status':10s} "
            f"{'Total':6s} {'New':6s} {'Ingested':8s} {'Error':30s}"
        )
        typer.echo("-" * 100)
        for r in runs:
            err = (r.error or "")[:30]
            typer.echo(
                f"{r.started_at:%Y-%m-%d %H:%M:%S}   {r.job_name:20s} {r.status.value:10s} "
                f"{r.events_total:<6d} {r.events_new:<6d} {r.events_ingested:<8d} {err}"
            )
    finally:
        session.close()


# ─── Daemon command ─────────────────────────────────────────────────────


@app.command("daemon")
def daemon_cmd(
    ingest: bool = typer.Option(False, "--ingest", help="Also ingest new events into Nexus RAG"),
) -> None:
    """Start the scheduler daemon — runs enabled jobs on their cron schedules."""
    _setup_logging()
    from web_scrapers.scheduler.scheduler import run_daemon

    run_daemon(ingest=ingest)


# ─── Entry point ────────────────────────────────────────────────────────


def main() -> None:
    app()


if __name__ == "__main__":
    main()
