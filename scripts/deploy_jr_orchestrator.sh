#!/bin/bash
# Deploy Jr Orchestrator Service
# Run as: sudo bash /ganuda/scripts/deploy_jr_orchestrator.sh

set -e

echo "=== Deploying Jr Orchestrator ==="

# 1. Create the service file
echo "[1/7] Creating service file..."
cat > /ganuda/scripts/systemd/jr-orchestrator.service << 'SERVICEEOF'
[Unit]
Description=Cherokee AI Jr Orchestrator - Graduated Priority Queue
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python jr_orchestrator.py
Restart=always
RestartSec=30
StandardOutput=append:/ganuda/logs/jr_orchestrator.log
StandardError=append:/ganuda/logs/jr_orchestrator.log
SyslogIdentifier=jr-orchestrator

[Install]
WantedBy=multi-user.target
SERVICEEOF

echo "   Created /ganuda/scripts/systemd/jr-orchestrator.service"

# 2. Link to systemd
echo "[2/7] Linking to systemd..."
ln -sf /ganuda/scripts/systemd/jr-orchestrator.service /etc/systemd/system/
echo "   Linked to /etc/systemd/system/"

# 3. Reload systemd
echo "[3/7] Reloading systemd..."
systemctl daemon-reload
echo "   Daemon reloaded"

# 4. Stop old workers
echo "[4/7] Stopping old Jr workers..."
pkill -f "jr_queue_worker.py" 2>/dev/null || true
systemctl stop jr-queue-worker 2>/dev/null || true
echo "   Old workers stopped"

# 5. Disable old service
echo "[5/7] Disabling old service..."
systemctl disable jr-queue-worker 2>/dev/null || true
echo "   Old service disabled"

# 6. Enable and start orchestrator
echo "[6/7] Enabling and starting jr-orchestrator..."
systemctl enable jr-orchestrator
systemctl start jr-orchestrator
echo "   Jr Orchestrator started"

# 7. Verify
echo "[7/7] Verifying..."
sleep 2
systemctl status jr-orchestrator --no-pager

echo ""
echo "=== Deployment Complete ==="
echo "Monitor with: tail -f /ganuda/logs/jr_orchestrator.log"
