# [RECURSIVE] DC-16: Body Report Timer Deployment (retry) - Step 3

**Parent Task**: #1318
**Auto-decomposed**: 2026-03-12T20:03:04.267915
**Original Step Title**: Copy unit files to systemd directory

---

### Step 3: Copy unit files to systemd directory

```bash
sudo cp /ganuda/scripts/body-report.service /etc/systemd/system/body-report.service
sudo cp /ganuda/scripts/body-report.timer /etc/systemd/system/body-report.timer
```
