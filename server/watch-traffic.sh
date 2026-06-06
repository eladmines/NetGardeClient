#!/usr/bin/env bash
# Watch per-peer WireGuard traffic on the VPN server (MiB totals + interval delta).
# Usage: sudo bash watch-traffic.sh [wg0] [interval_seconds]
set -euo pipefail

WG_IF="${1:-wg0}"
INTERVAL="${2:-5}"

if ! command -v wg &>/dev/null; then
  echo "error: wireguard-tools (wg) required" >&2
  exit 1
fi

echo "Watching $WG_IF every ${INTERVAL}s (Ctrl+C to stop)"
echo "  down = received on server (client upload)"
echo "  up   = sent from server (client download)"
echo ""

declare -A LAST_RX LAST_TX

while true; do
  while IFS= read -r line; do
    [[ "$line" =~ ^peer:\ (.+)$ ]] && PEER="${BASH_REMATCH[1]}" && continue
    [[ "$line" =~ ^[[:space:]]+transfer:\ ([0-9]+),\ ([0-9]+) ]] || continue
    RX="${BASH_REMATCH[1]}"
    TX="${BASH_REMATCH[2]}"
    KEY="${PEER:0:16}"
    if [[ -n "${LAST_RX[$KEY]:-}" ]]; then
      DRX=$((RX - LAST_RX[$KEY]))
      DTX=$((TX - LAST_TX[$KEY]))
      DRX_MIB=$(awk "BEGIN {printf \"%.2f\", $DRX/1048576}")
      DTX_MIB=$(awk "BEGIN {printf \"%.2f\", $DTX/1048576}")
      RX_MIB=$(awk "BEGIN {printf \"%.2f\", $RX/1048576}")
      TX_MIB=$(awk "BEGIN {printf \"%.2f\", $TX/1048576}")
      echo "$(date -u +%H:%M:%S) peer ${KEY}… +${DTX_MIB} MiB down (client dl), +${DRX_MIB} MiB up | total ${TX_MIB} / ${RX_MIB} MiB"
    else
      RX_MIB=$(awk "BEGIN {printf \"%.2f\", $RX/1048576}")
      TX_MIB=$(awk "BEGIN {printf \"%.2f\", $TX/1048576}")
      echo "$(date -u +%H:%M:%S) peer ${KEY}… total ${TX_MIB} MiB down / ${RX_MIB} MiB up"
    fi
    LAST_RX[$KEY]=$RX
    LAST_TX[$KEY]=$TX
    PEER=""
  done < <(wg show "$WG_IF")
  sleep "$INTERVAL"
done
