#!/bin/bash
# Fix VetAssist Backend - Stop crash loop and disable until fixed
# Run as: sudo bash /ganuda/scripts/fix_vetassist_backend.sh

echo "=== Stopping VetAssist Backend Crash Loop ==="

# Stop the service
systemctl stop vetassist-backend
echo "Service stopped"

# Disable to prevent restart on boot
systemctl disable vetassist-backend
echo "Service disabled (will not start on boot)"

# Show status
systemctl status vetassist-backend --no-pager | head -5

echo ""
echo "Backend has circular import bug in auth system."
echo "Jr task will be queued to fix it."
echo "Re-enable with: sudo systemctl enable --now vetassist-backend"
