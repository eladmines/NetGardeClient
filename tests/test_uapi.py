from __future__ import annotations

import sys

import pytest

from trustedge_wg.wireguard.config import WireGuardConfig
from trustedge_wg.wireguard.uapi import _allowed_ips_for_uapi, build_uapi


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


def test_allowed_ips_for_uapi_filters_ipv6_on_darwin(private_key: str, public_key: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    cfg = WireGuardConfig(
        private_key=private_key,
        public_key=public_key,
        endpoint="gw:51820",
        allowed_ips=["0.0.0.0/0", "::/0"],
    )
    assert _allowed_ips_for_uapi(cfg) == ["0.0.0.0/0"]


def test_build_uapi_includes_preshared_key(private_key: str, public_key: str) -> None:
    psk = "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC="
    cfg = WireGuardConfig(
        private_key=private_key,
        public_key=public_key,
        endpoint="gw:51820",
        preshared_key=psk,
        allowed_ips=["0.0.0.0/0"],
    )
    assert "preshared_key=" in build_uapi(cfg)
