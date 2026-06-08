# NetGardeClient

**macOS WireGuard VPN client** for the [NetGarde](https://github.com/NetGarde) platform — API enrollment, TUN tunnel, DNS routing, usage reporting, and a menu bar app.

**Organization:** [github.com/NetGarde](https://github.com/NetGarde) · **Platform:** [NetGarde](https://github.com/NetGarde/NetGarde) · **Client:** [NetGardeClient](https://github.com/NetGarde/NetGardeClient)

---

## Overview

NetGardeClient connects enrolled devices to the NetGarde control plane over **WireGuard**. It handles device identity at enroll time, applies server-assigned DNS policy routing, and reports tunnel usage back to the platform API.

The macOS build ships as **`NetGarde.app`** — a menu bar app with connect/disconnect, live traffic stats, and a connection details panel. A cross-platform **CLI** (`netgarde-wg`) is also available for Linux and Windows.

**Production API (default):** `http://44.218.45.174:8000` — same backend as the NetGarde dashboard. Override with `--api-url`, `NETGARDE_API_URL`, or GUI settings.

---

## Features

| Capability | Implementation |
|------------|----------------|
| Secure enroll | `POST /v1/enroll` with device identity + WireGuard key exchange |
| Tunnel | `wireguard-go` (macOS/Windows) or kernel WireGuard (Linux) |
| DNS policy | Applies WireGuard DNS from server config (macOS system DNS) |
| Usage reporting | Periodic `POST /v1/usage` for live dashboard charts |
| macOS GUI | Menu bar app (PyInstaller), shield status icons, connection panel |
| Offline mode | Manual `.conf` file without API enroll |

---

## Requirements

- Python 3.9+
- macOS, Linux, or Windows
- Elevated privileges (`sudo` on macOS/Linux; Administrator on Windows)
- Tunnel backend: `wireguard-go` on macOS/Windows, or `wg` + kernel WireGuard on Linux

---

## Quick start

```bash
git clone https://github.com/NetGarde/NetGardeClient.git
cd NetGardeClient
make install
source .venv/bin/activate
```

**CLI enroll (production server):**

```bash
sudo netgarde-wg
# with enroll bootstrap token (if ENROLL_BOOTSTRAP_TOKEN is set on the server):
sudo netgarde-wg --api-token YOUR_TOKEN
```

---

## macOS app

Build **`NetGarde.app`** (menu bar, production API built-in):

```bash
make build-mac
open dist/NetGarde.app
```

Install permanently:

```bash
cp -R dist/NetGarde.app /Applications/
```

Double-click **NetGarde** in Applications → shield icon in menu bar → **Connect**.

If macOS blocks the first launch: **right-click** `NetGarde.app` → **Open**.

The app bundles `netgarde-wg`, `wireguard-go`, and the menu bar GUI. VPN still prompts for your admin password on Connect.

**Development (without building `.app`):**

```bash
make install-gui
make run-gui
```

---

## Enroll flow

```
NetGardeClient → POST /v1/enroll → NetGarde API → device + IP allocation
              → wg-agent apply-peer → WireGuard config returned to client
              → tunnel up → DNS via server → usage POST /v1/usage
```

**Enroll API**

- `POST {api-url}/v1/enroll` (override path with `--api-enroll-path`)
- Body: `device_id`, `public_key`, optional `hostname`, `mac_address`
- Response: WireGuard config fields or `wireguard_conf` INI, plus `device_token` for `/v1/usage`

WireGuard DNS from enroll should be the server wg IP (e.g. `10.0.0.1`), not the AWS VPC resolver (`172.31.0.2`).

---

## Common flags

| Flag | Meaning |
|------|---------|
| `--config` | WireGuard `.conf` (offline mode) |
| `--api-url` | Override production API URL |
| `--api-token` | Enroll bootstrap token (`ENROLL_BOOTSTRAP_TOKEN` on server) |
| `--no-routing` | Skip system routes |
| `--apply-dns` / `--no-apply-dns` | macOS DNS from config (on by default) |
| `--stats-interval SEC` | Report tunnel traffic every SEC seconds |
| `--install-policy-ca` | macOS: trust block-page CA from API |

Run `netgarde-wg --help` for all options.

**Offline config:**

```bash
cp client.example.conf my.conf
sudo netgarde-wg --config ./my.conf
```

**macOS policy CA** (one-time, for HTTPS block page):

```bash
sudo netgarde-wg --install-policy-ca
```

---

## macOS: wireguard-go

Bundled automatically by `make build-mac`, or install manually:

```bash
git clone https://git.zx2c4.com/wireguard-go
cd wireguard-go && make && sudo cp wireguard-go /usr/local/bin/
```

---

## Platform documentation

This repo is the **client only**. Backend, dashboard, DNS policy, and deployment live in the platform repo:

| Document | Description |
|----------|-------------|
| [NetGarde README](https://github.com/NetGarde/NetGarde/blob/develop/README.md) | Platform overview and architecture |
| [docs/README.md](https://github.com/NetGarde/NetGarde/blob/develop/docs/README.md) | Technical documentation index |
| [docs/DESIGN.md](https://github.com/NetGarde/NetGarde/blob/develop/docs/DESIGN.md) | Design guide and domain model |
| [docs/ENV_SETUP.md](https://github.com/NetGarde/NetGarde/blob/develop/docs/ENV_SETUP.md) | Server env vars (`ENROLL_BOOTSTRAP_TOKEN`, etc.) |

---

## License

Portfolio and educational use. See repository for terms.
