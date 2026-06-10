from __future__ import annotations

from pathlib import Path

from trustedge_wg.gui.settings import log_file


def read_log_lines(path: Path | None = None) -> list[str]:
    target = path or log_file()
    if not target.is_file():
        return []
    try:
        return target.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
