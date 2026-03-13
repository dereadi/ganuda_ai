# [RECURSIVE] DC-16: Body Report Timer Deployment (retry) - Step 4

**Parent Task**: #1318
**Auto-decomposed**: 2026-03-12T20:03:04.268552
**Original Step Title**: Reload systemd and enable the timer

---

### Step 4: Reload systemd and enable the timer

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now body-report.timer
```
