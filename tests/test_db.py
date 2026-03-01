# Version: v0.2.0
"""Tests for the database layer — models, repository, queries, engine."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from web_scrapers.db.models import (
    Base,
    RunStatus,
    ScrapeJobRow,
    ScrapeRunRow,
    SignalEventRow,
)
from web_scrapers.db.repository import EventRepository, JobRepository, RunRepository
from web_scrapers.models.base import SignalEvent

TEST_DB_URL = "postgresql://admin:password123@localhost:5432/turiya_memory"
TEST_SCHEMA = "web_scrapers_test"


def _make_event(
    source: str = "reddit",
    event_type: str = "post",
    event_id: str = "reddit:test1",
    payload: dict | None = None,
) -> SignalEvent:
    return SignalEvent(
        source=source,
        event_type=event_type,
        payload=payload or {"title": "Test post", "subreddit": "wallstreetbets"},
        event_id=event_id,
    )


# ─── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def db_engine():
    """Create a test engine and schema. Tears down after all tests."""
    engine = create_engine(TEST_DB_URL)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {TEST_SCHEMA}"))
            conn.commit()
    except Exception:
        pytest.skip("PostgreSQL not available")

    # Remap all tables to test schema
    for table in Base.metadata.tables.values():
        table.schema = TEST_SCHEMA

    Base.metadata.create_all(engine)
    yield engine

    # Teardown: use CASCADE to handle enum dependencies
    with engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        conn.commit()
    engine.dispose()

    # Restore original schema
    for table in Base.metadata.tables.values():
        table.schema = "web_scrapers"


@pytest.fixture
def db_session(db_engine):
    """Provide a transactional session that rolls back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, expire_on_commit=False)()
    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


# ─── ORM Model Tests ────────────────────────────────────────────────────


@pytest.mark.integration
class TestScrapeJobRow:
    def test_create_job(self, db_session: Session) -> None:
        job = ScrapeJobRow(name="test-job", scraper="reddit", schedule="*/30 * * * *")
        db_session.add(job)
        db_session.flush()
        assert job.id is not None
        assert job.enabled is True

    def test_job_defaults(self, db_session: Session) -> None:
        job = ScrapeJobRow(name="defaults", scraper="news")
        db_session.add(job)
        db_session.flush()
        assert job.config == {}
        assert job.enabled is True
        assert job.schedule is None


@pytest.mark.integration
class TestScrapeRunRow:
    def test_create_run(self, db_session: Session) -> None:
        run = ScrapeRunRow(job_name="test", scraper="reddit", status=RunStatus.RUNNING)
        db_session.add(run)
        db_session.flush()
        assert run.id is not None
        assert run.events_total == 0
        assert run.events_new == 0

    def test_run_status_enum(self) -> None:
        assert RunStatus.PENDING.value == "pending"
        assert RunStatus.RUNNING.value == "running"
        assert RunStatus.COMPLETED.value == "completed"
        assert RunStatus.FAILED.value == "failed"


@pytest.mark.integration
class TestSignalEventRow:
    def test_create_event(self, db_session: Session) -> None:
        event = SignalEventRow(
            event_id="reddit:abc123",
            source="reddit",
            event_type="post",
            payload={"title": "Test"},
        )
        db_session.add(event)
        db_session.flush()
        assert event.id is not None

    def test_event_id_unique(self, db_session: Session) -> None:
        e1 = SignalEventRow(
            event_id="reddit:unique1", source="reddit", event_type="post", payload={}
        )
        db_session.add(e1)
        db_session.flush()
        e2 = SignalEventRow(
            event_id="reddit:unique1", source="reddit", event_type="post", payload={}
        )
        db_session.add(e2)
        with pytest.raises(Exception):
            db_session.flush()


# ─── EventRepository Tests ──────────────────────────────────────────────


