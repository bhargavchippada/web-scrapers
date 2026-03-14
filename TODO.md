# TODO.md — Web Scrapers

<!-- Pending tasks: [ ] incomplete, [x] completed -->

**Version:** v1.8

## SurrealDB Migration (v2 — deferred)

> **Status:** Deferred to v2 — workspace v1.0 milestone complete with GC/AT/MC migrated. Web Scrapers remains on PostgreSQL.
> **Workspace artifact:** `artifacts/2026-03-11/ANTIGRAVITY_ARCHITECTURE_surrealdb_migration_plan.md`
> **Goal:** Replace 3 PostgreSQL tables with SurrealDB 3.0 + enable full-text search on signal payloads
> **SurrealDB target:** namespace `antigravity`, database `web_scrapers` (credentials: turiya/antigravity)
> **Estimated effort:** 1-2 sessions

### Infrastructure
- [ ] Add `surrealdb[pydantic]` to `pyproject.toml`
- [ ] Create `web_scrapers/db/surreal_client.py` — Async SurrealDB client
- [ ] Create `scripts/surrealdb-schema.surql` — 3 tables + FTS index + computed searchable_text field
- [ ] Add `SURREAL_*` env vars to config

### Migration
- [ ] Migrate scrape_jobs table → SurrealDB `scrape_job`
- [ ] Migrate scrape_runs table → SurrealDB `scrape_run` with `record<scrape_job>` link
- [ ] Migrate signal_events table → SurrealDB `signal_event` with UNIQUE event_id dedup
- [ ] Replace `ON CONFLICT DO UPDATE` with SurrealDB `ON DUPLICATE KEY UPDATE`
- [ ] Replace `engine.py` SQLAlchemy engine with SurrealDB connection
- [ ] Rewrite `repository.py` with SurrealQL queries
- [ ] Create `scripts/migrate-pg-to-surreal.py` — One-time data migration

### New Capabilities (enabled by SurrealDB)
- [ ] Full-text search on signal payloads via computed `searchable_text` field + BM25 index
- [ ] Record links replace FK joins (scrape_job → scrape_run → signal_event)

### Validation
- [ ] Verify row counts match across all 3 tables
- [ ] Test dedup: duplicate event_ids correctly update payload + scraped_at
- [ ] Benchmark FTS queries on signal content

### Cleanup (after validation)
- [ ] Remove SQLAlchemy models (keep Pydantic models in `models/`)
- [ ] Archive `alembic/` directory
- [ ] Remove `psycopg2-binary` dependency

## Maintenance

- [ ] Bump `pyproject.toml` version to `0.7.0` (currently `0.5.0`, out of sync with README/MEMORY)
- [ ] Remove dead code in `bridge/nexus.py` (Nexus RAG removed — dead since SurrealDB migration step 1)
- [ ] Set up systemd service for daemon mode (currently manual start only)

## Phase 3 — New Scrapers

- [ ] YouTube Transcript scraper (`youtube-transcript-api`)
- [ ] Twitter/X scraper (`tweepy` or `snscrape`)
- [ ] SEC EDGAR scraper (8-K filings)

## Phase 4 — Infrastructure

- [ ] Grafana dashboards for scrape stats
- [ ] Real-time streaming via SurrealDB LIVE SELECT (replaces removed Nexus RAG bridge)

## Completed (Archive)

<details>
<summary>Phases 2.0–2.10 (v0.1.0 → v0.6.1)</summary>

- [x] Reddit scraper with sentiment analysis (v0.1.0)
- [x] News/RSS scraper (v0.1.0)
- [x] PostgreSQL persistence with deduplication (v0.2.0)
- [x] Job scheduler — APScheduler (v0.2.0)
- [x] Nexus RAG ingestion bridge (v0.2.0)
- [x] Reddit comment scraping with configurable N comments/post (v0.3.0)
- [x] Library packaging — `pip install -e`, public API exports (v0.4.0)
- [x] Cross-project integration — agentic-trader imports web-scrapers (v0.5.0)
- [x] Symbol mapping module (v0.5.0)
- [x] UniversalScraper + trafilatura (v0.6.0)
- [x] Fix nexus bridge to use unified `ingest_document` API (v0.6.0)
- [x] Fix bridge `source_identifier` duplication (v0.6.1)
- [x] Harden news scraper network-error logging (v0.6.1)

</details>
