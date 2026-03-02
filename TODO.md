# TODO.md — Web Scrapers

<!-- Pending tasks: [ ] incomplete, [x] completed -->

**Version:** v1.2

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
