from __future__ import annotations

import ipaddress
import json
import subprocess
from collections.abc import Callable

WINDOWS_ENDPOINT_BYPASS_METRIC = 9000
WINDOWS_TUNNEL_ROUTE_METRIC = 1

Cleanup = Callable[[], None]

_PS_DEFAULT_ROUTE = r"""
$r = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Sort-Object RouteMetric | Select-Object -First 1
if ($null -eq $r) { Write-Error 'no default route'; exit 1 }
$r | Select-Object -Property NextHop, InterfaceIndex | ConvertTo-Json -Compress
"""


def apply_full_tunnel_routes(
    tun_name: str, endpoint_ips: list[ipaddress.IPv4Address]
) -> Cleanup:
    gw, phys_if = _windows_default_route()
    tun_if = _windows_interface_index(tun_name)
    cleanups: list[Cleanup] = []

    for ip in endpoint_ips:
        args = [
            "add",
            str(ip),
            "mask",
            "255.255.255.255",
            str(gw),
            "METRIC",
            str(WINDOWS_ENDPOINT_BYPASS_METRIC),
            "IF",
            str(phys_if),
        ]
        try:
            _route(args)
        except RuntimeError:
            _rollback(cleanups)
            raise
        ip_s = str(ip)

        def _del_ep(i: str = ip_s, g: str = str(gw), pif: int = phys_if) -> None:
            subprocess.run(
                ["route", "delete", i, "mask", "255.255.255.255", g, "IF", str(pif)],
                capture_output=True,
            )

        cleanups.append(_del_ep)

    for dest, mask in (("0.0.0.0", "128.0.0.0"), ("128.0.0.0", "128.0.0.0")):
        args = [
            "add",
            dest,
            "mask",
            mask,
            "0.0.0.0",
            "METRIC",
            str(WINDOWS_TUNNEL_ROUTE_METRIC),
            "IF",
            str(tun_if),
        ]
        try:
            _route(args)
        except RuntimeError:
            _rollback(cleanups)
            raise
        d, m, tif = dest, mask, tun_if

        def _del_half(
            destination: str = d, netmask: str = m, iface: int = tif
        ) -> None:
            subprocess.run(
                ["route", "delete", destination, "mask", netmask, "0.0.0.0", "IF", str(iface)],
                capture_output=True,
            )

        cleanups.append(_del_half)

    return lambda: _rollback(cleanups)


def _rollback(cleanups: list[Cleanup]) -> None:
    for fn in reversed(cleanups):
        fn()


def _route(args: list[str]) -> None:
    r = subprocess.run(["route", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"route {args}: {r.stderr or r.stdout}")


def _windows_default_route() -> tuple[ipaddress.IPv4Address, int]:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", _PS_DEFAULT_ROUTE],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"powershell default route: {r.stderr or r.stdout}")
    row = json.loads(r.stdout.strip())
    gw = ipaddress.IPv4Address(row["NextHop"])
    if_index = int(row["InterfaceIndex"])
    if if_index <= 0:
        raise RuntimeError(f"invalid InterfaceIndex {if_index}")
    return gw, if_index


def _windows_interface_index(if_name: str) -> int:
    if_name = if_name.strip()
    if not if_name:
        raise RuntimeError("empty interface name")
    r = subprocess.run(
        ["netsh", "interface", "ipv4", "show", "interfaces"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"netsh show interfaces: {r.stderr or r.stdout}")
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("---"):
            continue
        fields = line.split()
        if len(fields) < 5:
            continue
        try:
            idx = int(fields[0])
        except ValueError:
            continue
        name = " ".join(fields[4:])
        if name.lower() == if_name.lower():
            return idx
    raise RuntimeError(
        f"no interface index for {if_name!r} (is Wintun installed and the adapter up?)"
    )
