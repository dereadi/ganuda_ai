# KB: Slack-Telegram Bridge Migration Pattern

**Built:** 2026-03-10 by TPM (grindstone surge, Leaders Meeting #1)
**Kanban:** #2080 | **Bridge:** `/ganuda/lib/slack_telegram_bridge.py`

## Problem

17 Python files send alerts directly to Telegram via `requests.post("https://api.telegram.org/bot...")`. This creates split-brain alerting — some alerts go to Slack, some to Telegram, some to both. Attack surface: silencing one channel silences those alerts.

## Solution

Created `/ganuda/lib/slack_telegram_bridge.py` — a drop-in replacement that:
1. Routes to Slack first (via slack_federation.py)
2. Falls back to Telegram if Slack fails
3. Auto-routes to appropriate Slack channel by keyword matching
4. Has the SAME function signature as the old `send_telegram()` calls

## Migration Pattern (for Jrs)

### Option A: Full replacement (simple files)

If the file's `send_telegram()` is simple (just formats and sends):

```python
# OLD (delete the whole function)
def send_telegram(message):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"},
                  timeout=10)

# NEW (one import, delete the function)
from lib.slack_telegram_bridge import send_telegram
```

### Option B: Minimal insertion (complex files)

If the function does formatting, retries, or other logic — add Slack routing at the TOP of the function body:

```python
def send_telegram(message, severity="info"):
    # Slack-first routing (Leaders Meeting #1, Mar 10 2026)
    try:
        import sys
        if '/ganuda/lib' not in sys.path:
            sys.path.insert(0, '/ganuda/lib')
        from slack_federation import send as _slack_send
        channel = 'fire-guard'  # adjust: jr-tasks, dawn-mist, deer-signals, etc.
        if _slack_send(channel, message):
            return True
    except Exception:
        pass  # fall through to existing Telegram code

    # --- existing Telegram code below (now acts as fallback) ---
    ...
```

### Channel Routing Guide

| Alert Source | Slack Channel | Keywords |
|-------------|--------------|----------|
| Fire Guard, power, health | #fire-guard | fire guard, health, critical, power |
| Jr tasks, executor | #jr-tasks | jr task, mission, executor |
| Dawn mist, daily | #dawn-mist | dawn mist, standup, digest |
| Deer, jobs, LinkedIn | #deer-signals | deer, linkedin, market, job |
| Council, votes | #council-votes | council, vote, longhouse |
| Other daemons | #longhouse | sanctuary, shadow, dependency, canary |

## Files Migrated (TPM direct, Mar 10)

1. `/ganuda/lib/alert_manager.py` — DONE (earlier session)
2. `/ganuda/daemons/governance_agent.py` — DONE (earlier session)
3. `/ganuda/telegram_bot/telegram_chief.py` — DONE (earlier session)
4. `/ganuda/scripts/council_dawn_mist.py` — DONE (earlier session)
5. `/ganuda/scripts/safety_canary.py` — DONE (earlier session)
6. `/ganuda/jr_executor/telegram_notify.py` — DONE (grindstone surge)
7. `/ganuda/services/power_monitor/solix_monitor_daemon.py` — DONE (grindstone surge)
8. `/ganuda/services/power_monitor/power_monitor.py` — DONE (grindstone surge)
9. `/ganuda/daemons/sanctuary_state.py` — DONE (grindstone surge)
10. `/ganuda/daemons/tpm_autonomic.py` — DONE (grindstone surge)
11. `/ganuda/daemons/tpm_autonomic_v2.py` — DONE (grindstone surge)
12. `/ganuda/daemons/shadow_council_sync.py` — DONE (grindstone surge)
13. `/ganuda/daemons/dependency_checker.py` — DONE (grindstone surge)

## Files Migrated (TPM grindstone surge, Mar 10)

14. `/ganuda/scripts/deer_jewel_digest.py` — deer-signals channel — DONE
15. `/ganuda/scripts/council_telegram_async.py` — council-votes channel — DONE
16. `/ganuda/scripts/safety/canary_probe.py` — longhouse channel — DONE
17. `/ganuda/services/research_worker.py` — jr-tasks channel — DONE
18. `/ganuda/email_daemon/telegram_alerts.py` — deer-signals channel — DONE
19. `/ganuda/email_daemon/job_email_daemon_v2.py` — deer-signals channel — DONE
20. `/ganuda/services/ulisi/observer.py` — longhouse channel — DONE
21. `/ganuda/services/ulisi/heartbeat.py` — fire-guard channel — DONE
22. `/ganuda/backend/telegram_integration.py` — N/A (bot handler, not alert sender) — SKIPPED

**ALL 21 ALERT FILES MIGRATED.** Telegram→Slack complete. Leaders Meeting #1 mandate fulfilled.

## Gotchas

- `SLACK_BOT_TOKEN` must be in the environment. Services need `EnvironmentFile=/ganuda/config/secrets.env` in their systemd unit.
- `PYTHONPATH` must include `/ganuda/lib` for the import to work.
- Some files use `urllib.request` instead of `requests` — the bridge uses `requests`.
- HTML parse_mode alerts may need formatting adjustment for Slack (Slack uses mrkdwn, not HTML).
- Test with `--dry-run` or `urgent=False` first to avoid flooding Slack during migration.
