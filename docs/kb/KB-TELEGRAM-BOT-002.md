# KB-TELEGRAM-BOT-002: Cherokee Chief Telegram Bot Capabilities

**Created**: 2025-12-11
**Updated**: 2025-12-11
**Bot**: @CherokeeChiefBot
**Location**: `/ganuda/telegram_bot/telegram_chief.py` on redfin (192.168.132.223)
**Status**: Active

---

## Overview

The Cherokee Chief Telegram Bot provides mobile access to tribal operations. It uses intent classification to route requests and integrates with thermal memory for context.

---

## Commands

### Explicit Commands (use /)

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome message and command list | |
| `/status` | System status and node health | |
| `/metrics` | Detailed node metrics | |
| `/mission <task>` | Create Jr mission for delegation | `/mission fetch solar weather data` |
| `/jrs` | Show recent Jr executions | |
| `/solar` | Get solar weather data | |
| `/sh <cmd>` | Run shell command | `/sh df -h` |
| `/script list` | List saved scripts | |
| `/script run <name>` | Run a saved script | `/script run disk_check.py` |
| `/script <name> <code>` | Save new script | `/script hello.py print("hi")` |
| `/workflow <name> <desc>` | Create Jr mission template | `/workflow backup_check 'Verify backups'` |
| `/db <query>` | Run SELECT query | `/db SELECT COUNT(*) FROM emails` |
| `/run [script]` | Run most recent or specified script | `/run` |

### Natural Language (Intent-Based)

The bot classifies natural language into intents:

| Intent | Trigger Phrases | Handler |
|--------|-----------------|---------|
| `mission` | "delegate", "create mission", "jr should" | `handle_mission_creation()` |
| `consultation` | "consult", "ask the triad", "what does" | `handle_consultation()` |
| `status` | "status", "how is", "check on" | `handle_status_query()` |
| `resonance` | "resonate", "connect with", "sync" | `handle_resonance()` |
| `code_gen` | "write script", "create code", "generate" | `handle_code_generation()` |
| default | Any other text | Routes to LLM with thermal context |

**Examples:**
- "What's the system status?" → status intent
- "Delegate to Jr: fetch solar weather" → mission intent
- "Ask the Triad about server health" → consultation intent
- "Write a script to check disk space" → code_gen intent
- "What do you know about solar weather?" → LLM with thermal memory

---

## Architecture

```
Telegram API
    ↓
telegram_chief.py (python-telegram-bot v20+)
    ↓
ChiefCLI class
    ├── Intent Classification
    │   ├── mission → handle_mission_creation()
    │   ├── consultation → handle_consultation()
    │   ├── status → handle_status_query()
    │   ├── code_gen → handle_code_generation()
    │   └── default → LLM query
    │
    ├── LLMRouter (Ollama/Anthropic)
    │   └── Context from thermal_memories table
    │
    └── Database (triad_federation on bluefin)
        ├── thermal_memories
        ├── telegram_resonance
        ├── jr_executions
        └── solar_weather
```

---

## Data Storage

### Messages Logged To
- `telegram_resonance` table (hub: 192.168.132.222)
  - user_id, username, message, response, intent, created_at

### Thermal Memory Integration
- Queries `thermal_memories` table for context
- Logs important interactions back to thermal memory
- Used for personalization and context-aware responses

---

## Jr Mission Creation

When `/mission` or mission intent detected:

1. Creates markdown file in `/ganuda/missions/`
2. Filename format: `{NAME}-JR.md`
3. Jr executor polls and picks up missions
4. Execution logged to `jr_executions` table

**Example mission file created:**
```markdown
# SOLAR-FETCH-JR: Fetch solar weather data from NOAA

## Task: Fetch solar weather data from NOAA

### Step 1: Implementation
\`\`\`python
# TODO: Add implementation
\`\`\`

## Verification
\`\`\`bash
# TODO: Add verification
\`\`\`
```

---

## Script Management

Scripts saved to: `/ganuda/scripts/`

**Flow:**
1. `/script backup.py <code>` → saves to `/ganuda/scripts/backup.py`
2. `/script run backup.py` → executes with 60s timeout
3. Output returned to Telegram (truncated at 4000 chars)

**Auto-save (TELEGRAM-BOT-008-JR - pending):**
- Natural language code requests auto-detect
- LLM generates code
- Auto-saves to `/ganuda/scripts/`
- Returns path and offers to run

---

## Security

- Authorization check on all commands via `bot.is_authorized(user_id)`
- Authorized users stored in config
- `/db` command blocks dangerous operations (DROP, DELETE, etc.)
- Shell commands run in contained environment
- Script timeout: 60 seconds

---

## Related Files

- `/ganuda/telegram_bot/telegram_chief.py` - Main bot code
- `/ganuda/telegram_bot/config.py` - Bot token, authorized users
- `/tmp/telegram_chief.log` - Bot logs
- `/ganuda/missions/` - Jr mission files
- `/ganuda/scripts/` - Saved scripts

---

## Troubleshooting

### Bot not responding
```bash
ssh dereadi@192.168.132.223 "ps aux | grep telegram_chief"
ssh dereadi@192.168.132.223 "tail -50 /tmp/telegram_chief.log"
```

### Restart bot
```bash
ssh dereadi@192.168.132.223 "pkill -f telegram_chief; cd /ganuda/telegram_bot && nohup python3 telegram_chief.py > /tmp/telegram_chief.log 2>&1 &"
```

### Check if Jr is running
```bash
ssh dereadi@192.168.132.223 "ps aux | grep jr_cli; tail -20 /tmp/jr_executor.log"
```

---

## Pending Enhancements

| Mission | Description | Status |
|---------|-------------|--------|
| TELEGRAM-BOT-007-JR | Add /solar, /jrs, /script, /workflow, /db | Completed |
| TELEGRAM-BOT-008-JR | Auto-detect code requests, auto-save scripts | Pending |
| SAG-EMAIL-005-JR | AI draft generation with thermal context | Pending |
| SAG-EMAIL-006-JR | Email senders categorization table | Pending |

---

**For Seven Generations**: Mobile access to tribal wisdom and operations.
