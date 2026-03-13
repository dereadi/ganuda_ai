# [RECURSIVE] DC-16: Body Report Timer Deployment (retry) - Step 6

**Parent Task**: #1318
**Auto-decomposed**: 2026-03-12T20:03:04.270886
**Original Step Title**: Test the service manually (one-shot dry run)

---

### Step 6: Test the service manually (one-shot dry run)

```bash
sudo systemctl start body-report.service
journalctl -u body-report.service --since "1 minute ago" --no-pager
```

Expected output: log lines showing "Generating body report", the digest text, and
"Body report complete". If Slack post fails, that is acceptable (best-effort).

## Acceptance Criteria

1. `body-report.timer` appears in `systemctl list-timers` with next firing time.
2. `body-report.service` runs `/ganuda/scripts/body_report.py` as user dereadi.
3. Manual `systemctl start body-report.service` completes without error (exit 0).
4. Journal logs show the digest output from the manual run.
5. No modifications to `/ganuda/scripts/body_report.py`.
