# Version: v0.1.0
"""CLI entry point for web-scrapers."""

from __future__ import annotations

import asyncio
import sys

import typer
from loguru import logger

from web_scrapers.config import settings

app = typer.Typer(help="Web Scrapers — Financial intelligence gathering toolkit")
scrape_app = typer.Typer(help="Run individual scrapers")
app.add_typer(scrape_app, name="scrape")


def _setup_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.scraper_log_level)


@scrape_app.command("reddit")
def scrape_reddit(
    output_json: bool = typer.Option(False, "--json", help="Output events as JSON"),
) -> None:
    """Scrape Reddit posts from configured subreddits."""
    _setup_logging()
    from web_scrapers.coordinator import run_single

    events = run_single("reddit")
    if output_json:
        for ev in events:
            typer.echo(ev.model_dump_json())
    else:
        typer.echo(f"Collected {len(events)} Reddit events")


@scrape_app.command("news")
def scrape_news(
    output_json: bool = typer.Option(False, "--json", help="Output events as JSON"),
) -> None:
    """Scrape news articles from configured RSS feeds."""
    _setup_logging()
    from web_scrapers.coordinator import run_single

    events = run_single("news")
    if output_json:
        for ev in events:
            typer.echo(ev.model_dump_json())
    else:
        typer.echo(f"Collected {len(events)} news events")


@app.command("run-all")
def run_all(
    ingest: bool = typer.Option(False, "--ingest", help="Ingest events into Nexus RAG"),
    output_json: bool = typer.Option(False, "--json", help="Output events as JSON"),
) -> None:
    """Run all configured scrapers."""
    _setup_logging()

    if ingest:
        from web_scrapers.coordinator import run_all_with_ingest

        total, ingested = asyncio.run(run_all_with_ingest())
        typer.echo(f"Collected {total} events, ingested {ingested} into Nexus RAG")
    else:
        from web_scrapers.coordinator import run_all as _run_all

        events = _run_all()
        if output_json:
            for ev in events:
                typer.echo(ev.model_dump_json())
        else:
            typer.echo(f"Collected {len(events)} total events")


@app.command("health")
def health() -> None:
    """Check connectivity to all data sources."""
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

    raise typer.Exit(code=0 if all_ok else 1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
