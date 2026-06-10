from __future__ import annotations

from trustedge_wg.wireguard.stats import (
    TransferStats,
    _parse_uapi_get,
    _parse_wg_show,
    delta,
    mib,
    uapi_socket_path,
)


def test_mib_and_delta() -> None:
    prev = TransferStats(rx_bytes=1024 * 1024, tx_bytes=0)
    cur = TransferStats(rx_bytes=3 * 1024 * 1024, tx_bytes=512)
    assert mib(cur.rx_bytes) == 3.0
    assert delta(prev, cur) == (2 * 1024 * 1024, 512)


def test_parse_wg_show_extracts_peer_transfer() -> None:
    text = """interface: wg0
  public key: serverkey=
peer: peerkey1234567890123456789012345678901234567890=
  endpoint: 1.2.3.4:51820
  transfer: 4096, 8192
"""
    stats = _parse_wg_show(text, "peerkey1234567890123456789012345678901234567890=")
    assert stats.rx_bytes == 4096
    assert stats.tx_bytes == 8192


def test_parse_wg_show_falls_back_without_peer_match() -> None:
    text = """peer: otherpeer=
  transfer: 100, 200
peer: targetpeer=
  transfer: 300, 400
"""
    stats = _parse_wg_show(text, "missingpeer=")
    assert stats.rx_bytes == 100
    assert stats.tx_bytes == 200


def test_parse_uapi_get() -> None:
    text = "errno=0\nrx_bytes=12345\ntx_bytes=67890\n"
    stats = _parse_uapi_get(text)
    assert stats.rx_bytes == 12345
    assert stats.tx_bytes == 67890


def test_uapi_socket_path() -> None:
    path = uapi_socket_path("utun7")
    if path is not None:
        assert path.name == "utun7.sock"
