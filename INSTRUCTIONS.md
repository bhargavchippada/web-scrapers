# INSTRUCTIONS — Web Scrapers

> Version: v0.2.0 | Agent: Ari | Project: Nexus

## Operations

### Install

```bash
cd projects/web-scrapers
poetry install
```

### Configure

```bash
cp .env.example .env
# Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
# Get credentials: https://www.reddit.com/prefs/apps (create a "script" type app)
# DATABASE_URL defaults to postgresql://admin:password123@localhost:5432/turiya_memory
```

### Database Setup

```bash
# Ensure PostgreSQL is running (turiya-postgres container via mcp-nexus-rag/docker-compose.yml)
docker ps | grep postgres

# Initialize schema + run Alembic migrations
poetry run python -m web_scrapers.cli db init

# Load default job definitions from config/jobs.yaml
poetry run python -m web_scrapers.cli db seed-jobs
```

### Run Scrapers

```bash
# Individual scrapers (auto-persist to DB)
poetry run python -m web_scrapers.cli scrape reddit
poetry run python -m web_scrapers.cli scrape news

# Skip DB persistence
poetry run python -m web_scrapers.cli scrape reddit --no-persist

# All scrapers
poetry run python -m web_scrapers.cli run-all

# With JSON output
poetry run python -m web_scrapers.cli scrape news --json

# With RAG ingestion (requires Neo4j + Qdrant running)
poetry run python -m web_scrapers.cli run-all --ingest

# Health check (scrapers + DB connectivity)
poetry run python -m web_scrapers.cli health
```

### Query Database

```bash
# Event statistics
poetry run python -m web_scrapers.cli db stats

# Query events by source
poetry run python -m web_scrapers.cli db query --source reddit --limit 20

# Filter by subreddit and date range
poetry run python -m web_scrapers.cli db query --source reddit --subreddit wallstreetbets --since 2026-03-01

# Filter by news feed
poetry run python -m web_scrapers.cli db query --source news --feed "Reuters Business"

# JSON output for piping
poetry run python -m web_scrapers.cli db query --source news --json
```

### Manage Jobs

```bash
# List configured jobs
poetry run python -m web_scrapers.cli jobs list

# Manually trigger a tracked job run
poetry run python -m web_scrapers.cli jobs run reddit-financial
poetry run python -m web_scrapers.cli jobs run news-rss --ingest

# Enable/disable jobs
poetry run python -m web_scrapers.cli jobs enable reddit-financial
poetry run python -m web_scrapers.cli jobs disable news-rss

# View run history
poetry run python -m web_scrapers.cli jobs history
poetry run python -m web_scrapers.cli jobs history --scraper reddit --limit 10
```

### Daemon Mode

```bash
# Start scheduler — runs enabled jobs on their cron schedule
poetry run python -m web_scrapers.cli daemon

# With RAG ingestion of new events
poetry run python -m web_scrapers.cli daemon --ingest

# Stop: Ctrl+C (graceful SIGINT shutdown)
```

### Database Migrations

```bash
# Run pending migrations
cd projects/web-scrapers
poetry run alembic upgrade head

# Generate a new migration after model changes
poetry run alembic revision --autogenerate -m "description of change"

# View migration history
poetry run alembic history
```

### Run Tests

```bash
poetry run pytest                              # Unit tests only
poetry run pytest -m integration               # Integration tests (requires PostgreSQL)
poetry run pytest --cov=web_scrapers --cov-report=term-missing
```

### Lint

```bash
poetry run ruff check .
poetry run ruff format .
```

## Troubleshooting

### Database Connection Refused

- Ensure PostgreSQL is running: `docker ps | grep postgres`
- Verify `DATABASE_URL` in `.env` matches the running instance
- Default: `postgresql://admin:password123@localhost:5432/turiya_memory`
- Start the container: `cd projects/mcp-nexus-rag && docker-compose up -d`

### Alembic Migration Errors

- Ensure the `web_scrapers` schema exists: `poetry run python -m web_scrapers.cli db init`
- Check current revision: `poetry run alembic current`
- Reset if needed: `poetry run alembic downgrade base && poetry run alembic upgrade head`

### Reddit API 401/403

- Verify `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in `.env`
- Ensure the Reddit app type is "script" (not "web" or "installed")
- Check rate limits: Reddit allows ~60 requests/minute

### RSS Feed Timeouts

- Some feeds (Bloomberg, Investing.com) may block automated requests
- Check feed URL in browser first
- Adjust timeout in `web_scrapers/scrapers/news.py` (`_TIMEOUT`)

### Nexus RAG Ingestion Fails

- Ensure Neo4j is running: `docker ps | grep neo4j`
- Ensure Qdrant is running: `docker ps | grep qdrant`
- Ensure mcp-nexus-rag exists at `projects/mcp-nexus-rag/`

## Adding Subreddits

Edit `config/subreddits.yaml`:

```yaml
subreddits:
  - name: your_subreddit
    sort: new          # new, hot, top, rising
    limit: 25          # Posts per scrape
    category: your_cat # For metadata tagging
```

## Adding RSS Feeds

Edit `config/feeds.yaml`:

```yaml
feeds:
  - name: Your Feed Name
    url: https://example.com/rss
    category: markets
```

## Adding Scheduled Jobs

Edit `config/jobs.yaml`:

```yaml
jobs:
  - name: my-custom-job
    scraper: reddit       # Must match a registered scraper name
    schedule: "0 */2 * * *"  # Cron expression (every 2 hours)
    enabled: true
    config: {}            # Scraper-specific overrides (future)
```

Then reload: `poetry run python -m web_scrapers.cli db seed-jobs`

## Project Structure

```
web_scrapers/
├── __init__.py         # Package version
├── config.py           # Settings (env vars + YAML loading)
├── cli.py              # Typer CLI (scrape, db, jobs, daemon)
├── coordinator.py      # Scraper orchestration + persistence
├── models/             # Pydantic data models
│   ├── base.py         # SignalEvent envelope
│   ├── reddit.py       # RedditPost + SentimentScore
│   └── news.py         # NewsArticle
├── scrapers/           # Scraper implementations
│   ├── base.py         # BaseScraper ABC
│   ├── reddit.py       # Reddit scraper (praw)
│   └── news.py         # News/RSS scraper (feedparser)
├── db/                 # Database layer
│   ├── engine.py       # Engine + session factory
│   ├── models.py       # SQLAlchemy 2.0 ORM models (3 tables)
│   ├── repository.py   # EventRepo, RunRepo, JobRepo (DAO)
│   └── queries.py      # High-level query helpers
├── scheduler/          # Job scheduling
│   └── scheduler.py    # APScheduler daemon
├── analysis/
│   └── sentiment.py    # VADER sentiment scoring
└── bridge/
    └── nexus.py        # Nexus RAG ingestion bridge

config/
├── subreddits.yaml     # Target subreddits
├── feeds.yaml          # RSS feed URLs
└── jobs.yaml           # Scheduled job definitions

alembic/                # Database migrations
├── env.py
└── versions/
    └── 001_initial_schema.py
```

## Maintenance Commands

```bash
# Update dependencies
poetry update

# Check for security vulnerabilities
poetry run pip-audit

# Full test + lint cycle
poetry run pytest && poetry run ruff check .

# Database stats
poetry run python -m web_scrapers.cli db stats

# Recent run history
poetry run python -m web_scrapers.cli jobs history
```
