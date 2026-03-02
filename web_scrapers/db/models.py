# Version: v0.2.0
"""SQLAlchemy ORM models for persistent storage."""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class RunStatus(enum.Enum):
    """Status of a scrape run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for web_scrapers schema."""

    pass


class ScrapeJobRow(Base):
    """Persistent job definition for a scheduled scraper."""

    __tablename__ = "scrape_jobs"
    __table_args__ = {"schema": "web_scrapers"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    scraper: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    schedule: Mapped[str | None] = mapped_column(String(50), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    runs: Mapped[list[ScrapeRunRow]] = relationship(back_populates="job", lazy="selectin")


class ScrapeRunRow(Base):
    """Record of a single scraper execution."""

    __tablename__ = "scrape_runs"
    __table_args__ = (
        Index("idx_scrape_runs_started_at", "started_at"),
        {"schema": "web_scrapers"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("web_scrapers.scrape_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    job_name: Mapped[str] = mapped_column(String(100), nullable=False)
    scraper: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, schema="web_scrapers", name="run_status"),
        nullable=False,
        default=RunStatus.PENDING,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    events_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_ingested: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    job: Mapped[ScrapeJobRow | None] = relationship(back_populates="runs")
    events: Mapped[list[SignalEventRow]] = relationship(back_populates="run", lazy="selectin")


class SignalEventRow(Base):
    """Persistent, deduplicated signal event."""

    __tablename__ = "signal_events"
    __table_args__ = (
        Index("idx_signal_events_source", "source"),
        Index("idx_signal_events_source_type", "source", "event_type"),
        Index("idx_signal_events_scraped_at", "scraped_at"),
        Index("idx_signal_events_created_at", "created_at"),
        {"schema": "web_scrapers"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    run_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("web_scrapers.scrape_runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    run: Mapped[ScrapeRunRow | None] = relationship(back_populates="events")
