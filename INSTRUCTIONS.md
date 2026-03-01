# INSTRUCTIONS — Web Scrapers

> Version: v0.1.0 | Agent: Ari | Project: Nexus

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
```

### Run Scrapers

```bash
# Individual scrapers
poetry run python -m web_scrapers.cli scrape reddit
poetry run python -m web_scrapers.cli scrape news

# All scrapers
poetry run python -m web_scrapers.cli run-all

# With JSON output
poetry run python -m web_scrapers.cli scrape news --json

# With RAG ingestion (requires Neo4j + Qdrant running)
poetry run python -m web_scrapers.cli run-all --ingest

# Health check
poetry run python -m web_scrapers.cli health
```

### Run Tests

```bash
poetry run pytest
poetry run pytest --cov=web_scrapers --cov-report=term-missing
```

### Lint

```bash
poetry run ruff check .
poetry run ruff format .
```

## Troubleshooting

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

## Project Structure

```
web_scrapers/
├── config.py           # Settings (env vars + YAML loading)
├── cli.py              # Typer CLI
├── coordinator.py      # Scraper orchestration
├── models/             # Pydantic data models
│   ├── base.py         # SignalEvent envelope
│   ├── reddit.py       # RedditPost + SentimentScore
│   └── news.py         # NewsArticle
├── scrapers/           # Scraper implementations
│   ├── base.py         # BaseScraper ABC
│   ├── reddit.py       # Reddit scraper (praw)
│   └── news.py         # News/RSS scraper (feedparser)
├── analysis/
│   └── sentiment.py    # VADER sentiment scoring
└── bridge/
    └── nexus.py        # Nexus RAG ingestion bridge
```

## Maintenance Commands

```bash
# Update dependencies
poetry update

# Check for security vulnerabilities
poetry run pip-audit

# Full test + lint cycle
poetry run pytest && poetry run ruff check .
```
