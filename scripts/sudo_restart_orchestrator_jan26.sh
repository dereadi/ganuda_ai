#!/bin/bash
# Restart Jr Orchestrator to spawn missing workers
# Run as: sudo bash /ganuda/scripts/sudo_restart_orchestrator_jan26.sh

echo "=== Restarting Jr Orchestrator ==="
systemctl restart jr-orchestrator
sleep 3
systemctl status jr-orchestrator --no-pager | head -20

echo ""
echo "=== Active Workers ==="
ps aux | grep jr_queue_worker | grep -v grep
