# Version: v0.1.0
"""Tests for configuration loading, YAML parsing, and path safety."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from web_scrapers.config import (
    get_feed_targets,
    get_subreddit_targets,
    load_yaml_config,
)


class TestLoadYamlConfig:
    def test_loads_valid_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "test.yaml"
        config_file.write_text("key: value\nitems:\n  - one\n  - two\n")
        with patch("web_scrapers.config.CONFIG_DIR", tmp_path):
            result = load_yaml_config("test.yaml")
        assert result == {"key": "value", "items": ["one", "two"]}

    def test_returns_empty_dict_for_missing_file(self) -> None:
        with patch("web_scrapers.config.CONFIG_DIR", Path("/nonexistent")):
            result = load_yaml_config("missing.yaml")
        assert result == {}

    def test_returns_empty_dict_for_empty_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        with patch("web_scrapers.config.CONFIG_DIR", tmp_path):
            result = load_yaml_config("empty.yaml")
        assert result == {}

    def test_rejects_path_traversal_dotdot(self) -> None:
        with pytest.raises(ValueError, match="Invalid config filename"):
            load_yaml_config("../../../etc/passwd")

    def test_rejects_absolute_path(self) -> None:
        with pytest.raises(ValueError, match="Invalid config filename"):
            load_yaml_config("/etc/passwd")

    def test_rejects_path_escaping_config_dir(self, tmp_path: Path) -> None:
        # Symlink attack: file inside config dir resolves outside
        with patch("web_scrapers.config.CONFIG_DIR", tmp_path):
            # Even a valid-looking name with embedded traversal is blocked
            with pytest.raises(ValueError):
                load_yaml_config("..%2f..%2fetc%2fpasswd")

    def test_handles_malformed_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("{{{{invalid yaml content")
        with patch("web_scrapers.config.CONFIG_DIR", tmp_path):
            with pytest.raises(yaml.YAMLError):
                load_yaml_config("bad.yaml")


class TestGetSubredditTargets:
    def test_loads_from_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "subreddits.yaml"
        data = {
            "subreddits": [
                {"name": "test_sub", "sort": "new", "limit": 10, "category": "test"},
            ]
        }
        config_file.write_text(yaml.dump(data))
        with patch("web_scrapers.config.CONFIG_DIR", tmp_path):
            targets = get_subreddit_targets()
        assert len(targets) == 1
        assert targets[0]["name"] == "test_sub"

    def test_returns_empty_when_no_subreddits_key(self, tmp_path: Path) -> None:
        config_file = tmp_path / "subreddits.yaml"
        config_file.write_text("other_key: value\n")
        with patch("web_scrapers.config.CONFIG_DIR", tmp_path):
            targets = get_subreddit_targets()
        assert targets == []

    def test_returns_empty_when_file_missing(self) -> None:
        with patch("web_scrapers.config.CONFIG_DIR", Path("/nonexistent")):
            targets = get_subreddit_targets()
        assert targets == []


class TestGetFeedTargets:
    def test_loads_from_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "feeds.yaml"
        data = {
            "feeds": [
                {"name": "Test Feed", "url": "https://example.com/rss", "category": "test"},
            ]
        }
        config_file.write_text(yaml.dump(data))
        with patch("web_scrapers.config.CONFIG_DIR", tmp_path):
            targets = get_feed_targets()
        assert len(targets) == 1
        assert targets[0]["url"] == "https://example.com/rss"

    def test_returns_empty_when_no_feeds_key(self, tmp_path: Path) -> None:
        config_file = tmp_path / "feeds.yaml"
        config_file.write_text("other_key: value\n")
        with patch("web_scrapers.config.CONFIG_DIR", tmp_path):
            targets = get_feed_targets()
        assert targets == []


class TestActualConfigFiles:
    """Verify the shipped config files are valid."""

    def test_subreddits_yaml_loads(self) -> None:
        targets = get_subreddit_targets()
        assert len(targets) > 0
        for t in targets:
            assert "name" in t
            assert "sort" in t
            assert "limit" in t

    def test_feeds_yaml_loads(self) -> None:
        targets = get_feed_targets()
        assert len(targets) > 0
        for t in targets:
            assert "name" in t
            assert "url" in t
