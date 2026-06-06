from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


def _user_data_dir() -> Path:
    """User-writable app data (never written by root tunnel process)."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "NetGardeClient"
    if sys.platform.startswith("linux"):
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
        return base / "netgarde-client"
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home()
    return base / "NetGardeClient"


def settings_path() -> Path:
    return _user_data_dir() / "gui-settings.json"


def tunnel_runtime_dir(uid: int | None = None) -> Path:
    """Per-user runtime files; tunnel (root) and GUI (user) must use the same path."""
    user_id = os.getuid() if uid is None else uid
    return Path(f"/tmp/netgarde-wg-{user_id}")


def pid_file(uid: int | None = None) -> Path:
    return tunnel_runtime_dir(uid) / "tunnel.pid"


def log_file(uid: int | None = None) -> Path:
    return tunnel_runtime_dir(uid) / "tunnel.log"


@dataclass
class GuiSettings:
    api_url: str = ""
    api_token: str = ""
    install_policy_ca: bool = False

    @classmethod
    def load(cls, path: Path | None = None) -> GuiSettings:
        target = path or settings_path()
        try:
            if not target.is_file():
                return cls()
            data = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, PermissionError, json.JSONDecodeError):
            return cls()
        return cls(
            api_url=str(data.get("api_url", "")).strip(),
            api_token=str(data.get("api_token", "")).strip(),
            install_policy_ca=bool(data.get("install_policy_ca", False)),
        )

    def save(self, path: Path | None = None) -> None:
        target = path or settings_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
