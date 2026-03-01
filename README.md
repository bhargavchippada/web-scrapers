# Web Scrapers

> Version: v0.1.0 | Agent: Ari | Project: Nexus

Modular web scraping toolkit for financial intelligence gathering. Collects data from Reddit, news RSS feeds, and (future) YouTube transcripts and Twitter/X — feeding it into Nexus RAG for semantic search and graph analysis by AI agents.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                    CLI (typer)                    │
│         scrape reddit | scrape news | run-all    │
├──────────────────────────────────────────────────┤
│                  Coordinator                     │
│         Orchestrates scrapers + ingestion        │
├────────────┬─────────────┬───────────────────────┤
│  Reddit    │  News/RSS   │  (Future: YT, X)      │
│  Scraper   │  Scraper    │                       │
├────────────┴─────────────┴───────────────────────┤
│              BaseScraper ABC                      │
│         scrape() → list[SignalEvent]             │
├──────────────────────────────────────────────────┤
│         Models (Pydantic v2)                     │
│   SignalEvent → RedditPost | NewsArticle | ...   │
├──────────────────────────────────────────────────┤
│   Analysis (VADER sentiment) │ Nexus Bridge      │
│                              │ (RAG ingestion)   │
└──────────────────────────────────────────────────┘
```

## Quick Start

```bash
cd projects/web-scrapers

# Install dependencies
poetry install

# Copy and configure environment
cp .env.example .env
# Edit .env with your Reddit API credentials

# Run news scraper (no API key needed)
poetry run python -m web_scrapers.cli scrape news

# Run Reddit scraper (requires API keys)
poetry run python -m web_scrapers.cli scrape reddit

# Run all scrapers
poetry run python -m web_scrapers.cli run-all

# Run all + ingest into Nexus RAG
poetry run python -m web_scrapers.cli run-all --ingest

# Health check
poetry run python -m web_scrapers.cli health
```

## Scrapers

### Reddit Scraper

Fetches posts from financial subreddits using the official Reddit API (`praw`). Includes VADER sentiment analysis on post title + body.

**Configured subreddits:** `config/subreddits.yaml`

- r/wallstreetbets, r/options, r/stocks, r/cryptocurrency, r/investing, r/SecurityAnalysis

**Requires:** `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` in `.env`

### News Scraper

Parses RSS/Atom feeds from major financial news sources using `feedparser` + `httpx`.

**Configured feeds:** `config/feeds.yaml`

- Reuters Business, Yahoo Finance, MarketWatch, CNBC, Investing.com, Seeking Alpha, Bloomberg Markets

**No API key required.**

## Data Models

All scraped data is wrapped in a `SignalEvent` envelope:

```python
SignalEvent(
    source="reddit",           # Scraper source
    event_type="post",         # Event type
    payload={...},             # RedditPost or NewsArticle (dict)
    event_id="reddit:abc123",  # Unique ID for dedup
    ingested_at=datetime,      # UTC timestamp
)
```

## Configuration

### Environment Variables (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `REDDIT_CLIENT_ID` | For Reddit | — | Reddit OAuth app client ID |
| `REDDIT_CLIENT_SECRET` | For Reddit | — | Reddit OAuth app secret |
| `REDDIT_USER_AGENT` | No | `web-scrapers/0.1` | Reddit API user agent |
| `NEO4J_URL` | For ingestion | `bolt://localhost:7687` | Neo4j connection URL |
| `QDRANT_URL` | For ingestion | `http://localhost:6333` | Qdrant connection URL |
| `SCRAPER_LOG_LEVEL` | No | `INFO` | Log level |

### YAML Configs

- `config/subreddits.yaml` — Target subreddits with sort order, limit, category
- `config/feeds.yaml` — RSS feed URLs with name and category

## RAG Ingestion

When using `--ingest`, events are pushed to Nexus RAG:

- **project_id:** `WEB_SCRAPERS`
- **scope:** `WEB_RESEARCH`
- **Backends:** Neo4j (graph) + Qdrant (vector)

## Adding a New Scraper

1. Create model in `web_scrapers/models/your_source.py`
2. Implement `web_scrapers/scrapers/your_source.py` extending `BaseScraper`
3. Add config file `config/your_config.yaml`
4. Register in `web_scrapers/coordinator.py` → `get_all_scrapers()`
5. Add CLI subcommand in `web_scrapers/cli.py`
6. Add tests in `tests/test_your_source.py`

## Testing

```bash
poetry run pytest                    # Run all tests
poetry run pytest --cov=web_scrapers # With coverage
poetry run ruff check .              # Lint check
poetry run ruff format .             # Auto-format
```

## Tech Stack

- **Python** 3.11+
- **praw** — Reddit API client
- **feedparser** — RSS/Atom parsing
- **httpx** — HTTP client
- **Pydantic v2** — Data validation
- **vaderSentiment** — Sentiment analysis
- **typer** — CLI framework
- **loguru** — Structured logging
- **Poetry** — Package management

## Future (Phase 2)

- **YouTube Transcript Scraper** — `youtube-transcript-api` for financial channel transcripts
- **Twitter/X Scraper** — `tweepy` or `snscrape` for market-moving tweets
- **SEC EDGAR Scraper** — 8-K filings (reference: `~/.openclaw/workspace/projects/sentinel/sec_scraper.py`)
- **Scheduled runs** — APScheduler or cron integration
