from __future__ import annotations

from trustedge_wg.wireguard.config import WireGuardConfig
from trustedge_wg.wireguard.uapi import build_uapi


def test_build_uapi_includes_peer_and_endpoint(private_key: str, public_key: str) -> None:
    cfg = WireGuardConfig(
        private_key=private_key,
        public_key=public_key,
        endpoint="gw.example.com:51820",
        allowed_ips=["0.0.0.0/0", "::/0"],
        persistent_keepalive=25,
    )
    body = build_uapi(cfg)
    assert body.startswith("private_key=")
    assert "public_key=" in body
    assert "allowed_ip=0.0.0.0/0" in body
    assert "endpoint=gw.example.com:51820" in body
    assert "persistent_keepalive_interval=25" in body
    assert "replace_peers=true" in body
