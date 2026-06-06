"""Locate helper binaries shipped next to a frozen (PyInstaller) executable."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def executable_dir() -> Path:
    """Directory containing the running program (venv script or frozen binary)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(sys.argv[0]).resolve().parent


def find_sibling_binary(*names: str) -> str | None:
    """Return the first executable found beside the program, or None."""
    base = executable_dir()
    for name in names:
        candidate = base / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None
