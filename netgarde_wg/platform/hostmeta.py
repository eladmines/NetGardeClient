from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def first_physical_mac() -> str:
    if sys.platform.startswith("linux"):
        return _linux_first_mac()
    if sys.platform == "darwin":
        return _darwin_first_mac()
    if sys.platform == "win32":
        return _windows_first_mac()
    return ""


def _linux_first_mac() -> str:
    net = Path("/sys/class/net")
    if not net.is_dir():
        return ""
    for name in sorted(net.iterdir()):
        if name.name in ("lo",) or name.name.startswith(("docker", "veth", "br-", "wg")):
            continue
        oper = name / "operstate"
        if oper.is_file() and oper.read_text().strip() not in ("up", "unknown"):
            continue
        addr = name / "address"
        if not addr.is_file():
            continue
        mac = addr.read_text().strip().lower()
        if re.fullmatch(r"([0-9a-f]{2}:){5}[0-9a-f]{2}", mac) and mac != "00:00:00:00:00:00":
            return mac
    return ""


def _darwin_first_mac() -> str:
    try:
        out = subprocess.check_output(["ifconfig"], text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        return ""
    current = ""
    for line in out.splitlines():
        if line and not line.startswith("\t") and not line.startswith(" "):
            current = line.split(":")[0]
            if current == "lo0":
                current = ""
            continue
        if not current or current == "lo0":
            continue
        m = re.search(r"\bether\s+([0-9a-f:]{17})\b", line, re.I)
        if m:
            return m.group(1).lower()
    return ""


def _windows_first_mac() -> str:
    try:
        out = subprocess.check_output(
            ["getmac", "/fo", "csv", "/nh"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    for line in out.splitlines():
        parts = line.split(",")
        if len(parts) < 2:
            continue
        mac = parts[0].strip().strip('"').replace("-", ":").lower()
        if re.fullmatch(r"([0-9a-f]{2}:){5}[0-9a-f]{2}", mac):
            return mac
    return ""
