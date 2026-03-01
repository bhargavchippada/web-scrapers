# Version: v0.2.0
"""Application settings loaded from environment variables and YAML configs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


class Settings(BaseSettings):
    """Environment-based settings."""

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "web-scrapers/0.1"

    neo4j_url: str = "bolt://localhost:7687"
    qdrant_url: str = "http://localhost:6333"
    ollama_url: str = "http://localhost:11434"

    database_url: str = "postgresql://admin:password123@localhost:5432/turiya_memory"

    scraper_log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()


def load_yaml_config(filename: str) -> dict[str, Any]:
    """Load a YAML config file from the config/ directory."""
    if ".." in filename or filename.startswith("/"):
        raise ValueError(f"Invalid config filename: {filename}")
    path = (CONFIG_DIR / filename).resolve()
    if not path.is_relative_to(CONFIG_DIR.resolve()):
        raise ValueError(f"Config file escapes config directory: {filename}")
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def get_subreddit_targets() -> list[dict[str, Any]]:
    """Load subreddit scraping targets from config/subreddits.yaml."""
    config = load_yaml_config("subreddits.yaml")
    return config.get("subreddits", [])


def get_feed_targets() -> list[dict[str, Any]]:
    """Load RSS feed targets from config/feeds.yaml."""
    config = load_yaml_config("feeds.yaml")
    return config.get("feeds", [])


def get_job_definitions() -> list[dict[str, Any]]:
    """Load job definitions from config/jobs.yaml."""
    config = load_yaml_config("jobs.yaml")
    return config.get("jobs", [])
