from __future__ import annotations

import ipaddress
from unittest.mock import patch

import pytest

from trustedge_wg.constants import DEFAULT_WIREGUARD_PORT
from trustedge_wg.wireguard.tunnel import normalize_endpoint, resolve_endpoint_v4


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


def test_resolve_endpoint_v4_dns_lookup() -> None:
    fake_info = [(2, 2, 17, "", ("198.51.100.5", 0))]
    with patch("trustedge_wg.wireguard.tunnel.socket.getaddrinfo", return_value=fake_info):
        ips = resolve_endpoint_v4("gw.example.com")
    assert ips == [ipaddress.IPv4Address("198.51.100.5")]
