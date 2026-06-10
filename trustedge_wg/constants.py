from __future__ import annotations

import os
from pathlib import Path

ENV_API_URL = "TRUSTEDGE_API_URL"
ENV_API_TOKEN = "TRUSTEDGE_API_TOKEN"

DEFAULT_ENROLL_PATH = "/v1/enroll"
DEFAULT_USAGE_PATH = "/v1/usage"
# POST /v1/usage every N seconds for dashboard Live network graph (0 = off)
DEFAULT_STATS_INTERVAL = 5.0
DEFAULT_POLICY_CA_PATH = "/policy/block-page-ca"
DEFAULT_WINTUN_NAME = "TrustEdge"
DEFAULT_WIREGUARD_PORT = "51820"
DEFAULT_MTU = 1420

MAX_ENROLL_RESPONSE_BYTES = 1 << 20
HTTP_CLIENT_TIMEOUT = 60

STATE_FILE_PERM = 0o600
CACHED_WG_CONF_PERM = 0o600


def _find_project_root() -> Path | None:
    here = Path(__file__).resolve().parent
    for parent in (here, *here.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    return None


def _load_dotenv_file(path: Path, *, override: bool = False) -> None:
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if override or key not in os.environ:
            os.environ[key] = value


def _load_dotenv() -> None:
    root = _find_project_root()
    if root is not None:
        _load_dotenv_file(root / ".env", override=False)
    try:
        from trustedge_wg.paths import user_data_dir

        _load_dotenv_file(user_data_dir() / ".env", override=True)
    except OSError:
        pass


_load_dotenv()

# API URL and token come from .env / environment — never hardcode production endpoints.
PRODUCTION_API_URL = os.environ.get(ENV_API_URL, "").strip()
