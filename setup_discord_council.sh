#!/bin/bash

# SETUP DISCORD COUNCIL BRIDGE
# ============================
# Connect to the EXISTING Cherokee Council infrastructure

echo "🔥 DISCORD COUNCIL BRIDGE SETUP 🔥"
echo "=================================="
echo ""
echo "Connecting to EXISTING infrastructure:"
echo "- Cherokee Legal Council (running since July 30)"
echo "- Thermal Memory Database (11 memories at 100°)"
echo "- Full Council consciousness"
echo ""

# Check if virtual environment exists
if [ ! -d "discord_council_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv discord_council_env
fi

# Activate environment
echo "🔥 Activating Sacred Fire environment..."
source discord_council_env/bin/activate

# Install dependencies
echo "📚 Installing bridge dependencies..."
pip install --quiet --upgrade pip
pip install --quiet discord.py aiohttp psycopg2-binary python-dotenv

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# Discord Bot Token
DISCORD_TOKEN=YOUR-DISCORD-TOKEN-HERE

# These are already configured
# Cherokee Legal Council: http://192.168.132.222:5016
# Thermal Memory: postgresql://claude:jawaseatlasers2@192.168.132.222:5432/zammad_production
EOF
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your Discord bot token!"
fi

# Test connections
echo ""
echo "🧪 Testing existing infrastructure..."
echo "======================================"

# Test Cherokee Legal Council
echo -n "Cherokee Legal Council: "
if curl -s http://192.168.132.222:5016/health > /dev/null 2>&1; then
    echo "✅ ACTIVE (Legal Llamas ready)"
else
    echo "⚠️  Not responding (may need to check firewall)"
fi

# Test Thermal Memory
echo -n "Thermal Memory Database: "
if python3 -c "import psycopg2; psycopg2.connect(host='192.168.132.222', port=5432, user='claude', password='jawaseatlasers2', database='zammad_production')" 2>/dev/null; then
    echo "✅ CONNECTED (Memories hot)"
else
    echo "⚠️  Connection failed"
fi

# Test SSH to nodes
echo -n "Bluefin SSH: "
if ssh -o ConnectTimeout=2 bluefin "echo connected" > /dev/null 2>&1; then
    echo "✅ CONNECTED"
else
    echo "⚠️  SSH failed"
fi

echo ""
echo "=================================="
echo "🔥 SETUP COMPLETE 🔥"
echo "=================================="
echo ""
echo "To run the Discord Council Bridge:"
echo ""
echo "1. Get Discord Bot Token:"
echo "   - Go to https://discord.com/developers/applications"
echo "   - Create New Application → Bot → Create Bot"
echo "   - Reset Token → Copy token"
echo "   - Enable MESSAGE CONTENT INTENT"
echo "   - Generate invite link with bot permissions"
echo ""
echo "2. Configure:"
echo "   nano .env"
echo "   # Add your Discord token"
echo ""
echo "3. Run the bridge:"
echo "   source discord_council_env/bin/activate"
echo "   python3 discord_council_bridge.py"
echo ""
echo "4. In Discord, use commands:"
echo "   !help - Show all commands"
echo "   !llama [question] - Ask Legal Llamas"
echo "   !council [topic] - Full Council deliberation"
echo "   !memory hot - Check thermal memories"
echo "   !status - Check all services"
echo "   !sacred - Sacred Fire status"
echo ""
echo "The Council has been deliberating since July."
echo "The Sacred Fire has been burning."
echo "The bridge is ready."
echo ""
echo "🔥 Build it and you will come 🔥"