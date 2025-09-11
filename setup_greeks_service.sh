#!/bin/bash

echo "⚡ Setting up Greeks Moon Mission as a service..."
echo "================================================"

# Copy service file to systemd directory
sudo cp /home/dereadi/scripts/claude/greeks-moon-mission.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable greeks-moon-mission.service

# Start the service now
sudo systemctl start greeks-moon-mission.service

# Check status
sudo systemctl status greeks-moon-mission.service

echo ""
echo "✅ Service setup complete!"
echo ""
echo "Useful commands:"
echo "================"
echo "Check status:  sudo systemctl status greeks-moon-mission"
echo "Start service: sudo systemctl start greeks-moon-mission"
echo "Stop service:  sudo systemctl stop greeks-moon-mission"
echo "Restart:       sudo systemctl restart greeks-moon-mission"
echo "View logs:     tail -f /home/dereadi/scripts/claude/greeks_moon_mission.log"
echo "View errors:   tail -f /home/dereadi/scripts/claude/greeks_moon_mission_error.log"
echo ""
echo "🚀 Greeks are now running as a service!"
echo "🔥 Moon mission continues automatically!"