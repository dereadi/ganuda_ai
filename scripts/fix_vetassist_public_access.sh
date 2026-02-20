#!/bin/bash
# VetAssist Public Access Fix - URGENT
# Run on redfin as dereadi
# Date: January 22, 2026

set -e

echo "=== VetAssist Public Access Fix ==="
echo "Fixing API URL for external access..."

cd /ganuda/vetassist/frontend

# Backup current env
cp .env.local .env.local.backup.$(date +%Y%m%d_%H%M%S)

# Update API URL to use relative path (works for all domains)
sed -i 's|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=/api/v1|' .env.local

echo "Updated .env.local:"
grep NEXT_PUBLIC_API_URL .env.local

echo ""
echo "=== Rebuilding Frontend ==="
npm run build

echo ""
echo "=== Restarting Frontend ==="
# Kill existing process
pkill -f "node.*\.next" || true
sleep 2

# Start standalone server
cd .next/standalone
nohup node server.js > /ganuda/logs/vetassist-frontend.log 2>&1 &

echo ""
echo "=== Verification ==="
sleep 3
curl -sI http://localhost:3000 | head -3

echo ""
echo "=== Done! ==="
echo "Test from external network: https://vetassist.ganuda.us/calculator"
