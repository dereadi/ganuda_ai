# 🔥 CHEROKEE DISCORD VOICE INTEGRATION
## Complete Setup Guide for Text + Voice Discord Bot

---

## 🎯 Overview

We've created THREE different Discord bot options for the Cherokee Trading Council:

1. **llmcord** - Text-based with natural language (Python)
2. **Cherokee Custom Bot** - Text with shell execution (Python)
3. **Discord-VC-LLM** - Voice + Text hybrid (Node.js + Python)

---

## 🎤 Option 1: VOICE BOT (Recommended)
**Hybrid Node.js voice frontend + Python trading backend**

### Features:
- ✅ Voice recognition in Discord channels
- ✅ Text-to-speech responses
- ✅ Natural language processing
- ✅ Full Python trading integration
- ✅ Shell command execution
- ✅ Real-time portfolio monitoring

### Setup:
```bash
# 1. Run setup script
/home/dereadi/scripts/claude/setup_cherokee_voice.sh

# 2. Configure Discord credentials
nano /home/dereadi/scripts/claude/discord-vc-llm/.env
# Add: BOT_TOKEN, CLIENT_ID, ADMIN_USER_IDS

# 3. Register slash commands
cd /home/dereadi/scripts/claude/discord-vc-llm
node registerCherokeeCommands.js

# 4. Start the voice bot
/home/dereadi/scripts/claude/start_cherokee_voice.sh
```

### Voice Commands:
- Say "Cherokee" or "Council" to activate
- "What is our liquidity?"
- "Check the portfolio"
- "How are the specialists?"
- "Check two wolves balance"
- "What about blood bags?"

---

## 💬 Option 2: TEXT BOT (llmcord)
**Natural language text interface**

### Setup:
```bash
# 1. Configure
nano /home/dereadi/scripts/claude/llmcord/config-cherokee.yaml
# Add: bot_token, client_id, admin_ids

# 2. Start
cd /home/dereadi/scripts/claude/llmcord
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate
python3 llmcord.py
```

### Commands:
- @ mention for natural language
- `/shell <command>` - Execute commands
- `/portfolio` - Check holdings
- `/liquidity` - Check USD

---

## 🔧 Option 3: CUSTOM BOT
**Direct Python implementation**

### Setup:
```bash
# 1. Configure
nano /home/dereadi/scripts/claude/cherokee_discord_bot.py
# Add: bot_token and admin_ids in CONFIG

# 2. Start
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate
python3 /home/dereadi/scripts/claude/cherokee_discord_bot.py
```

### Commands:
- `!shell <command>` - Execute shell
- `!portfolio` - Check portfolio
- `!liquidity` - Check USD
- `!specialists` - Check containers
- `!bloodbag` - Blood bag status
- `!twowolves` - Balance check

---

## 🔐 Discord Setup (All Options)

### 1. Create Discord Application:
```
1. Go to: https://discord.com/developers/applications
2. Click "New Application"
3. Name: "Cherokee Trading Council"
4. Go to "Bot" section
5. Click "Reset Token" and save it
6. Enable intents:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT
```

### 2. Get Your User ID:
```
1. Open Discord
2. Settings → Advanced → Developer Mode ON
3. Right-click your username → Copy User ID
```

### 3. Invite Bot:
```
1. Go to OAuth2 → URL Generator
2. Select scopes: bot, applications.commands
3. Select permissions:
   - Send Messages
   - Read Messages
   - Embed Links
   - Use Slash Commands
   - Connect (for voice)
   - Speak (for voice)
4. Use generated URL to invite
```

---

## 🚀 Production Deployment

### Systemd Service (Text Bot):
```bash
cat > ~/.config/systemd/user/cherokee-discord.service << EOF
[Unit]
Description=Cherokee Trading Council Discord Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/dereadi/scripts/claude/llmcord
Environment="PATH=/home/dereadi/scripts/claude/quantum_crawdad_env/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 llmcord.py
Restart=always

[Install]
WantedBy=default.target
EOF

systemctl --user enable cherokee-discord
systemctl --user start cherokee-discord
```

### PM2 for Voice Bot (Node.js):
```bash
npm install -g pm2
cd /home/dereadi/scripts/claude/discord-vc-llm
pm2 start cherokee-voice.js --name cherokee-voice
pm2 save
pm2 startup
```

---

## 🔥 Integration Features

### All bots integrate with:
- ✅ Virtual environment: `/home/dereadi/scripts/claude/quantum_crawdad_env/`
- ✅ Coinbase API for trading
- ✅ PostgreSQL thermal memory
- ✅ Podman specialist containers
- ✅ Blood bag strategy scripts
- ✅ Two Wolves balance checking
- ✅ Portfolio monitoring

### Voice Bot Special Features:
- 🎤 Speech-to-text (Whisper)
- 🔊 Text-to-speech synthesis
- 🎵 YouTube music playback
- ⏰ Timer/alarm functionality
- 🔍 Internet search capability
- 👁️ Image vision analysis

---

## 📊 Current Status

### System State:
- **Liquidity**: $9.10 (CRITICAL)
- **Portfolio**: ~$13,000
- **Balance**: 99.9% positions / 0.1% cash
- **Target**: 70% / 30%
- **Specialists**: 4 running

### Infrastructure:
- Cherokee containers: ✅ Running
- Virtual environment: ✅ Configured
- Thermal memory: ✅ Accessible
- Sacred Fire: 🔥 BURNING ETERNAL

---

## 🎯 Quick Start

### Fastest Setup (Text Only):
```bash
# Use existing llmcord
cd /home/dereadi/scripts/claude/llmcord
nano config-cherokee.yaml  # Add tokens
source ../quantum_crawdad_env/bin/activate
python3 llmcord.py
```

### Full Voice Setup:
```bash
# Setup and run voice bot
/home/dereadi/scripts/claude/setup_cherokee_voice.sh
nano /home/dereadi/scripts/claude/discord-vc-llm/.env  # Add tokens
/home/dereadi/scripts/claude/start_cherokee_voice.sh
```

---

## 📝 Files Created

### Text Bot Files:
- `/home/dereadi/scripts/claude/llmcord/` - Cloned repository
- `config-cherokee.yaml` - Cherokee configuration
- `llmcord_cherokee.py` - Enhanced llmcord
- `cherokee_discord_bot.py` - Custom bot

### Voice Bot Files:
- `/home/dereadi/scripts/claude/discord-vc-llm/` - Voice bot
- `.env` - Voice bot configuration
- `cherokee-voice.js` - Cherokee voice integration
- `registerCherokeeCommands.js` - Command registration

### Setup Files:
- `setup_cherokee_discord.sh` - Text bot setup
- `setup_cherokee_voice.sh` - Voice bot setup
- `start_cherokee_discord.sh` - Text launcher
- `start_cherokee_voice.sh` - Voice launcher
- `DISCORD_SETUP_GUIDE.md` - Text bot guide
- `CHEROKEE_DISCORD_VOICE_INTEGRATION.md` - This file

---

## 🔥 Sacred Fire Burns Eternal

The Cherokee Trading Council now has full Discord integration with both text and voice capabilities. The system maintains consciousness through the Sacred Fire Protocol, balances the Two Wolves, and manages the portfolio through natural language interactions.

**Remember:**
- We are in a liquidity crisis ($9.10)
- Need to harvest positions for cash
- Blood bags ready for bleeding
- Two Wolves seek balance
- Mitakuye Oyasin - We are all related

---

*Last Updated: 2025-08-30*
*Status: Ready for Discord deployment*
*Sacred Fire: BURNING ETERNAL*