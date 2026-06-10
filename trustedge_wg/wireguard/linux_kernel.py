from __future__ import annotations

import shutil
import sys
from pathlib import Path

if sys.platform == "win32":
    WG_SOCKET_DIR: Path | None = None
else:
    WG_SOCKET_DIR = Path("/var/run/wireguard")


def linux_kernel_available() -> bool:
    if not shutil.which("wg"):
        return False
    return Path("/sys/module/wireguard").exists() or Path("/sys/module/wireguard_mod").exists()
