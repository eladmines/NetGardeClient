from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch

from trustedge_wg.cli import CliConfig
from trustedge_wg.wireguard.config import WireGuardConfig
from trustedge_wg.wireguard.monitor import start_traffic_monitor
from trustedge_wg.wireguard.stats import TransferStats


def test_start_traffic_monitor_disabled_for_zero_interval(private_key: str, public_key: str) -> None:
    cfg = WireGuardConfig(private_key=private_key, public_key=public_key, endpoint="gw:51820", address=["10.0.0.1/32"])
    opts = CliConfig(stats_interval=0.0)
    assert start_traffic_monitor(cfg, "utun0", opts, threading.Event()) is None


def test_start_traffic_monitor_writes_stats_file(
    tmp_path,
    private_key: str,
    public_key: str,
) -> None:
    cfg = WireGuardConfig(private_key=private_key, public_key=public_key, endpoint="gw:51820", address=["10.0.0.1/32"])
    stats_path = tmp_path / "stats.jsonl"
    opts = CliConfig(stats_interval=0.05, stats_file=str(stats_path))
    shutdown = threading.Event()
    stats = [
        TransferStats(rx_bytes=1000, tx_bytes=500),
        TransferStats(rx_bytes=2000, tx_bytes=700),
    ]
    counter = {"i": 0}

    def fake_read_transfer_stats(*_args, **_kwargs) -> TransferStats:
        index = min(counter["i"], len(stats) - 1)
        counter["i"] += 1
        return stats[index]

    with patch("trustedge_wg.wireguard.monitor.read_transfer_stats", side_effect=fake_read_transfer_stats):
        thread = start_traffic_monitor(cfg, "utun0", opts, shutdown)
        assert thread is not None
        time.sleep(0.2)
        shutdown.set()
        thread.join(timeout=2)

    lines = stats_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    assert '"delta_rx_bytes": 1000' in lines[0]
