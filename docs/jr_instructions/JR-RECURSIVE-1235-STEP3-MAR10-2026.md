# [RECURSIVE] DC-16: 6-Hour Body Report Digest Timer - Step 3

**Parent Task**: #1235
**Auto-decomposed**: 2026-03-10T11:25:31.239987
**Original Step Title**: Create systemd timer unit

---

### Step 3: Create systemd timer unit

Create new file: `/ganuda/scripts/body-report.timer`

```ini
[Unit]
Description=DC-16 Body Report Timer — every 6 hours

[Timer]
OnCalendar=*-*-* 00,06,12,18:15:00
Persistent=true

[Install]
WantedBy=timers.target
```
