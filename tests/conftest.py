from __future__ import annotations

from pathlib import Path

import pytest

from trustedge_wg import env as env_module
from trustedge_wg.constants import ENV_API_TOKEN, ENV_API_URL
from trustedge_wg.wireguard.keys import generate_private_key, public_key_from_private


@pytest.fixture(autouse=True)
def reset_dotenv_state(monkeypatch: pytest.MonkeyPatch) -> None:
    env_module._loaded = False
    monkeypatch.delenv(ENV_API_URL, raising=False)
    monkeypatch.delenv(ENV_API_TOKEN, raising=False)


@pytest.fixture
def private_key() -> str:
    return generate_private_key()


@pytest.fixture
def public_key(private_key: str) -> str:
    return public_key_from_private(private_key)


@pytest.fixture
def tmp_user_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "TrustEdgeClient"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("trustedge_wg.paths.user_data_dir", lambda: data_dir)
    return data_dir


@pytest.fixture
def sample_wireguard_ini(private_key: str, public_key: str) -> str:
    return f"""[Interface]
PrivateKey = {private_key}
Address = 10.0.0.3/32
DNS = 10.0.0.1
MTU = 1420

[Peer]
PublicKey = {public_key}
Endpoint = gw.example.com:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
