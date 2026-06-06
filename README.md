# NetGarde client (`netgarde-wg`)

Python WireGuard client for [NetGarde](https://github.com/eladmines/NetGarde): TUN tunnel, full IPv4 routing, API enroll, macOS DNS apply, and usage reporting.

**Production API (default):** `http://44.218.45.174:8000` — same as the NetGarde dashboard backend. Override with `--api-url`, `NETGARDE_API_URL`, or GUI Settings.

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

```bash
make install-gui
make run-gui
```

1. Click **NG** in the menu bar → **Connect** (uses production API by default)  
2. Enter your Mac password when prompted (VPN needs admin rights)  
3. **Disconnect** when done  

Optional: **Settings…** to change API URL, set enroll token, or enable policy CA install.

If your server requires enroll auth, set the token once:

```bash
export NETGARDE_API_TOKEN=your-ENROLL_BOOTSTRAP_TOKEN
make run-gui
```

Or save it in GUI Settings. Tunnel logs: `/tmp/netgarde-wg-<uid>/tunnel.log`.

## macOS standalone binary

```bash
make build-mac
sudo ./dist/netgarde-wg
```

## Usage

**API enroll (default — production server):**

```bash
sudo netgarde-wg
# with enroll bootstrap token (if ENROLL_BOOTSTRAP_TOKEN is set on EC2):
sudo netgarde-wg --api-token YOUR_TOKEN
```

**Offline config** (manual WireGuard file, no API):

```bash
cp client.example.conf my.conf
sudo netgarde-wg --config ./my.conf
```

**macOS policy CA** (one-time, for HTTPS block page):

```bash
sudo netgarde-wg --install-policy-ca
```

WireGuard DNS from enroll should be the server wg IP (e.g. `10.0.0.1`), not the AWS VPC resolver (`172.31.0.2`).

## Enroll API

- `POST {api-url}/v1/enroll` (default path; override with `--api-enroll-path`)
- Body: `device_id`, `public_key`, optional `hostname`, `mac_address`
- Response: WireGuard config fields or `wireguard_conf` INI, plus `device_token` for `/v1/usage`

## Common flags

| Flag | Meaning |
|------|---------|
| `--config` | WireGuard `.conf` (offline mode) |
| `--api-url` | Override production API URL |
| `--api-token` | Enroll bootstrap token (`ENROLL_BOOTSTRAP_TOKEN` on server) |
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
