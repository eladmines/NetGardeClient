from __future__ import annotations

import ipaddress
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

Cleanup = Callable[[], None]


def apply_full_tunnel_routes(tun_name: str, endpoint_ips: list[ipaddress.IPv4Address]) -> Cleanup:
    if sys.platform == "darwin":
        from trustedge_wg.platform.routing.darwin import apply_full_tunnel_routes as _apply

        return _apply(tun_name, endpoint_ips)
    if sys.platform.startswith("linux"):
        from trustedge_wg.platform.routing.linux import apply_full_tunnel_routes as _apply

        return _apply(tun_name, endpoint_ips)
    if sys.platform == "win32":
        from trustedge_wg.platform.routing.windows import apply_full_tunnel_routes as _apply

        return _apply(tun_name, endpoint_ips)
    raise RuntimeError(f"full-tunnel routing is not implemented on {sys.platform}")
