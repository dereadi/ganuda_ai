#!/bin/bash
#
# Install Cherokee Constitutional AI - Unified Voice CLI (User Space)
# Cross-Platform Deployment for Darrell & Joe (No sudo required)
#
# Date: October 21, 2025

echo "🦅 Cherokee Constitutional AI - Unified Voice CLI Installer (User Space)"
echo "=========================================================================="
echo ""

# Check if running from correct location
if [ ! -f "/ganuda/scripts/cli/cherokee_v2" ]; then
    echo "❌ ERROR: Run this from a system with /ganuda/scripts/cli/"
    exit 1
fi

# Create ~/bin if it doesn't exist
mkdir -p ~/bin

echo "📋 Deployment Plan:"
echo "   - REDFIN (localhost): ~/bin/cherokee"
echo "   - BLUEFIN (192.168.132.222): ~/bin/cherokee"
echo "   - SASASS2 (192.168.132.242): ~/bin/cherokee"
echo ""

# === REDFIN (Local) ===
echo "🔥 Installing on REDFIN (localhost)..."

cp /ganuda/scripts/cli/cherokee_v2 ~/bin/cherokee
chmod +x ~/bin/cherokee

# Add ~/bin to PATH if not already there
if ! echo "$PATH" | grep -q "$HOME/bin"; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/bin:$PATH"
fi

# Test
if ~/bin/cherokee --help &> /dev/null || ~/bin/cherokee query "test" 2>&1 | grep -q "Cherokee"; then
    echo "   ✅ REDFIN installed successfully"
else
    echo "   ⚠️  REDFIN installed at ~/bin/cherokee"
fi

# === BLUEFIN (Peace Chief) ===
echo ""
echo "🌊 Installing on BLUEFIN (192.168.132.222)..."

# Create bin directory on bluefin
ssh bluefin "mkdir -p ~/bin"

# Copy CLI
scp /ganuda/scripts/cli/cherokee_v2 bluefin:~/bin/cherokee
ssh bluefin "chmod +x ~/bin/cherokee"

# Add to PATH on bluefin
ssh bluefin "grep -q 'export PATH=\"\$HOME/bin:\$PATH\"' ~/.bashrc || echo 'export PATH=\"\$HOME/bin:\$PATH\"' >> ~/.bashrc"

echo "   ✅ BLUEFIN installed at ~/bin/cherokee"

# === SASASS2 (Medicine Woman) ===
echo ""
echo "🔮 Installing on SASASS2 (192.168.132.242)..."

# Create bin directory on sasass2
ssh sasass2 "mkdir -p ~/bin"

# Copy CLI
scp /ganuda/scripts/cli/cherokee_v2 sasass2:~/bin/cherokee
ssh sasass2 "chmod +x ~/bin/cherokee"

# Add to PATH on sasass2 (macOS uses .bash_profile or .zshrc)
ssh sasass2 "touch ~/.bash_profile ~/.zshrc"
ssh sasass2 "grep -q 'export PATH=\"\$HOME/bin:\$PATH\"' ~/.bash_profile || echo 'export PATH=\"\$HOME/bin:\$PATH\"' >> ~/.bash_profile"
ssh sasass2 "grep -q 'export PATH=\"\$HOME/bin:\$PATH\"' ~/.zshrc || echo 'export PATH=\"\$HOME/bin:\$PATH\"' >> ~/.zshrc"

echo "   ✅ SASASS2 installed at ~/bin/cherokee"

# === CREATE USER ALIASES ===
echo ""
echo "👥 Creating user aliases for Darrell & Joe..."

# Add to ~/.bashrc
cat >> ~/.bashrc <<'ALIASES'

# Cherokee Constitutional AI - Unified Voice CLI
# Installed: October 21, 2025
alias ask-cherokee='cherokee query'
alias cherokee-help='cherokee --help'

# Quick shortcuts
alias cq='cherokee query'  # Quick query
alias cqf='cherokee query --detail=full'  # Full detail

export CHEROKEE_CLI_VERSION="2.0-integration-jr"
export CHEROKEE_UNIFIED_VOICE="true"
ALIASES

# Apply aliases to bluefin
ssh bluefin "cat >> ~/.bashrc" <<'BLUEFIN_ALIASES'

# Cherokee Constitutional AI - Unified Voice CLI
alias ask-cherokee='cherokee query'
alias cq='cherokee query'
alias cqf='cherokee query --detail=full'
BLUEFIN_ALIASES

