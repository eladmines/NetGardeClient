from __future__ import annotations

import logging
import sys
from unittest.mock import MagicMock

import pytest

from trustedge_wg.cli import CliConfig
from trustedge_wg.platform.trust_ca.install import install_policy_ca_if_requested


def test_install_policy_ca_skipped_when_flag_off() -> None:
    client = MagicMock()
    install_policy_ca_if_requested(CliConfig(api_url="https://api.example.com"), client)
    client.fetch_block_page_ca.assert_not_called()


def test_install_policy_ca_downloads_on_darwin(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    client.fetch_block_page_ca.return_value = b"-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n"
    install_mock = MagicMock()
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(
        "trustedge_wg.platform.trust_ca.darwin.install_trusted_root_ca",
        install_mock,
    )
    install_policy_ca_if_requested(
        CliConfig(api_url="https://api.example.com", install_policy_ca=True),
        client,
    )
    client.fetch_block_page_ca.assert_called_once()
    install_mock.assert_called_once_with(client.fetch_block_page_ca.return_value)


def test_install_policy_ca_warns_on_non_darwin(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    client = MagicMock()
    client.fetch_block_page_ca.return_value = b"pem"
    monkeypatch.setattr(sys, "platform", "linux")
    with caplog.at_level(logging.WARNING):
        install_policy_ca_if_requested(
            CliConfig(api_url="https://api.example.com", install_policy_ca=True),
            client,
        )
    assert "only automated on macOS" in caplog.text
