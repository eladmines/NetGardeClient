from __future__ import annotations

import subprocess
from collections.abc import Callable

Cleanup = Callable[[], None]


def apply_dns(servers: list[str], service_override: str = "") -> Cleanup:
    svc = service_override.strip()
    if not svc:
        svc = _darwin_primary_network_service()
    prev = _darwin_get_dns_servers(svc)
    _darwin_set_dns_servers(svc, servers)

    def restore() -> None:
        _darwin_set_dns_servers(svc, prev)

    return restore


def _darwin_primary_network_service() -> str:
    try:
        out = subprocess.check_output(["route", "-n", "get", "default"], text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"route get default: {e.output}") from e
    iface = ""
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("interface:"):
            iface = line.split(":", 1)[1].strip()
            break
    if not iface:
        raise RuntimeError("could not determine default route interface")

    try:
        ns_out = subprocess.check_output(
            ["networksetup", "-listnetworkserviceorder"],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"networksetup -listnetworkserviceorder: {e.output}") from e

    cur_service = ""
    for raw in ns_out.splitlines():
        line = raw.strip()
        if line.startswith("(") and ")" in line:
            idx = line.index(")")
            if idx + 1 < len(line):
                cur_service = line[idx + 1 :].strip()
            continue
        if not cur_service:
            continue
        dev, ok = _darwin_extract_device_token(line)
        if ok and dev == iface:
            return cur_service

    svc = _darwin_service_from_hardware_ports(iface)
    if svc:
        return svc

    raise RuntimeError(
        f'could not map interface "{iface}" to a network service '
        '(try --dns-service "Wi-Fi")'
    )


def _darwin_service_from_hardware_ports(iface: str) -> str | None:
    """Map en0 -> Wi-Fi via networksetup -listallhardwareports."""
    try:
        out = subprocess.check_output(
            ["networksetup", "-listallhardwareports"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    port = ""
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Hardware Port:"):
            port = line.split(":", 1)[1].strip()
        elif line.startswith("Device:"):
            dev = line.split(":", 1)[1].strip()
            if dev == iface and port:
                return port
    return None


def _darwin_extract_device_token(line: str) -> tuple[str, bool]:
    i = line.find("Device:")
    if i < 0:
        return "", False
    rest = line[i + len("Device:") :].strip()
    if not rest:
        return "", False
    end = len(rest)
    for j, ch in enumerate(rest):
        if ch in "),\t ":
            end = j
            break
    if end <= 0:
        return "", False
    return rest[:end], True


def _darwin_get_dns_servers(service: str) -> list[str]:
    try:
        out = subprocess.check_output(
            ["networksetup", "-getdnsservers", service],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"networksetup -getdnsservers {service!r}: {e.output}") from e
    s = out.strip()
    if "There aren't any DNS Servers set" in s:
        return ["empty"]
    servers = [ln.strip() for ln in s.splitlines() if ln.strip()]
    return servers or ["empty"]


def _darwin_set_dns_servers(service: str, servers: list[str]) -> None:
    args = ["networksetup", "-setdnsservers", service]
    if len(servers) == 1 and servers[0].lower() in ("empty",):
        args.append("Empty")
    else:
        for s in servers:
            t = s.strip()
            if t:
                args.append(t)
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"networksetup {args}: {r.stderr or r.stdout}")
