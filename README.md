# NetGarde client (`netgarde-wg`)

Python WireGuard client for [NetGarde](https://github.com/eladmines/NetGarde): TUN tunnel, full IPv4 routing, API enroll, macOS DNS apply, and usage reporting.

## Requirements

- Python 3.9+
- macOS, Linux, or Windows
- Elevated privileges (`sudo` on macOS/Linux; Administrator on Windows)
- Tunnel backend: `wireguard-go` on macOS/Windows, or `wg` + kernel WireGuard on Linux

## Install

```bash
git clone https://github.com/eladmines/NetGardeClient.git
cd NetGardeClient
make install
source .venv/bin/activate
```

## macOS menu bar GUI

Install and run the menu bar app (icon in the top-right menu bar):

```bash
make install-gui
make run-gui
# or: netgarde-wg-gui
```

1. Click **NG** in the menu bar → **Settings…** → enter API URL and token  
2. **Connect** — macOS prompts for your password (admin rights for VPN)  
3. **Disconnect** when done  

Settings are stored in `~/Library/Application Support/netgarde/gui-settings.json`.

## macOS standalone binary

```bash
make build-mac
sudo ./dist/netgarde-wg --api-url https://api.example.com --api-token YOUR_TOKEN
```

CI builds artifacts on push to `main`/`develop`. Tag `v*` for GitHub Release uploads.

## Usage

**Offline config:**

```bash
cp client.example.conf my.conf
sudo netgarde-wg --config ./my.conf
```

**API enroll** (ignores `--config`):

```bash
export NETGARDE_API_URL=https://api.example.com
export NETGARDE_API_TOKEN=YOUR_TOKEN   # optional bootstrap token
sudo netgarde-wg --api-url "$NETGARDE_API_URL" --api-token "$NETGARDE_API_TOKEN"
```

**macOS policy CA** (one-time, for HTTPS block page):

```bash
sudo netgarde-wg --api-url https://api.example.com --api-token TOKEN --install-policy-ca
```

Set `DNS = 10.0.0.1` (server WireGuard IP) in config or enroll response — not the AWS VPC resolver (`172.31.0.2`).

## Enroll API

- `POST {api-url}/v1/enroll` (default path; override with `--api-enroll-path`)
- Body: `device_id`, `public_key`, optional `hostname`, `mac_address`
- Response: WireGuard config fields or `wireguard_conf` INI, plus `device_token` for `/v1/usage`

## Common flags

| Flag | Meaning |
|------|---------|
| `--config` | WireGuard `.conf` (offline mode) |
| `--api-url` | NetGarde API base URL (enroll mode) |
| `--no-routing` | Skip system routes |
| `--apply-dns` / `--no-apply-dns` | macOS DNS from config (on by default) |
| `--stats-interval SEC` | Log tunnel traffic every SEC seconds |
| `--install-policy-ca` | macOS: trust block-page CA from API |

Run `netgarde-wg --help` for all options.

## macOS: wireguard-go

Bundled automatically by `make build-mac`, or install manually:

```bash
git clone https://git.zx2c4.com/wireguard-go
cd wireguard-go && make && sudo cp wireguard-go /usr/local/bin/
```
