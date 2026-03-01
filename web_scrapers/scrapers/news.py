# Version: v0.1.0
"""News/RSS scraper — fetches articles from configured RSS/Atom feeds."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from time import mktime, struct_time
from typing import Any

import feedparser
import httpx
from loguru import logger

from web_scrapers.config import get_feed_targets
from web_scrapers.models.base import SignalEvent
from web_scrapers.models.news import NewsArticle
from web_scrapers.scrapers.base import BaseScraper

_USER_AGENT = "web-scrapers/0.1 (financial-intelligence)"
_TIMEOUT = 30.0


def _parse_published(entry: Any) -> datetime | None:
    """Extract published datetime from a feed entry."""
    published_parsed = getattr(entry, "published_parsed", None)
    if not isinstance(published_parsed, struct_time):
        return None
    try:
        return datetime.fromtimestamp(mktime(published_parsed), tz=UTC)
    except (ValueError, OSError, OverflowError):
        return None


def _entry_id(entry: Any, feed_name: str) -> str:
    """Generate a stable ID for a feed entry."""
    raw_id = str(getattr(entry, "id", "") or getattr(entry, "link", ""))
    if raw_id:
        return hashlib.sha256(raw_id.encode()).hexdigest()[:16]
    title = str(getattr(entry, "title", ""))
    return hashlib.sha256(f"{feed_name}:{title}".encode()).hexdigest()[:16]


def _parse_entry(entry: Any, feed_name: str, category: str) -> NewsArticle:
    """Parse a feedparser entry into a NewsArticle."""
    return NewsArticle(
        id=_entry_id(entry, feed_name),
        feed_name=feed_name,
        title=getattr(entry, "title", ""),
        summary=getattr(entry, "summary", ""),
        link=getattr(entry, "link", ""),
        author=getattr(entry, "author", None),
        published=_parse_published(entry),
        category=category,
    )


class NewsScraper(BaseScraper):
    """Scrapes news articles from configured RSS/Atom feeds."""

    @property
    def name(self) -> str:
        return "news"

    def scrape(self) -> list[SignalEvent]:
        targets = get_feed_targets()
        if not targets:
            logger.warning("No feed targets configured")
            return []

        events: list[SignalEvent] = []

        for target in targets:
            feed_name = target["name"]
            url = target["url"]
            category = target.get("category", "")

            logger.info("Fetching feed: {} ({})", feed_name, url)
            try:
                events.extend(self._scrape_feed(feed_name, url, category))
            except Exception:
                logger.exception("Failed to fetch feed: {}", feed_name)

        logger.info("News scraper finished: {} events collected", len(events))
        return events

    def _scrape_feed(
        self, feed_name: str, url: str, category: str
    ) -> list[SignalEvent]:
        with httpx.Client(
            headers={"User-Agent": _USER_AGENT},
            timeout=_TIMEOUT,
            follow_redirects=True,
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        events: list[SignalEvent] = []

        for entry in feed.entries:
            try:
                article = _parse_entry(entry, feed_name, category)
                event = SignalEvent(
                    source="news",
                    event_type="article",
                    payload=article.model_dump(mode="json"),
                    event_id=f"news:{article.id}",
                )
                logger.debug("news | {} | {}", feed_name, article.title[:80])
                events.append(event)
            except Exception:
                logger.exception("Failed to parse entry from {}", feed_name)

        return events

    def health_check(self) -> bool:
        targets = get_feed_targets()
        if not targets:
            return False
        url = targets[0]["url"]
        try:
            with httpx.Client(
                headers={"User-Agent": _USER_AGENT},
                timeout=10.0,
                follow_redirects=True,
            ) as client:
                resp = client.get(url)
                return resp.status_code == 200
        except Exception:
            logger.exception("News health check failed")
            return False
