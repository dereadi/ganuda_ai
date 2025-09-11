#!/bin/bash
# Council Milker Service Setup

echo "🏛️ Installing Council Milker Service..."

# Copy service file
sudo cp /tmp/council-milker.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable council-milker.service

# Start service
sudo systemctl start council-milker.service

# Check status
sudo systemctl status council-milker.service

echo "✅ Council Milker Service installed and started!"
