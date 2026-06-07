from __future__ import annotations

import re
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from netgarde_wg.constants import PRODUCTION_API_URL
from netgarde_wg.enroll.public_ip import fetch_public_ipv4
from netgarde_wg.gui.settings import log_file
from netgarde_wg.gui.tunnel_session import session_connected_at

_ENROLL_RE = re.compile(
    r"enroll ok endpoint=(\S+) address=(\S+) dns=(\S+)",
)
_INTERFACE_RE = re.compile(r"interface (\S+) up")
_DNS_RE = re.compile(r"DNS applied: (.+)")
_TRAFFIC_RE = re.compile(
    r"traffic \+([\d.]+) MiB down \(([\d.]+) MiB/s\), \+([\d.]+) MiB up \(([\d.]+) MiB/s\)",
)
_IP_HOST_RE = re.compile(
    r"^(?:\d{1,3}\.){3}\d{1,3}$|^(?:[0-9a-fA-F:]{2,}:)+[0-9a-fA-F:]{2,}$"
)

DEFAULT_SERVICE_NAME = "NetGarde"
DEFAULT_GATEWAY_NAME = "NetGarde gateway"


@dataclass
class TunnelConnectionInfo:
    endpoint: str = ""
    address: str = ""
    dns: str = ""
    interface: str = ""
    down_total_mib: str = ""
    up_total_mib: str = ""
    last_down_mib_s: str = ""
    last_up_mib_s: str = ""


@dataclass(frozen=True)
class ConnectionSnapshot:
    connected: bool
    status_label: str
    server_display: str
    gateway_display: str
    vpn_address: str
    dns: str
    hostname: str
    public_ip: str
    connected_for: str
    down_rate: str
    up_rate: str
    down_total: str
    up_total: str


def parse_tunnel_log(lines: list[str]) -> TunnelConnectionInfo:
    info = TunnelConnectionInfo()
    for line in lines:
        line = line.strip()
        if not line.startswith("netgarde-wg:"):
            continue
        body = line[len("netgarde-wg:") :].strip()
        if m := _ENROLL_RE.search(body):
            info.endpoint = m.group(1)
            info.address = m.group(2)
            info.dns = m.group(3)
            continue
        if m := _INTERFACE_RE.search(body):
            info.interface = m.group(1)
            continue
        if m := _DNS_RE.search(body):
            info.dns = m.group(1).strip()
            continue
        if m := _TRAFFIC_RE.search(body):
            info.down_total_mib = m.group(1)
            info.last_down_mib_s = m.group(2)
            info.up_total_mib = m.group(3)
            info.last_up_mib_s = m.group(4)
    return info


def _read_log_lines(path: Path | None = None) -> list[str]:
    target = path or log_file()
    if not target.is_file():
        return []
    try:
        return target.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def _format_duration(seconds: float) -> str:
    if seconds < 0:
        return "—"
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _looks_like_ip(host: str) -> bool:
    return bool(_IP_HOST_RE.match(host.strip()))


def friendly_service_name(api_url: str) -> str:
    url = api_url.strip()
    if not url:
        return "Not configured"
    if url.rstrip("/") == PRODUCTION_API_URL.rstrip("/"):
        return DEFAULT_SERVICE_NAME
    parsed = urlparse(url)
    host = (parsed.hostname or "").strip()
    if host and not _looks_like_ip(host):
        return host
    return DEFAULT_SERVICE_NAME


def friendly_gateway_name(endpoint_host: str) -> str:
    if not endpoint_host or endpoint_host == "—":
        return "—"
    return DEFAULT_GATEWAY_NAME


def build_connection_snapshot(
    *,
    connected: bool,
    api_url: str,
    log_path: Path | None = None,
    include_public_ip: bool = True,
) -> ConnectionSnapshot:
    lines = _read_log_lines(log_path)
    info = parse_tunnel_log(lines)
    public_ip = fetch_public_ipv4() if (connected and include_public_ip) else ""
    connected_at = session_connected_at()
    connected_for = _format_duration(time.time() - connected_at) if connected and connected_at else "—"
    endpoint_host = info.endpoint or "—"

    return ConnectionSnapshot(
        connected=connected,
        status_label="Connected" if connected else "Disconnected",
        server_display=friendly_service_name(api_url),
        gateway_display=friendly_gateway_name(endpoint_host),
        vpn_address=info.address or "—",
        dns=info.dns or "—",
        hostname=socket.gethostname() or "—",
        public_ip=public_ip or "—",
        connected_for=connected_for if connected else "—",
        down_rate=f"{info.last_down_mib_s} MiB/s" if info.last_down_mib_s else "—",
        up_rate=f"{info.last_up_mib_s} MiB/s" if info.last_up_mib_s else "—",
        down_total=f"{info.down_total_mib} MiB" if info.down_total_mib else "—",
        up_total=f"{info.up_total_mib} MiB" if info.up_total_mib else "—",
    )


def menu_detail_lines(snapshot: ConnectionSnapshot) -> tuple[str, str, str]:
    if snapshot.connected:
        line1 = f"VPN IP: {snapshot.vpn_address}"
        line2 = f"Gateway: {snapshot.gateway_display}"
        if snapshot.down_rate != "—" and snapshot.up_rate != "—":
            line3 = f"Traffic: ↓ {snapshot.down_rate}  ↑ {snapshot.up_rate}"
        else:
            line3 = "Traffic: collecting samples…"
        return line1, line2, line3
    return (
        "VPN IP: —",
        f"Service: {snapshot.server_display}",
        "Click Connect to join the network",
    )
