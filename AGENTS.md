# AGENTS.md — Web Scrapers

<!-- Commands for AI agents: testing, building, running -->

## Setup

```bash
poetry install
cp .env.example .env

# Initialize database
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

# With RAG ingestion
poetry run python -m web_scrapers.cli run-all --ingest

# Daemon mode (scheduler)
poetry run python -m web_scrapers.cli daemon
poetry run python -m web_scrapers.cli daemon --ingest

# Health check
poetry run python -m web_scrapers.cli health
```

## Test

```bash
poetry run pytest                                             # Unit tests
poetry run pytest -m integration                              # Integration tests
poetry run pytest --cov=web_scrapers --cov-report=term-missing
```

## Lint

```bash
poetry run ruff check .
poetry run ruff format .
```

## Database

```bash
# Migrations
poetry run alembic upgrade head
poetry run alembic history

# Stats and queries
poetry run python -m web_scrapers.cli db stats
poetry run python -m web_scrapers.cli jobs list
poetry run python -m web_scrapers.cli jobs history
```
