from __future__ import annotations

import ipaddress
import subprocess
from collections.abc import Callable

Cleanup = Callable[[], None]


def apply_full_tunnel_routes(
    tun_name: str, endpoint_ips: list[ipaddress.IPv4Address]
) -> Cleanup:
    gw = _darwin_default_gateway()
    cleanups: list[Cleanup] = []

    for ip in endpoint_ips:
        cidr = f"{ip}/32"
        try:
            subprocess.run(
                ["route", "-q", "-n", "add", "-inet", cidr, gw],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            _rollback(cleanups)
            raise RuntimeError(f"route add host {ip} via {gw}: {e.stderr or e}") from e
        ip_s = str(ip)

        def _del_host(i: str = ip_s, g: str = gw) -> None:
            subprocess.run(
                ["route", "-q", "-n", "delete", "-inet", f"{i}/32", g],
                capture_output=True,
            )

        cleanups.append(_del_host)

    for half in ("0.0.0.0/1", "128.0.0.0/1"):
        try:
            subprocess.run(
                ["route", "-q", "-n", "add", "-inet", half, "-interface", tun_name],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            _rollback(cleanups)
            raise RuntimeError(f"route add {half} -interface {tun_name}: {e.stderr or e}") from e
        h = half

        def _del_half(route: str = h, iface: str = tun_name) -> None:
            subprocess.run(
                ["route", "-q", "-n", "delete", "-inet", route, "-interface", iface],
                capture_output=True,
            )

        cleanups.append(_del_half)

    return lambda: _rollback(cleanups)


def _rollback(cleanups: list[Cleanup]) -> None:
    for fn in reversed(cleanups):
        fn()


def _darwin_default_gateway() -> str:
    try:
        out = subprocess.check_output(["route", "-n", "get", "default"], text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"route get default: {e.output}") from e
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("gateway:"):
            gw = line.split(":", 1)[1].strip()
            if gw:
                return gw
    raise RuntimeError("no gateway in route output")
