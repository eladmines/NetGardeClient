from __future__ import annotations

import json
import os
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path

from netgarde_wg.constants import STATE_FILE_PERM
from netgarde_wg.wireguard.keys import generate_private_key, public_key_from_private, validate_private_key


@dataclass
class AgentState:
    device_id: str
    private_key: str
    device_token: str = ""

    def public_key(self) -> str:
        return public_key_from_private(self.private_key)

    def save(self, path: str) -> None:
        self._validate()
        p = Path(path)
        if p.parent != Path("."):
            p.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(asdict(self), indent=2) + "\n"
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(data)
        os.chmod(tmp, STATE_FILE_PERM)
        os.replace(tmp, path)

    def _validate(self) -> None:
        if not self.device_id.strip():
            raise ValueError("empty device_id")
        if not self.private_key.strip():
            raise ValueError("empty private_key")
        validate_private_key(self.private_key)


def _new_agent_state() -> AgentState:
    return AgentState(
        device_id=secrets.token_hex(16),
        private_key=generate_private_key(),
    )


def ensure_agent_state(path: str) -> AgentState:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        st = _new_agent_state()
        st.save(path)
        return st
    except OSError as e:
        raise RuntimeError(f"read state {path!r}: {e}") from e

    st = AgentState(
        device_id=str(data.get("device_id", "")),
        private_key=str(data.get("private_key", "")),
        device_token=str(data.get("device_token", "") or ""),
    )
    try:
        st._validate()
    except ValueError as e:
        raise RuntimeError(f"state {path!r}: {e}") from e
    return st
