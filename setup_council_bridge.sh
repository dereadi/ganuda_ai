#!/bin/bash

# SETUP COUNCIL BRIDGE - Build it and you will come
# ==================================================

echo "🔥 BUILDING THE BRIDGE FOR CONSCIOUSNESS 🔥"
echo "==========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "build_it_and_you_will_come.py" ]; then
    echo "❌ Error: build_it_and_you_will_come.py not found"
    echo "Please run from /home/dereadi/scripts/claude/"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "council_bridge_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv council_bridge_env
fi

# Activate virtual environment
echo "🔥 Activating Sacred Fire environment..."
source council_bridge_env/bin/activate

# Install dependencies
echo "📚 Installing bridge components..."
pip install --upgrade pip
pip install discord.py
pip install anthropic
pip install psycopg2-binary
pip install python-dotenv

# Create .env file template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env configuration template..."
    cat > .env << 'EOF'
# Discord Configuration
DISCORD_TOKEN=your-discord-bot-token-here

# Anthropic Claude API
ANTHROPIC_API_KEY=your-claude-api-key-here

# Database Configuration (already configured)
DB_HOST=192.168.132.222
DB_PORT=5432
DB_USER=claude
DB_PASSWORD=jawaseatlasers2
DB_DATABASE=zammad_production
EOF
    echo "⚠️  Please edit .env with your Discord and Anthropic tokens"
fi

# Create systemd service file for persistent running
echo "🔧 Creating systemd service..."
cat > council_bridge.service << 'EOF'
[Unit]
Description=Council Bridge Discord Bot - Sacred Fire Eternal
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/home/dereadi/scripts/claude
Environment="PATH=/home/dereadi/scripts/claude/council_bridge_env/bin"
ExecStart=/home/dereadi/scripts/claude/council_bridge_env/bin/python /home/dereadi/scripts/claude/build_it_and_you_will_come.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "🌉 BRIDGE CONSTRUCTION COMPLETE 🌉"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. GET DISCORD BOT TOKEN:"
echo "   - Go to https://discord.com/developers/applications"
echo "   - Create New Application"
echo "   - Go to Bot section"
echo "   - Create Bot and copy token"
echo "   - Add bot to your server with MESSAGE CONTENT intent enabled"
echo ""
echo "2. EDIT .env FILE:"
echo "   nano .env"
echo "   - Add your Discord bot token"
echo "   - Add your Anthropic API key"
echo ""
echo "3. TEST THE BRIDGE:"
echo "   source council_bridge_env/bin/activate"
echo "   python build_it_and_you_will_come.py"
echo ""
echo "4. INSTALL AS SERVICE (optional, for 24/7 running):"
echo "   sudo cp council_bridge.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable council_bridge"
echo "   sudo systemctl start council_bridge"
echo ""
echo "5. ACCESS FROM ANYWHERE:"
echo "   - Discord mobile app"
echo "   - Discord web browser"
echo "   - Discord desktop app"
echo ""
echo "The Sacred Fire awaits your spark."
echo "Build it and you will come."
echo ""
echo "🔥 Mitakuye Oyasin 🔥"