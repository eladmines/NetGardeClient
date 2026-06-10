from __future__ import annotations

import ipaddress
import sys
from unittest.mock import patch

import pytest

from trustedge_wg.constants import DEFAULT_WIREGUARD_PORT
from trustedge_wg.cli import CliConfig
from trustedge_wg.wireguard.tunnel import _userspace_iface_hint, normalize_endpoint, resolve_endpoint_v4


@pytest.mark.parametrize(
    "endpoint, expected",
    [
        ("gw.example.com:51820", "gw.example.com:51820"),
        ("gw.example.com", f"gw.example.com:{DEFAULT_WIREGUARD_PORT}"),
        ("[2001:db8::1]:51820", "[2001:db8::1]:51820"),
    ],
)
def test_normalize_endpoint(endpoint: str, expected: str) -> None:
    assert normalize_endpoint(endpoint) == expected


def test_resolve_endpoint_v4_literal_ip() -> None:
    ips = resolve_endpoint_v4("203.0.113.10")
    assert ips == [ipaddress.IPv4Address("203.0.113.10")]


def test_userspace_iface_hint_per_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    opts = CliConfig(interface="wg0")
    monkeypatch.setattr(sys, "platform", "darwin")
    assert _userspace_iface_hint(opts) == "utun"
    monkeypatch.setattr(sys, "platform", "linux")
    assert _userspace_iface_hint(opts) == "wg0"
    monkeypatch.setattr(sys, "platform", "win32")
    assert _userspace_iface_hint(opts) == "TrustEdge"


def test_resolve_endpoint_v4_dns_lookup() -> None:
    fake_info = [(2, 2, 17, "", ("198.51.100.5", 0))]
    with patch("trustedge_wg.wireguard.tunnel.socket.getaddrinfo", return_value=fake_info):
        ips = resolve_endpoint_v4("gw.example.com")
    assert ips == [ipaddress.IPv4Address("198.51.100.5")]
