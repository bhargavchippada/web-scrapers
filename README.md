# Web Scrapers

<!-- Executive summary: tech stack, mission, architecture -->

**Version:** v0.6.2

> See [AGENTS.md](AGENTS.md) for commands | [MEMORY.md](MEMORY.md) for state | [TODO.md](TODO.md) for tasks

Modular web scraping toolkit for financial intelligence gathering. Collects data from Reddit, news RSS feeds, and (future) YouTube transcripts and Twitter/X — feeding it into a deduplicated PostgreSQL database and Nexus RAG for semantic search and graph analysis by AI agents.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLI (typer)                              │
│  scrape reddit | scrape news | run-all | db | jobs | daemon     │
├──────────────────────────────────────────────────────────────────┤
│                   Scheduler (APScheduler)                        │
│            Cron-triggered jobs → run_tracked()                   │
├──────────────────────────────────────────────────────────────────┤
│                      Coordinator                                 │
│     scrape() → persist to DB (dedup) → (optional) RAG ingest    │
├────────────┬─────────────┬───────────────────────────────────────┤
│  Reddit    │  News/RSS   │  (Future: YT, X, SEC)                │
│  Scraper   │  Scraper    │                                       │
├────────────┴─────────────┴───────────────────────────────────────┤
│              BaseScraper ABC → list[SignalEvent]                  │
├─────────────────────────────┬────────────────────────────────────┤
│   DB Layer (SQLAlchemy 2.0) │     Nexus RAG Bridge               │
│   Repository (DAO)          │  (Memgraph + pgvector)             │
│   EventRepo | RunRepo       │                                    │
│   JobRepo                   │                                    │
│   ────────────────────────  │                                    │
│   PostgreSQL 16 (pgvector)  │                                    │
└─────────────────────────────┴────────────────────────────────────┘
```

**Data flow:** `Scraper.scrape()` → `list[SignalEvent]` → `EventRepository.bulk_upsert()` (ON CONFLICT DO NOTHING) → only NEW events forwarded to Nexus RAG bridge.

## Current Status (v0.6.1)

- **211 tests** (174 passing, 37 DB errors — require PostgreSQL `web_scrapers` schema)
- **Scrapers:** Reddit (PRAW + VADER sentiment), News (feedparser + httpx), Universal (trafilatura)
- **Database:** PostgreSQL 16 with dedup (`ON CONFLICT DO NOTHING`), APScheduler daemon, Alembic migrations
- **RAG:** Nexus bridge with unified `ingest_document` API, stable `source_identifier=event_id`
- **Cross-project:** agentic-trader imports sentiment, feeds, and symbol mapping as path dependency

## Quick Start

```bash
cd projects/web-scrapers

# Install dependencies
poetry install

# Copy and configure environment
cp .env.example .env
# Edit .env with your Reddit API credentials + DATABASE_URL

# Initialize database (requires PostgreSQL running)
poetry run python -m web_scrapers.cli db init
poetry run python -m web_scrapers.cli db seed-jobs

# Run news scraper (no API key needed — persists to DB)
poetry run python -m web_scrapers.cli scrape news

# Run Reddit scraper (requires API keys)
poetry run python -m web_scrapers.cli scrape reddit

# Run all scrapers
poetry run python -m web_scrapers.cli run-all

# Run all + ingest into Nexus RAG
poetry run python -m web_scrapers.cli run-all --ingest

# Health check (scrapers + DB)
poetry run python -m web_scrapers.cli health
```

## Library Usage (from Other Projects)

This package can be installed as an editable dependency in other Antigravity projects:

### Installation

```bash
# Install as editable package
pip install -e /path/to/projects/web-scrapers

