# Version: v0.2.0
"""Tests for the Typer CLI commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from web_scrapers.cli import app
from web_scrapers.models.base import SignalEvent

runner = CliRunner()


def _make_event(source: str = "test", event_id: str = "t:1") -> SignalEvent:
    return SignalEvent(
        source=source, event_type="test", payload={"key": "value"}, event_id=event_id
    )


def _mock_db_health():
    """Context manager to mock DB health check in the health command."""
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    mock_engine.connect.return_value = mock_ctx
    return patch("web_scrapers.db.engine.get_engine", return_value=mock_engine)


class TestScrapeReddit:
    @patch("web_scrapers.coordinator.run_single")
    def test_scrape_reddit_summary(self, mock_run: MagicMock) -> None:
        mock_run.return_value = [_make_event("reddit")]
        result = runner.invoke(app, ["scrape", "reddit"])
        assert result.exit_code == 0
        assert "1 Reddit events" in result.output

    @patch("web_scrapers.coordinator.run_single")
    def test_scrape_reddit_json_output(self, mock_run: MagicMock) -> None:
        mock_run.return_value = [_make_event("reddit")]
        result = runner.invoke(app, ["scrape", "reddit", "--json"])
        assert result.exit_code == 0
        assert '"source":"reddit"' in result.output or '"source": "reddit"' in result.output

    @patch("web_scrapers.coordinator.run_single")
    def test_scrape_reddit_empty(self, mock_run: MagicMock) -> None:
        mock_run.return_value = []
        result = runner.invoke(app, ["scrape", "reddit"])
        assert result.exit_code == 0
        assert "0 Reddit events" in result.output


class TestScrapeNews:
    @patch("web_scrapers.coordinator.run_single")
    def test_scrape_news_summary(self, mock_run: MagicMock) -> None:
        mock_run.return_value = [_make_event("news"), _make_event("news", "t:2")]
        result = runner.invoke(app, ["scrape", "news"])
        assert result.exit_code == 0
        assert "2 news events" in result.output

    @patch("web_scrapers.coordinator.run_single")
    def test_scrape_news_json(self, mock_run: MagicMock) -> None:
        mock_run.return_value = [_make_event("news")]
        result = runner.invoke(app, ["scrape", "news", "--json"])
        assert result.exit_code == 0
        assert '"source":"news"' in result.output or '"source": "news"' in result.output


class TestRunAll:
    @patch("web_scrapers.coordinator.run_all")
    def test_run_all_summary(self, mock_run: MagicMock) -> None:
        mock_run.return_value = [_make_event(), _make_event(event_id="t:2")]
        result = runner.invoke(app, ["run-all"])
        assert result.exit_code == 0
        assert "2 total events" in result.output

    @patch("web_scrapers.coordinator.run_all")
    def test_run_all_json(self, mock_run: MagicMock) -> None:
        mock_run.return_value = [_make_event()]
        result = runner.invoke(app, ["run-all", "--json"])
        assert result.exit_code == 0
        assert "source" in result.output

    @patch("web_scrapers.cli.asyncio.run", return_value=(5, 3))
    def test_run_all_with_ingest(self, mock_async_run: MagicMock) -> None:
        result = runner.invoke(app, ["run-all", "--ingest"])
        assert result.exit_code == 0
        assert "5 events" in result.output
        assert "3" in result.output


class TestHealth:
    @patch("web_scrapers.scrapers.news.NewsScraper.health_check", return_value=True)
    @patch("web_scrapers.scrapers.reddit.RedditScraper.health_check", return_value=True)
    def test_health_all_ok(self, *_: MagicMock) -> None:
        with _mock_db_health():
            result = runner.invoke(app, ["health"])
        assert result.exit_code == 0
        assert "reddit: OK" in result.output
        assert "news: OK" in result.output
        assert "database: OK" in result.output

    @patch("web_scrapers.scrapers.news.NewsScraper.health_check", return_value=False)
    @patch("web_scrapers.scrapers.reddit.RedditScraper.health_check", return_value=True)
    def test_health_partial_failure(self, *_: MagicMock) -> None:
        with _mock_db_health():
            result = runner.invoke(app, ["health"])
        assert result.exit_code == 1
        assert "reddit: OK" in result.output
        assert "news: FAIL" in result.output

    @patch("web_scrapers.scrapers.news.NewsScraper.health_check", return_value=False)
    @patch("web_scrapers.scrapers.reddit.RedditScraper.health_check", return_value=False)
    def test_health_all_fail(self, *_: MagicMock) -> None:
        with _mock_db_health():
            result = runner.invoke(app, ["health"])
        assert result.exit_code == 1
