#!/usr/bin/env bash
# Run on the WireGuard Ubuntu server (as root): sudo bash setup-dnsmasq.sh
set -euo pipefail

WG_IF="${WG_IF:-wg0}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! ip link show "$WG_IF" &>/dev/null; then
  echo "error: interface $WG_IF not found. Start WireGuard first (wg-quick@wg0)." >&2
  exit 1
fi

WG_IP="$(ip -4 -o addr show dev "$WG_IF" | awk '{print $4}' | cut -d/ -f1 | head -1)"
if [[ -z "$WG_IP" ]]; then
  echo "error: no IPv4 on $WG_IF" >&2
  exit 1
fi

echo "WireGuard server IP on $WG_IF: $WG_IP"

install -d -m 0755 /etc/dnsmasq.d
CONF="/etc/dnsmasq.d/wireguard.conf"
sed "s/10.0.0.1/${WG_IP}/g; s/interface=wg0/interface=${WG_IF}/" \
  "$SCRIPT_DIR/dnsmasq-wireguard.conf" >"$CONF"
chmod 0644 "$CONF"

# Allow DNS from VPN subnet (adjust CIDR to match your wg0 Address= line)
VPN_CIDR="${VPN_CIDR:-10.0.0.0/24}"
if command -v ufw &>/dev/null && ufw status 2>/dev/null | grep -q "Status: active"; then
  ufw allow in on "$WG_IF" to any port 53 proto udp comment "dnsmasq wg" || true
fi

# iptables: accept DNS to dnsmasq on wg
iptables -C INPUT -i "$WG_IF" -p udp --dport 53 -j ACCEPT 2>/dev/null || \
  iptables -I INPUT -i "$WG_IF" -p udp --dport 53 -j ACCEPT
iptables -C INPUT -i "$WG_IF" -p tcp --dport 53 -j ACCEPT 2>/dev/null || \
  iptables -I INPUT -i "$WG_IF" -p tcp --dport 53 -j ACCEPT

systemctl enable dnsmasq
systemctl restart dnsmasq
systemctl --no-pager status dnsmasq

echo ""
echo "Client my.conf should use:  DNS = ${WG_IP}"
echo "Test from a connected client:  dig @${WG_IP} example.com"
echo "Watch logs:  sudo tail -f /var/log/dnsmasq.log"
