# JR Instruction: Grafana Monitoring Fix
## Task ID: MONITOR-FIX-001
## Priority: P3
## Estimated Complexity: Low

---

## Objective

Fix the Grafana DOWN monitoring alert that incorrectly reports Grafana as down. The alert checks bluefin but Grafana actually runs on redfin.

---

## Current Issue

```
Alert: Grafana (redfin) on bluefin DOWN
Expected: Grafana UP on 192.168.132.220:3000
```

**Root Cause**: Monitoring configuration checks the wrong host.

---

## Verification

```bash
# Grafana is actually UP on redfin
curl -s -o /dev/null -w "%{http_code}" http://192.168.132.220:3000/
# Returns: 200

# Check what's on bluefin:3000
curl -s -o /dev/null -w "%{http_code}" http://192.168.132.222:3000/
# Returns: Connection refused (nothing on this port)
```

---

## Solution

### Step 1: Locate Monitoring Configuration

Check these common locations:
```bash
# Prometheus targets
grep -r "grafana" /etc/prometheus/
grep -r "3000" /etc/prometheus/targets.d/

# Healthcheck scripts
grep -r "grafana" /ganuda/scripts/
grep -r "grafana" /etc/cron.d/

# Systemd services
grep -r "grafana" /etc/systemd/system/
```

### Step 2: Update Target Host

Change monitoring target from:
- `bluefin:3000` or `192.168.132.222:3000`

To:
- `redfin:3000` or `192.168.132.220:3000`

### Step 3: Verify Alert Resolution

After fix, confirm:
```bash
# Alert should show UP
curl -s http://192.168.132.220:3000/api/health
# Expected: {"commit":"...","database":"ok","version":"..."}
```

---

## Infrastructure Reference

| Service | Host | Port |
|---------|------|------|
| Grafana | redfin (192.168.132.220) | 3000 |
| Prometheus | redfin (192.168.132.220) | 9090 |
| vLLM | redfin (192.168.132.220) | 8000 |
| PostgreSQL | bluefin (192.168.132.222) | 5432 |
| VetAssist API | bluefin (192.168.132.222) | 8001 |

---

## Acceptance Criteria

1. Grafana monitoring alert shows UP status
2. No false positive DOWN alerts
3. Alert actually detects when Grafana is truly down

---

## Files to Check/Modify

- `/etc/prometheus/prometheus.yml`
- `/etc/prometheus/targets.d/*.yml`
- `/ganuda/scripts/health_check*.sh`
- Any cron jobs doing HTTP checks

---

*Cherokee AI Federation - For Seven Generations*
