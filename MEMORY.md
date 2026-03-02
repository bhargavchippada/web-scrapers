# MEMORY.md — Web Scrapers

<!-- Logical state: known bugs, key findings, changelog -->

**Version:** v0.4

## Known Issues

- [ ] Some RSS feeds (Bloomberg, Investing.com) may block automated requests
- [ ] Daemon not running — needs systemd service or manual start
- [ ] Low coverage on `bridge/nexus.py` (41%) — requires running services to test

## Key Findings

### Architecture

- **Data flow:** Scraper.scrape() → list[SignalEvent] → EventRepository.bulk_upsert()
- **Deduplication:** `ON CONFLICT (event_id) DO NOTHING` for idempotent upserts
- **RAG bridge:** Only NEW events forwarded to Nexus RAG

### Scrapers

| Scraper | Implementation | Features |
|---------|----------------|----------|
| **Reddit** | PRAW (praw) | VADER sentiment on posts + comments, configurable N comments per post |
| **News** | feedparser + httpx | RSS/Atom feeds with category tagging |

### Database Schema (3 tables)

- `signal_events` — scraped content with `event_id` unique constraint (posts: `reddit:{id}`, comments: `reddit:comment:{id}`)
- `scrape_runs` — execution history with status and timing
- `scrape_jobs` — scheduler job definitions from `config/jobs.yaml`

### Configuration

- `config/subreddits.yaml` — target subreddits with sort/limit/comments_limit options
- `config/feeds.yaml` — RSS feed URLs with categories
- `config/jobs.yaml` — cron schedules for automated scraping

## Changelog

### v0.4.0 — Library Packaging (Current)

- Enabled `package-mode` in pyproject.toml — now installable as `pip install -e`
- Full public API exported from `web_scrapers/__init__.py`
- Added `get_settings()` factory for injectable configuration
- Exported query helpers: `get_latest_events()`, `get_events_since()`, `get_stats()`, `get_subreddit_summary()`
- Added 11 new tests for query helpers and public API imports
- Coverage increased from 83% to 86%
- `db/queries.py` coverage increased from 23% to 100%
- Added "Library Usage" section to README.md

> **Guideline:** Other projects can now import `from web_scrapers import ...` after `pip install -e`.

### v0.3.0 — Comment Scraping

- RedditComment Pydantic model with sentiment analysis
- Configurable `comments_limit` per subreddit in `config/subreddits.yaml`
- Comments stored as `SignalEvent` with `event_type="comment"`
- Event IDs: posts use `reddit:{id}`, comments use `reddit:comment:{id}`
- Top N comments fetched per post, sorted by "best"

### v0.2.0 — Job Scheduler

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
