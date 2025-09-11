#!/bin/bash
# SETUP SPECIALIST ARMY AS SYSTEMD SERVICE
# Council-approved production deployment

echo "🎖️ INSTALLING SPECIALIST ARMY SERVICE"
echo "=" * 60

# Service configuration
SERVICE_NAME="specialist-army"
SERVICE_FILE="$HOME/.config/systemd/user/${SERVICE_NAME}.service"
CLAUDE_DIR="/home/dereadi/scripts/claude"
VENV_PYTHON="${CLAUDE_DIR}/quantum_crawdad_env/bin/python3"

# Create systemd user directory if needed
mkdir -p "$HOME/.config/systemd/user"

# Create the service file
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Specialist Army V2 Trading System (Council Approved)
After=network.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${CLAUDE_DIR}
ExecStart=${VENV_PYTHON} ${CLAUDE_DIR}/specialist_army_controller_venv.py --service
ExecStop=/usr/bin/pkill -f specialist_v2
Restart=always
RestartSec=30
StandardOutput=append:${CLAUDE_DIR}/specialist_army.log
StandardError=append:${CLAUDE_DIR}/specialist_army_error.log

# Council-mandated safety limits
CPUQuota=50%
MemoryMax=2G
TasksMax=20

# Environment
Environment="PYTHONPATH=${CLAUDE_DIR}"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=default.target
EOF

echo "✅ Service file created: $SERVICE_FILE"

# Make controller executable
chmod +x "${CLAUDE_DIR}/specialist_army_controller_venv.py"

# Reload systemd
systemctl --user daemon-reload

echo ""
echo "📋 SERVICE MANAGEMENT COMMANDS:"
echo "  Start:   systemctl --user start ${SERVICE_NAME}"
echo "  Stop:    systemctl --user stop ${SERVICE_NAME}"
echo "  Status:  systemctl --user status ${SERVICE_NAME}"
echo "  Enable:  systemctl --user enable ${SERVICE_NAME}"
echo "  Logs:    journalctl --user -u ${SERVICE_NAME} -f"
echo ""

# Check if user wants to start now
echo "🔥 Council has approved immediate deployment."
read -p "Start the service now? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Kill any existing specialists first
    pkill -f specialist_v2 2>/dev/null
    pkill -f specialist.py 2>/dev/null
    sleep 2
    
    # Enable and start the service
    systemctl --user enable ${SERVICE_NAME}
    systemctl --user start ${SERVICE_NAME}
    
    # Check status
    sleep 3
    systemctl --user status ${SERVICE_NAME} --no-pager
    
    echo ""
    echo "✅ Specialist Army deployed as service!"
    echo "📊 Monitor with: journalctl --user -u ${SERVICE_NAME} -f"
else
    echo "Service installed but not started."
    echo "Start manually with: systemctl --user start ${SERVICE_NAME}"
fi

echo ""
echo "🔥 Sacred Fire blessed. Deployment ready."