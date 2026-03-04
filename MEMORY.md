# MEMORY.md — Web Scrapers

<!-- Logical state: known bugs, key findings, changelog -->

**Version:** v0.9

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

### Shared Utilities

| Utility | Module | Purpose |
| ------- | ------ | ------- |
| **Symbol Mapping** | `utils/symbol_mapping.py` | Ticker→company name mapping (AAPL→Apple) |
| **VADER Sentiment** | `analysis/sentiment.py` | Social media optimized sentiment (handles emojis) |
| **Feed Targets** | `config.py` | RSS feed configuration from YAML |

> **Cross-Project:** agentic-trader imports these utilities as a path dependency.

### Database Schema (3 tables)

- `signal_events` — scraped content with `event_id` unique constraint (posts: `reddit:{id}`, comments: `reddit:comment:{id}`)
- `scrape_runs` — execution history with status and timing
- `scrape_jobs` — scheduler job definitions from `config/jobs.yaml`

### Configuration

- `config/subreddits.yaml` — target subreddits with sort/limit/comments_limit options
- `config/feeds.yaml` — RSS feed URLs with categories
- `config/jobs.yaml` — cron schedules for automated scraping

## Changelog

### v0.6.1 — Bridge Identifier + Network Error Robustness (Current)

- **Bug Fix:** `bridge/nexus.py` now passes `source_identifier=event.event_id` (instead of `f"{event.source}:{event.event_id}"`)
  - Root cause: `event_id` already includes source prefix (`reddit:...`, `news:...`), so previous code duplicated prefixes
  - Impact: Prevents identifier drift and duplicate identity keys in Nexus ingest pipeline
  - Prevention: Treat `SignalEvent.event_id` as canonical external identifier; never re-prefix in adapters
- **Bug Fix:** Bridge now handles `ImportError` for `nexus.tools.ingest_document` and returns 0 instead of crashing
  - Root cause: Import performed inside runtime path without guard
  - Prevention: Wrap dynamic imports with explicit error handling for optional/dependency-linked modules
- **Robustness:** `NewsScraper` now logs `httpx.RequestError` as warnings in `scrape()` and `health_check()`
  - Root cause: Expected network/DNS failures were logged with full stack traces, creating noisy operational logs
  - Prevention: Reserve stack traces for unexpected exceptions; use concise warning logs for expected network failures
- **Tests:** Added regression tests for bridge ingest behavior and news health request error path (211 passing tests total)

> **Guideline:** Normalize identifiers once at event creation and pass them through unchanged across DB/RAG boundaries.

### v0.6.0 — UniversalScraper + Nexus Bridge Fix

- **Bug Fix:** `bridge/nexus.py` now uses unified `ingest_document` instead of separate `ingest_graph_document` + `ingest_vector_document` calls
  - Root cause: Legacy code predating `ingest_document` API
  - Prevention: Always use `ingest_document` for structured content (CLAUDE.md guidance)
- **Feature:** Exported `UniversalScraper`, `scrape_url`, `scrape_urls` from root module
  - Enables scraping any URL without API keys (uses trafilatura for content extraction)
  - 26 new tests for universal scraper (209 total tests)
- **Robustness:** Coverage improved from 78% to ~85% with UniversalScraper tests
- **Dependency:** Installed trafilatura 2.0.0 (was in pyproject.toml but not installed)

> **Guideline:** When adding new scraper types, always export from root module and add comprehensive tests.

### v0.5.1 — Documentation Sync

- **README.md v0.5.1:** Fixed schedule table (reddit is `*/10 * * * *`, not `*/30`), added symbol utilities to Public API section
- **AGENTS.md v1.4:** Added `db query` and `jobs run/enable/disable/history` commands
- **TODO.md v1.3:** Added Phase 2.7 (Symbol Mapping) and Phase 2.8 (Bug Fixes) as completed
- **MEMORY.md v0.7:** This entry

> **Guideline:** Keep documentation version numbers in sync with the codebase version.

### v0.5.1 — Bug Fix: RAG Ingestion

- **Bug Fix:** `run_all_with_ingest()` now only ingests NEW events instead of ALL events
  - Previously ingested all events on every run, causing duplicate RAG entries
  - Now matches `run_tracked()` behavior: detect new → persist → ingest only new
  - Root cause: Missing deduplication check before RAG ingestion
- **Code Review:** 8-pillar review completed — all pillars PASS
- **Tests:** 183 passing, lint clean

> **Guideline:** When implementing ingestion, always detect new events BEFORE persisting to DB, then filter for RAG ingestion.

### v0.5.0 — Cross-Project Integration

- **Symbol Mapping Module:** `utils/symbol_mapping.py` for ticker→company name mapping
  - 70+ stock symbols with company names, products, CEO names
  - `get_company_names(symbol)` — returns list of searchable terms
  - `is_relevant_to_symbol(text, symbol)` — checks if text mentions the symbol
  - Exported from root module: `from web_scrapers import is_relevant_to_symbol`
- **Cross-Project Integration:** agentic-trader now depends on web-scrapers
  - Shared VADER sentiment analysis (replaces agentic-trader's keyword-based)
  - Shared RSS feed configuration (agentic-trader uses 7 feeds instead of 4)
  - Symbol mapping canonical source (agentic-trader re-exports for backward compat)
- **Config Fix:** Added `extra="ignore"` to Settings to allow parent projects' env vars
- **Tests:** 18 new tests for symbol_mapping (183 total tests)

> **Guideline:** Symbol mapping functions are now shared across projects. Maintain the SYMBOL_TO_COMPANY dict here as the canonical source.

### v0.4.0 — Library Packaging

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
