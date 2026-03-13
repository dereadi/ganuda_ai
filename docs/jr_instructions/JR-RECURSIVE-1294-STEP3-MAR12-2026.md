# [RECURSIVE] Greenfin Sentinel — Sub-Claude Watchdog on Critical Infrastructure Node - Step 3

**Parent Task**: #1294
**Auto-decomposed**: 2026-03-12T17:57:59.077139
**Original Step Title**: Deploy the systemd unit to greenfin and start the service

---

### Step 3: Deploy the systemd unit to greenfin and start the service

Run on greenfin (SSH via 192.168.132.224 or WireGuard 10.100.0.3):

```bash
sudo cp /ganuda/services/greenfin-sentinel.service /etc/systemd/system/greenfin-sentinel.service && sudo systemctl daemon-reload && sudo systemctl enable --now greenfin-sentinel
```

---
