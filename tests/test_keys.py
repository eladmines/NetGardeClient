from __future__ import annotations

import base64

import pytest

from trustedge_wg.wireguard.keys import (
    clamp_private_key,
    generate_private_key,
    parse_key,
    public_key_from_private,
    validate_private_key,
)


def test_generate_and_derive_public_key_round_trip() -> None:
    private_key = generate_private_key()
    public_key = public_key_from_private(private_key)
    validate_private_key(private_key)
    assert len(base64.b64decode(private_key)) == 32
    assert len(base64.b64decode(public_key)) == 32
    assert public_key_from_private(private_key) == public_key


def test_parse_key_rejects_invalid_length() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        parse_key(base64.b64encode(b"short").decode())


def test_clamp_private_key_sets_required_bits() -> None:
    raw = bytes(range(32))
    clamped = clamp_private_key(raw)
    assert clamped[0] & 0b11111000 == clamped[0]
    assert clamped[31] & 0b01000000