# Or add to pyproject.toml
[tool.poetry.dependencies]
web-scrapers = {path = "../web-scrapers", develop = true}
```

### Public API

```python
from web_scrapers import (
    # Data models
    SignalEvent,        # Universal event envelope
    RedditPost,         # Reddit post with sentiment
    RedditComment,      # Reddit comment with sentiment
    NewsArticle,        # RSS/Atom news article
    SentimentScore,     # VADER sentiment scores

    # Scrapers
    BaseScraper,        # ABC for custom scrapers
    RedditScraper,      # Reddit API scraper
    NewsScraper,        # RSS/Atom scraper
    UniversalScraper,   # Scrape any URL (trafilatura)

    # Universal scraping utilities
    scrape_url,         # Scrape single URL → ScrapeResult
    scrape_urls,        # Scrape multiple URLs → list[ScrapeResult]

    # Analysis
    score_sentiment,    # VADER sentiment analysis

    # Symbol utilities
    get_company_names,      # Ticker → list of company names/products
    is_relevant_to_symbol,  # Check if text mentions a ticker
    get_all_symbols,        # List all known tickers

    # Query helpers (requires DATABASE_URL)
    get_latest_events,      # Get recent events
    get_events_since,       # Get events from last N hours
    get_stats,              # Database statistics
    get_subreddit_summary,  # Aggregated subreddit stats

    # Coordinator (for programmatic scraping)
    run_all,            # Run all scrapers
    run_single,         # Run single scraper by name
    run_tracked,        # Run with tracking + optional RAG ingest
    persist_events,     # Persist events to DB

    # Configuration
    Settings,           # Pydantic settings model
    get_settings,       # Factory with overrides
    settings,           # Default singleton
)
```

### Examples

```python
# Analyze sentiment without database
from web_scrapers import score_sentiment
score = score_sentiment("Bitcoin is mooning! 🚀")
print(f"Compound: {score.compound}")  # 0.7506

# Check symbol relevance (filter news by ticker)
from web_scrapers import is_relevant_to_symbol, get_company_names
is_relevant_to_symbol("Apple announces new iPhone", "AAPL")  # True
get_company_names("AAPL")  # ["Apple", "iPhone", "iPad", "Mac", "Tim Cook"]

# Create custom scraper instance
from web_scrapers import RedditScraper
scraper = RedditScraper()
events = scraper.scrape()

# Query stored events (requires DATABASE_URL in env)
from web_scrapers import get_latest_events, get_subreddit_summary
events = get_latest_events(source="reddit", limit=10)
summary = get_subreddit_summary("wallstreetbets", hours=24)

# Custom settings for another project
from web_scrapers import get_settings
custom = get_settings(database_url="postgresql://user:pass@host/db")
```

## Database

### Setup

PostgreSQL 16 must be running. The default config uses the shared `turiya_memory` database with a `web_scrapers` schema for tenant isolation.

```bash
# Initialize schema + run migrations
poetry run python -m web_scrapers.cli db init

# Load default job definitions from config/jobs.yaml
poetry run python -m web_scrapers.cli db seed-jobs
```

### Schema (3 tables in `web_scrapers` schema)

| Table | Purpose |
|---|---|
| `signal_events` | Deduplicated event store (UNIQUE on `event_id`) |
| `scrape_runs` | Execution history with status, counts, errors |
| `scrape_jobs` | Scheduled job definitions (name, scraper, cron schedule) |

### Deduplication

Events are identified by `event_id` (e.g., `reddit:abc123`, `reddit:comment:xyz789`, `news:fa3b...`). Inserts use `ON CONFLICT (event_id) DO NOTHING` for zero-cost idempotent upserts. Running the same scraper twice produces 0 new events.

### Querying

```bash
# Event stats
poetry run python -m web_scrapers.cli db stats

# Query stored events
poetry run python -m web_scrapers.cli db query --source reddit --limit 10
poetry run python -m web_scrapers.cli db query --source reddit --subreddit wallstreetbets --since 2026-03-01
poetry run python -m web_scrapers.cli db query --source news --json
```

## Job Scheduler

### Job Management

```bash
# List all configured jobs
poetry run python -m web_scrapers.cli jobs list

# Manually trigger a tracked job
poetry run python -m web_scrapers.cli jobs run reddit-financial

# Enable/disable jobs
poetry run python -m web_scrapers.cli jobs enable reddit-financial
poetry run python -m web_scrapers.cli jobs disable news-rss

# View run history
poetry run python -m web_scrapers.cli jobs history
poetry run python -m web_scrapers.cli jobs history --scraper reddit --limit 10
```

### Daemon Mode

Start a long-running scheduler that executes enabled jobs on their cron schedules:

```bash
# Run daemon (persists to DB only)
poetry run python -m web_scrapers.cli daemon

