# WireGuard server: dnsmasq DNS logging

VPN clients must send DNS to **dnsmasq on the WireGuard interface**, not to `172.31.0.2` (AWS VPC resolver). Otherwise `/var/log/dnsmasq.log` stays empty.

## Quick setup (Ubuntu)

```bash
# On the EC2 host (wg0 up, server IP e.g. 10.0.0.1)
cd server
sudo bash setup-dnsmasq.sh

# From a connected client
dig @10.0.0.1 example.com

# On the server
sudo tail -f /var/log/dnsmasq.log
```

You should see lines like:

```text
query[A] example.com from 10.0.0.3
```

## Client (`netgarde-wg`)

In `my.conf`:

```ini
DNS = 10.0.0.1
```

The client auto-replaces `172.31.0.2` with the inferred server DNS (`10.0.0.1` when your address is `10.0.0.x/32`).

On macOS, DNS is applied by default (`--apply-dns`); override with `--no-apply-dns`.

```bash
sudo netgarde-wg --config ./my.conf
# or explicitly:
sudo netgarde-wg --config ./my.conf --apply-dns --dns-service "Wi-Fi"
```

## API enroll

Return `"dns": ["10.0.0.1"]` (your wg0 IP), not `172.31.0.2`.

## Traffic monitoring (MiB per client)

On the server, watch all peers:

```bash
sudo bash watch-traffic.sh wg0 5
```

`+X MiB down` on the server = **client download** (server sent to client). Large spikes while someone is downloading.

On the Mac/Linux **client** (`netgarde-wg`):

```bash
sudo netgarde-wg --config ./my.conf --stats-interval 10
# optional JSON log:
sudo netgarde-wg --config ./my.conf --stats-interval 10 --stats-file ./traffic.jsonl
```

With API mode, usage is also **POST**ed to `{api-url}/v1/usage` (override with `--api-usage-path`).

## Files

| File | Purpose |
|------|---------|
| `dnsmasq-wireguard.conf` | Template for `/etc/dnsmasq.d/` |
| `setup-dnsmasq.sh` | Installs config, opens port 53 on `wg0`, restarts dnsmasq |
| `watch-traffic.sh` | Live per-peer MiB totals and deltas |
