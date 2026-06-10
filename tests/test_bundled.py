from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

from trustedge_wg.platform.bundled import executable_dir, find_sibling_binary


def test_executable_dir_uses_argv0_when_not_frozen(tmp_path: Path) -> None:
    script = tmp_path / "trustedge-wg"
    script.write_text("", encoding="utf-8")
    with patch.object(sys, "argv", [str(script)]):
        with patch.object(sys, "frozen", False, create=True):
            assert executable_dir() == tmp_path.resolve()


def test_find_sibling_binary_returns_executable(tmp_path: Path) -> None:
    binary = tmp_path / "wireguard-go"
    binary.write_text("", encoding="utf-8")
    binary.chmod(0o755)
    with patch("trustedge_wg.platform.bundled.executable_dir", return_value=tmp_path):
        assert find_sibling_binary("wireguard-go", "missing") == str(binary)


def test_find_sibling_binary_missing(tmp_path: Path) -> None:
    with patch("trustedge_wg.platform.bundled.executable_dir", return_value=tmp_path):
        assert find_sibling_binary("missing-binary") is None
