#!/bin/bash
# Fix VetAssist Frontend Build - Jan 30 2026
# Problem: Root-owned files in .next/standalone from previous sudo build
# Run as: sudo bash /ganuda/scripts/sudo_fix_frontend_build_jan30.sh
set -e

echo "=== Stopping Frontend Service ==="
systemctl stop vetassist-frontend || true

echo ""
echo "=== Removing root-owned .next directory ==="
rm -rf /ganuda/vetassist/frontend/.next
echo "Removed .next/"

echo ""
echo "=== Rebuilding as dereadi ==="
cd /ganuda/vetassist/frontend
su - dereadi -c "cd /ganuda/vetassist/frontend && npm run build"

echo ""
echo "=== Copying static files to standalone ==="
su - dereadi -c "cd /ganuda/vetassist/frontend && cp -r .next/static .next/standalone/.next/ && cp -r public .next/standalone/ 2>/dev/null || true"

echo ""
echo "=== Starting Frontend Service ==="
systemctl start vetassist-frontend
sleep 3

echo ""
echo "=== Status ==="
systemctl status vetassist-frontend --no-pager | head -10

echo ""
echo "Done. Login page corruption fixed, build cache cleaned."
