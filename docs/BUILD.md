# Building & developing TrustEdgeClient

This guide is for **contributors and builders** — not required for normal users installing `TrustEdge.app`.

End-user install instructions are in the [README](../README.md).

---

## Requirements

- **macOS** (for building `TrustEdge.app`)
- **Python 3.9+**
- **Xcode Command Line Tools**
- **wireguard-go** — bundled automatically by `make build-mac`, or `brew install wireguard-go`

---

## Quick setup (from source)

```bash
git clone https://github.com/TrustEdgeOrg/TrustEdgeClient.git
cd TrustEdgeClient
make install-gui
```

Configure API access for local runs:

```bash
cp .env.example .env
# edit TRUSTEDGE_API_URL
make run-gui
```

When running from source, `.env` in the repo root is used. The installed `.app` uses:

`~/Library/Application Support/TrustEdgeClient/.env`

---

## Make targets

| Command | Purpose |
|---------|---------|
| `make install` | Install CLI package in `.venv` |
| `make install-gui` | Install with macOS menu bar dependencies |
| `make install-dev` | Install + pytest + PyInstaller |
| `make run-gui` | Launch menu bar app from source |
| `make run ARGS='…'` | Run CLI (usually needs `sudo`) |
| `make test` | Run pytest (112 tests) |
| `make build-mac` | Build `dist/TrustEdge.app` + `dist/trustedge-wg` |
| `make help` | List all targets |

---

## Build standalone app

```bash
make build-mac
```

Outputs:

| Path | Description |
|------|-------------|
| `dist/TrustEdge.app` | Menu bar application |
| `dist/trustedge-wg` | CLI binary |
| `dist/wireguard-go` | Tunnel backend |

Install for daily use:

```bash
cp -R dist/TrustEdge.app /Applications/
```

CI also builds these artifacts on push to `main` / `develop` (see `.github/workflows/build-macos.yml`).

---

## Project structure

```
trustedge_wg/
├── app/           CLI orchestration
├── agent/         Device identity & keys
├── enroll/        API enrollment
├── wireguard/     Tunnel, config, stats
├── platform/      macOS DNS, routing, trust CA
└── gui/           Menu bar app

tests/             pytest suite
packaging/         PyInstaller specs (if present)
scripts/           build-macos.sh
examples/          WireGuard config template (if present)
```

---

## Running tests

```bash
make test
```

Or manually:

```bash
pip install ".[dev]"
pytest -q
```

CI runs tests on Ubuntu via `.github/workflows/test.yml`.

---

## Troubleshooting (build)

| Problem | What to do |
|---------|------------|
| `wireguard-go not found` | Run `make build-mac` (bundles it) or `brew install wireguard-go` |
| PyInstaller fails | `make install-dev` first; needs macOS |
| GUI won’t start | `make install-gui` — requires `rumps` (macOS only) |
| Tests fail on import | `pip install ".[dev]"` from repo root |

---

## Related docs

- [CLI reference](CLI.md) — `trustedge-wg` command-line usage
- [README](../README.md) — end-user install guide
