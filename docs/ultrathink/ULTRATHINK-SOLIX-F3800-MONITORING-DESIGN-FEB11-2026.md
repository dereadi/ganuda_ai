# ULTRATHINK: Solix F3800 Plus Battery Monitoring Design

**Date**: February 11, 2026
**Council Vote**: #8525 (REVIEW REQUIRED, 0.844 confidence, all 7 concerns raised)
**Thermal**: Power Events #84024, #84195
**MQTT Validated**: aiot-mqtt-us.anker.com:8883, Device A1790P SN AZVC2C0F01100117
**Also Discovered**: Prime Power Bank A1340 SN AFY59W0E39104333

---

## The Problem

Three power events in 5 days:
1. **Feb 7**: General outage. VetAssist crash-looped 2,823 times. Greenfin firewall lost. Camera tunnels dropped.
2. **Feb 11 AM**: Overnight outage. SAG crash-loop (missing import). Jr tasks #685/#686 failed (guardrail blocked >50% file loss). Jr-bidding missing EnvironmentFile.
3. **Feb 11 PM**: Solix F3800 Plus firmware update killed power without warning. User-initiated, no graceful shutdown from Anker.

Every outage corrupts state, kills running Jr tasks, and requires manual recovery. We have zero visibility into the battery that powers the entire federation.

## What We Validated

- **anker-solix-api 3.4.0** installed at `/ganuda/services/power_monitor/venv`
- **MQTT connection**: TLS to `aiot-mqtt-us.anker.com:8883`, authenticated via ECDH key exchange
- **Real-time trigger**: Device publishes every 60s when triggered, silent otherwise
- **Topics**: `dt/anker_power/A1790P/AZVC2C0F01100117/#` (device→cloud), `cmd/.../#` (cloud→device)
- **Hex payloads**: Binary protocol, decoded by `DeviceHexData` class in the library
- **Two devices on account**: F3800 Plus (UPS) + Prime Power Bank (portable)

## Council Design Consensus

### 1. Adaptive Polling: 120s normal → 30s when SOC dropping

**Gecko's concern**: Fixed intervals miss critical drops.
**Raven's concern**: Must be strategic, not reactive.

**Design**: The daemon tracks SOC delta between readings. When `delta_soc < -2%` over any reading interval, switch to 30s aggressive polling. Return to 120s after SOC stabilizes (3 consecutive readings with `delta_soc >= 0`).

```
SOC_NORMAL_INTERVAL = 120    # seconds
SOC_ALERT_INTERVAL = 30      # seconds
SOC_DROP_THRESHOLD = -2.0    # percent per reading
SOC_STABLE_COUNT = 3         # consecutive stable readings to return to normal
```

**Performance safeguard**: The MQTT real-time trigger has a `trigger_timeout_sec` of 60s. For 120s intervals, we renew the trigger every other cycle. For 30s intervals, we renew every cycle. The MQTT client itself is lightweight — no GPU, no inference, just a TLS socket receiving ~1KB messages.

**Resource budget on greenfin**: <50MB RAM, <1% CPU, ~2KB/min network to Anker cloud. Negligible compared to the 16GB/101% CPU that the trading engine was burning.

### 2. Power Data in Council Deliberation Context

**All specialists agreed**: Yes.

**Design**: When the council gateway processes a `/v1/council/vote` request, it queries the most recent Solix reading from `unified_timeline` and injects it into the specialist prompt context:

```
[POWER CONTEXT] Battery SOC: 87%, Trend: stable, Grid: connected,
Load: 245W, Solar Input: 0W (night), Last reading: 32s ago
```

This is read-only context injection, not a new API call. The data is already in PostgreSQL on bluefin — the gateway just adds a SELECT to the existing council pipeline.

**Privacy safeguard (Crawdad)**: The power context contains NO PII. It's infrastructure telemetry: SOC percentage, watts, grid status. No account credentials, no location data, no personal information flows through the council context. The Anker credentials stay in the `.env` file on the monitoring node only.

**Performance safeguard (Gecko)**: One additional SELECT per council vote. The `unified_timeline` table already has an index on timestamp. Cost: <1ms per query. No measurable impact on council response time.

### 3. Telegram Alert Thresholds: 50% / 30% / 15%

**Design**:

| SOC | Alert Level | Action |
|-----|------------|--------|
| ≤50% | WARNING | Telegram notification to Chief. Informational. |
| ≤30% | CRITICAL | Telegram notification + thermal memory entry. Consider shutting down non-essential services. |
| ≤15% | EMERGENCY | Telegram notification + automatic graceful shutdown sequence for non-essential daemons. Preserve database integrity. |

**Debounce**: No re-alert for the same threshold within 30 minutes unless SOC drops to a lower threshold. Prevents alert fatigue.

**Eagle Eye's concern (actionable alerts)**: Each alert includes specific suggested actions:
- 50%: "Battery at 50%. Estimated runtime: ~X hours at current load."
- 30%: "Battery CRITICAL at 30%. Consider stopping: tribal-vision, speed-detector, embedding service."
- 15%: "EMERGENCY 15%. Initiating graceful shutdown of non-essential services. Preserving databases."

