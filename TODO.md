# TODO.md — Web Scrapers

<!-- Pending tasks: [ ] incomplete, [x] completed -->

**Version:** v1.5

## Phase 2.10 — Code Review Bug Fixes (Completed v0.6.1)

- [x] Fix Nexus bridge `source_identifier` duplication (`source:event_id` → `event_id`)
- [x] Add bridge regression tests for ingest call contract + import failure handling
- [x] Harden news scraper network-error logging (warning for expected `httpx.RequestError`)
- [x] Add news health-check request-error regression test
- [x] End-to-end CLI validation (`db init`, `db seed-jobs`, `db stats`, `jobs list`, `scrape news`, `health`)

## Phase 2.9 — Code Review & Robustness (Completed v0.6.0)

- [x] Fix nexus bridge to use `ingest_document` (unified API)
- [x] Export `UniversalScraper`, `scrape_url`, `scrape_urls` from root module
- [x] Add 26 tests for UniversalScraper (209 total)
- [x] Install trafilatura dependency
- [x] Security audit passed (0 critical/high issues)

## Phase 2.8 — Bug Fixes (Completed v0.5.1)

- [x] Fix `run_all_with_ingest()` to only ingest NEW events (not duplicates)
- [x] Code review: 8-pillar review — all pillars PASS

## Phase 2.7 — Cross-Project Integration (Completed v0.5.0)

- [x] Symbol mapping module (`utils/symbol_mapping.py`)
- [x] Export symbol utilities from root module
- [x] Cross-project dependency: agentic-trader now imports web-scrapers
- [x] Add `extra="ignore"` to Settings for parent project env vars
- [x] 18 new tests for symbol_mapping (183 total)

## Phase 2.6 — Library Packaging (Completed)

- [x] Enable `package-mode` in pyproject.toml
- [x] Export full public API from `__init__.py`
- [x] Add `get_settings()` factory for injectable configuration
- [x] Export query helpers from `db` module
- [x] Add tests for query helpers (100% coverage on `db/queries.py`)
- [x] Add "Library Usage" section to README.md
- [x] Verify `pip install -e` works correctly

## Phase 2.5 — Comments Scraping (Completed)

- [x] Reddit comment scraping with N comments per post
- [x] RedditComment Pydantic model with sentiment analysis
- [x] Database storage for comments (event_type: "comment")
- [x] Configurable comments_limit per subreddit

## Phase 2 — Completed

- [x] Reddit scraper with sentiment analysis
- [x] News/RSS scraper
- [x] PostgreSQL persistence with deduplication
- [x] Job scheduler (APScheduler)
- [x] Nexus RAG ingestion bridge

## Phase 3 — Upcoming

- [ ] YouTube Transcript scraper (youtube-transcript-api)
- [ ] Twitter/X scraper (tweepy or snscrape)
- [ ] SEC EDGAR scraper (8-K filings)

## Phase 4 — Future

- [ ] pgvector embeddings in PostgreSQL
- [ ] Grafana dashboards for scrape stats
- [ ] Real-time streaming to Nexus RAG
