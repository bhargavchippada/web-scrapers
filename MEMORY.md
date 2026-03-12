# MEMORY.md — Web Scrapers

<!-- Logical state: known bugs, key findings, changelog -->

**Version:** v1.0

## Known Issues

- [ ] 37 test errors in `test_db.py` — `ProgrammingError` from SQLAlchemy (schema/migration issue, not code bug)
- [ ] Some RSS feeds (Bloomberg, Investing.com) may block automated requests
- [ ] Daemon not running — needs systemd service or manual start
- [ ] Low coverage on `bridge/nexus.py` (41%) — requires running Nexus services to test
- [ ] `pyproject.toml` version stuck at `0.5.0` — README/docs reference `v0.6.1`

## Architecture

- **Data flow:** `Scraper.scrape()` → `list[SignalEvent]` → `EventRepository.bulk_upsert()` (ON CONFLICT DO NOTHING) → only NEW events forwarded to Nexus RAG bridge
- **Deduplication:** `event_id` is canonical (e.g., `reddit:abc123`, `news:fa3b...`). Never re-prefix in adapters.
- **DB schema:** 3 tables in `web_scrapers` schema — `signal_events`, `scrape_runs`, `scrape_jobs`
- **RAG bridge:** Uses `ingest_document` (unified API), `project_id=WEB_SCRAPERS`, `scope=WEB_RESEARCH`

## Cross-Project Dependencies

- **agentic-trader** imports web-scrapers as path dependency — uses VADER sentiment, RSS feeds, symbol mapping
- `utils/symbol_mapping.py` is the canonical source for ticker→company name mapping (70+ symbols)
- `Settings` has `extra="ignore"` to tolerate parent project env vars

## Guidelines (Proven Patterns)

1. **Identifiers:** Normalize once at event creation. `SignalEvent.event_id` is the canonical external ID — pass through unchanged across DB/RAG boundaries.
2. **RAG ingestion:** Always detect new events BEFORE persisting to DB, then filter for RAG ingest. Never ingest all events on every run.
3. **Bridge imports:** Wrap `nexus.tools.ingest_document` import with `try/except ImportError` — it's an optional dependency.
4. **Network errors:** Log `httpx.RequestError` as warnings (concise), reserve stack traces for unexpected exceptions.
5. **New scrapers:** Always export from root `__init__.py` module and add comprehensive tests.
6. **Config:** Use `config/*.yaml` for external configuration. `Settings` (Pydantic) for env vars.

## Changelog Summary

| Version | Key Changes |
|---------|-------------|
| v0.6.1 | Fix bridge `source_identifier` duplication, harden network error logging (211 tests) |
| v0.6.0 | UniversalScraper (trafilatura), fix bridge to use unified `ingest_document` (209 tests) |
| v0.5.1 | Fix `run_all_with_ingest()` duplicate RAG ingestion, doc sync (183 tests) |
| v0.5.0 | Symbol mapping, cross-project integration with agentic-trader (183 tests) |
| v0.4.0 | Library packaging (`pip install -e`), public API, query helpers (172 tests) |
| v0.3.0 | Reddit comment scraping, configurable N comments/post |
| v0.2.0 | APScheduler daemon, SQLAlchemy DB, Alembic migrations, Nexus bridge, CLI |
| v0.1.0 | Reddit + News scrapers, SignalEvent model, VADER sentiment |
