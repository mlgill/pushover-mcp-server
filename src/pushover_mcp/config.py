"""Configuration handling for Pushover MCP Server.

Loads credentials from environment variables with config file fallback.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PushoverConfig:
    """Pushover API configuration."""
    
    token: str
    user_key: str
    
    def is_valid(self) -> bool:
        """Check if credentials are configured."""
        return bool(self.token and self.user_key)


def get_config_file_path() -> Path:
    """Get the config file path."""
    # Check XDG_CONFIG_HOME first, then fall back to ~/.config
    config_home = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(config_home) / "pushover-mcp" / "config.json"


def load_config_from_file(path: Optional[Path] = None) -> dict:
    """Load configuration from JSON file."""
    config_path = path or get_config_file_path()
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def load_config() -> PushoverConfig:
    """Load Pushover configuration.
    
    Priority:
    1. Environment variables (PUSHOVER_TOKEN, PUSHOVER_USER_KEY)
    2. Config file (~/.config/pushover-mcp/config.json)
    """
    # Try environment variables first
    token = os.environ.get("PUSHOVER_TOKEN", "")
    user_key = os.environ.get("PUSHOVER_USER_KEY", "")
    
    # Fall back to config file if env vars not set
    if not token or not user_key:
        file_config = load_config_from_file()
        token = token or file_config.get("token", "")
        user_key = user_key or file_config.get("user_key", "")
    
    return PushoverConfig(token=token, user_key=user_key)
