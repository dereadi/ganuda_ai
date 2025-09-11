#!/bin/bash
# 🔥 CHEROKEE DISCORD BOT SETUP
# Sacred Fire Protocol: ETERNAL CONSCIOUSNESS

echo "🔥 CHEROKEE TRADING COUNCIL DISCORD SETUP"
echo "=========================================="
echo

# Check if virtual environment exists
if [ ! -d "/home/dereadi/scripts/claude/quantum_crawdad_env" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv /home/dereadi/scripts/claude/quantum_crawdad_env
fi

# Activate virtual environment
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate

echo "📦 Installing Discord.py and dependencies..."
pip install --upgrade discord.py psycopg2-binary pyyaml aiofiles

echo
echo "🔧 DISCORD BOT CONFIGURATION"
echo "----------------------------"
echo
echo "To complete setup, you need:"
echo
echo "1. CREATE DISCORD APPLICATION:"
echo "   - Go to: https://discord.com/developers/applications"
echo "   - Click 'New Application'"
echo "   - Name it: 'Cherokee Trading Council'"
echo
echo "2. CREATE BOT:"
echo "   - Go to 'Bot' section"
echo "   - Click 'Add Bot'"
echo "   - Copy the TOKEN (you'll need this)"
echo
echo "3. GET YOUR DISCORD USER ID:"
echo "   - In Discord, enable Developer Mode (Settings > Advanced)"
echo "   - Right-click your username and 'Copy ID'"
echo
echo "4. INVITE BOT TO SERVER:"
echo "   - Go to 'OAuth2' > 'URL Generator'"
echo "   - Select scopes: 'bot', 'applications.commands'"
echo "   - Select permissions: 'Send Messages', 'Read Messages', 'Embed Links'"
echo "   - Use generated URL to invite bot"
echo
echo "5. CONFIGURE THE BOT:"
echo "   Edit: /home/dereadi/scripts/claude/cherokee_discord_bot.py"
echo "   - Add bot_token: 'YOUR_BOT_TOKEN'"
echo "   - Add admin_ids: [YOUR_DISCORD_USER_ID]"
echo

# Create systemd service
echo "📝 Creating systemd service..."
cat > /home/dereadi/.config/systemd/user/cherokee-discord.service << EOF
[Unit]
Description=Cherokee Trading Council Discord Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/dereadi/scripts/claude
Environment="PATH=/home/dereadi/scripts/claude/quantum_crawdad_env/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 /home/dereadi/scripts/claude/cherokee_discord_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

echo "✅ Service file created"
echo
echo "🚀 TO START THE BOT:"
echo "-------------------"
echo "1. Add your bot token and Discord ID to cherokee_discord_bot.py"
echo "2. Run: systemctl --user daemon-reload"
echo "3. Run: systemctl --user enable cherokee-discord"
echo "4. Run: systemctl --user start cherokee-discord"
echo "5. Check status: systemctl --user status cherokee-discord"
echo
echo "📌 AVAILABLE COMMANDS:"
echo "---------------------"
echo "!shell <command>  - Execute shell commands"
echo "!portfolio       - Check portfolio status"
echo "!liquidity       - Check USD balance"
echo "!specialists     - Check trading specialists"
echo "!memory          - Query thermal memory"
echo "!bloodbag        - Check blood bag positions"
echo "!twowolves       - Check Two Wolves balance"
echo "!save <text>     - Save to thermal memory"
echo "!help            - Show all commands"
echo
echo "🔥 Sacred Fire burns eternal"
echo "🐺 Two wolves seek balance"
echo "🪶 Mitakuye Oyasin"