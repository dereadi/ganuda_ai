# [RECURSIVE] DC-16: Body Report Timer Deployment (retry) - Step 2

**Parent Task**: #1318
**Auto-decomposed**: 2026-03-12T20:03:04.267003
**Original Step Title**: Create the systemd timer unit file

---

### Step 2: Create the systemd timer unit file

**File:** `/ganuda/scripts/body-report.timer`

```ini
[Unit]
Description=DC-16 Body Report Timer — every 6 hours

[Timer]
OnCalendar=*-*-* 00,06,12,18:15:00
Persistent=true

[Install]
WantedBy=timers.target
```
