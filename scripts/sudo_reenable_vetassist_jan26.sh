#!/bin/bash
# Re-enable VetAssist Backend after repairs
# Run as: sudo bash /ganuda/scripts/sudo_reenable_vetassist_jan26.sh

echo "=== Re-enabling VetAssist Backend ==="

# Enable and start the service
systemctl enable vetassist-backend
systemctl start vetassist-backend

sleep 3

# Show status
systemctl status vetassist-backend --no-pager | head -15

echo ""
echo "=== Testing endpoint ==="
curl -s http://localhost:8001/health 2>/dev/null || curl -s http://localhost:8000/health 2>/dev/null || echo "Health check endpoint not responding yet"

echo ""
echo "VetAssist backend re-enabled!"
echo "Dashboard: https://vetassist.ganuda.us/"
