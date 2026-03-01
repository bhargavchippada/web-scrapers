# Version: v0.1.0
"""Base scraper interface — all scrapers implement this ABC."""

from __future__ import annotations

from abc import ABC, abstractmethod

from web_scrapers.models.base import SignalEvent


class BaseScraper(ABC):
    """Abstract base for all data scrapers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable scraper name."""

    @abstractmethod
    def scrape(self) -> list[SignalEvent]:
        """Execute the scraper and return a list of signal events."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the data source is reachable."""
