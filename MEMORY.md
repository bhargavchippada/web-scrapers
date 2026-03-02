# MEMORY.md — Web Scrapers

<!-- Logical state: known bugs, key findings, changelog -->

**Version:** v0.2

## Known Issues

- [ ] Some RSS feeds (Bloomberg, Investing.com) may block automated requests
- [ ] YouTube Transcript scraper not yet implemented (Phase 3)
- [ ] Twitter/X scraper not yet implemented (Phase 3)
- [ ] SEC EDGAR scraper not yet implemented (Phase 3)

## Key Findings

### Architecture

- **Data flow:** Scraper.scrape() → list[SignalEvent] → EventRepository.bulk_upsert()
- **Deduplication:** `ON CONFLICT (event_id) DO NOTHING` for idempotent upserts
- **RAG bridge:** Only NEW events forwarded to Nexus RAG

### Scrapers

| Scraper | Implementation | Features |
|---------|----------------|----------|
| **Reddit** | PRAW (praw) | VADER sentiment analysis on title + body |
| **News** | feedparser + httpx | RSS/Atom feeds with category tagging |

### Database Schema (3 tables)

- `signal_events` — scraped content with `event_id` unique constraint
- `scrape_runs` — execution history with status and timing
- `scrape_jobs` — scheduler job definitions from `config/jobs.yaml`

### Configuration

- `config/subreddits.yaml` — target subreddits with sort/limit options
- `config/feeds.yaml` — RSS feed URLs with categories
- `config/jobs.yaml` — cron schedules for automated scraping

## Changelog

### v0.2.0 — Job Scheduler (Current)

- APScheduler daemon mode for continuous scraping
- Database layer with SQLAlchemy 2.0 ORM
- Alembic migrations for schema versioning
- Nexus RAG ingestion bridge (`--ingest` flag)
- Typer CLI with `scrape`, `db`, `jobs`, `daemon`, `health` commands
- PostgreSQL persistence with deduplication

### v0.1.0 — Initial Scrapers

- Reddit scraper with PRAW
- News/RSS scraper with feedparser
- SignalEvent Pydantic model
- VADER sentiment analysis
