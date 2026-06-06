from __future__ import annotations

import ipaddress
import sys

from netgarde_wg.wireguard.config import WireGuardConfig
from netgarde_wg.wireguard.keys import parse_key


def _allowed_ips_for_uapi(cfg: WireGuardConfig) -> list[str]:
    """wireguard-go on macOS mishandles ::/0; use IPv4 routes only."""
    raw = cfg.allowed_ips or ["0.0.0.0/0"]
    if sys.platform != "darwin":
        return [c.strip() for c in raw if c.strip()]
    v4: list[str] = []
    for cidr in raw:
        c = cidr.strip()
        if not c:
            continue
        try:
            net = ipaddress.ip_network(c, strict=False)
        except ValueError:
            continue
        if isinstance(net, ipaddress.IPv4Network):
            v4.append(c)
    return v4 or ["0.0.0.0/0"]


def build_uapi(cfg: WireGuardConfig) -> str:
    sk = parse_key(cfg.private_key)
    pk = parse_key(cfg.public_key)

    lines = [
        f"private_key={sk.hex()}",
        f"listen_port={cfg.listen_port if cfg.listen_port > 0 else 0}",
        "replace_peers=true",
        f"public_key={pk.hex()}",
        "protocol_version=1",
        "replace_allowed_ips=true",
    ]
    for cidr in _allowed_ips_for_uapi(cfg):
        lines.append(f"allowed_ip={cidr}")
    lines.append(f"endpoint={cfg.endpoint.strip()}")
    if cfg.persistent_keepalive > 0:
        lines.append(f"persistent_keepalive_interval={cfg.persistent_keepalive}")
    if cfg.preshared_key.strip():
        psk = parse_key(cfg.preshared_key)
        lines.append(f"preshared_key={psk.hex()}")
    lines.append("")
    return "\n".join(lines)
