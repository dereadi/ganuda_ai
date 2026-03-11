# [RECURSIVE] Fire Guard Wire L3 Productivity Checks - Step 2

**Parent Task**: #1139
**Auto-decomposed**: 2026-03-09T14:17:52.652764
**Original Step Title**: Add Jr Work Queue card to health page HTML

---

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
