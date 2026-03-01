# Version: v0.1.0
"""Reddit scraper — fetches posts from configured subreddits with sentiment analysis."""

from __future__ import annotations

from datetime import UTC, datetime

import praw
from loguru import logger
from praw.models import Submission

from web_scrapers.analysis.sentiment import score_sentiment
from web_scrapers.config import get_subreddit_targets, settings
from web_scrapers.models.base import SignalEvent
from web_scrapers.models.reddit import RedditPost
from web_scrapers.scrapers.base import BaseScraper


def _build_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )


def _parse_submission(submission: Submission, subreddit_name: str) -> RedditPost:
    text = f"{submission.title} {submission.selftext}"
    return RedditPost(
        id=submission.id,
        subreddit=subreddit_name,
        title=submission.title,
        selftext=submission.selftext or "",
        author=getattr(submission.author, "name", None) if submission.author else None,
        score=submission.score,
        upvote_ratio=submission.upvote_ratio,
        num_comments=submission.num_comments,
        created_utc=datetime.fromtimestamp(submission.created_utc, tz=UTC),
        url=f"https://reddit.com{submission.permalink}",
        flair=submission.link_flair_text,
        sentiment=score_sentiment(text),
    )


class RedditScraper(BaseScraper):
    """Scrapes Reddit posts from configured subreddits."""

    @property
    def name(self) -> str:
        return "reddit"

    def __init__(self, client: praw.Reddit | None = None) -> None:
        self._client = client

    def _get_client(self) -> praw.Reddit:
        if self._client is None:
            self._client = _build_client()
        return self._client

    def scrape(self) -> list[SignalEvent]:
        targets = get_subreddit_targets()
        if not targets:
            logger.warning("No subreddit targets configured")
            return []

        client = self._get_client()
        events: list[SignalEvent] = []

        for target in targets:
            sub_name = target["name"]
            sort = target.get("sort", "new")
            limit = target.get("limit", 25)

            logger.info("Scraping r/{} (sort={}, limit={})", sub_name, sort, limit)
            try:
                events.extend(self._scrape_subreddit(client, sub_name, sort, limit))
            except Exception:
                logger.exception("Failed to scrape r/{}", sub_name)

        logger.info("Reddit scraper finished: {} events collected", len(events))
        return events

    def _scrape_subreddit(
        self,
        client: praw.Reddit,
        subreddit_name: str,
        sort: str,
        limit: int,
    ) -> list[SignalEvent]:
        subreddit = client.subreddit(subreddit_name)
        listing = getattr(subreddit, sort)(limit=limit)
        events: list[SignalEvent] = []

        for submission in listing:
            try:
                post = _parse_submission(submission, subreddit_name)
                event = SignalEvent(
                    source="reddit",
                    event_type="post",
                    payload=post.model_dump(mode="json"),
                    event_id=f"reddit:{post.id}",
                )
                logger.debug(
                    "reddit | r/{} | {} | compound={:.3f}",
                    subreddit_name,
                    post.id,
                    post.sentiment.compound,
                )
                events.append(event)
            except Exception:
                logger.exception("Failed to parse submission {}", submission.id)

        return events

    def health_check(self) -> bool:
        try:
            client = self._get_client()
            sub = client.subreddit("test")
            _ = sub.display_name
            return True
        except Exception:
            logger.exception("Reddit health check failed")
            return False
