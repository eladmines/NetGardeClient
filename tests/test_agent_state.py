from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from trustedge_wg.agent.state import AgentState, ensure_agent_state
from trustedge_wg.constants import STATE_FILE_PERM
from trustedge_wg.wireguard.keys import generate_private_key, public_key_from_private


def test_ensure_agent_state_creates_file_on_first_run(tmp_path: Path) -> None:
    path = tmp_path / "agent-state.json"
    st = ensure_agent_state(str(path))
    assert path.is_file()
    assert len(st.device_id) == 32
    assert st.public_key() == public_key_from_private(st.private_key)
    mode = stat.S_IMODE(path.stat().st_mode)
    assert mode == STATE_FILE_PERM


def test_ensure_agent_state_loads_existing(tmp_path: Path) -> None:
    private_key = generate_private_key()
    path = tmp_path / "agent-state.json"
    path.write_text(
        json.dumps({"device_id": "abc123", "private_key": private_key, "device_token": "tok"}),
        encoding="utf-8",
    )
    st = ensure_agent_state(str(path))
    assert st.device_id == "abc123"
    assert st.private_key == private_key
    assert st.device_token == "tok"


def test_ensure_agent_state_rejects_invalid_key(tmp_path: Path) -> None:
    path = tmp_path / "agent-state.json"
    path.write_text(
        json.dumps({"device_id": "abc123", "private_key": "not-a-valid-key"}),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="wireguard key"):
        ensure_agent_state(str(path))


def test_agent_state_save_atomic_replace(tmp_path: Path) -> None:
    private_key = generate_private_key()
    path = tmp_path / "agent-state.json"
    st = AgentState(device_id="device1", private_key=private_key)
    st.save(str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["device_id"] == "device1"
    assert not (tmp_path / "agent-state.json.tmp").exists()
