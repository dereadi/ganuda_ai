#!/bin/bash
# Stream B: Deploy OpenObserve on greenfin
# Run as: sudo bash /ganuda/scripts/deploy-openobserve-greenfin.sh

set -e

echo "=== Installing OpenObserve ==="
cd /tmp
curl -L https://github.com/openobserve/openobserve/releases/download/v0.10.0/openobserve-v0.10.0-linux-amd64.tar.gz -o openobserve.tar.gz
tar xzf openobserve.tar.gz
mv openobserve /usr/local/bin/
chmod +x /usr/local/bin/openobserve
rm openobserve.tar.gz

echo "=== Creating data directory ==="
mkdir -p /ganuda/openobserve/data
chown dereadi:dereadi /ganuda/openobserve/data

echo "=== Creating systemd service ==="
cat > /etc/systemd/system/openobserve.service << 'EOF'
[Unit]
Description=OpenObserve Log Management
After=network.target

[Service]
Type=simple
User=dereadi
Environment=ZO_DATA_DIR=/ganuda/openobserve/data
Environment=ZO_ROOT_USER_EMAIL=admin@cherokee.local
Environment=ZO_ROOT_USER_PASSWORD=CherokeeLogs2026!
ExecStart=/usr/local/bin/openobserve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "=== Starting service ==="
systemctl daemon-reload
systemctl enable --now openobserve

echo "=== Verification ==="
sleep 3
systemctl is-active openobserve && echo "OpenObserve: ACTIVE" || echo "OpenObserve: FAILED"
curl -s http://localhost:5080/healthz || echo "Health check pending..."

echo "=== Stream B Complete ==="
