from __future__ import annotations

from unittest.mock import patch

from trustedge_wg.enroll.public_ip import fetch_public_ipv4
from tests.helpers import mock_urlopen_response


def test_fetch_public_ipv4_success() -> None:
    with patch(
        "trustedge_wg.enroll.public_ip.urlopen",
        return_value=mock_urlopen_response({"ip": "203.0.113.55"}),
    ):
        assert fetch_public_ipv4() == "203.0.113.55"


def test_fetch_public_ipv4_network_failure() -> None:
    from urllib.error import URLError

    with patch("trustedge_wg.enroll.public_ip.urlopen", side_effect=URLError("timeout")):
        assert fetch_public_ipv4() == ""


def test_fetch_public_ipv4_invalid_json() -> None:
    with patch(
        "trustedge_wg.enroll.public_ip.urlopen",
        return_value=mock_urlopen_response(b"not-json"),
    ):
        assert fetch_public_ipv4() == ""
