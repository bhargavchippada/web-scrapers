# Version: v0.2.0
"""Reddit scraper — fetches posts from configured subreddits with sentiment analysis."""

from __future__ import annotations

from datetime import UTC, datetime

import praw
from loguru import logger
from praw.models import Comment, MoreComments, Submission

from web_scrapers.analysis.sentiment import score_sentiment
from web_scrapers.config import get_subreddit_targets, settings
from web_scrapers.models.base import SignalEvent
from web_scrapers.models.reddit import RedditComment, RedditPost
from web_scrapers.scrapers.base import BaseScraper

_ALLOWED_SORTS = frozenset({"new", "hot", "top", "rising", "controversial"})


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


def _parse_comment(
    comment: Comment, post_id: str, subreddit_name: str, depth: int = 0
) -> RedditComment:
    """Parse a PRAW comment into a RedditComment model."""
    parent_id = comment.parent_id
    is_top_level = parent_id.startswith("t3_")
    return RedditComment(
        id=comment.id,
        post_id=post_id,
        subreddit=subreddit_name,
        body=comment.body or "",
        author=getattr(comment.author, "name", None) if comment.author else None,
        score=comment.score,
        created_utc=datetime.fromtimestamp(comment.created_utc, tz=UTC),
        parent_id=parent_id,
        is_top_level=is_top_level,
        depth=depth,
        permalink=f"https://reddit.com{comment.permalink}",
        sentiment=score_sentiment(comment.body or ""),
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
            comments_limit = target.get("comments_limit", 0)

            logger.info(
                "Scraping r/{} (sort={}, limit={}, comments_limit={})",
                sub_name,
                sort,
                limit,
                comments_limit,
            )
            try:
                events.extend(self._scrape_subreddit(client, sub_name, sort, limit, comments_limit))
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
        comments_limit: int = 0,
    ) -> list[SignalEvent]:
        if sort not in _ALLOWED_SORTS:
            raise ValueError(f"Invalid sort method '{sort}'. Allowed: {sorted(_ALLOWED_SORTS)}")
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

                if comments_limit > 0:
                    comment_events = self._scrape_post_comments(
                        submission, subreddit_name, comments_limit
                    )
                    events.extend(comment_events)
            except Exception:
                logger.exception("Failed to parse submission {}", submission.id)

        return events

    def _scrape_post_comments(
        self,
        submission: Submission,
        subreddit_name: str,
        limit: int,
    ) -> list[SignalEvent]:
        """Fetch top N comments from a post, sorted by score."""
        if limit <= 0:
            return []

        events: list[SignalEvent] = []
        submission.comment_sort = "best"
        submission.comments.replace_more(limit=0)

        count = 0
        for comment in submission.comments:
            if isinstance(comment, MoreComments):
                continue
            if count >= limit:
                break
            try:
                parsed = _parse_comment(comment, submission.id, subreddit_name, depth=0)
                event = SignalEvent(
                    source="reddit",
                    event_type="comment",
                    payload=parsed.model_dump(mode="json"),
                    event_id=f"reddit:comment:{parsed.id}",
                )
                events.append(event)
                count += 1
                logger.debug(
                    "reddit | r/{} | comment:{} | compound={:.3f}",
                    subreddit_name,
                    parsed.id,
                    parsed.sentiment.compound,
                )
            except Exception:
                logger.exception("Failed to parse comment {}", comment.id)

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
