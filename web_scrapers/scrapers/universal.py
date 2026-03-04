# Version: v0.1.0
"""Universal web scraper — extracts structured content from any URL.

Uses trafilatura for intelligent text extraction with metadata.
Supports any website, blog, article, or social media page.
"""

from __future__ import annotations

import hashlib
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import trafilatura
from loguru import logger
from trafilatura.settings import use_config

from web_scrapers.models.base import SignalEvent
from web_scrapers.models.web import ScrapedContent, ScrapeResult
from web_scrapers.scrapers.base import BaseScraper

# Configure trafilatura for best extraction
_TRAFILATURA_CONFIG = use_config()
_TRAFILATURA_CONFIG.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")


def _generate_event_id(url: str) -> str:
    """Generate a stable event ID from URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _parse_date(date_str: str | None) -> datetime | None:
    """Parse date string from trafilatura."""
    if not date_str:
        return None
    try:
        # trafilatura returns dates in YYYY-MM-DD format
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return None


def _parse_tags(tags_str: str | None) -> list[str]:
    """Parse comma-separated tags string."""
    if not tags_str:
        return []
    return [tag.strip() for tag in tags_str.split(",") if tag.strip()]


def _parse_categories(categories_str: str | None) -> list[str]:
    """Parse comma-separated categories string."""
    if not categories_str:
        return []
    return [cat.strip() for cat in categories_str.split(",") if cat.strip()]


class UniversalScraper(BaseScraper):
    """Scrapes structured content from any URL using trafilatura.

    Features:
    - Intelligent main content extraction
    - Metadata extraction (title, author, date, etc.)
    - Handles JavaScript-rendered pages (basic support)
    - Works with any website, blog, or article

    Example:
        scraper = UniversalScraper()
        result = scraper.extract("https://example.com/article")
        print(result.content.title)
        print(result.content.text)
    """

    def __init__(
        self,
        urls: list[str] | None = None,
        include_comments: bool = False,
        include_tables: bool = True,
        include_links: bool = False,
        include_images: bool = False,
        output_format: str = "text",
        favor_recall: bool = False,
    ):
        """Initialize the universal scraper.

        Args:
            urls: List of URLs to scrape (for batch mode)
            include_comments: Extract comments section
            include_tables: Extract tables as text
            include_links: Include links in output
            include_images: Include image references
            output_format: Output format (text, markdown, xml, html)
            favor_recall: Favor recall over precision (more content)
        """
        self.urls = urls or []
        self.include_comments = include_comments
        self.include_tables = include_tables
        self.include_links = include_links
        self.include_images = include_images
        self.output_format = output_format
        self.favor_recall = favor_recall

    @property
    def name(self) -> str:
        return "universal"

    def extract(self, url: str, raw_html: str | None = None) -> ScrapeResult:
        """Extract structured content from a single URL.

        Args:
            url: The URL to scrape
            raw_html: Optional pre-fetched HTML content

        Returns:
            ScrapeResult with success status and extracted content
        """
        start_time = time.time()

        try:
            # Fetch HTML if not provided
            if raw_html is None:
                logger.debug("Fetching URL: {}", url)
                downloaded = trafilatura.fetch_url(url)
                if not downloaded:
                    return ScrapeResult(
                        success=False,
                        url=url,
                        error="Failed to fetch URL",
                        duration_ms=(time.time() - start_time) * 1000,
                    )
            else:
                downloaded = raw_html

            # Extract main content
            logger.debug("Extracting content from: {}", url)
            text = trafilatura.extract(
                downloaded,
                include_comments=self.include_comments,
                include_tables=self.include_tables,
                include_links=self.include_links,
                include_images=self.include_images,
                favor_recall=self.favor_recall,
                output_format=self.output_format if self.output_format != "text" else None,
                config=_TRAFILATURA_CONFIG,
            )

            if not text:
                return ScrapeResult(
                    success=False,
                    url=url,
                    error="No content extracted",
                    duration_ms=(time.time() - start_time) * 1000,
                )

            # Extract metadata
            metadata = trafilatura.extract_metadata(downloaded)

            # Build structured content
            content = ScrapedContent(
                url=url,
                title=metadata.title if metadata else None,
                author=metadata.author if metadata else None,
                date=_parse_date(metadata.date if metadata else None),
                text=text,
                description=metadata.description if metadata else None,
                sitename=metadata.sitename if metadata else None,
                categories=_parse_categories(metadata.categories if metadata else None),
                tags=_parse_tags(metadata.tags if metadata else None),
                license=metadata.license if metadata else None,
                raw_html=downloaded if self.output_format == "html" else None,
                metadata=self._build_metadata(url, metadata),
            )

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "Extracted {} words from {} in {:.0f}ms",
                content.word_count,
                url,
                duration_ms,
            )

            return ScrapeResult(
                success=True,
                url=url,
                content=content,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.exception("Failed to extract content from: {}", url)
            return ScrapeResult(
                success=False,
                url=url,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

    def _build_metadata(self, url: str, metadata: Any) -> dict[str, Any]:
        """Build metadata dict from trafilatura metadata."""
        parsed = urlparse(url)
        result = {
            "domain": parsed.netloc,
            "scheme": parsed.scheme,
            "path": parsed.path,
        }

        if metadata:
            if metadata.url:
                result["canonical_url"] = metadata.url
            if metadata.hostname:
                result["hostname"] = metadata.hostname
            if metadata.pagetype:
                result["page_type"] = metadata.pagetype

        return result

    def scrape(self) -> list[SignalEvent]:
        """Scrape all configured URLs and return SignalEvents.

        This method implements the BaseScraper interface for batch scraping.
        """
        if not self.urls:
            logger.warning("No URLs configured for scraping")
            return []

        events: list[SignalEvent] = []

        for url in self.urls:
            result = self.extract(url)
            if result.success and result.content:
                event = SignalEvent(
                    source="web",
                    event_type="article",
                    payload=result.content.model_dump(mode="json"),
                    event_id=f"web:{_generate_event_id(url)}",
                )
                events.append(event)

        logger.info("Universal scraper finished: {} events collected", len(events))
        return events

    def health_check(self) -> bool:
        """Check if the scraper can fetch a test URL."""
        try:
            result = self.extract("https://example.com")
            return result.success
        except Exception:
            logger.exception("Universal scraper health check failed")
            return False


def scrape_url(
    url: str,
    include_comments: bool = False,
    include_tables: bool = True,
    output_format: str = "text",
) -> ScrapeResult:
    """Convenience function to scrape a single URL.

    Args:
        url: The URL to scrape
        include_comments: Extract comments section
        include_tables: Extract tables as text
        output_format: Output format (text, markdown, xml, html)

    Returns:
        ScrapeResult with extracted content

    Example:
        result = scrape_url("https://news.ycombinator.com")
        if result.success:
            print(result.content.title)
            print(result.content.text)
    """
    scraper = UniversalScraper(
        include_comments=include_comments,
        include_tables=include_tables,
        output_format=output_format,
    )
    return scraper.extract(url)


def scrape_urls(urls: list[str], **kwargs) -> list[ScrapeResult]:
    """Scrape multiple URLs and return results.

    Args:
        urls: List of URLs to scrape
        **kwargs: Additional arguments for UniversalScraper

    Returns:
        List of ScrapeResult objects
    """
    scraper = UniversalScraper(**kwargs)
    return [scraper.extract(url) for url in urls]
