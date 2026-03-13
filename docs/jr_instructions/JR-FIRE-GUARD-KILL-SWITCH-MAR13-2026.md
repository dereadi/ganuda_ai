# JR-FIRE-GUARD-KILL-SWITCH-MAR13-2026

## Task: Fire Guard Emergency Brake — Kill Switch

**Priority**: 1 (Critical)
**Source**: Longhouse c4e68ce0fcea60a3 (consensus with standing dissent), Foundation Agents GAP 7
**Kanban**: FA-GAP7-001
**Design Constraints**: DC-10 (Reflex Principle), DC-7 (Noyawisgi)

## Context

The Foundation Agents paper (arxiv 2504.01990) identifies kill switches as a field-wide gap. Fire Guard currently monitors health but cannot halt runaway processes. Crawdad's security assessment: "non-negotiable — ship this week."

## What to Build

### Multi-Factor Emergency Brake

Fire Guard (`/ganuda/scripts/fire_guard.py`) needs three independent brake triggers:

#### Trigger 1: Automatic Threshold
```python
EMERGENCY_THRESHOLDS = {
    "jr_failure_rate_1h": 0.5,        # >50% Jr failures in last hour
    "thermal_write_rate_1m": 100,      # >100 thermals/minute (runaway)
    "cpu_percent": 95,                 # sustained >95% CPU
    "disk_percent": 95,                # >95% disk
    "council_confidence_avg_24h": 0.15, # avg confidence below 0.15
    "postgres_connections": 90,         # >90 active connections
}
```

When ANY threshold is exceeded:
1. Set `EMERGENCY_BRAKE = True` in a shared state file (`/ganuda/state/emergency_brake.json`)
2. The Jr executor checks this file before starting any new task
3. Running Jr tasks are allowed to complete (graceful, not hard kill)
4. Alert Partner via Slack #fire-guard channel + Telegram fallback

#### Trigger 2: Manual Partner Override
```python
# Partner can trigger from any node:
# python3 /ganuda/scripts/fire_guard.py --brake on
# python3 /ganuda/scripts/fire_guard.py --brake off
# python3 /ganuda/scripts/fire_guard.py --brake status
```

CLI interface. No web UI needed. Simple, fast, works over SSH.

#### Trigger 3: Coyote Anomaly Circuit Breaker
If Fire Guard detects 3+ consecutive anomalies across different subsystems within 5 minutes, engage brake automatically. This is the "something is wrong but I can't name it" pattern — multiple small signals = one big signal.

### State File Format
```json
{
    "brake_engaged": false,
    "engaged_at": null,
    "engaged_by": null,
    "reason": null,
    "auto_disengage_at": null,
    "history": []
}
```

### Auto-Disengage
Automatic brakes disengage after 30 minutes IF the triggering condition has resolved. Manual brakes require manual release. This prevents the organism from staying frozen if Partner is asleep.

## Files to Modify
- `/ganuda/scripts/fire_guard.py` — add threshold checks, brake engagement logic, CLI --brake flag
- `/ganuda/state/emergency_brake.json` — NEW, shared state file (create /ganuda/state/ dir)

## Files to Check (read-only, for integration)
- `/ganuda/jr_executor/jr_task_executor.py` — must check brake state before task start
- `/ganuda/lib/slack_federation.py` — for alert routing

## Acceptance Criteria
1. `fire_guard.py --brake on` engages brake, `--brake off` releases, `--brake status` reports
2. Automatic threshold trigger engages brake and sends Slack alert
3. Jr executor refuses new tasks when brake is engaged
4. Auto-disengage after 30 min if condition resolved
5. All brake events logged to `/ganuda/state/emergency_brake.json` history array
6. Brake state survives Fire Guard restarts (file-based, not in-memory)

## What NOT to Do
- Do NOT hard-kill running processes. Graceful only.
- Do NOT require database access for brake state. File-based so it works even if postgres is down.
- Do NOT add web UI. CLI only for Phase 1.
