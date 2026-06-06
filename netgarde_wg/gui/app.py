from __future__ import annotations

import sys

import rumps

from netgarde_wg.cli import CliConfig
from netgarde_wg.constants import PRODUCTION_API_URL
from netgarde_wg.gui.privileged import is_tunnel_running, start_tunnel, stop_tunnel
from netgarde_wg.gui.settings import GuiSettings, log_file


class NetGardeMenuBarApp(rumps.App):
    def __init__(self) -> None:
        super().__init__(
            "NetGarde",
            title="NG",
            quit_button="Quit NetGarde",
            template=True,
        )
        self.settings = GuiSettings.load()
        self.server_item = rumps.MenuItem("", callback=None)
        self.status_item = rumps.MenuItem("Status: Disconnected", callback=None)
        self.menu = [
            self.status_item,
            self.server_item,
            None,
            "Connect",
            "Disconnect",
            None,
            "Settings…",
            "View Log…",
        ]
        self._refresh_status()

    def _refresh_status(self) -> None:
        self.settings = self.settings.with_defaults()
        if self.settings.api_url:
            self.server_item.title = f"Server: {self.settings.api_url}"
        else:
            self.server_item.title = "Server: (not configured)"
        if is_tunnel_running():
            self.status_item.title = "Status: Connected"
            self.title = "NG ●"
        else:
            self.status_item.title = "Status: Disconnected"
            self.title = "NG"

    def _cli_config(self) -> CliConfig:
        return CliConfig(
            api_url=self.settings.api_url,
            api_token=self.settings.api_token,
            apply_dns=True,
            install_policy_ca=self.settings.install_policy_ca,
        )

    @rumps.timer(2)
    def poll_status(self, _: rumps.Timer) -> None:
        self._refresh_status()

    @rumps.clicked("Connect")
    def connect(self, _: rumps.MenuItem) -> None:
        self.settings = self.settings.with_defaults()
        if not self.settings.api_url.strip():
            rumps.alert("NetGarde", self.settings.missing_api_url_message())
            return
        ok, message = start_tunnel(self._cli_config())
        self._refresh_status()
        if ok:
            rumps.notification("NetGarde", "Connected", message)
        else:
            rumps.alert("Connect failed", message)

    @rumps.clicked("Disconnect")
    def disconnect(self, _: rumps.MenuItem) -> None:
        ok, message = stop_tunnel()
        self._refresh_status()
        if not ok:
            rumps.alert("Disconnect failed", message)
        elif message != "Already disconnected.":
            rumps.notification("NetGarde", "Disconnected", message)

    @rumps.clicked("Settings…")
    def settings(self, _: rumps.MenuItem) -> None:
        effective = self.settings.with_defaults()
        url_window = rumps.Window(
            message=f"NetGarde API base URL (default: {PRODUCTION_API_URL})",
            title="Settings",
            default_text=effective.api_url,
            ok="Next",
            cancel="Cancel",
            dimensions=(420, 24),
        )
        url_response = url_window.run()
        if not url_response.clicked:
            return

        token_window = rumps.Window(
            message="API token (optional; or set NETGARDE_API_TOKEN)",
            title="Settings",
            default_text=effective.api_token,
            ok="Next",
            cancel="Cancel",
            dimensions=(420, 24),
        )
        token_response = token_window.run()
        if not token_response.clicked:
            return

        policy_window = rumps.Window(
            message="Install policy CA on connect? (yes/no)",
            title="Settings",
            default_text="yes" if self.settings.install_policy_ca else "no",
            ok="Save",
            cancel="Cancel",
            dimensions=(420, 24),
        )
        policy_response = policy_window.run()
        if not policy_response.clicked:
            return

        self.settings.api_url = url_response.text.strip()
        self.settings.api_token = token_response.text.strip()
        self.settings.install_policy_ca = policy_response.text.strip().lower() in {
            "yes",
            "y",
            "true",
            "1",
        }
        self.settings.save()
        rumps.notification("NetGarde", "Settings saved", self.settings.api_url or "API URL cleared")

    @rumps.clicked("View Log…")
    def view_log(self, _: rumps.MenuItem) -> None:
        path = log_file()
        if not path.is_file():
            rumps.alert("NetGarde", "No tunnel log yet.")
            return
        try:
            tail = path.read_text(encoding="utf-8", errors="replace").splitlines()[-20:]
        except OSError as e:
            rumps.alert("NetGarde", str(e))
            return
        rumps.alert("Tunnel log (last 20 lines)", "\n".join(tail) or "(empty)")


def main() -> int:
    if sys.platform != "darwin":
        print("netgarde-wg-gui is macOS only.", file=sys.stderr)
        return 1
    NetGardeMenuBarApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
