from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock


def mock_urlopen_response(body: dict[str, Any] | bytes, *, status: int = 200) -> MagicMock:
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = raw
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=resp)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx
