from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


def _default_settings_path() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "netgarde"
    elif sys.platform.startswith("linux"):
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config" / "netgarde"
    else:
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) / "netgarde" if appdata else Path.home() / "netgarde"
    return base / "gui-settings.json"


def _runtime_dir() -> Path:
    path = _default_settings_path().parent
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class GuiSettings:
    api_url: str = ""
    api_token: str = ""
    install_policy_ca: bool = False

    @classmethod
    def load(cls, path: Path | None = None) -> GuiSettings:
        settings_path = path or _default_settings_path()
        if not settings_path.is_file():
            return cls()
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        return cls(
            api_url=str(data.get("api_url", "")).strip(),
            api_token=str(data.get("api_token", "")).strip(),
            install_policy_ca=bool(data.get("install_policy_ca", False)),
        )

    def save(self, path: Path | None = None) -> None:
        settings_path = path or _default_settings_path()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")


def pid_file() -> Path:
    return _runtime_dir() / "tunnel.pid"


def log_file() -> Path:
    return _runtime_dir() / "tunnel.log"
