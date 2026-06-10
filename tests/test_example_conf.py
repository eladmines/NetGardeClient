from __future__ import annotations

from pathlib import Path

from tests.conftest import MOCK_VPN_ADDRESS, MOCK_VPN_DNS


def test_example_conf_uses_placeholders_not_real_addresses() -> None:
    text = Path("examples/client.example.conf").read_text(encoding="utf-8")
    assert "YOUR_VPN_ADDRESS" in text
    assert "YOUR_VPN_DNS" in text
    assert MOCK_VPN_ADDRESS not in text
    assert MOCK_VPN_DNS not in text
