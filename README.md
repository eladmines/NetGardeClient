# NetGarde client (`netgarde-wg`)

Python WireGuard client: TUN tunnel, optional **full IPv4 routing** (split `0.0.0.0/1` + `128.0.0.0/1`), endpoint bypass routes, API enroll, and macOS DNS apply (`--apply-dns`).

## Requirements

- **Python** 3.9+
- **macOS**, **Linux**, or **Windows**
- **Elevated privileges** where the OS requires them:
  - **macOS / Linux**: `sudo` for TUN, routes, and `ifconfig` / `ip`
  - **Windows**: Administrator for Wintun, `netsh`, and `route`; **PowerShell** for default-route lookup
- **Tunnel backend** (one of):
  - **Linux (preferred)**: `wireguard` kernel module, `wg`, and `ip`
  - **macOS / Windows / Linux fallback**: [`wireguard-go`](https://git.zx2c4.com/wireguard-go/) on `PATH`
- **Windows**: [Wintun](https://www.wintun.net/) (WireGuard installer ships it)

## Install

```bash
cd /path/to/NetGardeClient
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install .
```

Or:

```bash
make install
```

## macOS standalone binary

Build a self-contained CLI (no Python/venv required on the target Mac). Produces `dist/netgarde-wg` and bundles `dist/wireguard-go` beside it.

```bash
make build-mac
# or: bash scripts/build-macos.sh

sudo ./dist/netgarde-wg --config ./client.example.conf
sudo ./dist/netgarde-wg --api-url https://api.example.com --api-token YOUR_TOKEN
```

**CI:** GitHub Actions workflow [`.github/workflows/build-macos.yml`](.github/workflows/build-macos.yml) builds on every push to `main`/`develop` and uploads artifacts. Tag `v*` releases attach binaries to the GitHub release.

**Distribution notes:** TUN and routes still require `sudo`. For distribution outside your machine, code-sign and notarize the binaries (Apple Developer account) to avoid Gatekeeper warnings.

## Run (offline `.conf`)

```bash
cp client.example.conf my.conf
# Edit PrivateKey, PublicKey, Endpoint

sudo netgarde-wg --config ./my.conf
# macOS: --apply-dns is on by default; set DNS = server wg IP (e.g. 10.0.0.1) for dnsmasq logs
sudo netgarde-wg --config ./my.conf --dns-service "Wi-Fi"
# traffic every 10s (detect downloads via MiB/s):
sudo netgarde-wg --config ./my.conf --stats-interval 10
```

`*.conf` files are gitignored (except `client.example.conf`).

## Run (API enroll)

With **`--api-url`**, **`--config` is ignored**. The agent loads or creates state (device id + locally generated private key) and **POSTs** enroll.

Environment: **`NETGARDE_API_URL`**, **`NETGARDE_API_TOKEN`** (bootstrap token for enroll when the server sets `ENROLL_BOOTSTRAP_TOKEN`).

After enroll, the client stores **`device_token`** in agent state and uses it for usage reporting.

```bash
sudo netgarde-wg --api-url https://api.example.com --api-token YOUR_TOKEN
sudo netgarde-wg --api-url https://api.example.com --api-token YOUR_TOKEN --config-out ./cached.conf
```

### HTTPS block page (macOS, one-time)

When policy DNS sends blocked domains to the block page (`10.0.0.1`), browsers need the **NetGarde Policy CA** trusted so `https://facebook.com` (etc.) shows the block page instead of a certificate warning. You can do that manually (`scp` + `security add-trusted-cert`) or let the client fetch the CA from the API:

```bash
sudo netgarde-wg --api-url https://api.example.com --api-token YOUR_TOKEN --install-policy-ca
```

This downloads `GET /policy/block-page-ca` and runs `security add-trusted-cert` (requires **sudo**). Use once per Mac; re-run only if the server rotates the CA.

### Enroll contract (default)

- **POST** `{api-url}/v1/enroll` (override with `--api-enroll-path`)
- **Headers**: `Content-Type: application/json`; optional `Authorization: Bearer <token>`
- **Body**: `device_id`, `public_key`, optional `hostname`, `mac_address`
- **Response**: `wireguard_conf` INI **or** structured fields (`address` / `addresses`, `server_public_key`, `endpoint`, `allowed_ips`, `dns`, `mtu`, …), plus **`device_token`** (device credential for `/v1/usage`). Private key always stays on the client.

## Flags

| Flag | Meaning |
|------|--------|
| `--config` | WireGuard INI; **offline mode** |
| `--api-url` | HTTPS API base URL (**enroll mode**) |
| `--api-token` | Bearer token (`NETGARDE_API_TOKEN`) |
| `--api-enroll-path` | Enroll path (default `/v1/enroll`) |
| `--state` | Agent state JSON (default: user config dir `netgarde/agent-state.json`) |
| `--config-out` | Write merged `.conf` after enroll |
| `--interface` | Linux TUN name (`wg0`). Windows: Wintun name (`wg0` → `NetGarde`). macOS: `utun`. |
| `--no-routing` | WireGuard only; no system routes |
| `--apply-dns` | Apply DNS from config while up (**macOS**) |
| `--dns-service` | macOS service name (e.g. `Wi-Fi`) |
| `--stats-interval SEC` | Log tunnel traffic every SEC seconds (MiB; 0=off) |
| `--stats-file PATH` | Append JSON traffic samples to PATH |
| `--api-usage-path` | With API + stats: POST usage path (default `/v1/usage`) |
| `--install-policy-ca` | macOS: trust block-page CA from API (needs `--api-url`, sudo) |
| `--api-policy-ca-path` | CA download path (default `/policy/block-page-ca`) |

## Layout

```
netgarde_wg/
  cli.py              # CLI flags
  constants.py        # Defaults, env var names
  app/main.py         # Entry: resolve config, run tunnel
  wireguard/          # Config, keys, UAPI, tunnel lifecycle
  enroll/api.py       # HTTPS enroll client
  agent/state.py      # device_id + private key on disk
  platform/
    hostmeta.py       # Hostname / MAC for enroll
    routing/          # Full-tunnel routes (darwin / linux / windows)
    dns/              # DNS apply (macOS)
```

## macOS: `wireguard-go`

```bash
git clone https://git.zx2c4.com/wireguard-go
cd wireguard-go && make && sudo cp wireguard-go /usr/local/bin/
```

## AWS server checklist

- UDP **51820** (or your port) open in the security group
- `net.ipv4.ip_forward=1`
- NAT for VPN subnet egress
- Server peer for client public key; IPs match API / `.conf`
- **DNS logging:** run dnsmasq on `wg0` on the [NetGarde server](https://github.com/eladmines/NetGarde). Clients must use `DNS = 10.0.0.1` (server wg IP), not `172.31.0.2`.

## Notes

- macOS applies DNS by default (`--no-apply-dns` to disable). Other OS: DNS from config is not auto-applied.
- No kill switch yet.
