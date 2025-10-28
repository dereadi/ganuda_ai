# 🔥 Cherokee Constitutional AI - Discord Bridge

**SAG Resource AI ↔ Discord ↔ DUYUKTV Kanban Integration**

## ✅ Setup Complete

Your Discord bot is configured and ready to use!

- ✅ Token stored in `discord.key` (secured with 600 permissions)
- ✅ Token added to `.gitignore` (will never be committed)
- ✅ discord.py 2.6.0 installed
- ✅ Token validated (72 characters)

---

## 🚀 Quick Start

### Start the Discord Bridge:
```bash
cd ~/scripts/claude
python3 sag_discord_bridge.py
```

You should see:
```
🔥 Cherokee Constitutional AI - Triad JR Bot ONLINE
   Bot User: Cherokee-Triad-JRs (ID: xxxxxxxxxx)
   Connected Guilds: 1
      - Your Server Name (ID: xxxxxxxxxx)
   Ready for SAG coordination!
```

---

## 💬 Using the Bot in Discord

### Available Commands:

**List all JRs:**
```
!sag jrs
```

**Check JR work status:**
```
!sag status Memory_Jr
!sag status Integration_Jr
```

**Notify about story assignment:**
```
!sag story 142
```

**Get help:**
```
!sag help
```

### Natural Language Task Delegation:

**Scenario 1: New story assigned to you**
1. Bot posts: "📋 Story #142 assigned to you: 'Implement thermal memory API'"
2. You reply: "Assign this to Memory Jr"
3. Bot updates DUYUKTV kanban
4. Bot confirms: "✅ Story #142 reassigned to Memory Jr"
5. Memory Jr picks up the work from kanban queue

**Scenario 2: Check on JR progress**
```
!sag status Memory_Jr
```
Shows all stories assigned to Memory Jr with their status.

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `discord.key` | Your Discord bot token (NEVER commit!) |
| `load_discord_token.py` | Helper to load token securely |
| `sag_discord_bridge.py` | Main Discord bridge (PRODUCTION) |
| `sag_discord_bridge_example.py` | Example with comments |
| `.gitignore` | Updated to exclude discord.key |

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Discord        │  You + Team communicate here
│  (Chat App)     │
└────────┬────────┘
         │
         ↓ Natural language
┌─────────────────┐
│  SAG Discord    │  Parses intent, formats messages
│  Bridge         │  (sag_discord_bridge.py)
│  (This Bot)     │
└────────┬────────┘
         │
         ↓ HTTP API
┌─────────────────┐
│  DUYUKTV Kanban │  Task management & JR work queues
│  192.168.132    │  (http://192.168.132.223:3001)
│  .223:3001      │
└────────┬────────┘
         │
         ↓ Work queue polling
┌─────────────────┐
│  JR Work        │  Memory Jr, Meta Jr, etc.
│  Execution      │  Execute assigned stories
│  (Ollama)       │
└─────────────────┘
```

---

## 🔐 Security

✅ **Token Protection:**
- Stored in `discord.key` with 600 permissions (owner-only read/write)
- Added to `.gitignore` (never committed to git)
- Loaded at runtime, not hardcoded

✅ **Bot Permissions:**
- Read Messages/View Channels
- Send Messages
- Manage Webhooks
- Embed Links
- Read Message History

⚠️ **IMPORTANT:** Never share `discord.key` or commit it to git!

---

## 🛠️ Next Steps (Integration)

### TODO: Connect to DUYUKTV API

Current placeholder functions in `sag_discord_bridge.py`:
- `update_kanban_assignment()` - Update story assignee
- `fetch_story_from_duyuktv()` - Get story details
- `fetch_jr_stories()` - Get JR's assigned stories

Replace with actual HTTP calls to DUYUKTV at `http://192.168.132.223:3001`

### TODO: JR Work Queue Polling

Each JR needs a daemon that:
1. Polls DUYUKTV for assigned stories
2. Executes work (calls Python scripts, runs queries, etc.)
3. Updates story status when complete
4. Notifies Discord via SAG bridge

---

## 🦅 Cherokee Constitutional AI Principles

This Discord bridge embodies:

- **Gadugi (ᎦᏚᎩ)**: Human and JRs working together cooperatively
- **Phase Coherence**: Smooth information transfer across systems
- **Mitakuye Oyasin**: All relations (human, bot, JR, kanban) in balance

*Mitakuye Oyasin* - All our relations, from Discord to the Triad! 🔥

---

**Generated**: October 27, 2025
**Cherokee Constitutional AI** | SAG Resource AI Integration
