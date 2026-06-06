"""WireGuard key generation and validation."""

from __future__ import annotations

import base64
import os
import secrets

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


def clamp_private_key(key: bytes) -> bytes:
    k = bytearray(key)
    k[0] &= 248
    k[31] &= 127
    k[31] |= 64
    return bytes(k)


def parse_key(b64_key: str) -> bytes:
    raw = base64.b64decode(b64_key.strip())
    if len(raw) != 32:
        raise ValueError("wireguard key must be 32 bytes after base64 decode")
    return raw


def generate_private_key() -> str:
    return base64.b64encode(clamp_private_key(os.urandom(32))).decode()


def public_key_from_private(b64_private: str) -> str:
    priv = clamp_private_key(parse_key(b64_private))
    pk = X25519PrivateKey.from_private_bytes(priv).public_key().public_bytes_raw()
    return base64.b64encode(pk).decode()


def validate_private_key(b64_private: str) -> None:
    parse_key(b64_private)
