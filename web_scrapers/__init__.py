# Version: v0.4.0
"""Web Scrapers — Modular financial intelligence gathering toolkit.

This package provides tools for scraping financial data from Reddit, news RSS feeds,
and other sources. Data is persisted to PostgreSQL with deduplication.

Library Usage (from other projects):

    # Install as editable package
    pip install -e /path/to/web-scrapers

    # Import models and utilities
    from web_scrapers import (
        # Data models
        SignalEvent, RedditPost, RedditComment, NewsArticle, SentimentScore,

        # Scrapers
        BaseScraper, RedditScraper, NewsScraper,

        # Analysis
        score_sentiment,

        # Query helpers (requires DB connection)
        get_latest_events, get_events_since, get_stats,

        # Configuration
        Settings, get_settings,
    )

    # Create custom scraper instance
    scraper = RedditScraper()
    events = scraper.scrape()

    # Analyze sentiment
    score = score_sentiment("Bitcoin is mooning!")

    # Query stored events (requires DATABASE_URL)
    events = get_latest_events(source="reddit", limit=10)
"""

__version__ = "0.4.0"

# Core models
# Analysis utilities
from web_scrapers.analysis import score_sentiment

# Configuration
from web_scrapers.config import Settings, get_settings, settings

# Coordinator functions (for programmatic scraping)
from web_scrapers.coordinator import (
    persist_events,
    run_all,
    run_single,
    run_tracked,
)

# Query helpers (for accessing stored data)
from web_scrapers.db.queries import (
    get_events_since,
    get_latest_events,
    get_stats,
    get_subreddit_summary,
)
from web_scrapers.models import (
    NewsArticle,
    RedditComment,
    RedditPost,
    SentimentScore,
    SignalEvent,
)

# Scrapers
from web_scrapers.scrapers import BaseScraper, NewsScraper, RedditScraper

__all__ = [
    # Version
    "__version__",
    # Models
    "NewsArticle",
    "RedditComment",
    "RedditPost",
    "SentimentScore",
    "SignalEvent",
    # Scrapers
    "BaseScraper",
    "NewsScraper",
    "RedditScraper",
    # Analysis
    "score_sentiment",
    # Coordinator
    "persist_events",
    "run_all",
    "run_single",
    "run_tracked",
    # Query helpers
    "get_events_since",
    "get_latest_events",
    "get_stats",
    "get_subreddit_summary",
    # Configuration
    "Settings",
    "get_settings",
    "settings",
]
