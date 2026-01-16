"""Tests for configuration handling."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from pushover_mcp.config import (
    PushoverConfig,
    get_config_file_path,
    load_config,
    load_config_from_file,
)


class TestPushoverConfig:
    """Tests for PushoverConfig dataclass."""

    def test_is_valid_with_both_credentials(self):
        """Config is valid when both token and user_key are set."""
        config = PushoverConfig(token="abc123", user_key="user456")
        assert config.is_valid() is True

    def test_is_valid_with_empty_token(self):
        """Config is invalid when token is empty."""
        config = PushoverConfig(token="", user_key="user456")
        assert config.is_valid() is False

    def test_is_valid_with_empty_user_key(self):
        """Config is invalid when user_key is empty."""
        config = PushoverConfig(token="abc123", user_key="")
        assert config.is_valid() is False

    def test_is_valid_with_both_empty(self):
        """Config is invalid when both are empty."""
        config = PushoverConfig(token="", user_key="")
        assert config.is_valid() is False


class TestGetConfigFilePath:
    """Tests for get_config_file_path function."""

    def test_default_path(self):
        """Uses ~/.config when XDG_CONFIG_HOME is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove XDG_CONFIG_HOME if it exists
            os.environ.pop("XDG_CONFIG_HOME", None)
            path = get_config_file_path()
            assert path == Path.home() / ".config" / "pushover-mcp" / "config.json"

    def test_xdg_config_home(self):
        """Uses XDG_CONFIG_HOME when set."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}):
            path = get_config_file_path()
            assert path == Path("/custom/config/pushover-mcp/config.json")


class TestLoadConfigFromFile:
    """Tests for load_config_from_file function."""

    def test_nonexistent_file_returns_empty_dict(self, tmp_path):
        """Returns empty dict when file doesn't exist."""
        result = load_config_from_file(tmp_path / "nonexistent.json")
        assert result == {}

    def test_valid_json_file(self, tmp_path):
        """Loads valid JSON config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"token": "test_token", "user_key": "test_user"}')

        result = load_config_from_file(config_file)
        assert result == {"token": "test_token", "user_key": "test_user"}

    def test_invalid_json_returns_empty_dict(self, tmp_path):
        """Returns empty dict for invalid JSON."""
        config_file = tmp_path / "config.json"
        config_file.write_text("not valid json {")

        result = load_config_from_file(config_file)
        assert result == {}

    def test_empty_file_returns_empty_dict(self, tmp_path):
        """Returns empty dict for empty file."""
        config_file = tmp_path / "config.json"
        config_file.write_text("")

        result = load_config_from_file(config_file)
        assert result == {}


class TestLoadConfig:
    """Tests for load_config function."""

    def test_loads_from_environment_variables(self):
        """Environment variables take priority."""
        with patch.dict(
            os.environ,
            {"PUSHOVER_TOKEN": "env_token", "PUSHOVER_USER_KEY": "env_user"},
        ):
            config = load_config()
            assert config.token == "env_token"
            assert config.user_key == "env_user"
            assert config.is_valid() is True

    def test_falls_back_to_config_file(self, tmp_path):
        """Falls back to config file when env vars not set."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"token": "file_token", "user_key": "file_user"}')

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PUSHOVER_TOKEN", None)
            os.environ.pop("PUSHOVER_USER_KEY", None)
            with patch(
                "pushover_mcp.config.get_config_file_path", return_value=config_file
            ):
                config = load_config()
                assert config.token == "file_token"
                assert config.user_key == "file_user"

    def test_env_vars_override_config_file(self, tmp_path):
        """Environment variables override config file values."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"token": "file_token", "user_key": "file_user"}')

        with patch.dict(
            os.environ,
            {"PUSHOVER_TOKEN": "env_token", "PUSHOVER_USER_KEY": "env_user"},
        ):
            with patch(
                "pushover_mcp.config.get_config_file_path", return_value=config_file
            ):
                config = load_config()
                assert config.token == "env_token"
                assert config.user_key == "env_user"

    def test_partial_env_vars_with_file_fallback(self, tmp_path):
        """Can use env var for one and file for another."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"token": "file_token", "user_key": "file_user"}')

        with patch.dict(os.environ, {"PUSHOVER_TOKEN": "env_token"}, clear=True):
            os.environ.pop("PUSHOVER_USER_KEY", None)
            with patch(
                "pushover_mcp.config.get_config_file_path", return_value=config_file
            ):
                config = load_config()
                assert config.token == "env_token"
                assert config.user_key == "file_user"

    def test_returns_empty_config_when_nothing_configured(self):
        """Returns config with empty strings when nothing is configured."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PUSHOVER_TOKEN", None)
            os.environ.pop("PUSHOVER_USER_KEY", None)
            with patch(
                "pushover_mcp.config.load_config_from_file", return_value={}
            ):
                config = load_config()
                assert config.token == ""
                assert config.user_key == ""
                assert config.is_valid() is False
