from __future__ import annotations

from pathlib import Path

from trustedge_wg.gui.log_reader import read_log_lines


def test_read_log_lines_missing_file(tmp_path: Path) -> None:
    assert read_log_lines(tmp_path / "missing.log") == []


def test_read_log_lines_reads_file(tmp_path: Path) -> None:
    log_path = tmp_path / "tunnel.log"
    log_path.write_text("line one\nline two\n", encoding="utf-8")
    assert read_log_lines(log_path) == ["line one", "line two"]
