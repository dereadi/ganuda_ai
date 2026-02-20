#!/bin/bash
# Restart VetAssist Frontend to fix CSS mismatch
# Run as: sudo bash /ganuda/scripts/sudo_restart_vetassist_frontend.sh

echo "=== Restarting VetAssist Frontend ==="

systemctl restart vetassist-frontend
sleep 3

systemctl status vetassist-frontend --no-pager | head -10

echo ""
echo "=== Checking CSS ==="
curl -s http://localhost:3000/ | grep -oP 'href="[^"]*\.css[^"]*"' | head -3

echo ""
echo "Frontend restarted. Clear browser cache and reload."