# Run daemon + ingest new events into Nexus RAG
poetry run python -m web_scrapers.cli daemon --ingest
```

### Default Jobs (`config/jobs.yaml`)

| Job | Scraper | Schedule |
|---|---|---|
| `reddit-financial` | reddit | Every 10 min (`*/10 * * * *`) |
| `news-rss` | news | Every 15 min (`*/15 * * * *`) |

## Scrapers

### Reddit Scraper

Fetches posts and comments from financial subreddits using the official Reddit API (`praw`). Includes VADER sentiment analysis on post title + body and comment text.

**Features:**

- Configurable N comments per post via `comments_limit` in config
- Comments sorted by "best" score
- Sentiment analysis on both posts and comments
- Posts stored with `event_id="reddit:{post_id}"`, comments with `event_id="reddit:comment:{comment_id}"`

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
    event_type="post",         # "post" or "comment"
    payload={...},             # RedditPost, RedditComment, or NewsArticle (dict)
    event_id="reddit:abc123",  # Unique ID for dedup
    ingested_at=datetime,      # UTC timestamp
)
```

### Reddit Models

- **RedditPost** — Post with title, selftext, score, upvote_ratio, num_comments, sentiment
- **RedditComment** — Comment with body, score, parent_id, is_top_level, depth, sentiment

## Configuration

### Environment Variables (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `postgresql://admin:password123@localhost:5432/turiya_memory` | PostgreSQL connection URL |
| `REDDIT_CLIENT_ID` | For Reddit | — | Reddit OAuth app client ID |
| `REDDIT_CLIENT_SECRET` | For Reddit | — | Reddit OAuth app secret |
| `REDDIT_USER_AGENT` | No | `web-scrapers/0.1` | Reddit API user agent |
| `MEMGRAPH_URL` | For ingestion | `bolt://localhost:7689` | Memgraph RAG connection URL |
| `SCRAPER_LOG_LEVEL` | No | `INFO` | Log level |

### YAML Configs

- `config/subreddits.yaml` — Target subreddits with sort order, limit, category, comments_limit
- `config/feeds.yaml` — RSS feed URLs with name and category
- `config/jobs.yaml` — Scheduled job definitions (name, scraper, cron, enabled)

## RAG Ingestion

When using `--ingest`, only **new** events (after deduplication) are pushed to Nexus RAG:

- **project_id:** `WEB_SCRAPERS`
- **scope:** `WEB_RESEARCH`
- **Backends:** Memgraph (graph) + pgvector (vector via PostgreSQL)

## Adding a New Scraper

1. Create model in `web_scrapers/models/your_source.py`
2. Implement `web_scrapers/scrapers/your_source.py` extending `BaseScraper`
3. Add config file `config/your_config.yaml`
4. Register in `web_scrapers/coordinator.py` → `get_all_scrapers()`
5. Add CLI subcommand in `web_scrapers/cli.py`
6. Add tests in `tests/test_your_source.py`

## Testing

```bash
poetry run pytest                              # Unit tests (no DB needed)
poetry run pytest -m integration               # Integration tests (requires PostgreSQL)
poetry run pytest --cov=web_scrapers           # With coverage
poetry run ruff check .                        # Lint check
poetry run ruff format .                       # Auto-format
```

## Tech Stack

- **Python** 3.11+
- **SQLAlchemy 2.0** — ORM + database layer (sync)
- **psycopg2** — PostgreSQL driver
- **Alembic** — Database migrations
- **APScheduler 3.x** — Cron-based job scheduling
- **praw** — Reddit API client
- **feedparser** — RSS/Atom parsing
- **httpx** — HTTP client
- **Pydantic v2** — Data validation
- **vaderSentiment** — Sentiment analysis
- **typer** — CLI framework
- **loguru** — Structured logging
- **Poetry** — Package management

## Future (Phase 3)

- **YouTube Transcript Scraper** — `youtube-transcript-api` for financial channel transcripts
- **Twitter/X Scraper** — `tweepy` or `snscrape` for market-moving tweets
- **SEC EDGAR Scraper** — 8-K filings (reference: `~/.openclaw/workspace/projects/sentinel/sec_scraper.py`)
- **pgvector embeddings** — Store embeddings in PostgreSQL alongside events
- **Grafana dashboards** — Visualize scrape stats and event trends
