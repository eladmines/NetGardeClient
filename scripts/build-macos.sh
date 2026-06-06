#!/usr/bin/env bash
# Build netgarde-wg macOS binary (PyInstaller) and bundle wireguard-go.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV="${VENV:-.venv}"
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"
DIST="$ROOT/dist"
BIN="$ROOT/bin"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "error: macOS build must run on Darwin (use GitHub Actions on macos-latest otherwise)" >&2
  exit 1
fi

if [[ ! -x "$PY" ]]; then
  python3 -m venv "$VENV"
fi

"$PIP" install -U pip
"$PIP" install -r requirements.txt
"$PIP" install -r requirements-dev.txt
"$PIP" install .

mkdir -p "$BIN" "$DIST"

WG_GO="$BIN/wireguard-go"
if [[ ! -x "$WG_GO" ]]; then
  echo "Building wireguard-go into $WG_GO ..."
  TMP="$(mktemp -d)"
  git clone --depth 1 https://git.zx2c4.com/wireguard-go "$TMP/wireguard-go"
  make -C "$TMP/wireguard-go"
  cp "$TMP/wireguard-go/wireguard-go" "$WG_GO"
  rm -rf "$TMP"
fi

rm -rf build dist
"$PY" -m PyInstaller --noconfirm netgarde-wg.spec
cp "$WG_GO" "$DIST/wireguard-go"
chmod +x "$DIST/netgarde-wg" "$DIST/wireguard-go"

echo ""
echo "Built:"
echo "  $DIST/netgarde-wg"
echo "  $DIST/wireguard-go"
echo ""
echo "Run (needs sudo for TUN/routes):"
echo "  sudo $DIST/netgarde-wg --help"
