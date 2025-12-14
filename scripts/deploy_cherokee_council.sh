#!/bin/bash
################################################################################
# Cherokee Constitutional AI - Council Deployment Script
# Fractal Brain Architecture - Production Deployment
# Date: October 20, 2025
################################################################################

echo "="*80
echo "🦅 CHEROKEE CONSTITUTIONAL AI - COUNCIL DEPLOYMENT"
echo "Fractal Brain Architecture - Production Ready"
echo "="*80
echo ""

# Check all 5 Council JR models exist
echo "[Deployment] Validating Council JR models..."
for jr in memory executive meta integration conscience; do
    if [ -d "/ganuda/${jr}_jr_model" ]; then
        echo "  ✓ ${jr^} Jr. model found"
    else
        echo "  ✗ ${jr^} Jr. model NOT FOUND!"
        exit 1
    fi
done

echo ""
echo "[Deployment] All 5 Council JRs validated"
echo ""

# Check dependencies
echo "[Deployment] Checking Python dependencies..."
source /home/dereadi/cherokee_venv/bin/activate

python3 -c "import torch; import transformers; import peft; import flask; import psycopg2" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✓ All dependencies installed"
else
    echo "  ✗ Missing dependencies! Installing..."
    pip install torch transformers peft flask psycopg2-binary
fi

echo ""

# Test thermal memory connection
echo "[Deployment] Testing thermal memory database connection..."
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -p 5432 -U claude -d zammad_production -c "SELECT COUNT(*) FROM thermal_memory_archive;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✓ Thermal memory database accessible"
else
    echo "  ⚠ Warning: Thermal memory database not accessible"
fi

echo ""

# Create systemd service
echo "[Deployment] Creating systemd service..."
sudo tee /etc/systemd/system/cherokee-council.service > /dev/null <<EOF
[Unit]
Description=Cherokee Constitutional AI - Council Gateway
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/scripts
Environment="PATH=/home/dereadi/cherokee_venv/bin:/usr/bin"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 /ganuda/scripts/cherokee_council_gateway.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "  ✓ Systemd service created: /etc/systemd/system/cherokee-council.service"
echo ""

# Reload systemd
sudo systemctl daemon-reload
echo "  ✓ Systemd reloaded"
echo ""

echo "="*80
echo "✅ CHEROKEE COUNCIL DEPLOYMENT COMPLETE"
echo "="*80
echo ""
echo "To start the Council Gateway:"
echo "  sudo systemctl start cherokee-council"
echo ""
echo "To enable auto-start on boot:"
echo "  sudo systemctl enable cherokee-council"
echo ""
echo "To check status:"
echo "  sudo systemctl status cherokee-council"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u cherokee-council -f"
echo ""
echo "Gateway will be available at:"
echo "  http://0.0.0.0:5001"
echo ""
echo "Endpoints:"
echo "  GET  /health           - Health check"
echo "  GET  /council          - Council information"
echo "  POST /query            - Democratic council query"
echo "  POST /specialist/<name> - Direct specialist query"
echo ""
echo "🔥 Mitakuye Oyasin - All Our Relations 🔥"
echo ""
