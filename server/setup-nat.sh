#!/usr/bin/env bash
# Enable IPv4 forwarding and NAT for WireGuard clients (10.0.0.0/24).
# Run on EC2 as root: sudo bash setup-nat.sh
set -euo pipefail

VPN_CIDR="${VPN_CIDR:-10.0.0.0/24}"
WG_IF="${WG_IF:-wg0}"

WAN_IF="$(ip -4 route show default 2>/dev/null | awk '{print $5; exit}')"
if [[ -z "$WAN_IF" ]]; then
  echo "error: could not detect default egress interface" >&2
  exit 1
fi

echo "VPN subnet: $VPN_CIDR via $WG_IF → NAT on $WAN_IF"

sysctl -w net.ipv4.ip_forward=1
if ! grep -q '^net.ipv4.ip_forward=1' /etc/sysctl.conf 2>/dev/null; then
  echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
fi

if command -v ufw &>/dev/null && ufw status 2>/dev/null | grep -q "Status: active"; then
  ufw route allow in on "$WG_IF" out on "$WAN_IF" comment "wg forward" || true
  ufw route allow in on "$WAN_IF" out on "$WG_IF" comment "wg return" || true
fi

iptables -C FORWARD -i "$WG_IF" -o "$WAN_IF" -j ACCEPT 2>/dev/null || \
  iptables -I FORWARD 1 -i "$WG_IF" -o "$WAN_IF" -j ACCEPT
iptables -C FORWARD -i "$WAN_IF" -o "$WG_IF" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || \
  iptables -I FORWARD 1 -i "$WAN_IF" -o "$WG_IF" -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -t nat -C POSTROUTING -s "$VPN_CIDR" -o "$WAN_IF" -j MASQUERADE 2>/dev/null || \
  iptables -t nat -A POSTROUTING -s "$VPN_CIDR" -o "$WAN_IF" -j MASQUERADE

echo "NAT rules applied. Test from a connected client: ping -c2 1.1.1.1 && dig @10.0.0.1 example.com"
