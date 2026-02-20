#!/bin/bash
# Cherokee AI Federation - Sudo Commands for Jan 26, 2026
# Run as: sudo bash /ganuda/scripts/sudo_commands_jan26.sh

set -e
echo "=== Cherokee AI Federation Sudo Tasks ==="

# 1. Ensure log directories have correct permissions
echo "[1/4] Setting log directory permissions..."
chown -R dereadi:dereadi /ganuda/logs/
chmod 755 /ganuda/logs/
echo "   Done: /ganuda/logs/ permissions set"

# 2. Create metrics log directory for orchestrator tuning
echo "[2/4] Creating metrics directory..."
mkdir -p /ganuda/logs/metrics
chown dereadi:dereadi /ganuda/logs/metrics
echo "   Done: /ganuda/logs/metrics created"

# 3. Ensure config directory exists and is writable
echo "[3/4] Setting config directory permissions..."
mkdir -p /ganuda/config
chown -R dereadi:dereadi /ganuda/config
chmod 755 /ganuda/config
echo "   Done: /ganuda/config permissions set"

# 4. Restart jr-orchestrator to pick up any changes
echo "[4/4] Restarting jr-orchestrator service..."
systemctl restart jr-orchestrator
sleep 2
systemctl status jr-orchestrator --no-pager | head -5
echo "   Done: jr-orchestrator restarted"

echo ""
echo "=== All Sudo Tasks Complete ==="
echo ""
echo "Verification:"
ls -la /ganuda/logs/ | head -5
ls -la /ganuda/config/ | head -5
