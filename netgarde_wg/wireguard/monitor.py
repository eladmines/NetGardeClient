from __future__ import annotations

import json
import logging
import threading
import time
from typing import TYPE_CHECKING

from netgarde_wg.wireguard.config import WireGuardConfig
from netgarde_wg.wireguard.stats import TransferStats, delta, mib, read_transfer_stats

if TYPE_CHECKING:
    from netgarde_wg.cli import CliConfig
    from netgarde_wg.enroll.api import Client

log = logging.getLogger("netgarde-wg")


def start_traffic_monitor(
    cfg: WireGuardConfig,
    tun_name: str,
    opts: CliConfig,
    shutdown_event: threading.Event,
    *,
    device_id: str = "",
    api_client: Client | None = None,
) -> threading.Thread | None:
    interval = float(opts.stats_interval)
    if interval <= 0:
        return None

    def _loop() -> None:
        last: TransferStats | None = None
        stats_path = opts.stats_file.strip()
        fp = None
        if stats_path:
            fp = open(stats_path, "a", encoding="utf-8")

        try:
            while not shutdown_event.wait(interval):
                try:
                    cur = read_transfer_stats(
                        cfg,
                        tun_name,
                        interface=opts.interface,
                        wintun_adapter=opts.wintun_adapter_name(),
                    )
                except OSError as e:
                    log.warning("traffic stats: %s", e)
                    continue
                except RuntimeError as e:
                    log.warning("traffic stats: %s", e)
                    continue

                if last is not None:
                    drx, dtx = delta(last, cur)
                    rate_down = mib(drx) / interval
                    rate_up = mib(dtx) / interval
                    log.info(
                        "traffic +%.2f MiB down (%.2f MiB/s), +%.2f MiB up (%.2f MiB/s) | total %.2f MiB down / %.2f MiB up",
                        mib(drx),
                        rate_down,
                        mib(dtx),
                        rate_up,
                        cur.rx_mib,
                        cur.tx_mib,
                    )
                    record = {
                        "ts": time.time(),
                        "interval_sec": interval,
                        "delta_rx_bytes": drx,
                        "delta_tx_bytes": dtx,
                        "rx_bytes": cur.rx_bytes,
                        "tx_bytes": cur.tx_bytes,
                        "tun": tun_name,
                    }
                    if fp:
                        fp.write(json.dumps(record) + "\n")
                        fp.flush()
                    if api_client and device_id:
                        try:
                            api_client.report_usage(
                                device_id=device_id,
                                rx_bytes=cur.rx_bytes,
                                tx_bytes=cur.tx_bytes,
                                delta_rx=drx,
                                delta_tx=dtx,
                                interval_sec=interval,
                            )
                        except Exception as e:
                            log.warning("usage report: %s", e)
                last = cur
        finally:
            if fp:
                fp.close()

    thread = threading.Thread(target=_loop, name="netgarde-traffic", daemon=True)
    thread.start()
    log.info("traffic monitor every %.0fs (down=received, up=sent)", interval)
    return thread
