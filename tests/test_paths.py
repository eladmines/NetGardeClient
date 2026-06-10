from __future__ import annotations

import sys
from pathlib import Path

import pytest

from trustedge_wg.paths import agent_state_path, user_data_dir


def test_user_data_dir_darwin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: Path("/Users/tester"))
    assert user_data_dir() == Path("/Users/tester/Library/Application Support/TrustEdgeClient")


def test_user_data_dir_linux_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: Path("/home/tester"))
    assert user_data_dir() == Path("/home/tester/.config/trustedge-client")


def test_user_data_dir_linux_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
    assert user_data_dir() == Path("/custom/config/trustedge-client")


def test_user_data_dir_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", r"C:\Users\tester\AppData\Roaming")
    assert user_data_dir() == Path(r"C:\Users\tester\AppData\Roaming") / "TrustEdgeClient"


def test_agent_state_path(tmp_user_data: Path) -> None:
    assert agent_state_path() == tmp_user_data / "agent-state.json"
