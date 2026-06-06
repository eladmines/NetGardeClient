from __future__ import annotations

import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from netgarde_wg.wireguard.config import WireGuardConfig

if sys.platform == "win32":
    WG_SOCKET_DIR: Path | None = None
else:
    WG_SOCKET_DIR = Path("/var/run/wireguard")


@dataclass(frozen=True)
class TransferStats:
    rx_bytes: int
    tx_bytes: int

    @property
    def rx_mib(self) -> float:
        return self.rx_bytes / (1024 * 1024)

    @property
    def tx_mib(self) -> float:
        return self.tx_bytes / (1024 * 1024)


def mib(n: int) -> float:
    return n / (1024 * 1024)


def delta(prev: TransferStats, cur: TransferStats) -> tuple[int, int]:
    return max(0, cur.rx_bytes - prev.rx_bytes), max(0, cur.tx_bytes - prev.tx_bytes)


def read_transfer_stats(
    cfg: WireGuardConfig,
    tun_name: str,
    *,
    interface: str = "wg0",
    wintun_adapter: str = "NetGarde",
) -> TransferStats:
    if sys.platform.startswith("linux") and _linux_kernel_available():
        return _read_wg_show(interface or tun_name, cfg.public_key)
    if sys.platform == "win32":
        return _read_wg_show(wintun_adapter, cfg.public_key)
    sock = uapi_socket_path(tun_name)
    if sock and sock.exists():
        return _read_uapi_get(sock)
    if shutil.which("wg"):
        return _read_wg_show(tun_name, cfg.public_key)
    raise RuntimeError("cannot read WireGuard transfer stats (no wg tool or UAPI socket)")


def uapi_socket_path(tun_name: str) -> Path | None:
    if WG_SOCKET_DIR is None:
        return None
    return WG_SOCKET_DIR / f"{tun_name}.sock"


def _linux_kernel_available() -> bool:
    if not shutil.which("wg"):
        return False
    return Path("/sys/module/wireguard").exists() or Path("/sys/module/wireguard_mod").exists()


def _read_wg_show(iface: str, peer_pubkey: str = "") -> TransferStats:
    r = subprocess.run(
        ["wg", "show", iface],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"wg show {iface!r}: {r.stderr or r.stdout}")
    return _parse_wg_show(r.stdout, peer_pubkey.strip())


def _parse_wg_show(text: str, peer_pubkey: str = "") -> TransferStats:
    rx = tx = 0
    in_peer = False
    peer_match = not peer_pubkey
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("peer:"):
            in_peer = True
            key = line.split(":", 1)[1].strip()
            peer_match = not peer_pubkey or key == peer_pubkey
            continue
        if line.startswith("interface:"):
            in_peer = False
            continue
        if in_peer and peer_match and line.startswith("transfer:"):
            parts = line.split(":", 1)[1].strip().split(",")
            if len(parts) >= 2:
                rx = int(parts[0].strip())
                tx = int(parts[1].strip())
            break
    if rx == 0 and tx == 0 and peer_pubkey:
        return _parse_wg_show(text, "")
    return TransferStats(rx_bytes=rx, tx_bytes=tx)


def _read_uapi_get(sock_path: Path) -> TransferStats:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(str(sock_path))
        sock.sendall(b"get=1\n\n")
        sock.shutdown(socket.SHUT_WR)
        chunks: list[bytes] = []
        while True:
            part = sock.recv(8192)
            if not part:
                break
            chunks.append(part)
        text = b"".join(chunks).decode(errors="replace")
    finally:
        sock.close()
    if "errno=" in text and "errno=0" not in text:
        raise RuntimeError(f"wireguard uapi get failed: {text.strip()}")
    return _parse_uapi_get(text)


def _parse_uapi_get(text: str) -> TransferStats:
    rx = tx = 0
    for line in text.splitlines():
        line = line.strip()
        if m := re.match(r"rx_bytes=(\d+)", line):
            rx = int(m.group(1))
        elif m := re.match(r"tx_bytes=(\d+)", line):
            tx = int(m.group(1))
    return TransferStats(rx_bytes=rx, tx_bytes=tx)