@pytest.mark.integration
class TestEventRepository:
    def test_bulk_upsert_inserts(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        events = [_make_event(event_id="reddit:u1"), _make_event(event_id="reddit:u2")]
        inserted = repo.bulk_upsert(events)
        assert inserted == 2

    def test_bulk_upsert_dedup(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        events = [_make_event(event_id="reddit:d1")]
        repo.bulk_upsert(events)
        inserted = repo.bulk_upsert(events)
        assert inserted == 0

    def test_bulk_upsert_mixed(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        repo.bulk_upsert([_make_event(event_id="reddit:m1")])
        events = [_make_event(event_id="reddit:m1"), _make_event(event_id="reddit:m2")]
        inserted = repo.bulk_upsert(events)
        assert inserted == 1

    def test_bulk_upsert_empty(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        assert repo.bulk_upsert([]) == 0

    def test_get_by_event_id(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        repo.bulk_upsert([_make_event(event_id="reddit:get1")])
        row = repo.get_by_event_id("reddit:get1")
        assert row is not None
        assert row.source == "reddit"

    def test_get_by_event_id_missing(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        assert repo.get_by_event_id("nonexistent") is None

    def test_query_events_all(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        repo.bulk_upsert([
            _make_event(event_id="reddit:q1"),
            _make_event(
                source="news", event_type="article", event_id="news:q2",
                payload={"feed_name": "Test"},
            ),
        ])
        results = repo.query_events()
        assert len(results) == 2

    def test_query_events_by_source(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        repo.bulk_upsert([
            _make_event(event_id="reddit:s1"),
            _make_event(
                source="news", event_type="article", event_id="news:s2",
                payload={"feed_name": "Test"},
            ),
        ])
        results = repo.query_events(source="reddit")
        assert len(results) == 1
        assert results[0].source == "reddit"

    def test_query_events_by_subreddit(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        repo.bulk_upsert([
            _make_event(event_id="reddit:sr1", payload={"subreddit": "options"}),
            _make_event(event_id="reddit:sr2", payload={"subreddit": "wallstreetbets"}),
        ])
        results = repo.query_events(subreddit="options")
        assert len(results) == 1
        assert results[0].payload["subreddit"] == "options"

    def test_query_events_since(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        repo.bulk_upsert([_make_event(event_id="reddit:ts1")])
        results = repo.query_events(since=datetime(2099, 1, 1, tzinfo=UTC))
        assert len(results) == 0

    def test_query_events_limit(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        repo.bulk_upsert([_make_event(event_id=f"reddit:lim{i}") for i in range(10)])
        results = repo.query_events(limit=3)
        assert len(results) == 3

    def test_count_events(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        repo.bulk_upsert([
            _make_event(event_id="reddit:c1"),
            _make_event(event_id="reddit:c2"),
            _make_event(source="news", event_type="article", event_id="news:c3", payload={}),
        ])
        assert repo.count_events() == 3
        assert repo.count_events(source="reddit") == 2
        assert repo.count_events(source="news") == 1

    def test_get_new_event_ids(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        repo.bulk_upsert([_make_event(event_id="reddit:exist1")])
        new_ids = repo.get_new_event_ids(["reddit:exist1", "reddit:new1", "reddit:new2"])
        assert new_ids == {"reddit:new1", "reddit:new2"}

    def test_get_new_event_ids_empty(self, db_session: Session) -> None:
        repo = EventRepository(db_session)
        assert repo.get_new_event_ids([]) == set()

    def test_bulk_upsert_with_run_id(self, db_session: Session) -> None:
        run_repo = RunRepository(db_session)
        run = run_repo.create_run(job_name="test", scraper="reddit")
        repo = EventRepository(db_session)
        repo.bulk_upsert([_make_event(event_id="reddit:run1")], run_id=run.id)
        row = repo.get_by_event_id("reddit:run1")
        assert row is not None
        assert row.run_id == run.id


# ─── RunRepository Tests ────────────────────────────────────────────────


@pytest.mark.integration
class TestRunRepository:
    def test_create_run(self, db_session: Session) -> None:
        repo = RunRepository(db_session)
        run = repo.create_run(job_name="test-reddit", scraper="reddit")
        assert run.id is not None
        assert run.status == RunStatus.RUNNING
        assert run.started_at is not None

    def test_complete_run_success(self, db_session: Session) -> None:
        repo = RunRepository(db_session)
        run = repo.create_run(job_name="test-reddit", scraper="reddit")
        repo.complete_run(run, events_total=10, events_new=5, events_ingested=3)
        assert run.status == RunStatus.COMPLETED
        assert run.finished_at is not None
        assert run.events_total == 10
        assert run.events_new == 5
        assert run.events_ingested == 3
        assert run.error is None

    def test_complete_run_failure(self, db_session: Session) -> None:
        repo = RunRepository(db_session)
        run = repo.create_run(job_name="fail", scraper="reddit")
        repo.complete_run(run, events_total=0, events_new=0, error="API error")
        assert run.status == RunStatus.FAILED
        assert run.error == "API error"

    def test_get_recent_runs(self, db_session: Session) -> None:
        repo = RunRepository(db_session)
        for i in range(5):
            repo.create_run(job_name=f"run-{i}", scraper="reddit")
        runs = repo.get_recent_runs(limit=3)
        assert len(runs) == 3

    def test_get_recent_runs_by_scraper(self, db_session: Session) -> None:
        repo = RunRepository(db_session)
        repo.create_run(job_name="reddit-run", scraper="reddit")
        repo.create_run(job_name="news-run", scraper="news")
        runs = repo.get_recent_runs(scraper="reddit")
        assert len(runs) == 1
        assert runs[0].scraper == "reddit"

    def test_get_last_run(self, db_session: Session) -> None:
        repo = RunRepository(db_session)
        repo.create_run(job_name="first", scraper="reddit")
        repo.create_run(job_name="second", scraper="reddit")
        last = repo.get_last_run("reddit")
        assert last is not None
        assert last.job_name == "second"

    def test_get_last_run_no_runs(self, db_session: Session) -> None:
        repo = RunRepository(db_session)
        assert repo.get_last_run("nonexistent") is None


# ─── JobRepository Tests ────────────────────────────────────────────────


@pytest.mark.integration
class TestJobRepository:
    def test_upsert_create(self, db_session: Session) -> None:
        repo = JobRepository(db_session)
        job = repo.upsert_job(name="new-job", scraper="reddit", schedule="*/30 * * * *")
        assert job.id is not None
        assert job.name == "new-job"
        assert job.scraper == "reddit"

    def test_upsert_update(self, db_session: Session) -> None:
        repo = JobRepository(db_session)
        repo.upsert_job(name="update-job", scraper="reddit", schedule="*/30 * * * *")
        updated = repo.upsert_job(name="update-job", scraper="reddit", schedule="*/15 * * * *")
        assert updated.schedule == "*/15 * * * *"

    def test_get_by_name(self, db_session: Session) -> None:
        repo = JobRepository(db_session)
        repo.upsert_job(name="find-me", scraper="news")
        found = repo.get_by_name("find-me")
        assert found is not None
        assert found.scraper == "news"

    def test_get_by_name_missing(self, db_session: Session) -> None:
        repo = JobRepository(db_session)
        assert repo.get_by_name("nonexistent") is None

    def test_get_all_enabled(self, db_session: Session) -> None:
        repo = JobRepository(db_session)
        repo.upsert_job(name="enabled-job", scraper="reddit", enabled=True)
        repo.upsert_job(name="disabled-job", scraper="news", enabled=False)
        enabled = repo.get_all_enabled()
        names = [j.name for j in enabled]
        assert "enabled-job" in names
        assert "disabled-job" not in names

    def test_get_all(self, db_session: Session) -> None:
        repo = JobRepository(db_session)
        repo.upsert_job(name="all-a", scraper="reddit")
        repo.upsert_job(name="all-b", scraper="news")
        all_jobs = repo.get_all()
        names = [j.name for j in all_jobs]
        assert "all-a" in names
        assert "all-b" in names

    def test_set_enabled(self, db_session: Session) -> None:
        repo = JobRepository(db_session)
        repo.upsert_job(name="toggle-job", scraper="reddit", enabled=True)
        assert repo.set_enabled("toggle-job", enabled=False) is True
        job = repo.get_by_name("toggle-job")
        assert job is not None
        assert job.enabled is False

    def test_set_enabled_missing(self, db_session: Session) -> None:
        repo = JobRepository(db_session)
        assert repo.set_enabled("no-such-job", enabled=True) is False


# ─── Engine Tests ────────────────────────────────────────────────────────


@pytest.mark.integration
class TestEngine:
    def test_ensure_schema(self, db_engine) -> None:
        from web_scrapers.db.engine import ensure_schema

        ensure_schema(db_engine)

    def test_get_session_factory(self, db_engine) -> None:
        from web_scrapers.db.engine import get_session_factory

        factory = get_session_factory(db_engine)
        session = factory()
        assert session is not None
        session.close()


# ─── CLI DB Command Tests (mocked DB) ───────────────────────────────────


class TestCLIDbCommands:
    def test_db_stats(self) -> None:
        from typer.testing import CliRunner

        from web_scrapers.cli import app

        runner = CliRunner()
        with patch("web_scrapers.db.queries.get_stats") as mock_stats:
            mock_stats.return_value = {
                "total_events": 100,
                "reddit_events": 80,
                "news_events": 20,
                "events_last_24h": 50,
                "recent_runs": [],
            }
            result = runner.invoke(app, ["db", "stats"])
            assert result.exit_code == 0
            assert "100" in result.output
            assert "80" in result.output

    def test_db_seed_jobs(self) -> None:
        from typer.testing import CliRunner

        from web_scrapers.cli import app

        runner = CliRunner()
        mock_session = MagicMock()
        with (
            patch("web_scrapers.db.engine.get_session", return_value=mock_session),
            patch("web_scrapers.config.get_job_definitions") as mock_defs,
            patch("web_scrapers.db.repository.JobRepository.get_by_name", return_value=None),
            patch("web_scrapers.db.repository.JobRepository.upsert_job") as mock_upsert,
        ):
            mock_defs.return_value = [
                {"name": "test-job", "scraper": "reddit", "schedule": "*/30 * * * *"},
            ]
            mock_upsert.return_value = MagicMock()
            result = runner.invoke(app, ["db", "seed-jobs"])
            assert result.exit_code == 0
            assert "Seeded" in result.output


class TestCLIJobsCommands:
    def test_jobs_list_empty(self) -> None:
        from typer.testing import CliRunner

        from web_scrapers.cli import app

        runner = CliRunner()
        mock_session = MagicMock()
        with (
            patch("web_scrapers.db.engine.get_session", return_value=mock_session),
            patch("web_scrapers.db.repository.JobRepository.get_all", return_value=[]),
        ):
            result = runner.invoke(app, ["jobs", "list"])
            assert result.exit_code == 0
            assert "No jobs" in result.output

    def test_jobs_enable(self) -> None:
        from typer.testing import CliRunner

        from web_scrapers.cli import app

        runner = CliRunner()
        mock_session = MagicMock()
        with (
            patch("web_scrapers.db.engine.get_session", return_value=mock_session),
            patch(
                "web_scrapers.db.repository.JobRepository.set_enabled", return_value=True
            ),
        ):
            result = runner.invoke(app, ["jobs", "enable", "test-job"])
            assert result.exit_code == 0
            assert "enabled" in result.output

    def test_jobs_disable(self) -> None:
        from typer.testing import CliRunner

        from web_scrapers.cli import app

        runner = CliRunner()
        mock_session = MagicMock()
        with (
            patch("web_scrapers.db.engine.get_session", return_value=mock_session),
            patch(
                "web_scrapers.db.repository.JobRepository.set_enabled", return_value=True
            ),
        ):
            result = runner.invoke(app, ["jobs", "disable", "test-job"])
            assert result.exit_code == 0
            assert "disabled" in result.output

    def test_jobs_history_empty(self) -> None:
        from typer.testing import CliRunner

        from web_scrapers.cli import app

        runner = CliRunner()
        mock_session = MagicMock()
        with (
            patch("web_scrapers.db.engine.get_session", return_value=mock_session),
            patch(
                "web_scrapers.db.repository.RunRepository.get_recent_runs", return_value=[]
            ),
        ):
            result = runner.invoke(app, ["jobs", "history"])
            assert result.exit_code == 0
            assert "No runs" in result.output


# ─── Scheduler Tests (mocked) ───────────────────────────────────────────


class TestScheduler:
    @patch("web_scrapers.scheduler.scheduler.get_session")
    def test_build_scheduler_no_jobs(self, mock_get_session: MagicMock) -> None:
        from web_scrapers.scheduler.scheduler import build_scheduler

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        with patch("web_scrapers.db.repository.JobRepository.get_all_enabled", return_value=[]):
            scheduler = build_scheduler()
            assert len(scheduler.get_jobs()) == 0

    @patch("web_scrapers.scheduler.scheduler.get_session")
    def test_build_scheduler_with_jobs(self, mock_get_session: MagicMock) -> None:
        from web_scrapers.scheduler.scheduler import build_scheduler

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "test-reddit"
        mock_job.scraper = "reddit"
        mock_job.schedule = "*/30 * * * *"

        with patch(
            "web_scrapers.db.repository.JobRepository.get_all_enabled",
            return_value=[mock_job],
        ):
            scheduler = build_scheduler()
            jobs = scheduler.get_jobs()
            assert len(jobs) == 1
            assert "test-reddit" in jobs[0].name

    @patch("web_scrapers.scheduler.scheduler.get_session")
    def test_build_scheduler_job_without_schedule(self, mock_get_session: MagicMock) -> None:
        from web_scrapers.scheduler.scheduler import build_scheduler

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "manual-only"
        mock_job.scraper = "reddit"
        mock_job.schedule = None

        with patch(
            "web_scrapers.db.repository.JobRepository.get_all_enabled",
            return_value=[mock_job],
        ):
            scheduler = build_scheduler()
            assert len(scheduler.get_jobs()) == 0
