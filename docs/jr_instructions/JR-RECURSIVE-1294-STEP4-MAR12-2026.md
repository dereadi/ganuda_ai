# [RECURSIVE] Greenfin Sentinel — Sub-Claude Watchdog on Critical Infrastructure Node - Step 4

**Parent Task**: #1294
**Auto-decomposed**: 2026-03-12T17:57:59.078110
**Original Step Title**: Verify the sentinel is running

---

### Step 4: Verify the sentinel is running

```bash
systemctl status greenfin-sentinel && journalctl -u greenfin-sentinel --no-pager -n 20
```

---
