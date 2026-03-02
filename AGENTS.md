# AGENTS.md — Web Scrapers

<!-- Commands for AI agents: testing, building, running -->

**Version:** v1.3

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

## Daemon Mode

The daemon runs APScheduler with cron-based jobs defined in `config/jobs.yaml`:

| Job | Schedule | Description |
|-----|----------|-------------|
| `reddit-financial` | `*/10 * * * *` | Scrape Reddit posts + comments every 10 mins |
| `news-rss` | `*/15 * * * *` | Scrape RSS feeds every 15 mins |

### Running the Daemon

```bash
# Start daemon (foreground)
poetry run python -m web_scrapers.cli daemon

# Start daemon with RAG ingestion
poetry run python -m web_scrapers.cli daemon --ingest

# Run in background with nohup
nohup poetry run python -m web_scrapers.cli daemon --ingest > logs/daemon.log 2>&1 &
```

### Systemd Service (Optional)

Create `/etc/systemd/user/web-scrapers.service`:

```ini
[Unit]
Description=Web Scrapers Daemon
After=postgresql.service

[Service]
Type=simple
WorkingDirectory=/home/turiya/antigravity/projects/web-scrapers
ExecStart=/home/turiya/.local/bin/poetry run python -m web_scrapers.cli daemon --ingest
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
# Enable and start
systemctl --user daemon-reload
systemctl --user enable web-scrapers
systemctl --user start web-scrapers

# Check status
systemctl --user status web-scrapers
journalctl --user -u web-scrapers -f
```

## Library Usage (from Other Projects)

```bash
# Install as editable dependency
pip install -e /path/to/projects/web-scrapers

# Verify imports work
python -c "from web_scrapers import RedditScraper, score_sentiment, __version__; print(f'OK: {__version__}')"
```

```python
# Import in your project
from web_scrapers import (
    SignalEvent, RedditPost, NewsArticle,  # Models
    RedditScraper, NewsScraper,             # Scrapers
    score_sentiment,                         # Analysis
    get_latest_events, get_stats,           # Query helpers
    get_settings,                            # Configuration
)
```

## Mission Control UI

View scraped Reddit posts in the Mission Control dashboard:

1. Start mission-control: `cd projects/mission-control && npm run dev`
2. Navigate to `/reddit` in the dashboard
3. Filter by post/comment type or subreddit
4. View sentiment analysis scores for each item
