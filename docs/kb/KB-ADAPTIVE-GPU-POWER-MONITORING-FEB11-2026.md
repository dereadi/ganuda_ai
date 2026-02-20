# KB: Adaptive GPU Power Monitoring Architecture

**Date**: February 11, 2026
**Council Vote**: #ba677ef5213772b7 — REVIEW REQUIRED (0.844 confidence)
**Kanban**: #1763 (Solix) + GPU monitoring extension
**Jr Task**: #704 (Adaptive GPU Power Monitor Daemon)

## Decision

Replaced fixed 60-second polling with adaptive two-mode architecture per Council consensus.

## Architecture

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Idle interval | 300s (5 min) | All 7 specialists agreed |
| Active interval | 15s | Compromise: Gecko/Raven 10s, Turtle 15s, Spider 30s |
| Util threshold | 40% GPU | Compromise: Raven 30%, Spider/Eagle Eye 50% |
| Power delta trigger | 20% from baseline | Eagle Eye recommendation |
| Cooldown to idle | 3 consecutive readings | Spider recommendation |
| Overhead budget | <1% CPU | All 7 specialists agreed |
| CPU monitoring | Yes, idle interval only | 5/7 requested, Turtle: don't add load in active mode |
| DB connection | Persistent, single conn | Spider: avoid connection churn |
| Mode transition logging | Required | Crawdad: security audit trail |

## Mode Behavior

**IDLE (300s)**: Records power draw per GPU + cluster total + CPU stats. Minimal DB writes (5 records per cycle).

**ACTIVE (15s)**: Records power draw + temperature + utilization per GPU + cluster total. More DB writes but captures load transients.

**Transitions**: Logged as `power_monitor_mode_change` events in unified_timeline with trigger reason and GPU readings at transition point.

## Key Files

- `/ganuda/scripts/gpu_power_monitor.py` — Main daemon (adaptive)
- `/ganuda/scripts/systemd/gpu-power-monitor.service` — Type=simple with Restart=on-failure
- `/ganuda/scripts/systemd/gpu-power-monitor.timer` — DEPRECATED (daemon self-schedules)

## Deployment

```text
# On redfin as sudo:
sudo cp /ganuda/scripts/systemd/gpu-power-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-power-monitor
# Verify:
journalctl -u gpu-power-monitor -f
```

## Monitoring Queries

```sql
-- Recent power readings
SELECT event_type, source, value, metadata->>'monitoring_mode' as mode,
       timestamp FROM unified_timeline
WHERE source LIKE 'gpu_%' ORDER BY timestamp DESC LIMIT 20;

-- Mode transitions
SELECT metadata->>'old_mode', metadata->>'new_mode',
       metadata->>'trigger', timestamp
FROM unified_timeline WHERE event_type = 'power_monitor_mode_change'
ORDER BY timestamp DESC;

-- Hourly power aggregation (Eagle Eye: avoid data saturation)
SELECT date_trunc('hour', timestamp) as hour,
       avg(value) as avg_watts, max(value) as peak_watts
FROM unified_timeline WHERE event_type = 'cluster_gpu_power_total'
AND timestamp > NOW() - interval '24 hours'
GROUP BY 1 ORDER BY 1;
```

## Council Concerns Matrix

| Specialist | Concern | Resolution |
|------------|---------|------------|
| Gecko | Performance overhead | 300s idle, persistent DB conn, <1% budget |
| Raven | Strategy alignment | Adaptive intervals match federation capacity planning |
| Spider | Integration stability | 10MB memory ceiling, no connection churn |
| Turtle | Seven Generations | Monitor must not increase energy consumption |
| Crawdad | Security | All transitions logged, no dynamic config endpoint |
| Eagle Eye | Visibility | Idle-mode aggregation prevents timeline saturation |
| Peace Chief | Consensus | All 6 concerns addressed in implementation |

## Related

- KB-SOLIX-3800-MONITORING-API-DISCOVERY-FEB11-2026.md (UPS/battery side)
- KB-II-RESEARCHER-GPU-RUNAWAY-ROOT-CAUSE-FEB11-2026.md (why monitoring matters)
- Thermal #82859 (Nate Hagens compute crisis — energy awareness)
