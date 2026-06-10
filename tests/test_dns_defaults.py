from __future__ import annotations

from trustedge_wg.wireguard.config import WireGuardConfig
from trustedge_wg.wireguard.dns_defaults import ensure_vpn_dns, infer_server_dns


def test_infer_server_dns_from_client_address() -> None:
    assert infer_server_dns(["10.0.0.3/32"]) == "10.0.0.1"


def test_infer_server_dns_from_subnet() -> None:
    assert infer_server_dns(["10.0.0.0/24"]) == "10.0.0.1"


def test_ensure_vpn_dns_fills_missing_dns(private_key: str, public_key: str) -> None:
    cfg = WireGuardConfig(
        private_key=private_key,
        public_key=public_key,
        endpoint="gw:51820",
        address=["10.0.0.3/32"],
    )
    ensure_vpn_dns(cfg)
    assert cfg.dns == ["10.0.0.1"]


def test_ensure_vpn_dns_replaces_vpc_resolver(private_key: str, public_key: str) -> None:
    cfg = WireGuardConfig(
        private_key=private_key,
        public_key=public_key,
        endpoint="gw:51820",
        address=["10.0.0.3/32"],
        dns=["172.31.0.2"],
    )
    ensure_vpn_dns(cfg)
    assert cfg.dns == ["10.0.0.1"]
