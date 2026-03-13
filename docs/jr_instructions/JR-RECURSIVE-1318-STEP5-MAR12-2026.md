# [RECURSIVE] DC-16: Body Report Timer Deployment (retry) - Step 5

**Parent Task**: #1318
**Auto-decomposed**: 2026-03-12T20:03:04.269518
**Original Step Title**: Verify timer is active and scheduled

---

### Step 5: Verify timer is active and scheduled

```bash
systemctl list-timers body-report.timer --no-pager
systemctl status body-report.timer --no-pager
```

Expected output: timer shows next firing at :15 past the next 6-hour mark.
