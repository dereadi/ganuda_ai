# [RECURSIVE] Fire Guard Queue Depth Metric on Health Page - Step 2

**Parent Task**: #1132
**Auto-decomposed**: 2026-03-09T14:19:50.232985
**Original Step Title**: Add queue section to HTML render

---

### Step 2: Add queue section to HTML render

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
- Fire Guard health page shows pending count, in_progress count, last completion time
- DB failure shows "?" rather than crashing
- Queue section appears between Timer Health and the back link
