from __future__ import annotations

import os
import sys
from pathlib import Path


def user_data_dir() -> Path:
    """User-writable app data (never written by root tunnel process without --state)."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "NetGardeClient"
    if sys.platform.startswith("linux"):
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
        return base / "netgarde-client"
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home()
    return base / "NetGardeClient"


def agent_state_path() -> Path:
    return user_data_dir() / "agent-state.json"
