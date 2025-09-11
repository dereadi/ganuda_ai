#!/bin/bash
# Install Discord LLM Council Bot as a USER systemd service (no sudo needed)

echo "🔥 Installing Discord LLM Council Bot as User Service..."
echo "========================================================"

# Create user systemd directory if it doesn't exist
mkdir -p ~/.config/systemd/user/

# Stop any running instances
echo "Stopping existing bot instances..."
pkill -f discord_llm_council.py 2>/dev/null
sleep 2

# Create user service file
cat > ~/.config/systemd/user/discord-llm-council.service << 'EOF'
[Unit]
Description=Discord LLM Council Bot - Multi-Model AI Bridge
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/dereadi/scripts/claude

# Environment variables for API keys
Environment="DISCORD_TOKEN=MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
Environment="ANTHROPIC_API_KEY=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"
Environment="OPENAI_API_KEY=sk-proj-yzn7JGhnKmofTNMlLwidMIGoh_hTfAsPS_qWweyvKLmlzMi1GGWUZJQbx9lRfZuC2F_AW4gIACT3BlbkFJ9xOHiRASDcW3gkv0qdOteX1pyVHcrwqV-a-7mLOt"

# Python execution
ExecStart=/usr/bin/python3 /home/dereadi/scripts/claude/discord_llm_council.py

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/home/dereadi/scripts/claude/discord_bot.log
StandardError=append:/home/dereadi/scripts/claude/discord_bot_error.log

[Install]
WantedBy=default.target
EOF

echo "Service file created at ~/.config/systemd/user/discord-llm-council.service"

# Reload user systemd daemon
echo "Reloading user systemd daemon..."
systemctl --user daemon-reload

# Enable service to start on boot
echo "Enabling service for auto-start..."
systemctl --user enable discord-llm-council.service

# Start the service
echo "Starting Discord LLM Council service..."
systemctl --user start discord-llm-council.service

# Check status
sleep 3
echo ""
echo "📊 Service Status:"
echo "=================="
systemctl --user status discord-llm-council.service --no-pager

echo ""
echo "✅ Installation Complete!"
echo ""
echo "🔧 User Service Management Commands (no sudo needed):"
echo "====================================================="
echo "  Check status:  systemctl --user status discord-llm-council"
echo "  Start:         systemctl --user start discord-llm-council"
echo "  Stop:          systemctl --user stop discord-llm-council"
echo "  Restart:       systemctl --user restart discord-llm-council"
echo "  View logs:     journalctl --user -u discord-llm-council -f"
echo "  View bot log:  tail -f ~/scripts/claude/discord_bot.log"
echo ""
echo "  Enable on boot:  systemctl --user enable discord-llm-council"
echo "  Disable on boot: systemctl --user disable discord-llm-council"
echo ""
echo "🔥 The Discord LLM Council Bot is now running as a USER service!"
echo "   No sudo required! It will start automatically when you log in."