from __future__ import annotations

import ipaddress
import subprocess
from collections.abc import Callable

Cleanup = Callable[[], None]


def apply_full_tunnel_routes(
    tun_name: str, endpoint_ips: list[ipaddress.IPv4Address]
) -> Cleanup:
    gw, iface = _linux_default_route()
    cleanups: list[Cleanup] = []

    for ip in endpoint_ips:
        cidr = f"{ip}/32"
        ok = _ip_route(["replace", cidr, "via", gw, "dev", iface])
        if not ok:
            ok = _ip_route(["add", cidr, "via", gw, "dev", iface])
        if not ok:
            _rollback(cleanups)
            raise RuntimeError(f"ip route for endpoint {ip}")

        def _del_ep(i: str = cidr) -> None:
            subprocess.run(["ip", "-4", "route", "del", i], capture_output=True)

        cleanups.append(_del_ep)

    for half in ("0.0.0.0/1", "128.0.0.0/1"):
        if not _ip_route(["replace", half, "dev", tun_name]) and not _ip_route(["add", half, "dev", tun_name]):
            _rollback(cleanups)
            raise RuntimeError(f"ip route add {half} dev {tun_name}")
        h = half

        def _del_half(route: str = h, dev: str = tun_name) -> None:
            subprocess.run(["ip", "-4", "route", "del", route, "dev", dev], capture_output=True)

        cleanups.append(_del_half)

    return lambda: _rollback(cleanups)


def _rollback(cleanups: list[Cleanup]) -> None:
    for fn in reversed(cleanups):
        fn()


def _ip_route(args: list[str]) -> bool:
    r = subprocess.run(["ip", "-4", "route", *args], capture_output=True, text=True)
    return r.returncode == 0


def _linux_default_route() -> tuple[str, str]:
    try:
        out = subprocess.check_output(["ip", "-4", "route", "show", "default"], text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ip route show default: {e}") from e
    line = out.strip().split("\n", 1)[0].strip()
    if not line:
        raise RuntimeError("no default route")
    fields = line.split()
    via_idx = dev_idx = -1
    for i, f in enumerate(fields):
        if f == "via":
            via_idx = i
        elif f == "dev":
            dev_idx = i
    if via_idx < 0 or dev_idx < 0 or via_idx + 1 >= len(fields) or dev_idx + 1 >= len(fields):
        raise RuntimeError(f"unparsed default route: {line!r}")
    return fields[via_idx + 1], fields[dev_idx + 1]
