from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import patch

import pytest
from urllib.error import HTTPError, URLError

from trustedge_wg.enroll.api import Client, EnrollRequest
from tests.helpers import mock_urlopen_response


def test_client_enroll_success(private_key: str, public_key: str) -> None:
    body = {
        "server_public_key": public_key,
        "endpoint": "gw.example.com:51820",
        "address": "10.0.0.3/32",
        "dns": ["10.0.0.1"],
        "device_token": "tok",
    }
    client = Client("https://api.example.com", enroll_token="bootstrap")
    req = EnrollRequest(
        device_id="dev1",
        public_key=public_key,
        hostname="laptop",
        client_public_ip="203.0.113.1",
    )

    with patch("trustedge_wg.enroll.api.urlopen", return_value=mock_urlopen_response(body)) as mock_open:
        resp = client.enroll(req)

    assert resp.endpoint == "gw.example.com:51820"
    assert resp.device_token == "tok"
    sent = mock_open.call_args[0][0]
    assert sent.full_url == "https://api.example.com/v1/enroll"
    assert sent.method == "POST"
    assert sent.headers["Authorization"] == "Bearer bootstrap"
    payload = json.loads(sent.data.decode())
    assert payload["device_id"] == "dev1"
    assert payload["hostname"] == "laptop"
    assert payload["client_public_ip"] == "203.0.113.1"


def test_client_enroll_http_error() -> None:
    client = Client("https://api.example.com", enroll_token="bad")
    req = EnrollRequest(device_id="dev1", public_key="pub")
    err = HTTPError(
        "https://api.example.com/v1/enroll",
        401,
        "Unauthorized",
        hdrs=None,
        fp=BytesIO(b'{"detail":"invalid token"}'),
    )

    with patch("trustedge_wg.enroll.api.urlopen", side_effect=err):
        with pytest.raises(RuntimeError, match="returned 401"):
            client.enroll(req)


def test_client_enroll_network_error() -> None:
    client = Client("https://api.example.com")
    req = EnrollRequest(device_id="dev1", public_key="pub")

    with patch("trustedge_wg.enroll.api.urlopen", side_effect=URLError("connection refused")):
        with pytest.raises(RuntimeError, match="round trip"):
            client.enroll(req)


def test_client_fetch_block_page_ca() -> None:
    client = Client("https://api.example.com")
    pem = b"-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----\n"
    with patch("trustedge_wg.enroll.api.urlopen", return_value=mock_urlopen_response(pem)) as mock_open:
        assert client.fetch_block_page_ca() == pem
    sent = mock_open.call_args[0][0]
    assert sent.full_url == "https://api.example.com/policy/block-page-ca"


def test_client_report_usage_uses_device_token() -> None:
    client = Client("https://api.example.com", device_token="device-tok")
    with patch("trustedge_wg.enroll.api.urlopen", return_value=mock_urlopen_response(b"")) as mock_open:
        client.report_usage(
            device_id="dev1",
            rx_bytes=100,
            tx_bytes=50,
            delta_rx=10,
            delta_tx=5,
            interval_sec=5.0,
        )

    sent = mock_open.call_args[0][0]
    assert sent.full_url == "https://api.example.com/v1/usage"
    assert sent.headers["Authorization"] == "Bearer device-tok"
    payload = json.loads(sent.data.decode())
    assert payload["delta_rx_bytes"] == 10
