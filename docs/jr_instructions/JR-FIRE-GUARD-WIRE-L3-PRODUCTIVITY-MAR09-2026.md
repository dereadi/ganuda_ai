# Jr Instruction: Wire Fire Guard L3 Productivity Checks into run_checks

## Context
Fire Guard has `check_stale_tasks()` and `reset_zombie_tasks()` functions (added Mar 8) but they are NOT called from `run_checks()`. The functions exist as dead code. This is the exact gap identified in ULTRATHINK-FIRE-GUARD-PRODUCTIVITY-GAP-MAR08-2026.md — the sensor was built but never plugged in. DC-13 (Observation Levels) requires L3 Productivity checks to be active, not just defined.

## Task
Wire `check_stale_tasks()` and `reset_zombie_tasks()` into `run_checks()`, and add the Jr Work Queue card to the health page HTML.

## File: `/ganuda/scripts/fire_guard.py`

### Step 1: Wire stale task detection and zombie reset into run_checks

Inside `run_checks()`, after the queue depth metrics block and before `results["alerts"] = alerts`:

```
<<<<<<< SEARCH
    results["queue"] = queue_metrics

    results["alerts"] = alerts
    results["healthy"] = len(alerts) == 0
    return results
=======
    results["queue"] = queue_metrics

    # Stale task detection (L3 productivity check — DC-13)
    stale_alerts = check_stale_tasks()
    for sa in stale_alerts:
        alerts.append(sa)

    # Zombie task auto-reset (self-healing reflex)
    reset_tasks = reset_zombie_tasks()
    if reset_tasks:
        alerts.append(f"ZOMBIE RESET: {len(reset_tasks)} task(s) auto-reset to pending after {ZOMBIE_THRESHOLD_HOURS}h stall")
    results["zombie_resets"] = [t[1] for t in reset_tasks]

    results["alerts"] = alerts
    results["healthy"] = len(alerts) == 0
    return results
>>>>>>> REPLACE
```

### Step 2: Add Jr Work Queue card to health page HTML

In `render_html`, after the Timer Health card div and before the back link div:

```
<<<<<<< SEARCH
<div style="text-align:center; margin-top:16px; font-size:0.7em; color:#444;">
=======
<div class="card">
  <h2>Jr Work Queue</h2>
  <div class="svc">Pending: {results.get('queue', {}).get('pending', '?')}</div>
  <div class="svc">In Progress: {results.get('queue', {}).get('in_progress', '?')}</div>
  <div class="svc">Last Completed: {results.get('queue', {}).get('last_completed', '?')}</div>
</div>

<div style="text-align:center; margin-top:16px; font-size:0.7em; color:#444;">
>>>>>>> REPLACE
```

## Acceptance Criteria
- `check_stale_tasks()` is called every Fire Guard cycle (2 min)
- `reset_zombie_tasks()` is called every cycle — resets tasks in_progress > 6h
- Zombie resets generate alerts visible on health page
- Jr Work Queue card shows pending, in_progress, last completed on health page
- DB failure does NOT crash Fire Guard (existing silent catch pattern)
- No changes to the function implementations — only wiring

## IMPORTANT
- Do NOT modify `check_stale_tasks()` or `reset_zombie_tasks()` — they are correct as written
- Only add the CALLS to these functions inside `run_checks()` and the HTML card to `render_html()`
- This completes kanban #2031, #2032, #2033 wiring
