# Version: v0.6.0
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
        BaseScraper, RedditScraper, NewsScraper, UniversalScraper,

        # Universal scraping utilities
        scrape_url, scrape_urls,

        # Analysis
        score_sentiment,

        # Symbol utilities (for filtering by stock ticker)
        get_company_names, is_relevant_to_symbol, get_all_symbols,

        # Query helpers (requires DB connection)
        get_latest_events, get_events_since, get_stats,

        # Configuration
        Settings, get_settings,
    )

    # Create custom scraper instance
    scraper = RedditScraper()
    events = scraper.scrape()

    # Scrape any URL (no API key needed)
    result = scrape_url("https://example.com/article")
    if result.success:
        print(result.content.title, result.content.text)

    # Analyze sentiment
    score = score_sentiment("Bitcoin is mooning!")

    # Check symbol relevance
    is_relevant_to_symbol("Apple announces new iPhone", "AAPL")  # True

    # Query stored events (requires DATABASE_URL)
    events = get_latest_events(source="reddit", limit=10)
"""

__version__ = "0.6.0"

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

# Universal scraper (scrape any URL)
from web_scrapers.scrapers.universal import UniversalScraper, scrape_url, scrape_urls

# Symbol utilities (for filtering by stock ticker)
from web_scrapers.utils.symbol_mapping import (
    get_all_symbols,
    get_company_names,
    is_relevant_to_symbol,
)

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
    "UniversalScraper",
    # Universal scraping utilities
    "scrape_url",
    "scrape_urls",
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
    # Symbol utilities
    "get_company_names",
    "is_relevant_to_symbol",
    "get_all_symbols",
]
