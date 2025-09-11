#!/bin/bash
# Install Discord LLM Council Bot as a systemd service

echo "🔥 Installing Discord LLM Council Bot Service..."
echo "=============================================="

# Stop any running instances
echo "Stopping existing bot instances..."
pkill -f discord_llm_council.py 2>/dev/null
sleep 2

# Copy service file to systemd
echo "Installing service file..."
sudo cp discord-llm-council.service /etc/systemd/system/

# Reload systemd daemon
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service to start on boot
echo "Enabling service for auto-start..."
sudo systemctl enable discord-llm-council.service

# Start the service
echo "Starting Discord LLM Council service..."
sudo systemctl start discord-llm-council.service

# Check status
sleep 3
echo ""
echo "📊 Service Status:"
echo "=================="
sudo systemctl status discord-llm-council.service --no-pager

echo ""
echo "✅ Installation Complete!"
echo ""
echo "🔧 Service Management Commands:"
echo "================================"
echo "  Check status:  sudo systemctl status discord-llm-council"
echo "  Start:         sudo systemctl start discord-llm-council"
echo "  Stop:          sudo systemctl stop discord-llm-council"
echo "  Restart:       sudo systemctl restart discord-llm-council"
echo "  View logs:     sudo journalctl -u discord-llm-council -f"
echo "  View bot log:  tail -f /home/dereadi/scripts/claude/discord_bot.log"
echo ""
echo "🔥 The Discord LLM Council Bot is now running as a service!"
echo "   It will automatically start on system boot."