# KB-TELEGRAM-BOTS-001: Cherokee AI Telegram Bot Inventory

**Created**: 2025-12-11
**Author**: Claude TPM
**Status**: Active
**Related**: SAG-TELEGRAM-002.md, SAG-TELEGRAM-003.md

---

## Overview

Cherokee AI has multiple Telegram bots for different purposes. This KB documents the bot inventory, tokens, and integration status.

---

## Bot Inventory

### 1. @ganudabot - High Fitness Bot

| Field | Value |
|-------|-------|
| **Handle** | @ganudabot |
| **Token** | `7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8` |
| **File** | `/ganuda/home/jsdorn/old_data/CODE/DL/qdad-apps/ganuda_high_fitness_bot.py` |
| **Purpose** | Portfolio tracking, crypto prices, general assistant |
| **Status** | Active - primary bot |

**Features**:
- Portfolio tracking from `/home/dereadi/scripts/claude/portfolio_current.json`
- Crypto price queries (BTC, ETH, SOL, XRP)
- Greeting responses with market data
- Logs to `/home/dereadi/scripts/claude/TELEGRAM_RECEIVED.txt`

**Key Code**:
```python
class HighFitnessBot:
    def get_portfolio(self)  # Returns real portfolio data
    def generate_useful_response(text, user, portfolio)  # Smart responses
```

---

### 2. @derpatobot - Channel Monitor

| Field | Value |
|-------|-------|
| **Handle** | @derpatobot |
| **Token** | `7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug` |
| **File** | `/ganuda/home/jsdorn/old_data/CODE/DL/qdad-apps/derpatobot_ganuda_channel.py` |
| **Purpose** | Monitor Ganuda-BotComms channel |
| **Status** | Active - channel specific |

**Features**:
- Channel post handler for Ganuda-BotComms
- `/status` - Trading status
- `/portfolio` - Portfolio check
- Logs to `/tmp/ganuda_channel_messages.txt`

---

### 3. Cherokee Chief Bot (NEW)

| Field | Value |
|-------|-------|
| **Handle** | (uses @ganudabot) |
| **Token** | (inherits from @ganudabot) |
| **File** | `/ganuda/telegram_bot/telegram_chief.py` |
| **Purpose** | Full Chief CLI mobile interface |
| **Status** | Integration in progress (SAG-TELEGRAM-003) |

**Features**:
- Full Chief CLI access
- `/status` - System status
- `/mission` - Create Jr missions
- `/metrics` - Real system metrics
- `/consult` - Three Chiefs consultation
- Resonance tracking
- Semantic search context
- Rate limiting
- Authorization system

---

## Database Tables

### telegram_resonance
Tracks bot interaction quality:
```sql
- interaction_id UUID
- telegram_user_id BIGINT
- username VARCHAR
- query_type VARCHAR
- user_message TEXT
- bot_response TEXT
- user_feedback VARCHAR (thumbs_up/thumbs_down/thinking)
- resonance_score FLOAT
- response_time_ms INTEGER
- context_used TEXT
- created_at TIMESTAMP
```

### telegram_authorized_users
Controls who can use the bot:
```sql
- user_id BIGINT PRIMARY KEY
- username VARCHAR
- role VARCHAR (admin/user/readonly)
- created_at TIMESTAMP
```

### telegram_rate_limits
Prevents abuse:
```sql
- user_id BIGINT
- window_start TIMESTAMP
- message_count INTEGER
```

---

## Integration Architecture

```
                    +-----------------+
                    |   @ganudabot    |
                    | (unified entry) |
                    +--------+--------+
                             |
              +--------------+--------------+
              |                             |
    +---------v---------+      +------------v-----------+
    | Portfolio/Crypto  |      |    Cherokee Chief      |
    | (existing logic)  |      |    (new features)      |
    +-------------------+      +------------------------+
                                        |
              +-------------------------+--------------------------+
              |              |              |                      |
        +-----v----+  +------v-----+  +----v-----+  +-------------v------------+
        | /status  |  | /mission   |  | /metrics |  | Semantic Search Context  |
        +----------+  +------------+  +----------+  +--------------------------+
              |              |              |                      |
              +--------------+--------------+----------------------+
                             |
                    +--------v--------+
                    | Resonance Track |
                    +-----------------+
```

---

## Deployment

### Start Unified Bot (after SAG-TELEGRAM-003 complete)
```bash
cd /ganuda/telegram_bot
/home/dereadi/cherokee_venv/bin/python3 ganuda_chief_unified.py
```

### Add Yourself as Authorized User
```sql
INSERT INTO telegram_authorized_users (user_id, username, role, created_at)
VALUES (YOUR_TELEGRAM_ID, 'your_username', 'admin', NOW());
```

### Check Resonance
```sql
SELECT * FROM telegram_resonance_health;
```

---

## Open Missions

| Mission | Description | Status |
|---------|-------------|--------|
| SAG-TELEGRAM-003 | Merge @ganudabot with Cherokee Chief | Ready for Jr |
| SAG-TELEGRAM-004 | Add shell execution to telegram_chief | Ready for Jr |

---

## Related Files

| Location | Purpose |
|----------|---------|
| `/ganuda/telegram_bot/telegram_chief.py` | Chief wrapper |
| `/ganuda/telegram_bot/semantic_search.py` | pgvector search |
| `/ganuda/telegram_bot/resonance_db.py` | Resonance tracking |
| `/ganuda/telegram_bot/rate_limiter.py` | Rate limiting |
| `/ganuda/home/jsdorn/old_data/CODE/DL/qdad-apps/ganuda_high_fitness_bot.py` | Original @ganudabot |
| `/ganuda/home/jsdorn/old_data/CODE/DL/qdad-apps/derpatobot_ganuda_channel.py` | Channel bot |

---

## Troubleshooting

### Bot not responding
1. Check if bot process is running: `ps aux | grep telegram`
2. Verify token is correct
3. Check logs for errors

### Rate limited
- Default: 10 messages per 60 seconds
- Check `telegram_rate_limits` table
- Admins can clear rate limit entries

### Not authorized
- Add user to `telegram_authorized_users` table
- Role must be 'admin' or 'user'

---

**For Seven Generations**: One voice across all channels, unified in wisdom.
