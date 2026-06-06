from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from netgarde_wg.cli import CliConfig
from netgarde_wg.gui.settings import log_file, pid_file


def _python_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [sys.executable, "-m", "netgarde_wg"]


def build_tunnel_argv(opts: CliConfig) -> list[str]:
    cmd = list(_python_command())
    if opts.config_path.strip():
        cmd.extend(["--config", opts.config_path.strip()])
    if opts.api_url.strip():
        cmd.extend(["--api-url", opts.api_url.strip()])
    if opts.api_token.strip():
        cmd.extend(["--api-token", opts.api_token.strip()])
    if opts.no_routing:
        cmd.append("--no-routing")
    if sys.platform == "darwin":
        if opts.apply_dns:
            cmd.append("--apply-dns")
        else:
            cmd.append("--no-apply-dns")
    elif opts.apply_dns:
        cmd.append("--apply-dns")
    if opts.dns_service.strip():
        cmd.extend(["--dns-service", opts.dns_service.strip()])
    if opts.stats_interval > 0:
        cmd.extend(["--stats-interval", str(opts.stats_interval)])
    if opts.install_policy_ca:
        cmd.append("--install-policy-ca")
    return cmd


def _run_admin_shell(script_body: str) -> subprocess.CompletedProcess[str]:
    fd, script_path = tempfile.mkstemp(prefix="netgarde-wg-", suffix=".sh")
    os.close(fd)
    path = Path(script_path)
    try:
        path.write_text("#!/bin/bash\nset -euo pipefail\n" + script_body + "\n", encoding="utf-8")
        path.chmod(0o700)
        applescript = f'do shell script {shlex.quote(str(path))} with administrator privileges'
        return subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
        )
    finally:
        path.unlink(missing_ok=True)


def is_tunnel_running() -> bool:
    path = pid_file()
    if not path.is_file():
        return False
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def start_tunnel(opts: CliConfig) -> tuple[bool, str]:
    if is_tunnel_running():
        return False, "Already connected."

    argv = build_tunnel_argv(opts)
    tunnel_cmd = " ".join(shlex.quote(part) for part in argv)
    script = (
        f"PID_FILE={shlex.quote(str(pid_file()))}\n"
        f"LOG_FILE={shlex.quote(str(log_file()))}\n"
        f"{tunnel_cmd} >> \"$LOG_FILE\" 2>&1 &\n"
        f"echo $! > \"$PID_FILE\"\n"
    )
    result = _run_admin_shell(script)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "admin command failed").strip()
        return False, detail
    for _ in range(30):
        if is_tunnel_running():
            return True, "Connected."
        time.sleep(0.5)
    tail = _log_tail()
    return False, tail or "Tunnel did not start. See tunnel.log in Application Support/netgarde."


def stop_tunnel() -> tuple[bool, str]:
    path = pid_file()
    if not path.is_file():
        return True, "Already disconnected."
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        path.unlink(missing_ok=True)
        return True, "Disconnected."

    script = f"""
kill {pid} 2>/dev/null || true
rm -f {shlex.quote(str(path))}
"""
    result = _run_admin_shell(script)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "could not stop tunnel").strip()
        return False, detail
    return True, "Disconnected."


def _log_tail(max_lines: int = 8) -> str:
    path = log_file()
    if not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-max_lines:]).strip()
