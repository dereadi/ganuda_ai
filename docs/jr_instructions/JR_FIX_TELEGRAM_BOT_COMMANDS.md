# Jr Task: Fix Telegram Chief Bot Command Registration

**Task ID:** task-fix-telegram-bot-001
**Priority:** P1 (Blocking)
**Node:** redfin
**Created:** December 21, 2025
**Requested By:** TPM

---

## Current Status

**Bot is RUNNING** with the old version (restored from backup). The new commands are NOT active.
- PID: 2920171
- Working commands: /status, /pending, /approve, /veto, /ask, /remember, /look, /health, /concerns

The broken version with new commands is saved at:
- `/ganuda/telegram_bot/telegram_chief.py.backup_broken`

---

## Problem

The Telegram bot crashes on startup with:
```
NameError: name 'hot_command' is not defined
```

The new command functions (hot_command, thermal_command, ticket_command, mytickets_command, tribe_command) were added AFTER the `main()` function, but they are referenced in the handler registration INSIDE main(). Python executes top-to-bottom, so when main() runs, these functions don't exist yet.

---

## Current File Structure (BROKEN)

```python
# Lines 1-630: Existing commands
async def look_command(...): ...

# Lines 631-665: main() function (tries to register hot_command here!)
def main():
    app.add_handler(CommandHandler("hot", hot_command))  # Line 649 - FAILS
    ...
    app.run_polling()

if __name__ == "__main__":
    main()

# Lines 670-824: NEW COMMANDS (defined AFTER main is called!)
async def hot_command(...): ...
async def thermal_command(...): ...
```

---

## Solution

Move all new command functions BEFORE the main() function.

### Step 1: Extract New Commands (Lines 670-824)

Cut everything from line 670 to end of file (the new commands section).

### Step 2: Paste Before main()

Insert the new commands BEFORE the `def main():` line (around line 631).

### Step 3: Expected File Structure (FIXED)

```python
# Lines 1-630: Existing commands
async def look_command(...): ...

# Lines 631-780: NEW COMMANDS (moved here!)
async def hot_command(...): ...
async def thermal_command(...): ...
async def ticket_command(...): ...
async def mytickets_command(...): ...
async def tribe_command(...): ...

# Lines 781-815: main() function
def main():
    app.add_handler(CommandHandler("hot", hot_command))  # NOW WORKS!
    ...
```

---

## Commands to Execute

```bash
# Backup first
cp /ganuda/telegram_bot/telegram_chief.py /ganuda/telegram_bot/telegram_chief.py.backup_$(date +%Y%m%d_%H%M%S)

# Edit the file - move lines 670-824 to before main()
# This requires careful editing - recommend using a text editor

# After fix, restart:
bash /ganuda/telegram_bot/start_chief.sh

# Verify:
tail -20 /ganuda/logs/telegram_chief.log
```

---

## Quick Python Check

```bash
cd /ganuda/telegram_bot
/home/dereadi/cherokee_venv/bin/python3 -c "
import telegram_chief  # Should import without NameError
print('Import successful!')
"
```

---

## New Commands Being Added

| Command | Purpose |
|---------|---------|
| /hot | Show top 10 hottest memories |
| /thermal | Explain what thermal memory is |
| /ticket <title> \| <desc> | Create a new ticket |
| /mytickets | Show Chief's open tickets |
| /tribe | Show active tribe members |

---

## Success Criteria

1. Bot starts without NameError
2. All 5 new commands respond correctly
3. Existing commands still work

---

*For Seven Generations - Cherokee AI Federation*