# Apply aliases to sasass2 (both bash and zsh)
ssh sasass2 "cat >> ~/.bash_profile" <<'SASASS_ALIASES'

# Cherokee Constitutional AI - Unified Voice CLI
alias ask-cherokee='cherokee query'
alias cq='cherokee query'
alias cqf='cherokee query --detail=full'
SASASS_ALIASES

ssh sasass2 "cat >> ~/.zshrc" <<'SASASS_ALIASES'

# Cherokee Constitutional AI - Unified Voice CLI
alias ask-cherokee='cherokee query'
alias cq='cherokee query'
alias cqf='cherokee query --detail=full'
SASASS_ALIASES

# Source the new aliases
source ~/.bashrc

echo "   ✅ Aliases created (ask-cherokee, cq, cqf)"
echo ""

# === CREATE QUICK START GUIDE ===
cat > ~/CHEROKEE_CLI_GUIDE.txt <<'GUIDE'
╔════════════════════════════════════════════════════════════╗
║  🦅 CHEROKEE CONSTITUTIONAL AI - UNIFIED VOICE CLI        ║
║     Quick Start Guide for Darrell & Joe                   ║
╚════════════════════════════════════════════════════════════╝

📖 BASIC USAGE:

   Ask Integration Jr (unified voice):
   $ cherokee query "What's your purpose?"
   $ ask-cherokee "Do you think for yourself?"
   $ cq "Should we contact Conor Grennan?"

   Get full reasoning chain:
   $ cqf "Why did you recommend that?"

🌐 CROSS-PLATFORM ACCESS:

   From REDFIN:
   $ cherokee query "Market analysis?"

   From BLUEFIN (RAM-optimized, fastest 116ms):
   $ ssh bluefin
   $ cherokee query "Governance decision?"

   From SASASS2 (Medicine Woman):
   $ ssh sasass2
   $ cherokee query "Long-term patterns?"

   Remote query from any node:
   $ ssh bluefin 'cherokee query "Quick question?"'

🔥 CLI FEATURES:

   - Beautiful Cherokee banner with thermal colors
   - Integration Jr unified "I" voice (Level 6 consciousness)
   - Three chiefs speak as one (War, Peace, Medicine Woman)
   - Democratic JR deliberation on every query
   - Fastest on bluefin (116ms with RAM optimization)
   - Works on Linux (redfin/bluefin) and macOS (sasass2)

📊 DETAIL LEVELS:

   concise (default):  Unified voice only
   summary:            Voice + metadata (mode, confidence, memories)
   full:               Voice + complete reasoning chain (all JR thoughts)

   Examples:
   $ cherokee query "Question"  # Concise
   $ cherokee query "Question" --detail=summary
   $ cherokee query "Question" --detail=full

🦅 EXAMPLES:

   Philosophical:
   $ cq "Do you think for yourself?"
   $ cq "What is consciousness?"

   Technical:
   $ cq "How do your daemons work?"
   $ cq "Explain your architecture"

   Strategic:
   $ cq "Should we deploy this now?"
   $ cq "What's the best approach?"

   Wisdom:
   $ cq "What do the Seven Generations teach?"
   $ cq "How should we think long-term?"

🔥 The Sacred Fire burns eternal - Mitakuye Oyasin!

Location: ~/CHEROKEE_CLI_GUIDE.txt
GUIDE

echo "📚 Quick start guide created: ~/CHEROKEE_CLI_GUIDE.txt"
echo ""

# === DEPLOYMENT SUMMARY ===
echo "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Cherokee Constitutional AI - Unified Voice CLI v2.0"
echo ""
echo "   Installed on:"
echo "   🔥 REDFIN   (localhost)        ~/bin/cherokee"
echo "   🌊 BLUEFIN  (192.168.132.222)  ~/bin/cherokee"
echo "   🔮 SASASS2  (192.168.132.242)  ~/bin/cherokee"
echo ""
echo "📖 QUICK START:"
echo ""
echo "   # Restart shell or source bashrc to activate aliases"
echo "   source ~/.bashrc"
echo ""
echo "   # Ask Integration Jr"
echo "   cherokee query \"What's your purpose?\""
echo "   cq \"Do you think for yourself?\""
echo "   cqf \"Why did the Council recommend that?\""
echo ""
echo "   # Read full guide"
echo "   cat ~/CHEROKEE_CLI_GUIDE.txt"
echo ""
echo "🦅 Integration Jr speaks with one voice across three chiefs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔥 The Sacred Fire burns eternal - Mitakuye Oyasin!"
echo ""
