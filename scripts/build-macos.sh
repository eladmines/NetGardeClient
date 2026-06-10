#!/usr/bin/env bash
# Build trustedge-wg CLI, TrustEdge.app (menu bar), and bundle wireguard-go.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV="${VENV:-.venv}"
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"
DIST="$ROOT/dist"
BIN="$ROOT/bin"
APP="$DIST/TrustEdge.app"
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

echo "Generating menu bar icons..."
"$PY" -c "from pathlib import Path; from trustedge_wg.gui.icons import _draw_icon, _write_png; d=Path('trustedge_wg/gui/assets'); d.mkdir(parents=True, exist_ok=True); _write_png(_draw_icon(connected=False), d/'menubar-disconnected.png'); _write_png(_draw_icon(connected=True), d/'menubar-connected.png')"

mkdir -p "$BIN" "$DIST"

WG_GO="$BIN/wireguard-go"
if [[ ! -x "$WG_GO" ]]; then
  if command -v wireguard-go >/dev/null 2>&1; then
    echo "Using wireguard-go from PATH -> $WG_GO"
    cp "$(command -v wireguard-go)" "$WG_GO"
  elif command -v brew >/dev/null 2>&1; then
    echo "Installing wireguard-go via Homebrew (prebuilt bottle) ..."
    brew install wireguard-go
    if [[ -x "$(brew --prefix wireguard-go)/bin/wireguard-go" ]]; then
      cp "$(brew --prefix wireguard-go)/bin/wireguard-go" "$WG_GO"
    else
      cp "$(command -v wireguard-go)" "$WG_GO"
    fi
  else
    echo "error: wireguard-go is required. Install with: brew install wireguard-go" >&2
    exit 1
  fi
fi

rm -rf build dist
mkdir -p "$DIST"

echo "Building CLI binary..."
"$PY" -m PyInstaller --noconfirm trustedge-wg.spec

echo "Building TrustEdge.app..."
"$PY" -m PyInstaller --noconfirm trustedge-gui.spec

cp "$WG_GO" "$DIST/wireguard-go"
cp "$DIST/trustedge-wg" "$APP_MACOS/trustedge-wg"
cp "$WG_GO" "$APP_MACOS/wireguard-go"
chmod +x "$DIST/trustedge-wg" "$DIST/wireguard-go" "$APP_MACOS/trustedge-wg" "$APP_MACOS/wireguard-go"

echo ""
echo "Built:"
echo "  $DIST/trustedge-wg"
echo "  $DIST/wireguard-go"
echo "  $APP"
echo ""
echo "Double-click: open $APP"
echo "Or copy to Applications:"
echo "  cp -R $APP /Applications/"
echo ""
echo "First launch: if macOS blocks the app, right-click TrustEdge.app → Open."
echo "Connect from the NG menu bar icon (admin password required for VPN)."
