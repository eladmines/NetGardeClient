from __future__ import annotations

import json
import os

import pytest

from trustedge_wg.gui import tunnel_session


@pytest.fixture
def session_file(tmp_path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "tunnel-session.json"
    monkeypatch.setattr(tunnel_session, "session_path", lambda: path)
    return path


def test_mark_and_validate_session(session_file) -> None:
    tunnel_session.mark_tunnel_session()
    assert session_file.is_file()
    assert tunnel_session.tunnel_session_valid() is True
    connected_at = tunnel_session.session_connected_at()
    assert connected_at is not None
    assert connected_at > 0


def test_clear_session(session_file) -> None:
    tunnel_session.mark_tunnel_session()
    tunnel_session.clear_tunnel_session()
    assert not session_file.exists()
    assert tunnel_session.tunnel_session_valid() is False


def test_session_invalid_for_other_pid(session_file, monkeypatch: pytest.MonkeyPatch) -> None:
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(
        json.dumps({"gui_pid": os.getpid() + 9999, "connected_at": 1.0}) + "\n",
        encoding="utf-8",
    )
    assert tunnel_session.tunnel_session_valid() is False
    assert tunnel_session.session_connected_at() is None
