# TODO.md — Web Scrapers

<!-- Pending tasks: [ ] incomplete, [x] completed -->

**Version:** v1.6

## Maintenance

- [ ] Bump `pyproject.toml` version to `0.6.1` (currently `0.5.0`, out of sync with README/MEMORY)
- [ ] Fix 37 test errors in `test_db.py` (SQLAlchemy `ProgrammingError` — schema/migration issue)
- [ ] Improve bridge test coverage (`bridge/nexus.py` at 41%)
- [ ] Set up systemd service for daemon mode (currently manual start only)

## Phase 3 — New Scrapers

- [ ] YouTube Transcript scraper (`youtube-transcript-api`)
- [ ] Twitter/X scraper (`tweepy` or `snscrape`)
- [ ] SEC EDGAR scraper (8-K filings)

## Phase 4 — Infrastructure

- [ ] pgvector embeddings in PostgreSQL
- [ ] Grafana dashboards for scrape stats
- [ ] Real-time streaming to Nexus RAG

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
