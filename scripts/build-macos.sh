#!/usr/bin/env bash
# Build netgarde-wg CLI, NetGarde.app (menu bar), and bundle wireguard-go.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV="${VENV:-.venv}"
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"
DIST="$ROOT/dist"
BIN="$ROOT/bin"
APP="$DIST/NetGarde.app"
APP_MACOS="$APP/Contents/MacOS"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "error: macOS build must run on Darwin (use GitHub Actions on macos-latest otherwise)" >&2
  exit 1
fi

if [[ ! -x "$PY" ]]; then
  python3 -m venv "$VENV"
fi

"$PIP" install -U pip
"$PIP" install ".[dev,gui]"

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
mkdir -p "$DIST"

echo "Building CLI binary..."
"$PY" -m PyInstaller --noconfirm netgarde-wg.spec

echo "Building NetGarde.app..."
"$PY" -m PyInstaller --noconfirm netgarde-gui.spec

cp "$WG_GO" "$DIST/wireguard-go"
cp "$DIST/netgarde-wg" "$APP_MACOS/netgarde-wg"
cp "$WG_GO" "$APP_MACOS/wireguard-go"
chmod +x "$DIST/netgarde-wg" "$DIST/wireguard-go" "$APP_MACOS/netgarde-wg" "$APP_MACOS/wireguard-go"

echo ""
echo "Built:"
echo "  $DIST/netgarde-wg"
echo "  $DIST/wireguard-go"
echo "  $APP"
echo ""
echo "Double-click: open $APP"
echo "Or copy to Applications:"
echo "  cp -R $APP /Applications/"
echo ""
echo "First launch: if macOS blocks the app, right-click NetGarde.app → Open."
echo "Connect from the NG menu bar icon (admin password required for VPN)."
