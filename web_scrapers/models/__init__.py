# Version: v0.3.0
"""Pydantic models for scraped data."""

from web_scrapers.models.base import SignalEvent
from web_scrapers.models.news import NewsArticle
from web_scrapers.models.reddit import RedditComment, RedditPost, SentimentScore
from web_scrapers.models.web import ScrapedContent, ScrapeResult

__all__ = [
    "NewsArticle",
    "RedditComment",
    "RedditPost",
    "ScrapedContent",
    "ScrapeResult",
    "SentimentScore",
    "SignalEvent",
]
