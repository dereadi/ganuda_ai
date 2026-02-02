#!/bin/bash
# Setup Caddy reverse proxy with SSL for VetAssist
# Run with: sudo bash /ganuda/scripts/setup_vetassist_ssl.sh

set -e

echo "=== VetAssist SSL Setup ==="
echo ""

# Install Caddy
echo "[1/4] Installing Caddy..."
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install -y caddy

# Create Caddyfile
echo "[2/4] Creating Caddyfile..."
cat > /etc/caddy/Caddyfile << 'EOF'
# VetAssist - Main site
vetassist.cherokee.ai {
    reverse_proxy localhost:3000
}

# Kanban board (if needed externally)
# kanban.cherokee.ai {
#     reverse_proxy localhost:3001
# }

# LLM Gateway API (if needed externally)
# api.cherokee.ai {
#     reverse_proxy localhost:8080
# }
EOF

# Enable and start Caddy
echo "[3/4] Starting Caddy..."
systemctl enable caddy
systemctl restart caddy

# Verify
echo "[4/4] Verifying..."
sleep 3
systemctl status caddy --no-pager
echo ""
ss -tlnp | grep -E ":80|:443"
echo ""

echo "=== Setup Complete ==="
echo ""
echo "Caddy will automatically obtain Let's Encrypt certificate."
echo "Test: https://vetassist.cherokee.ai"
echo ""
echo "To check certificate status:"
echo "  sudo caddy validate --config /etc/caddy/Caddyfile"
echo "  curl -I https://vetassist.cherokee.ai"
