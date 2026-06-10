from __future__ import annotations

import ipaddress
import sys
from unittest.mock import MagicMock, patch

import pytest

from trustedge_wg.platform.dns import apply_dns
from trustedge_wg.platform.routing import apply_full_tunnel_routes
from trustedge_wg.platform.routing.linux import _linux_default_route


def test_apply_dns_unsupported_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    with pytest.raises(RuntimeError, match="only implemented on macOS"):
        apply_dns(["10.0.0.1"])


def test_apply_full_tunnel_routes_unsupported_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "freebsd")
    with pytest.raises(RuntimeError, match="not implemented"):
        apply_full_tunnel_routes("wg0", [ipaddress.IPv4Address("203.0.113.1")])


def test_linux_default_route_parses_output() -> None:
    with patch(
        "trustedge_wg.platform.routing.linux.subprocess.check_output",
        return_value="default via 192.168.1.1 dev wlan0\n",
    ):
        assert _linux_default_route() == ("192.168.1.1", "wlan0")


def test_linux_apply_full_tunnel_routes_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    calls: list[list[str]] = []

    def fake_ip_route(args: list[str]) -> bool:
        calls.append(args)
        return True

    with (
        patch("trustedge_wg.platform.routing.linux._linux_default_route", return_value=("192.168.1.1", "eth0")),
        patch("trustedge_wg.platform.routing.linux._ip_route", side_effect=fake_ip_route),
        patch("trustedge_wg.platform.routing.linux.subprocess.run"),
    ):
        cleanup = apply_full_tunnel_routes("wg0", [ipaddress.IPv4Address("203.0.113.1")])
        assert callable(cleanup)
        assert any(args[:2] == ["replace", "203.0.113.1/32"] for args in calls)
        assert any(args[:2] == ["replace", "0.0.0.0/1"] for args in calls)
