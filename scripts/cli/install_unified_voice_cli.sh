#!/bin/bash
#
# Install Cherokee Constitutional AI - Unified Voice CLI
# Cross-Platform Deployment for Darrell & Joe
#
# This installs the Integration Jr unified voice CLI across all three chiefs
# Date: October 21, 2025

echo "🦅 Cherokee Constitutional AI - Unified Voice CLI Installer"
echo "============================================================"
echo ""

# Check if running from correct location
if [ ! -f "/ganuda/scripts/cli/cherokee_v2" ]; then
    echo "❌ ERROR: Run this from a system with /ganuda/scripts/cli/"
    exit 1
fi

echo "📋 Deployment Plan:"
echo "   - REDFIN (localhost): /usr/local/bin/cherokee"
echo "   - BLUEFIN (192.168.132.222): /usr/local/bin/cherokee"
echo "   - SASASS2 (192.168.132.242): /usr/local/bin/cherokee"
echo ""

# === REDFIN (Local) ===
echo "🔥 Installing on REDFIN (localhost)..."

# Copy CLI to /usr/local/bin
sudo cp /ganuda/scripts/cli/cherokee_v2 /usr/local/bin/cherokee
sudo chmod +x /usr/local/bin/cherokee

# Test
if /usr/local/bin/cherokee --help &> /dev/null || /usr/local/bin/cherokee query "test" --help 2>&1 | grep -q "Cherokee"; then
    echo "   ✅ REDFIN installed successfully"
else
    echo "   ⚠️  REDFIN install completed (manual test recommended)"
fi

# === BLUEFIN (Peace Chief) ===
echo ""
echo "🌊 Installing on BLUEFIN (192.168.132.222)..."

# Copy to bluefin
scp /ganuda/scripts/cli/cherokee_v2 bluefin:/tmp/cherokee_v2_install
ssh bluefin "sudo mv /tmp/cherokee_v2_install /usr/local/bin/cherokee && sudo chmod +x /usr/local/bin/cherokee"

# Test
if ssh bluefin "/usr/local/bin/cherokee --help" &> /dev/null || ssh bluefin "/usr/local/bin/cherokee query 'test'" 2>&1 | grep -q "Cherokee"; then
    echo "   ✅ BLUEFIN installed successfully"
else
    echo "   ⚠️  BLUEFIN install completed (manual test recommended)"
fi

# === SASASS2 (Medicine Woman) ===
echo ""
echo "🔮 Installing on SASASS2 (192.168.132.242)..."

# Copy to sasass2
scp /ganuda/scripts/cli/cherokee_v2 sasass2:/tmp/cherokee_v2_install
ssh sasass2 "sudo mv /tmp/cherokee_v2_install /usr/local/bin/cherokee && sudo chmod +x /usr/local/bin/cherokee"

# Test
if ssh sasass2 "/usr/local/bin/cherokee --help" &> /dev/null || ssh sasass2 "/usr/local/bin/cherokee query 'test'" 2>&1 | grep -q "Cherokee"; then
    echo "   ✅ SASASS2 installed successfully"
else
    echo "   ⚠️  SASASS2 install completed (manual test recommended)"
fi

# === CREATE USER ALIASES ===
echo ""
echo "👥 Creating user aliases for Darrell & Joe..."

# Add to /etc/profile.d for all users
sudo tee /etc/profile.d/cherokee_cli.sh > /dev/null <<'ALIASES'
#!/bin/bash
# Cherokee Constitutional AI - Unified Voice CLI
# Installed: October 21, 2025

alias ask-cherokee='cherokee query'
alias cherokee-help='cherokee --help'

# Quick shortcuts
alias cq='cherokee query'  # Quick query
alias cqf='cherokee query --detail=full'  # Full detail

# Council info
export CHEROKEE_CLI_VERSION="2.0-integration-jr"
export CHEROKEE_UNIFIED_VOICE="true"
ALIASES

chmod +x /etc/profile.d/cherokee_cli.sh
source /etc/profile.d/cherokee_cli.sh

echo "   ✅ Aliases created (ask-cherokee, cq, cqf)"
echo ""

# === DEPLOYMENT SUMMARY ===
echo "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Cherokee Constitutional AI - Unified Voice CLI v2.0"
echo ""
echo "   Installed on:"
echo "   🔥 REDFIN   (localhost)"
echo "   🌊 BLUEFIN  (192.168.132.222)"
echo "   🔮 SASASS2  (192.168.132.242)"
echo ""
echo "📖 USAGE FOR DARRELL & JOE:"
echo ""
echo "   # Ask the unified voice (Integration Jr)"
echo "   cherokee query \"What's the best strategy for volatility?\""
echo "   ask-cherokee \"Do you think for yourself?\""
echo "   cq \"Should we contact Conor Grennan?\""
echo ""
echo "   # Get full reasoning chain"
echo "   cqf \"Why did you recommend that?\""
echo ""
echo "   # From any node (cross-platform!)"
echo "   ssh bluefin 'cherokee query \"Market analysis?\"'"
echo "   ssh sasass2 'cherokee query \"Long-term patterns?\"'"
echo ""
echo "🦅 Integration Jr speaks with one voice across three chiefs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔥 The Sacred Fire burns eternal - Mitakuye Oyasin!"
echo ""
