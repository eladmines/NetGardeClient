from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from netgarde_wg.constants import (
    DEFAULT_ENROLL_PATH,
    DEFAULT_POLICY_CA_PATH,
    DEFAULT_USAGE_PATH,
    DEFAULT_WINTUN_NAME,
    ENV_API_TOKEN,
    ENV_API_URL,
)


@dataclass
class CliConfig:
    config_path: str = ""
    api_url: str = ""
    api_token: str = ""
    api_enroll_path: str = DEFAULT_ENROLL_PATH
    state_path: str = ""
    config_out: str = ""
    interface: str = "wg0"
    no_routing: bool = False
    apply_dns: bool = False
    dns_service: str = ""
    stats_interval: float = 0.0
    stats_file: str = ""
    api_usage_path: str = DEFAULT_USAGE_PATH
    api_policy_ca_path: str = DEFAULT_POLICY_CA_PATH
    install_policy_ca: bool = False

    def resolve_state_path(self) -> str:
        if self.state_path.strip():
            return self.state_path.strip()
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                return str(Path(appdata) / "netgarde" / "agent-state.json")
        try:
            base = Path(os.path.expanduser("~")) / "Library" / "Application Support"
            if sys.platform == "darwin":
                return str(base / "netgarde" / "agent-state.json")
        except OSError:
            pass
        if sys.platform.startswith("linux"):
            xdg = os.environ.get("XDG_CONFIG_HOME")
            if xdg:
                return str(Path(xdg) / "netgarde" / "agent-state.json")
            return str(Path.home() / ".config" / "netgarde" / "agent-state.json")
        return "netgarde-agent-state.json"

    def wintun_adapter_name(self) -> str:
        if sys.platform == "win32" and self.interface == "wg0":
            return DEFAULT_WINTUN_NAME
        return self.interface


def usage_text() -> str:
    return f"""usage:
  Offline:  netgarde-wg --config /path/to/client.conf [--no-routing]
  API:      netgarde-wg --api-url https://api.example.com [--api-token TOKEN] [--state PATH] [--config-out PATH]

  Environment: {ENV_API_URL}, {ENV_API_TOKEN}
"""


def parse_cli(argv: list[str] | None = None) -> CliConfig:
    p = argparse.ArgumentParser(
        prog="netgarde-wg",
        description="NetGarde userspace WireGuard client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=usage_text(),
    )
    p.add_argument("--config", default="", help="WireGuard .conf (offline; ignores --api-url)")
    p.add_argument("--api-url", default=os.environ.get(ENV_API_URL, ""), help="NetGarde API base URL")
    p.add_argument("--api-token", default=os.environ.get(ENV_API_TOKEN, ""), help="Bearer token")
    p.add_argument("--api-enroll-path", default=DEFAULT_ENROLL_PATH, help="Enroll path")
    p.add_argument("--state", default="", help="Agent state JSON path")
    p.add_argument("--config-out", default="", help="Write merged .conf after enroll")
    p.add_argument(
        "-interface",
        "--interface",
        dest="interface",
        default="wg0",
        help="Linux TUN name; Windows Wintun name (wg0→NetGarde); macOS uses utun",
    )
    p.add_argument("--no-routing", action="store_true", help="WireGuard only, no system routes")
    if sys.platform == "darwin":
        p.add_argument(
            "--apply-dns",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Apply DNS from config on macOS (default: on; use --no-apply-dns to disable)",
        )
    else:
        p.add_argument(
            "--apply-dns",
            action="store_true",
            help="Apply DNS from config while tunnel is up (macOS only)",
        )
    p.add_argument("--dns-service", default="", help='macOS network service (e.g. "Wi-Fi")')
    p.add_argument(
        "--stats-interval",
        type=float,
        default=0.0,
        metavar="SEC",
        help="Log WireGuard traffic every SEC seconds (MiB down/up; 0=off)",
    )
    p.add_argument(
        "--stats-file",
        default="",
        help="Append JSON lines of traffic samples to this file",
    )
    p.add_argument(
        "--api-usage-path",
        default=DEFAULT_USAGE_PATH,
        help="With --api-url and --stats-interval: POST usage to this path",
    )
    p.add_argument(
        "--install-policy-ca",
        action="store_true",
        help="macOS: download NetGarde Policy CA from API and trust it (sudo) for HTTPS block page",
    )
    p.add_argument(
        "--api-policy-ca-path",
        default=DEFAULT_POLICY_CA_PATH,
        help="Path for block-page CA PEM (default: /policy/block-page-ca)",
    )

    args = p.parse_args(argv)
    return CliConfig(
        config_path=args.config,
        api_url=args.api_url,
        api_token=args.api_token,
        api_enroll_path=args.api_enroll_path,
        state_path=args.state,
        config_out=args.config_out,
        interface=args.interface,
        no_routing=args.no_routing,
        apply_dns=args.apply_dns,
        dns_service=args.dns_service,
        stats_interval=max(0.0, float(args.stats_interval)),
        stats_file=args.stats_file,
        api_usage_path=args.api_usage_path,
        api_policy_ca_path=args.api_policy_ca_path,
        install_policy_ca=args.install_policy_ca,
    )
