#!/bin/bash
# Rebuild VetAssist Frontend
# Run as: sudo bash /ganuda/scripts/sudo_rebuild_vetassist_frontend.sh

set -e

echo "=== Stopping Frontend Service ==="
systemctl stop vetassist-frontend

echo ""
echo "=== Cleaning Old Build ==="
cd /ganuda/vetassist/frontend
rm -rf .next/cache .next/static 2>/dev/null || true

echo ""
echo "=== Rebuilding Frontend ==="
npm run build

echo ""
echo "=== Copying Static Files to Standalone ==="
cp -r .next/static .next/standalone/.next/
cp -r public .next/standalone/ 2>/dev/null || true
echo "Static files copied to standalone directory"

echo ""
echo "=== Restarting Frontend Service ==="
systemctl start vetassist-frontend
sleep 3

echo ""
echo "=== Verifying ==="
systemctl status vetassist-frontend --no-pager | head -8

echo ""
echo "=== CSS Files ==="
ls -la .next/static/css/

echo ""
echo "=== Testing ==="
CSS_FILE=$(curl -s http://localhost:3000/ | grep -oP '/_next/static/css/[^"]+' | head -1)
echo "Served CSS: $CSS_FILE"

if [ -f ".next/static/css/$(basename $CSS_FILE)" ]; then
    echo "✅ CSS file exists!"
else
    echo "⚠️ CSS mismatch - may need another rebuild"
fi

echo ""
echo "Done! Clear browser cache and reload."
