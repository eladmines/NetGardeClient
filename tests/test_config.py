from __future__ import annotations

import io

import pytest

from trustedge_wg.wireguard.config import (
    WireGuardConfig,
    finalize_wireguard_config,
    parse_wireguard_config,
    render_wireguard_conf,
    split_list,
)


def test_split_list_strips_and_skips_empty() -> None:
    assert split_list(" 10.0.0.1, ,10.0.0.2 ") == ["10.0.0.1", "10.0.0.2"]


def test_parse_wireguard_config(sample_wireguard_ini: str, private_key: str, public_key: str) -> None:
    cfg = parse_wireguard_config(io.StringIO(sample_wireguard_ini))
    assert cfg.private_key == private_key
    assert cfg.public_key == public_key
    assert cfg.address == ["10.0.0.3/32"]
    assert cfg.dns == ["10.0.0.1"]
    assert cfg.mtu == 1420
    assert cfg.endpoint == "gw.example.com:51820"
    assert cfg.allowed_ips == ["0.0.0.0/0", "::/0"]
    assert cfg.persistent_keepalive == 25


def test_parse_wireguard_config_defaults_allowed_ips(private_key: str, public_key: str) -> None:
    ini = f"""[Interface]
PrivateKey = {private_key}
Address = 10.0.0.3/32

[Peer]
PublicKey = {public_key}
Endpoint = gw.example.com:51820
"""
    cfg = parse_wireguard_config(io.StringIO(ini))
    assert cfg.allowed_ips == ["0.0.0.0/0", "::/0"]


@pytest.mark.parametrize(
    "ini, message",
    [
        (
            """[Interface]
Address = 10.0.0.3/32
[Peer]
PublicKey = abc
Endpoint = x:51820
""",
            "missing PrivateKey",
        ),
        (
            """[Interface]
PrivateKey = abcdefghijklmnopqrstuvwxyz012345=
Address = 10.0.0.3/32
[Peer]
Endpoint = x:51820
""",
            "missing PublicKey",
        ),
    ],
)
def test_parse_wireguard_config_validation_errors(ini: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_wireguard_config(io.StringIO(ini))


def test_finalize_wireguard_config_infers_dns_from_address(private_key: str, public_key: str) -> None:
    cfg = WireGuardConfig(
        private_key=private_key,
        public_key=public_key,
        endpoint="gw.example.com:51820",
        address=["10.0.0.3/32"],
    )
    finalized = finalize_wireguard_config(cfg)
    assert finalized.dns == ["10.0.0.1"]


def test_render_and_reparse_round_trip(sample_wireguard_ini: str) -> None:
    cfg = parse_wireguard_config(io.StringIO(sample_wireguard_ini))
    rendered = render_wireguard_conf(cfg)
    reparsed = parse_wireguard_config(io.StringIO(rendered))
    assert reparsed.private_key == cfg.private_key
    assert reparsed.public_key == cfg.public_key
    assert reparsed.address == cfg.address
    assert reparsed.endpoint == cfg.endpoint
