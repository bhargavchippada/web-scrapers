# AGENTS.md — Web Scrapers

<!-- Commands for AI agents: testing, building, running -->

**Version:** v1.6

## Setup

```bash
poetry install
cp .env.example .env
# Edit .env with Reddit API credentials + DATABASE_URL

poetry run python -m web_scrapers.cli db init
poetry run python -m web_scrapers.cli db seed-jobs
```

## Run

```bash
# Individual scrapers
poetry run python -m web_scrapers.cli scrape reddit
poetry run python -m web_scrapers.cli scrape news

# All scrapers
poetry run python -m web_scrapers.cli run-all
poetry run python -m web_scrapers.cli run-all --ingest    # + RAG ingestion

# Daemon mode (APScheduler cron)
poetry run python -m web_scrapers.cli daemon
poetry run python -m web_scrapers.cli daemon --ingest
nohup poetry run python -m web_scrapers.cli daemon --ingest > logs/daemon.log 2>&1 &

# Health check
poetry run python -m web_scrapers.cli health
```

## Test

```bash
poetry run pytest                                              # All tests (205 total)
poetry run pytest -m integration                               # Integration tests (requires PostgreSQL)
poetry run pytest --cov=web_scrapers --cov-report=term-missing # With coverage
```

## Lint

```bash
poetry run ruff check .
poetry run ruff check . --fix
poetry run ruff format .
```

## Database

```bash
# Migrations
poetry run alembic upgrade head
poetry run alembic history

# Stats and queries
poetry run python -m web_scrapers.cli db stats
poetry run python -m web_scrapers.cli db query --source reddit --limit 10
poetry run python -m web_scrapers.cli db query --source news --json
poetry run python -m web_scrapers.cli db query --source reddit --subreddit wallstreetbets --since 2026-03-01
```

## Jobs

```bash
poetry run python -m web_scrapers.cli jobs list
poetry run python -m web_scrapers.cli jobs run reddit-financial
poetry run python -m web_scrapers.cli jobs enable reddit-financial
poetry run python -m web_scrapers.cli jobs disable news-rss
poetry run python -m web_scrapers.cli jobs history --scraper reddit --limit 10
```
