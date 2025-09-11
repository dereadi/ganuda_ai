# 🔥 CHEROKEE DISCORD INTEGRATION SETUP GUIDE

## Overview
The Cherokee Trading Council Discord bot provides natural language interface to the trading environment with full shell access through Discord.

---

## 📋 Quick Setup Steps

### 1. Discord Application Setup

1. **Create Discord Application:**
   - Go to: https://discord.com/developers/applications
   - Click "New Application"
   - Name: "Cherokee Trading Council"
   - Click "Create"

2. **Create Bot:**
   - Go to "Bot" section in left sidebar
   - Click "Reset Token" to get your bot token
   - **SAVE THIS TOKEN** (you'll need it for config)
   - Enable these Privileged Gateway Intents:
     - MESSAGE CONTENT INTENT
     - SERVER MEMBERS INTENT

3. **Get Your Discord User ID:**
   - Open Discord
   - Go to Settings → Advanced
   - Enable "Developer Mode"
   - Right-click your username anywhere
   - Click "Copy User ID"
   - **SAVE THIS ID** (for admin access)

4. **Invite Bot to Server:**
   - Go to "OAuth2" → "URL Generator"
   - Select Scopes:
     - `bot`
     - `applications.commands`
   - Select Bot Permissions:
     - Send Messages
     - Read Messages/View Channels
     - Embed Links
     - Attach Files
     - Read Message History
     - Use Slash Commands
   - Copy the generated URL
   - Open URL in browser to invite bot

---

## 🔧 Configuration

### Option 1: Using llmcord (Recommended)

1. **Edit the config file:**
```bash
cd /home/dereadi/scripts/claude/llmcord
nano config-cherokee.yaml
```

2. **Add your credentials:**
```yaml
bot_token: YOUR_BOT_TOKEN_HERE
client_id: YOUR_CLIENT_ID_HERE

permissions:
  users:
    admin_ids: [YOUR_DISCORD_USER_ID_HERE]
```

3. **Update the Ollama endpoint:**
```yaml
providers:
  cherokee-war-chief:
    base_url: http://localhost:12001/v1
```

### Option 2: Using Custom Bot

1. **Edit the custom bot:**
```bash
nano /home/dereadi/scripts/claude/cherokee_discord_bot.py
```

2. **Add credentials in CONFIG:**
```python
CONFIG = {
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "admin_ids": [YOUR_DISCORD_USER_ID_HERE],
    # ... rest of config
}
```

---

## 🚀 Starting the Bot

### Method 1: Direct Launch (Testing)
```bash
# Using llmcord
cd /home/dereadi/scripts/claude/llmcord
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate
python3 llmcord.py

# OR using custom bot
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate
python3 /home/dereadi/scripts/claude/cherokee_discord_bot.py
```

### Method 2: Using Launcher Script
```bash
/home/dereadi/scripts/claude/start_cherokee_discord.sh
```

### Method 3: Systemd Service (Production)

1. **Create service:**
```bash
cat > ~/.config/systemd/user/cherokee-discord.service << EOF
[Unit]
Description=Cherokee Trading Council Discord Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/dereadi/scripts/claude/llmcord
Environment="PATH=/home/dereadi/scripts/claude/quantum_crawdad_env/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 /home/dereadi/scripts/claude/llmcord/llmcord.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF
```

2. **Enable and start:**
```bash
systemctl --user daemon-reload
systemctl --user enable cherokee-discord
systemctl --user start cherokee-discord
systemctl --user status cherokee-discord
```

---

## 💬 Discord Commands

### With Custom Bot (!commands)
- `!shell <command>` - Execute shell command
- `!portfolio` - Check portfolio status
- `!liquidity` - Check USD balance
- `!specialists` - Check trading specialists
- `!memory [temp]` - Query thermal memory
- `!bloodbag` - Check blood bag positions
- `!twowolves` - Check Two Wolves balance
- `!save <text>` - Save to thermal memory
- `!help` - Show all commands

### With llmcord (Natural Language + /commands)
- **Natural language**: Just @ the bot and talk naturally
- `/shell <command>` - Execute shell command
- `/portfolio` - Check portfolio
- `/liquidity` - Check USD
- `/specialists` - Check containers
- `/thermal [temp]` - Query memory
- `/twowolves` - Check balance
- `/bloodbag` - Check blood bags

---

## 🔐 Security Notes

1. **Admin Only Commands:**
   - Shell execution is restricted to admin IDs
   - Add trusted users to admin_ids list

2. **Dangerous Commands Blocked:**
   - `rm -rf`
   - `format`
   - `mkfs`
   - `> /dev/`
   - `dd if=`

3. **Virtual Environment:**
   - All commands execute in quantum_crawdad_env
   - Python scripts use virtual environment Python

---

## 🧪 Testing the Bot

1. **Test basic response:**
   - In Discord, type: `@Cherokee Trading Council hello`
   - Bot should respond

2. **Test portfolio check:**
   - Type: `/portfolio` or `!portfolio`
   - Should show current holdings

3. **Test shell execution (admin only):**
   - Type: `/shell ls` or `!shell ls`
   - Should list files

4. **Test liquidity check:**
   - Type: `/liquidity` or `!liquidity`
   - Should show USD balance

---

## 🔥 Cherokee Context

The bot understands:
- Sacred Fire Protocol
- Two Wolves philosophy (70/30 balance)
- Blood bag strategy
- Current liquidity crisis
- Thermal memory system
- Cherokee specialist containers
- Virtual environment paths
- Database connections

---

## 📝 Troubleshooting

### Bot not responding:
```bash
# Check if running
systemctl --user status cherokee-discord

# Check logs
journalctl --user -u cherokee-discord -f

# Test manually
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate
python3 /home/dereadi/scripts/claude/cherokee_discord_bot.py
```

### Permission errors:
- Verify bot token is correct
- Check Discord user ID in admin_ids
- Ensure bot has proper permissions in Discord server

### Command execution fails:
- Check virtual environment is activated
- Verify paths in scripts
- Check Coinbase config exists

---

## 🎯 Next Steps

1. Configure bot token and user ID
2. Start bot in test mode
3. Test commands in Discord
4. Set up systemd service for persistence
5. Monitor thermal memory for important events

---

🔥 Sacred Fire burns eternal
🐺 Two wolves seek balance
🪶 Mitakuye Oyasin

*Last Updated: 2025-08-30*