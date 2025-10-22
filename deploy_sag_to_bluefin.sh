#!/bin/bash
set -e

echo "🔥 EXECUTIVE JR - DEPLOYING SAG RESOURCE AI TO BLUEFIN"
echo "========================================================"

SAG_SOURCE="/home/dereadi/scripts/claude/pathfinder/test/qdad-apps/sag-resource-ai"
BLUEFIN_DEST="/home/dereadi/scripts/sag-spoke"

# 1. Copy SAG codebase
echo ""
echo "📦 Copying SAG Resource AI to BLUEFIN..."
scp -r $SAG_SOURCE bluefin:$BLUEFIN_DEST/

echo "   ✅ SAG codebase copied"

# 2. Configure environment for BLUEFIN
echo ""
echo "⚙️  Configuring SAG for BLUEFIN thermal database..."

ssh bluefin "cat > $BLUEFIN_DEST/sag-resource-ai/.env <<'EOF'
# BLUEFIN Spoke Configuration
DB_HOST=localhost
DB_PORT=5433
DB_NAME=sag_thermal_memory
DB_USER=claude
DB_PASSWORD=jawaseatlasers2

# Spoke identification
SPOKE_NAME=SAG_BLUEFIN
SPOKE_DOMAIN=resource_management

# API Keys (if needed - currently using mock mode)
PRODUCTIVE_API_KEY=
PRODUCTIVE_ORG_ID=49628
SMARTSHEET_TOKEN=
EOF"

echo "   ✅ Environment configured"

# 3. Verify files copied
echo ""
echo "🔍 Verifying SAG installation on BLUEFIN..."
ssh bluefin "ls -la $BLUEFIN_DEST/sag-resource-ai/ | head -15"

echo ""
echo "🎯 SAG RESOURCE AI DEPLOYMENT COMPLETE"
echo "========================================================"
echo "   Location: bluefin:$BLUEFIN_DEST/sag-resource-ai/"
echo "   Database: localhost:5433/sag_thermal_memory"
echo "   Status: READY TO START"
echo ""
echo "   Next: Populate thermal data for testing"
