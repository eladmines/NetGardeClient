from __future__ import annotations

import logging
import subprocess
from pathlib import Path

log = logging.getLogger("netgarde-wg")


def install_trusted_root_ca(ca_pem: bytes, *, keychain: str = "/Library/Keychains/System.keychain") -> None:
    """Add NetGarde Policy CA to macOS System keychain (requires sudo)."""
    cache_dir = Path.home() / "Library" / "Application Support" / "netgarde"
    cache_dir.mkdir(parents=True, exist_ok=True)
    ca_path = cache_dir / "netgarde-policy-ca.crt"
    ca_path.write_bytes(ca_pem)
    ca_path.chmod(0o644)

    cmd = [
        "sudo",
        "security",
        "add-trusted-cert",
        "-d",
        "-r",
        "trustRoot",
        "-k",
        keychain,
        str(ca_path),
    ]
    log.info("installing NetGarde Policy CA to System keychain (sudo required)")
    subprocess.run(cmd, check=True)
    log.info("NetGarde Policy CA installed: %s", ca_path)
