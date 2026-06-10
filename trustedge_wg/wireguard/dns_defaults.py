"""Default VPN DNS to the WireGuard server (dnsmasq on wg0)."""

from __future__ import annotations

import ipaddress
import logging

from trustedge_wg.wireguard.config import WireGuardConfig

log = logging.getLogger("trustedge-wg")

# VPC resolver bypasses server dnsmasq; use the tunnel gateway (.1) instead.
_AWS_VPC_DNS = frozenset({"172.31.0.2", "169.254.169.253"})


def infer_server_dns(addresses: list[str]) -> str | None:
    """Guess dnsmasq on the WG server: client 10.0.0.3/32 -> DNS 10.0.0.1."""
    for cidr in addresses:
        try:
            iface = ipaddress.ip_interface(cidr.strip())
        except ValueError:
            continue
        if not isinstance(iface, ipaddress.IPv4Interface):
            continue
        if iface.network.prefixlen >= 32:
            octets = bytearray(iface.ip.packed)
            octets[-1] = 1
            return str(ipaddress.IPv4Address(bytes(octets)))
        net = iface.network
        if net.num_addresses > 2:
            return str(net.network_address + 1)
    return None


def ensure_vpn_dns(cfg: WireGuardConfig) -> None:
    """Set DNS to server dnsmasq when missing or pointing at VPC resolver."""
    if not cfg.address:
        return

    inferred = infer_server_dns(cfg.address)
    if not inferred:
        return

    current = [d.strip() for d in cfg.dns if d.strip()]
    if not current:
        cfg.dns = [inferred]
        log.info("DNS not set; using WireGuard server dnsmasq at %s", inferred)
        return

    if any(d in _AWS_VPC_DNS for d in current):
        cfg.dns = [inferred]
        log.info(
            "DNS was %s (bypasses server dnsmasq); using %s instead",
            ", ".join(current),
            inferred,
        )
