from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import IO, TextIO


@dataclass
class WireGuardConfig:
    private_key: str
    address: list[str] = field(default_factory=list)
    dns: list[str] = field(default_factory=list)
    mtu: int = 0
    listen_port: int = 0
    public_key: str = ""
    preshared_key: str = ""
    endpoint: str = ""
    allowed_ips: list[str] = field(default_factory=list)
    persistent_keepalive: int = 0


def split_list(s: str) -> list[str]:
    return [p.strip() for p in s.split(",") if p.strip()]


def parse_wireguard_config(r: TextIO | IO[str]) -> WireGuardConfig:
    cfg = WireGuardConfig(private_key="")
    section = ""

    for raw in r:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].lower()
            continue
        if "=" not in line:
            continue
        key, val = (p.strip() for p in line.split("=", 1))

        if section == "interface":
            if key == "PrivateKey":
                cfg.private_key = val
            elif key == "Address":
                cfg.address.extend(split_list(val))
            elif key == "DNS":
                cfg.dns.extend(split_list(val))
            elif key == "MTU":
                try:
                    m = int(val)
                    if m > 0:
                        cfg.mtu = m
                except ValueError:
                    pass
            elif key == "ListenPort":
                try:
                    cfg.listen_port = int(val)
                except ValueError:
                    pass
        elif section == "peer":
            if key == "PublicKey":
                cfg.public_key = val
            elif key == "PresharedKey":
                cfg.preshared_key = val
            elif key == "Endpoint":
                cfg.endpoint = val
            elif key == "AllowedIPs":
                cfg.allowed_ips.extend(split_list(val))
            elif key == "PersistentKeepalive":
                try:
                    cfg.persistent_keepalive = int(val)
                except ValueError:
                    pass

    if not cfg.private_key:
        raise ValueError("missing PrivateKey under [Interface]")
    if not cfg.public_key:
        raise ValueError("missing PublicKey under [Peer]")
    if not cfg.endpoint:
        raise ValueError("missing Endpoint under [Peer]")
    if not cfg.address:
        raise ValueError("missing Address under [Interface]")
    if not cfg.allowed_ips:
        cfg.allowed_ips = ["0.0.0.0/0", "::/0"]
    return cfg


def finalize_wireguard_config(cfg: WireGuardConfig) -> WireGuardConfig:
    if not cfg.allowed_ips:
        cfg.allowed_ips = ["0.0.0.0/0", "::/0"]
    from netgarde_wg.wireguard.dns_defaults import ensure_vpn_dns

    ensure_vpn_dns(cfg)
    return cfg


def load_config(path: str) -> WireGuardConfig:
    with open(path, encoding="utf-8") as f:
        cfg = parse_wireguard_config(f)
    return finalize_wireguard_config(cfg)


def render_wireguard_conf(cfg: WireGuardConfig) -> str:
    lines = ["[Interface]", f"PrivateKey = {cfg.private_key}"]
    for a in cfg.address:
        lines.append(f"Address = {a}")
    for d in cfg.dns:
        lines.append(f"DNS = {d}")
    if cfg.mtu > 0:
        lines.append(f"MTU = {cfg.mtu}")
    if cfg.listen_port > 0:
        lines.append(f"ListenPort = {cfg.listen_port}")
    lines.append("")
    lines.append("[Peer]")
    lines.append(f"PublicKey = {cfg.public_key}")
    if cfg.preshared_key:
        lines.append(f"PresharedKey = {cfg.preshared_key}")
    lines.append(f"Endpoint = {cfg.endpoint}")
    if cfg.allowed_ips:
        lines.append(f"AllowedIPs = {', '.join(cfg.allowed_ips)}")
    if cfg.persistent_keepalive > 0:
        lines.append(f"PersistentKeepalive = {cfg.persistent_keepalive}")
    return "\n".join(lines) + "\n"
