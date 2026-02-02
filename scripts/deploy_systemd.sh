#!/bin/bash
# Cherokee AI Federation - Systemd Deployment Script
# Run with: sudo /ganuda/scripts/deploy_systemd.sh

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║          CHEROKEE AI FEDERATION - SYSTEMD DEPLOYMENT            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Copy service files
echo "[1/5] Installing service files..."
cp /ganuda/scripts/systemd/*.service /etc/systemd/system/
ls -la /etc/systemd/system/{vllm,llm-gateway,jr-*,telegram-*}.service

# Step 2: Reload systemd
echo ""
echo "[2/5] Reloading systemd daemon..."
systemctl daemon-reload

# Step 3: Stop manual processes
echo ""
echo "[3/5] Stopping manual processes..."
pkill -f 'vllm.entrypoints' 2>/dev/null || echo "  vLLM not running manually"
pkill -f 'uvicorn gateway:app' 2>/dev/null || echo "  Gateway not running manually"
pkill -f 'jr_bidding_daemon' 2>/dev/null || echo "  Jr Bidding not running manually"
pkill -f 'jr_task_executor' 2>/dev/null || echo "  Jr Executor not running manually"
pkill -f 'telegram_chief' 2>/dev/null || echo "  Telegram not running manually"
sleep 3

# Step 4: Enable and start services
echo ""
echo "[4/5] Starting services (vLLM first, then others)..."
systemctl enable vllm llm-gateway jr-bidding jr-executor telegram-chief

echo "  Starting vLLM (30s model load time)..."
systemctl start vllm
sleep 30

echo "  Starting LLM Gateway..."
systemctl start llm-gateway
sleep 3

echo "  Starting Jr services..."
systemctl start jr-bidding jr-executor
sleep 2

echo "  Starting Telegram Chief..."
systemctl start telegram-chief

# Step 5: Verify
echo ""
echo "[5/5] Verifying services..."
echo ""
systemctl status vllm llm-gateway jr-bidding jr-executor telegram-chief --no-pager | head -50

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT COMPLETE                          ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║  Verify health: curl http://localhost:8080/health               ║"
echo "║  View logs: journalctl -u llm-gateway -f                        ║"
echo "║  Restart all: systemctl restart vllm llm-gateway jr-*           ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "For Seven Generations."