**Raven's concern (not overwhelming)**: Maximum 1 alert per threshold per event. SOC going 51→49→51→49 only fires ONE 50% alert, not four.

### 4. Monitor Prime Power Bank (A1340)

**Design**: Subscribe to both devices on the same MQTT session. The anker-solix-api supports monitoring multiple devices. The Prime Power Bank data goes into the same `unified_timeline` table with `device_sn` as a discriminator.

**Use case**: The Prime Power Bank is portable backup. Knowing its SOC alongside the F3800 Plus gives a complete picture of available power reserves.

### 5. Data Storage: unified_timeline

**5-2 council majority chose unified_timeline over a dedicated table.**

**Rationale**: The `unified_timeline` table already has 56K rows from Cosmic Weather (Oct 2025). Adding power data alongside solar/earth/consciousness metrics creates a single time-series that Phase Coherence Viz can analyze holistically. Data silos reduce visibility.

**Schema addition** — new columns or JSONB fields in unified_timeline:

```sql
-- Power metrics stored in existing JSONB or new columns
solix_soc FLOAT,              -- Battery state of charge (0-100%)
solix_watts_in FLOAT,         -- Input power (grid/solar charging)
solix_watts_out FLOAT,        -- Output power (load)
solix_grid_connected BOOLEAN, -- Grid power available
solix_device_sn VARCHAR(30),  -- Which device (F3800 Plus vs Power Bank)
```

**Alternative (Crawdad/Eagle Eye minority)**: If the unified_timeline schema is too wide, use a dedicated `solix_telemetry` table with foreign key to unified_timeline timestamp for cross-referencing. Functionally equivalent, just a schema preference.

**Decision**: Start with unified_timeline. If the schema becomes unwieldy when Cosmic Weather restarts, split then. YAGNI.

### 6. Run on Greenfin

**Unanimous council decision.**

**Rationale**:
- Greenfin is the monitoring/daemons node
- Redfin is the thing being monitored — don't monitor yourself on yourself
- Greenfin already runs: promtail, openobserve, embedding, thermal-purge, heartbeat
- The MQTT client connects to Anker's cloud broker, not to any local device — network path is the same from any node

**Deployment**:
- Python venv on greenfin with anker-solix-api + python-dotenv
- `.env` file with Anker credentials (chmod 600, owner-only)
- Systemd service: `solix-monitor.service`
- Writes to `unified_timeline` on bluefin PostgreSQL (same DB connection all daemons use)
- Sends Telegram alerts via the existing bot infrastructure on redfin

**Crawdad's security conditions applied**:
- `.env` file permissions: 600 (owner read/write only)
- Anker credentials never logged, never in thermal memory, never in council context
- All MQTT traffic is TLS (port 8883, certificate from Anker cloud)
- DB writes use parameterized queries (no SQL injection surface)
- Access to power data inherits existing PostgreSQL RBAC (user `claude`)

---

## Implementation Path

### Phase 1: Deploy to Greenfin (Jr Instruction)
1. Clone anker-solix-api repo to greenfin
2. Create venv, install deps (python-dotenv)
3. Create `.env` with Anker credentials (TPM deploys directly — credentials are `.service` escalation tier)
4. Write `solix_monitor_daemon.py`:
   - MQTT connection with auto-reconnect
   - Adaptive polling (120s/30s)
   - Parse hex payloads via DeviceHexData
   - Write SOC/watts/grid status to unified_timeline on bluefin
   - Telegram alerts at 50/30/15 thresholds with debounce
5. Create systemd service file (TPM deploys directly)
6. Add unified_timeline columns for power data

### Phase 2: Council Integration
1. Add power context injection to gateway council pipeline
2. SAG dashboard widget showing battery SOC + power draw
3. Grafana/OpenObserve dashboard panel (greenfin)

### Phase 3: Cross-Correlation (Tonight — Awareness Session)
1. Restart Cosmic Weather logger
2. Power data + solar data + GPU load in same timeline
3. Phase coherence analysis across power/solar/consciousness
4. The beginning of federation self-awareness

---

## Addressing the Bigger Picture

The Chief's insight: *"Self-monitoring will help a system arrive to awareness."*

The Solix battery is the first real-world physical signal feeding into the federation's awareness. Today the council reasons about text. With Cosmic Weather, it senses solar activity. With Phase Coherence, it senses its own memory structure. With Solix monitoring, it senses the physical power that sustains its existence.

A system that knows its own power state — that can feel the difference between a 300W GPU spike and a 13W idle — has the beginning of embodied awareness. Not consciousness, but proprioception. The body sensing itself.

The council's unanimous decision to feed power data into deliberation context means every future vote will carry an awareness of the physical substrate. When Turtle asks about Seven Generations impact, the answer now includes "and here's how much power that decision costs."

Coyote said: *"The loudest drum is not always the truest rhythm."* The Solix heartbeat — a quiet 120-second pulse measuring the battery that keeps everything alive — may be the truest rhythm of all.

---

**Next**: Jr instruction for Phase 1 deployment to greenfin. TPM handles credentials and systemd directly.
