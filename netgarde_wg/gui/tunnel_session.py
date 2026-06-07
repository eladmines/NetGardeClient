from __future__ import annotations

import json
import os
import time
from pathlib import Path

from netgarde_wg.paths import user_data_dir


def session_path() -> Path:
    return user_data_dir() / "tunnel-session.json"


def mark_tunnel_session() -> None:
    path = session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"gui_pid": os.getpid(), "connected_at": time.time()}) + "\n",
        encoding="utf-8",
    )


def clear_tunnel_session() -> None:
    try:
        session_path().unlink(missing_ok=True)
    except OSError:
        pass


def tunnel_session_valid() -> bool:
    path = session_path()
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data.get("gui_pid", -1)) == os.getpid()
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False


def session_connected_at() -> float | None:
    path = session_path()
    if not path.is_file() or not tunnel_session_valid():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        value = float(data.get("connected_at", 0))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    return value if value > 0 else None
