# Jr Task: Disable False Positive Telegram Bot Health Check

**Priority:** P2
**Node:** redfin
**Created:** December 20, 2025
**Requested By:** TPM

---

## Context

The health monitor at `/ganuda/services/health_monitor/health_monitor.py` is checking for `telegram_chief.py` using `pgrep -f`, which is a relic from a previous build. The Telegram bot architecture has changed and this check is generating false positive alerts.

The alert text is:
```
ALERT: Telegram Bot on redfin DOWN - Command '['pgrep', '-f', 'telegram_chief.py']' timed out after 5 seconds
```

---

## Task

Remove or comment out the Telegram Bot service check from the health monitor configuration.

---

## File to Modify

`/ganuda/services/health_monitor/health_monitor.py` on **redfin** (192.168.132.223)

---

## Current Code (lines ~53-57)

```python
SERVICES = {
    "redfin": [
        {"name": "vLLM", "check_type": "http", "url": "http://localhost:8000/health", "restart_cmd": None, "critical": True},
        {"name": "LLM Gateway", "check_type": "http", "url": "http://localhost:8080/health", ... },
        {"name": "SAG UI", "check_type": "http", "url": "http://localhost:4000", "restart_cmd": None, "critical": True},
        {"name": "Telegram Bot", "check_type": "process", "process_name": "telegram_chief.py", ... },  # <-- REMOVE THIS
    ],
```

---

## Action Required

**Option A (Recommended):** Comment out the Telegram Bot entry:
```python
# DISABLED Dec 2025 - Telegram bot architecture changed, this check is obsolete
# {"name": "Telegram Bot", "check_type": "process", "process_name": "telegram_chief.py",
#  "restart_cmd": "export TELEGRAM_BOT_TOKEN='...' && cd /ganuda/telegram_bot && ...",
#  "critical": False},
```

**Option B:** Delete the entry entirely (cleaner but loses the reference)

---

## Verification

After editing, restart the health monitor timer:
```bash
sudo systemctl restart health-monitor.timer
```

Check logs to confirm no more Telegram alerts:
```bash
journalctl -u health-monitor.service -f
```

---

## Notes

- The health monitor runs every 2 minutes via `health-monitor.timer`
- The Telegram Bot was marked `critical: False` so these alerts are P2
- Keep vLLM, LLM Gateway, and SAG UI checks - those are still valid
- When new Telegram implementation is ready, add appropriate health check

---

*For Seven Generations - Cherokee AI Federation*
