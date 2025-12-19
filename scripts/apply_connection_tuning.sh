#!/bin/bash
# Connection Tuning Script for Redfin
# Run with: sudo bash /ganuda/scripts/apply_connection_tuning.sh

echo "=== Applying Connection Tuning ==="
echo ""

# 1. SSH idle connection killing
echo "1. Configuring SSH idle timeout..."
tee /etc/ssh/sshd_config.d/ganuda.conf << 'SSHEOF'
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30
SSHEOF
systemctl reload sshd
echo "   Done."

# 2. TCP keepalive tuning
echo ""
echo "2. Applying TCP keepalive tuning..."
tee /etc/sysctl.d/99-ganuda-tcp.conf << 'SYSEOF'
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
SYSEOF
sysctl -p /etc/sysctl.d/99-ganuda-tcp.conf
echo "   Done."

# 3. Verify
echo ""
echo "=== Verification ==="
echo "TCP keepalive time: $(sysctl -n net.ipv4.tcp_keepalive_time)"
echo "SSH ClientAliveInterval: $(sshd -T 2>/dev/null | grep clientaliveinterval)"
echo ""
echo "=== Complete ==="
