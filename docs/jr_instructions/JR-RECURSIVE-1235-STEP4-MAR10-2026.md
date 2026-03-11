# [RECURSIVE] DC-16: 6-Hour Body Report Digest Timer - Step 4

**Parent Task**: #1235
**Auto-decomposed**: 2026-03-10T11:25:31.241346
**Original Step Title**: Deploy and enable (run on redfin)

---

### Step 4: Deploy and enable (run on redfin)

```bash
sudo cp /ganuda/scripts/body-report.service /etc/systemd/system/
sudo cp /ganuda/scripts/body-report.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now body-report.timer
```
