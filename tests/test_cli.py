from __future__ import annotations

from pathlib import Path

import pytest

from trustedge_wg.cli import CliConfig, parse_cli
from trustedge_wg.constants import DEFAULT_STATS_INTERVAL, ENV_API_URL
from trustedge_wg.paths import agent_state_path


def test_parse_cli_offline_config() -> None:
    opts = parse_cli(["--config", "/tmp/client.conf", "--no-routing"])
    assert opts.config_path == "/tmp/client.conf"
    assert opts.no_routing is True
    assert opts.stats_interval == 0.0


def test_parse_cli_api_mode_enables_default_stats_interval(monkeypatch) -> None:
    monkeypatch.setenv(ENV_API_URL, "https://api.example.com")
    opts = parse_cli(["--api-url", "https://api.example.com"])
    assert opts.api_url == "https://api.example.com"
    assert opts.stats_interval == DEFAULT_STATS_INTERVAL


def test_resolve_state_path_explicit() -> None:
    opts = CliConfig(state_path="/custom/agent-state.json")
    assert opts.resolve_state_path() == "/custom/agent-state.json"


def test_resolve_state_path_default_matches_paths_module() -> None:
    opts = CliConfig()
    assert opts.resolve_state_path() == str(agent_state_path())


def test_parse_cli_explicit_stats_interval() -> None:
    opts = parse_cli(["--api-url", "https://api.example.com", "--stats-interval", "10"])
    assert opts.stats_interval == 10.0


def test_parse_cli_config_out_and_state() -> None:
    opts = parse_cli(
        [
            "--api-url",
            "https://api.example.com",
            "--state",
            "/tmp/state.json",
            "--config-out",
            "/tmp/out.conf",
            "--install-policy-ca",
        ]
    )
    assert opts.state_path == "/tmp/state.json"
    assert opts.config_out == "/tmp/out.conf"
    assert opts.install_policy_ca is True


def test_wintun_adapter_name() -> None:
    opts = CliConfig(interface="wg0")
    if __import__("sys").platform == "win32":
        assert opts.wintun_adapter_name() == "TrustEdge"
    else:
        assert opts.wintun_adapter_name() == "wg0"
