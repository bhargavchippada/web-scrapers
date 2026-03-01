# Version: v0.2.0
"""Database engine and session factory."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from web_scrapers.config import settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(url: str | None = None) -> Engine:
    """Create or return the global SQLAlchemy engine."""
    global _engine
    if _engine is None or url is not None:
        database_url = url or settings.database_url
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        if url is None:
            _engine = engine
        return engine
    return _engine


def get_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """Get or create the global session factory."""
    global _session_factory
    if _session_factory is None or engine is not None:
        eng = engine or get_engine()
        factory = sessionmaker(bind=eng, expire_on_commit=False)
        if engine is None:
            _session_factory = factory
        return factory
    return _session_factory


def get_session(engine: Engine | None = None) -> Session:
    """Create a new session."""
    factory = get_session_factory(engine)
    return factory()


def ensure_schema(engine: Engine | None = None) -> None:
    """Create the web_scrapers schema if it doesn't exist."""
    eng = engine or get_engine()
    with eng.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS web_scrapers"))
        conn.commit()


def reset_globals() -> None:
    """Reset module-level engine/factory (for testing)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
