# KB-TELEGRAM-GROUPS-002: Adding @ganudabot to Telegram Groups

**Created**: 2025-12-11
**Author**: Claude TPM
**Status**: Active
**Related**: KB-TELEGRAM-BOTS-001.md, SAG-TELEGRAM-005.md

---

## Overview

This guide explains how to add @ganudabot to Telegram groups and channels so the Cherokee AI assistant can help your team.

---

## Prerequisites

- You must be a group admin to add bots
- @ganudabot must be running (telegram_chief.py on Redfin)
- Your Telegram user_id must be in `telegram_authorized_users` table

---

## Step 1: Add Bot to Group

### Via Telegram App (Mobile/Desktop)

1. Open your Telegram group
2. Tap the group name at top to open Group Info
3. Tap "Add Members" or "Add"
4. Search for `@ganudabot`
5. Select and add the bot

### Via Telegram Link

Share this link in the group and click it:
```
https://t.me/ganudabot?startgroup=true
```

---

## Step 2: Make Bot Admin (Recommended)

For the bot to see all messages (not just commands):

1. Open Group Info
2. Tap "Administrators"
3. Tap "Add Administrator"
4. Select @ganudabot
5. Enable these permissions:
   - Read messages (essential)
   - Send messages (essential)
   - Delete messages (optional - for cleanup)

---

## Step 3: Configure BotFather Privacy (One-time Setup)

By default, bots only see /commands in groups. To see all messages:

1. Open Telegram and message @BotFather
2. Send: `/mybots`
3. Select `@ganudabot`
4. Select "Bot Settings"
5. Select "Group Privacy"
6. Select "Turn off"

This allows the bot to see regular messages, not just /commands.

---

## Step 4: Authorize the Group (After SAG-TELEGRAM-005)

Once group support is implemented, authorize groups via:

**Option A: In-chat command**
```
/addchat
```
(Admin only - adds current group to allowed list)

**Option B: Database insert**
```sql
INSERT INTO telegram_allowed_chats (chat_id, chat_name, chat_type, added_by)
VALUES (-1001234567890, 'Your Group Name', 'supergroup', 'yourusername');
```

To find your group's chat_id, the bot logs it when it receives messages.

---

## How the Bot Responds in Groups

| Trigger | Bot Response |
|---------|--------------|
| `/status` | Responds with system status |
| `/sh <cmd>` | Executes command (admin only) |
| `/metrics` | Shows node metrics |
| `/mission <task>` | Creates Jr mission |
| `@ganudabot <question>` | LLM responds with context |
| Reply to bot's message | LLM continues conversation |
| Regular message | Ignored (unless privacy off) |

---

## Current Limitations

Until SAG-TELEGRAM-005 is complete:
- Bot may respond to all group messages (no filtering)
- No per-group authorization
- Rate limiting is per-user only

---

## Security Considerations

1. **Only add to trusted groups** - Anyone in the group can use /sh if authorized
2. **Admin-only for /sh** - Shell commands require admin access_level
3. **Rate limiting** - Prevents abuse (10 msgs/60s per user)
4. **Audit trail** - All interactions logged to telegram_resonance

---

## Troubleshooting

### Bot doesn't respond in group
1. Check bot is admin in the group
2. Check BotFather privacy is OFF
3. Check bot process is running: `ps aux | grep telegram_chief`
4. Try a /command first (always works)

### Bot responds but says "Not authorized"
1. Add your user_id to telegram_authorized_users:
```sql
INSERT INTO telegram_authorized_users (user_id, username, access_level)
VALUES (YOUR_TELEGRAM_ID, 'yourusername', 'admin');
```

### Bot sees messages but doesn't reply
1. Check logs: `tail -f /tmp/telegram_chief.log`
2. May need to @mention the bot in groups

---

## Example: Create Cherokee Ops Group

1. Create new Telegram group called "Cherokee Ops"
2. Add @ganudabot
3. Make @ganudabot admin
4. Each team member:
   - Messages @ganudabot directly first (to get their user_id logged)
   - Gets added to telegram_authorized_users by existing admin
5. Team can now use bot in group

---

## Quick Reference

| Action | How |
|--------|-----|
| Add bot to group | Group Info → Add Members → @ganudabot |
| Make bot admin | Group Info → Admins → Add → @ganudabot |
| Check your user_id | Send any message to @ganudabot, check resonance table |
| Authorize user | `INSERT INTO telegram_authorized_users...` |
| Get group chat_id | Check bot logs after sending message in group |

---

**For Seven Generations**: Shared wisdom strengthens the tribe.
