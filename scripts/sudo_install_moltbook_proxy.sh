#!/bin/bash
# Cherokee AI Federation — Moltbook Proxy Installation
# Run with: sudo bash /ganuda/scripts/sudo_install_moltbook_proxy.sh
# For Seven Generations

set -e

echo "ᎣᏏᏲ — Installing Crawdad's Moltbook Proxy Service"
echo "=================================================="

# 1. Create log file
echo "[1/4] Setting up log file..."
touch /ganuda/logs/moltbook_proxy.log
chown dereadi:dereadi /ganuda/logs/moltbook_proxy.log

# 2. Install systemd service
echo "[2/4] Installing systemd service..."
cp /ganuda/scripts/systemd/moltbook-proxy.service /etc/systemd/system/moltbook-proxy.service
systemctl daemon-reload

# 3. Enable (but don't start yet — need to register first)
echo "[3/4] Enabling service (not starting)..."
systemctl enable moltbook-proxy.service

echo "[4/4] Done!"
echo ""
echo "=================================================="
echo "Next steps (as dereadi, NOT root):"
echo ""
echo "  1. Register Crawdad on Moltbook:"
echo "     cd /ganuda/services/moltbook_proxy"
echo "     python3 register_agent.py"
echo ""
echo "  2. Load initial posts:"
echo "     python3 load_initial_posts.py"
echo ""
echo "  3. Start the service:"
echo "     sudo systemctl start moltbook-proxy"
echo ""
echo "  4. Check status:"
echo "     sudo systemctl status moltbook-proxy"
echo "     tail -f /ganuda/logs/moltbook_proxy.log"
echo ""
echo "  Kill switch: touch /ganuda/services/moltbook_proxy/ENGAGEMENT_PAUSED"
echo "  Resume:      rm /ganuda/services/moltbook_proxy/ENGAGEMENT_PAUSED"
echo ""
echo "ᎣᏏᏲ — Crawdad is ready to swim."
