"""Best-effort public IPv4 before VPN tunnel (for enroll geo)."""

from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from trustedge_wg.constants import HTTP_CLIENT_TIMEOUT

_IPIFY_URL = "https://api.ipify.org?format=json"


def fetch_public_ipv4() -> str:
    """Return the machine's public IPv4, or empty string on failure."""
    req = Request(_IPIFY_URL, method="GET")
    try:
        with urlopen(req, timeout=HTTP_CLIENT_TIMEOUT) as resp:
            raw = resp.read(512)
    except URLError:
        return ""
    try:
        obj = json.loads(raw.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return ""
    ip = str(obj.get("ip") or "").strip()
    return ip
