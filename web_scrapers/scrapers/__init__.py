# Version: v0.1.0
"""Scraper implementations."""

from web_scrapers.scrapers.base import BaseScraper
from web_scrapers.scrapers.news import NewsScraper
from web_scrapers.scrapers.reddit import RedditScraper

__all__ = ["BaseScraper", "NewsScraper", "RedditScraper"]
