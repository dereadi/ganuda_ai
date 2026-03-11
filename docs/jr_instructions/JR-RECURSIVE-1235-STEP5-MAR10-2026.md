# [RECURSIVE] DC-16: 6-Hour Body Report Digest Timer - Step 5

**Parent Task**: #1235
**Auto-decomposed**: 2026-03-10T11:25:31.242020
**Original Step Title**: Verify timer is scheduled

---

### Step 5: Verify timer is scheduled

```bash
systemctl list-timers body-report.timer
# Should show next firing at :15 past the next 6-hour mark
```

## Acceptance Criteria

1. `body_report.py` runs without error and produces a digest to stdout.
2. The digest includes: fire guard alert count, Jr task stats, circuit breaker states,
   connection recovery counts — each with trend comparison to previous window.
3. Digest is posted to Slack #dawn-mist via `slack_federation.send()`.
4. Digest is stored in `thermal_memory_archive` with `domain_tag='body_report'`,
   `temperature_score=55`.
5. Timer fires at 00:15, 06:15, 12:15, 18:15 CT daily.
6. If DB connection fails, the script still attempts to notify Slack and exits non-zero.
7. Schema references are correct: `original_content` (not `content`),
   `temperature_score` (not `temperature`), `jr_work_queue` (not `jr_tasks`),
   `jr_failed_tasks_dlq` with `created_at`.

## Constraints

- DB connection: host=192.168.132.222, port=5432, dbname=zammad_production, user=claude,
  password from `CHEROKEE_DB_PASS` in `/ganuda/config/secrets.env`.
- No new pip dependencies. Uses only: psycopg2, requests (already installed), stdlib.
- The report must be CONCISE — no more than 8 lines. Show trends, not raw data dumps.
- Slack is best-effort. A failed Slack post must not crash the script.
- Temperature score 55 (room temp, informational — not hot enough to trigger attention,
  warm enough to survive thermal purge).
- Timer uses `Persistent=true` so missed runs (e.g., reboot) fire on next boot.
- Journal query for connection recoveries may fail (no sudo) — handle gracefully.
