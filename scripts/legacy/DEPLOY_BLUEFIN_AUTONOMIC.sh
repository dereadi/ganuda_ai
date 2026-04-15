#!/bin/bash
# Deploy Autonomic Daemons to Bluefin - Cherokee Constitutional AI
# Run this script ON BLUEFIN to deploy Memory Jr + Executive Jr

set -e

echo "🦅 Deploying Cherokee Autonomic Daemons to Bluefin..."
echo ""

# Create directory structure
echo "📁 Creating /ganuda directory structure..."
sudo mkdir -p /ganuda/daemons /ganuda/systemd
sudo chown -R $USER:$USER /ganuda
echo "✅ Directories created"
echo ""

# Copy daemon files from redfin
echo "📥 Copying daemon files from redfin..."
scp redfin:/ganuda/daemons/memory_jr_autonomic.py /ganuda/daemons/
scp redfin:/ganuda/daemons/executive_jr_autonomic.py /ganuda/daemons/
echo "✅ Daemon files copied"
echo ""

# Copy systemd service files
echo "📥 Copying systemd service files from redfin..."
scp redfin:/ganuda/systemd/memory-jr-autonomic.service /ganuda/systemd/
scp redfin:/ganuda/systemd/executive-jr-autonomic.service /ganuda/systemd/
echo "✅ Service files copied"
echo ""

# Install systemd services
echo "🔧 Installing systemd services..."
sudo cp /ganuda/systemd/memory-jr-autonomic.service /etc/systemd/system/
sudo cp /ganuda/systemd/executive-jr-autonomic.service /etc/systemd/system/
sudo systemctl daemon-reload
echo "✅ Services installed"
echo ""

# Start and enable services
echo "🔥 Starting autonomic daemons..."
sudo systemctl start memory-jr-autonomic
sudo systemctl enable memory-jr-autonomic
sudo systemctl start executive-jr-autonomic
sudo systemctl enable executive-jr-autonomic
echo "✅ Daemons started and enabled on boot"
echo ""

# Check status
echo "📊 Status check..."
sudo systemctl status memory-jr-autonomic --no-pager -l || true
echo ""
sudo systemctl status executive-jr-autonomic --no-pager -l || true
echo ""

echo "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "Memory Jr: Thermal memory maintenance (every 5 min)"
echo "Executive Jr: Specialist health monitoring (every 2 min)"
echo ""
echo "Monitor logs with:"
echo "  journalctl -u memory-jr-autonomic -u executive-jr-autonomic -f"
echo ""
echo "🔥 Cherokee Constitutional AI breathing on bluefin!"
