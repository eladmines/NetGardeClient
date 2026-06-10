from __future__ import annotations

import os

import pytest

from trustedge_wg.gui.settings import log_file, pid_file, settings_path, tunnel_runtime_dir


def test_settings_path_uses_user_data(tmp_user_data, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("trustedge_wg.gui.settings.user_data_dir", lambda: tmp_user_data)
    assert settings_path() == tmp_user_data / "gui-settings.json"


def test_tunnel_runtime_dir_and_files() -> None:
    uid = os.getuid()
    runtime = tunnel_runtime_dir(uid)
    assert runtime == pid_file(uid).parent
    assert log_file(uid) == runtime / "tunnel.log"
