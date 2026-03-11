# Jr Instruction: Slack Migration — Remaining 9 Telegram-Only Files

**Task #TBD**
**Date:** 2026-03-10
**Priority:** 3 (Non-urgent — critical files already migrated by TPM)
**TPM:** Claude Opus

## Context

Leaders Meeting #1 (Longhouse bb75fd4e3a693335) mandated completing the Telegram→Slack migration. TPM migrated 13 of 22 files directly (grindstone surge). These 9 remaining files are lower-priority (less frequently called or less critical alerts). The migration pattern is documented in `/ganuda/docs/kb/KB-SLACK-TELEGRAM-BRIDGE.md`.

## CRITICAL: Read the KB First

Before touching ANY file, read `/ganuda/docs/kb/KB-SLACK-TELEGRAM-BRIDGE.md`. It contains:
- The exact migration pattern (Option A and Option B)
- Channel routing guide (which alerts go to which Slack channel)
- Gotchas (PYTHONPATH, parse_mode, urllib vs requests)

## Task

For each of the 9 files below, add Slack-first routing using Option B (minimal insertion) from the KB. Keep all existing Telegram code as fallback.

## Files to Migrate

### 1. `/ganuda/scripts/deer_jewel_digest.py`
- **Function:** `send_digest()` (line ~87)
- **Slack channel:** `deer-signals`

### 2. `/ganuda/scripts/council_telegram_async.py`
- **Function:** `send_telegram()` (line ~49)
- **Slack channel:** `council-votes`

### 3. `/ganuda/scripts/safety/canary_probe.py`
- **Function:** `send_telegram()` (line ~30)
- **Slack channel:** `longhouse`

### 4. `/ganuda/services/research_worker.py`
- **Function:** Direct `requests.post` calls (line ~242)
- **Slack channel:** `jr-tasks`

### 5. `/ganuda/email_daemon/telegram_alerts.py`
- **Function:** `send_job_alert()` (line ~89)
- **Slack channel:** `deer-signals`

### 6. `/ganuda/email_daemon/job_email_daemon_v2.py`
- **Function:** Uses `telegram_alerts.py` module (line ~250)
- **Slack channel:** `deer-signals`
- **NOTE:** If you migrate telegram_alerts.py (#5), this file may not need changes.

### 7. `/ganuda/services/ulisi/observer.py`
- **Function:** `send_telegram_alert()` (line ~286)
- **Slack channel:** `longhouse`

### 8. `/ganuda/services/ulisi/heartbeat.py`
- **Function:** Direct API call (line ~115)
- **Slack channel:** `fire-guard`

### 9. `/ganuda/backend/telegram_integration.py`
- **SKIP THIS FILE** — It's a Telegram bot command handler, not an alert sender. No migration needed.

## The Pattern (copy this exactly)

At the TOP of each `send_telegram()` or alert-sending function body, add:

```python
    # Slack-first routing (Leaders Meeting #1, Mar 10 2026)
    try:
        import sys
        if '/ganuda/lib' not in sys.path:
            sys.path.insert(0, '/ganuda/lib')
        from slack_federation import send as _slack_send
        channel = 'CHANNEL_NAME_HERE'  # see channel routing in KB
        if _slack_send(channel, message):
            return True
    except Exception:
        pass  # fall through to existing Telegram code
```

Replace `CHANNEL_NAME_HERE` with the correct channel from the table above. Replace `message` with whatever variable holds the alert text in that function.

## Steps

For EACH file (1-8, skip #9):

### Step 1: Read the file
Read the full file to understand the send function.

### Step 2: Find the send function
Identify the function that calls `requests.post` with the Telegram API URL.

### Step 3: Add the Slack routing block
Insert the pattern above as the FIRST lines of the function body, BEFORE any existing code.

### Step 4: Verify the file still parses
```bash
python3 -c "import py_compile; py_compile.compile('/path/to/file', doraise=True)"
```

## Acceptance Criteria

- All 8 files (skip #9) have Slack-first routing added
- All 8 files still parse without syntax errors
- Existing Telegram code is preserved as fallback (NOT deleted)
- Channel routing matches the table above
- No new dependencies added (slack_federation.py is already in /ganuda/lib)

## Constraints

- Do NOT delete existing Telegram code — it is the fallback
- Do NOT modify the function signature (name, arguments)
- Do NOT add new pip dependencies
- Do NOT modify slack_federation.py or slack_telegram_bridge.py
- If a file uses `urllib.request` instead of `requests`, the Slack routing block still works (it imports slack_federation directly, not requests)
