from __future__ import annotations

import pytest

from trustedge_wg.enroll.api import (
    Client,
    EnrollResponse,
    inject_local_private_key_into_ini,
    wireguard_from_enroll,
)


def test_client_normalizes_base_url_and_paths() -> None:
    client = Client(
        "https://api.example.com/",
        enroll_path="v1/enroll",
        usage_path="v1/usage",
        policy_ca_path="policy/block-page-ca",
    )
    assert client.base_url == "https://api.example.com"
    assert client.enroll_path == "/v1/enroll"
    assert client.usage_path == "/v1/usage"
    assert client.policy_ca_path == "/policy/block-page-ca"


def test_client_rejects_empty_base_url() -> None:
    with pytest.raises(ValueError, match="empty base URL"):
        Client("  ")


def test_wireguard_from_enroll_structured_response(private_key: str, public_key: str) -> None:
    resp = EnrollResponse(
        address="10.0.0.3/32",
        dns=["10.0.0.1"],
        server_public_key=public_key,
        endpoint="gw.example.com:51820",
        allowed_ips=["0.0.0.0/0"],
        persistent_keepalive=25,
        mtu=1420,
    )
    cfg = wireguard_from_enroll(private_key, resp)
    assert cfg.private_key == private_key
    assert cfg.public_key == public_key
    assert cfg.address == ["10.0.0.3/32"]
    assert cfg.endpoint == "gw.example.com:51820"
    assert cfg.dns == ["10.0.0.1"]


def test_wireguard_from_enroll_wireguard_conf_ini(private_key: str, public_key: str) -> None:
    ini = f"""[Interface]
Address = 10.0.0.4/32

[Peer]
PublicKey = {public_key}
Endpoint = gw.example.com:51820
AllowedIPs = 0.0.0.0/0
"""
    resp = EnrollResponse(wireguard_conf=ini)
    cfg = wireguard_from_enroll(private_key, resp)
    assert cfg.private_key == private_key
    assert cfg.address == ["10.0.0.4/32"]


def test_wireguard_from_enroll_requires_private_key(public_key: str) -> None:
    resp = EnrollResponse(server_public_key=public_key, endpoint="x:51820", address="10.0.0.1/32")
    with pytest.raises(ValueError, match="private key"):
        wireguard_from_enroll("", resp)


def test_inject_local_private_key_into_interface_section(private_key: str) -> None:
    ini = "[Interface]\nAddress = 10.0.0.3/32\n\n[Peer]\nPublicKey = x\nEndpoint = y:51820\n"
    out = inject_local_private_key_into_ini(ini, private_key)
    assert f"PrivateKey = {private_key}" in out
    assert out.startswith("[Interface]")


def test_inject_local_private_key_preserves_existing(private_key: str) -> None:
    ini = f"[Interface]\nPrivateKey = {private_key}\nAddress = 10.0.0.3/32\n"
    assert inject_local_private_key_into_ini(ini, "other") == ini


def test_wireguard_from_enroll_rejects_mismatched_server_private_key(
    private_key: str,
    public_key: str,
) -> None:
    from trustedge_wg.wireguard.keys import generate_private_key

    other_private = generate_private_key()
    ini = f"""[Interface]
PrivateKey = {other_private}
Address = 10.0.0.3/32

[Peer]
PublicKey = {public_key}
Endpoint = gw:51820
"""
    resp = EnrollResponse(wireguard_conf=ini)
    with pytest.raises(ValueError, match="does not match local key"):
        wireguard_from_enroll(private_key, resp)
