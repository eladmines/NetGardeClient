from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from trustedge_wg.constants import ENV_API_TOKEN, ENV_API_URL, PRODUCTION_API_URL
from trustedge_wg.paths import user_data_dir


def settings_path() -> Path:
    return user_data_dir() / "gui-settings.json"


def tunnel_runtime_dir(uid: int | None = None) -> Path:
    """Per-user runtime files; tunnel (root) and GUI (user) must use the same path."""
    user_id = os.getuid() if uid is None else uid
    return Path(f"/tmp/trustedge-wg-{user_id}")


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
    def from_env(cls) -> GuiSettings:
        return cls(
            api_url=os.environ.get(ENV_API_URL, "").strip(),
            api_token=os.environ.get(ENV_API_TOKEN, "").strip(),
        )

    @classmethod
    def production_defaults(cls) -> GuiSettings:
        return cls(api_url=PRODUCTION_API_URL)

    @classmethod
    def load(cls, path: Path | None = None) -> GuiSettings:
        target = path or settings_path()
        saved = cls()
        try:
            if target.is_file():
                data = json.loads(target.read_text(encoding="utf-8"))
                saved = cls(
                    api_url=str(data.get("api_url", "")).strip(),
                    api_token=str(data.get("api_token", "")).strip(),
                    install_policy_ca=bool(data.get("install_policy_ca", False)),
                )
        except (OSError, PermissionError, json.JSONDecodeError):
            pass
        return saved.with_defaults()

    def with_defaults(self) -> GuiSettings:
        """Saved settings, then env overrides, then production API URL."""
        env = self.from_env()
        prod = self.production_defaults()
        return GuiSettings(
            api_url=self.api_url or env.api_url or prod.api_url,
            api_token=self.api_token or env.api_token,
            install_policy_ca=self.install_policy_ca,
        )

    def missing_api_url_message(self) -> str:
        return "No API URL configured."
