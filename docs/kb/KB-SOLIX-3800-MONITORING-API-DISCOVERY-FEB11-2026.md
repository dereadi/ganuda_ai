# KB: Anker Solix 3800 Plus Monitoring — API & Web Portal Discovery

**Date**: February 11, 2026
**Trigger**: Second power outage (Feb 10→11), zero automated alerting
**Related KB**: KB-POWER-FAILURE-RECOVERY-FEB07-2026
**Kanban**: #1763
**Council Vote**: PROCEED (confidence 0.875)

---

## Executive Summary

The Anker Solix 3800 Plus powering the Cherokee AI Federation has a **reverse-engineered Python API** and **Anker web portal** available for monitoring. This eliminates the need for a standalone smart plug as the primary monitoring method — we can read battery percentage, wattage, and solar input directly from the Solix.

---

## Monitoring Options (Ranked)

### Option 1: Anker Solix Professional Web Portal (Immediate)

**URL**: https://ankersolix-professional-us.anker.com/user/login

Sign in with the Anker account credentials used to set up the Solix 3800 Plus. Provides:
- Battery percentage
- Power consumption graphs
- Solar input (if panels connected)
- Historical usage data

**Limitation**: Visual monitoring only, no API access. Manual check, no automation.

### Option 2: anker-solix-api Python Library (Automated)

**Repository**: https://github.com/thomluther/anker-solix-api
**License**: MIT
**Maintained**: Active (2025-2026)
**Device Support**: A1790(P) F3800(P) explicitly listed

**What it provides**:
- Battery percentage (direct reading)
- Wattage in/out
- Solar input
- AC output
- Device control (shutdown, schedule)
- MQTT real-time monitoring

**Critical Requirements**:
1. **MQTT required** for real-time power station data — the REST cloud API does NOT provide real-time power values for standalone devices not configured into a Power System
2. Python 3.12+ (we have 3.12 on redfin)
3. Auth: Anker account email + password + country code ("US")
4. Dependencies: cryptography, aiohttp, aiofiles, paho-mqtt

**Rate Limiting**: Anker cloud API limited to 10-12 requests/minute

### Option 3: Home Assistant Integration (Infrastructure)

**Repository**: https://github.com/thomluther/ha-anker-solix
**Requires**: Home Assistant instance (not currently deployed)
**Benefit**: Would integrate with other smart home automation
**Status**: Not recommended as primary — we don't run HA. But good fallback if we ever deploy it.

### Option 4: Smart Plug on AC Output (Hardware Backup)

**Original approach** from Jr instruction JR-SOLIX-UPS-MONITORING-DAEMON-FEB11-2026.
**Still valid as backup**: TP-Link Kasa KP115 (~$20) on the Solix AC output monitors wattage.
**Advantage**: Works without internet, no Anker API dependency.
**Limitation**: Only sees output wattage, not battery percentage.

---

## Revised Architecture

### Primary: anker-solix-api via MQTT

```
Solix 3800 → WiFi → Anker Cloud → MQTT → power_monitor.py → Telegram alerts
                                                          → Graceful shutdown orchestrator
```

The power_monitor.py daemon (already built at `/ganuda/services/power_monitor/power_monitor.py` by Jr #694) needs to be enhanced to:
1. Add MQTT reader using `anker-solix-api` library
2. Read battery percentage directly (not just wattage)
3. Use battery % for shutdown decisions (more accurate than wattage inference)

### Backup: Smart Plug (No Internet Dependency)

```
Solix 3800 → AC Output → Smart Plug → Local WiFi API → power_monitor.py
```

Falls back to smart plug if Anker cloud is unreachable (e.g., during internet outage, which is a realistic scenario during power events).

### Alert Thresholds (Revised for Battery %)

| Battery % | Alert Level | Action |
|-----------|-------------|--------|
| >50% | HEALTHY | Normal operation |
| 30-50% | WARNING | Telegram alert to TPM |
| 15-30% | ALERT | Prepare graceful shutdown |
| <15% | CRITICAL | Execute graceful shutdown |
| 0% | DEAD | Nodes should already be off |

**Note**: With 3800Wh capacity and ~1800W cluster draw:
- 100% → 0% = ~2.1 hours
- Per 10% = ~12.7 minutes
- WARNING at 50% gives ~63 minutes of warning

---

## Next Steps

1. **Immediate**: Sign into Anker Solix Professional portal to verify account access and view current battery status
2. **Jr Task**: Update power_monitor.py to use anker-solix-api MQTT for real-time battery monitoring
3. **Hardware**: Still order smart plug as backup (no internet dependency)
4. **Integration**: Connect alerts to existing Telegram bot infrastructure

---

## Sources

- Python API library: https://github.com/thomluther/anker-solix-api
- Home Assistant integration: https://github.com/thomluther/ha-anker-solix
- Anker Solix Professional (US): https://ankersolix-professional-us.anker.com/user/login
- Anker community API discussion: https://community.anker.com/t/consumable-open-api/98099

---

*For Seven Generations — the rabbit who only looks for the hawk above misses the snake below. But the council sees both directions.*
