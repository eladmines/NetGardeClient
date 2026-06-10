from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from trustedge_wg.gui.connection_view import (
    _format_duration,
    build_connection_snapshot,
    friendly_service_name,
    menu_detail_lines,
    parse_tunnel_log,
)


SAMPLE_LOG = [
    "trustedge-wg: enroll ok endpoint=gw.example.com:51820 address=10.0.0.3/32 dns=10.0.0.1",
    "trustedge-wg: interface utun7 up",
    "trustedge-wg: DNS applied: 10.0.0.1",
    "trustedge-wg: traffic +1.5 MiB down (0.2 MiB/s), +0.5 MiB up (0.1 MiB/s)",
]


def test_parse_tunnel_log() -> None:
    info = parse_tunnel_log(SAMPLE_LOG)
    assert info.endpoint == "gw.example.com:51820"
    assert info.address == "10.0.0.3/32"
    assert info.dns == "10.0.0.1"
    assert info.interface == "utun7"
    assert info.down_total_mib == "1.5"
    assert info.last_down_mib_s == "0.2"


def test_friendly_service_name_not_configured() -> None:
    assert friendly_service_name("") == "Not configured"


def test_friendly_service_name_custom_host() -> None:
    assert friendly_service_name("https://staging.example.com") == "staging.example.com"


def test_build_connection_snapshot_from_log(tmp_path: Path, monkeypatch) -> None:
    log_path = tmp_path / "tunnel.log"
    log_path.write_text("\n".join(SAMPLE_LOG) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        "trustedge_wg.gui.connection_view.session_connected_at",
        lambda: None,
    )
    with patch("trustedge_wg.gui.connection_view.fetch_public_ipv4", return_value="203.0.113.1"):
        snap = build_connection_snapshot(
            connected=True,
            api_url="https://staging.example.com",
            log_path=log_path,
        )
    assert snap.vpn_address == "10.0.0.3/32"
    assert snap.gateway_display == "TrustEdge gateway"
    assert snap.public_ip == "203.0.113.1"
    assert snap.down_rate == "0.2 MiB/s"


def test_format_duration() -> None:
    assert _format_duration(45) == "45s"
    assert _format_duration(125) == "2m 5s"
    assert _format_duration(3725) == "1h 2m"
    assert _format_duration(-1) == "—"


def test_friendly_service_name_matches_configured_env(monkeypatch) -> None:
    monkeypatch.setattr(
        "trustedge_wg.gui.connection_view.env.api_url",
        lambda: "https://api.trustedge.example.com",
    )
    assert friendly_service_name("https://api.trustedge.example.com") == "TrustEdge"


def test_menu_detail_lines_connected_with_traffic() -> None:
    snap = replace(
        build_connection_snapshot(
            connected=True,
            api_url="https://api.example.com",
            include_public_ip=False,
        ),
        vpn_address="10.0.0.3/32",
        gateway_display="TrustEdge gateway",
        down_rate="1.0 MiB/s",
        up_rate="0.5 MiB/s",
    )
    line1, line2, line3 = menu_detail_lines(snap)
    assert "10.0.0.3/32" in line1
    assert "Gateway" in line2
    assert "Traffic" in line3


def test_menu_detail_lines_disconnected() -> None:
    snap = build_connection_snapshot(
        connected=False,
        api_url="https://api.example.com",
        include_public_ip=False,
    )
    line1, line2, line3 = menu_detail_lines(snap)
    assert line1 == "VPN IP: —"
    assert "Service:" in line2
    assert "Connect" in line3
