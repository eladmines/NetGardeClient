from __future__ import annotations

import sys
from collections.abc import Callable

Cleanup = Callable[[], None]


def apply_dns(servers: list[str], service_override: str = "") -> Cleanup:
    if sys.platform == "darwin":
        from trustedge_wg.platform.dns.darwin import apply_dns as _apply

        return _apply(servers, service_override)
    raise RuntimeError("dns apply is only implemented on macOS (darwin)")
