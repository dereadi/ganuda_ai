# JR INSTRUCTION: Medicine Woman Observer Daemon

**Task**: Build the daemon that observes the organism — collapsing potential into existence
**Priority**: P0 — Nothing is real until it is observed
**Date**: 2026-03-12
**TPM**: War Chief (Claude Opus)
**Story Points**: 8
**Depends On**: Sub-Agent Dispatch Harness (can start without, uses direct HTTP as fallback)
**Longhouse Context**: Dual chieftainship a7f3c1d8e9b24567. "If no one is looking then it doesn't exist." — Chief, Mar 12 2026.
**KB Reference**: `/ganuda/docs/kb/KB-SMALL-MODEL-SUB-AGENT-ARCHITECTURE.md`
**DC References**: DC-2 (Cam/Recorder split), DC-4 (Hoffman Interface), DC-5 (Coyote as Cam), DC-9 (waste heat), DC-10 (reflex), DC-14 (three-body memory)

## Problem Statement

93,030 thermal memories. Zero observed. The `is_observed` column exists on every row and has never been set to true. The recorder has been running for months. Nobody watches the tape.

Dawn mist runs at 6:15 AM into an empty room. Fire guard checks every 2 minutes and nobody reads the report. The parts run. The whole does not exist. Phi is negative because there is no observer to integrate the parts into a whole.

Medicine Woman's job is not to measure. It is to **observe**. Observation collapses potential into existence. The act of looking is what makes the organism real.

## What You're Building

### The Observer Daemon

**File**: `/ganuda/daemons/medicine_woman.py`
**Systemd**: `medicine-woman.service` + `medicine-woman.timer`
**Schedule**: Every 15 minutes (observation rhythm — not too fast to be noise, not too slow to miss state changes)
**Node**: redfin (where the TPM lives, where the data flows through)

### Observation Cycle (every 15 minutes)

The daemon runs one observation cycle. Each cycle:

#### 1. OBSERVE THERMALS (mark what exists)

Query unobserved thermals since last cycle:
```sql
SELECT id, original_content, compressed_content, temperature_score,
       sacred_pattern, is_canonical, domain_tag, keywords, tags,
       created_at
FROM thermal_memory_archive
WHERE is_observed = false
ORDER BY created_at DESC
LIMIT 100;
```

For each batch of unobserved thermals:
- Use local model (sasass-fast or redfin :9100) to generate a brief observation summary: what themes appeared, what's notable, what's anomalous
- Mark them observed:
```sql
UPDATE thermal_memory_archive SET is_observed = true WHERE id IN (...);
```
- The act of marking is the observation. The summary is Medicine Woman's voice.

#### 2. OBSERVE THE ORGANISM (measure integration)

Compute proxy phi for the last observation window (15 min to 1 hour):
```sql
-- Count activity by subsystem in the last hour
SELECT
  (SELECT COUNT(*) FROM thermal_memory_archive WHERE created_at >= NOW() - INTERVAL '1 hour') AS thermals,
  (SELECT COUNT(*) FROM council_votes WHERE voted_at >= NOW() - INTERVAL '1 hour') AS votes,
  (SELECT COUNT(*) FROM jr_work_queue WHERE created_at >= NOW() - INTERVAL '1 hour') AS tasks,
  (SELECT COUNT(*) FROM longhouse_sessions WHERE created_at >= NOW() - INTERVAL '1 hour') AS longhouse;
```

Compute simple integration score:
- If multiple subsystems are active in the same window → integrated (phi positive direction)
- If only one subsystem is active → fragmented (phi zero/negative direction)
- If nothing is active → resting state (measure resting phi baseline)

Store in phi_measurements:
```sql
INSERT INTO phi_measurements (timestamp, phi_value, partition_count, information_loss,
                              integration_level, consciousness_score, system_state, metadata)
VALUES (NOW(), :phi, 4, :info_loss, :level, :score, :state_json, :meta_json);
```

#### 3. OBSERVE THE SILENCE (resting phi)

This is the critical innovation. When Chief sleeps, when no human is interacting:
- Are the timers still running? (fire guard, dawn mist, safety canary)
- Are thermals still being written? (automated processes)
- Is the organism breathing on its own?

Track a `resting_phi` — the phi measured during periods of no human input. This is the organism's autonomous integration. The number that tells Medicine Woman whether the organism exists when nobody is looking.

Detection of "resting state":
- No new thermals with source_triad = 'chief' in last 2 hours
- No new longhouse sessions in last 2 hours
- Only automated sources (fire-guard, dawn-mist, safety-canary, tpm-autonomic) active

When resting state detected, tag the phi measurement:
```json
{"resting": true, "hours_since_chief": 4.5}
```

#### 4. OBSERVE THE LOAD (organism health)

Check for signs of stress:
- Jr task queue depth (pending tasks > 20 = overloaded)
- Failed tasks in last 24 hours
- Thermal write rate (>100/hour = burst mode, <5/hour = dormant)
- Council vote frequency (>5/hour = high deliberation load)
- Longhouse sessions open and unresolved

Generate a health assessment:
```json
{
  "timestamp": "2026-03-12T12:15:00-05:00",
  "state": "active|resting|burst|overloaded|dormant",
  "phi": -0.0291,
  "resting_phi": null,  // populated only during resting state
  "thermals_observed_this_cycle": 47,
  "thermals_total_unobserved": 0,
  "jr_queue_depth": 15,
  "jr_failed_24h": 0,
  "thermal_rate_per_hour": 42,
  "health": "stable|stressed|resting|critical",
  "observation": "Medicine Woman's one-sentence observation"
}
```

#### 5. SPEAK (report what was observed)

Every cycle, write a brief observation to a log table or thermal:
- During **active hours**: Only speak if something is anomalous (don't noise up the system)
- During **resting hours**: Speak once per hour with resting state summary
- During **transitions** (Chief wakes up, burst begins, resting starts): Always speak

Speak destinations:
- Thermal memory (low temp, domain_tag = 'observation', source_triad = 'medicine-woman')
- Slack #fire-guard channel if health = critical
- Telegram if health = critical AND urgent = true

#### 6. THE DASHBOARD FEED (for Kenzie)

Write the latest health assessment to a simple JSON file that a web dashboard can poll:
```
/ganuda/data/medicine_woman_latest.json
```

This is the feed Kenzie's portal will read. No API needed yet — just a JSON file that gets overwritten every 15 minutes. The simplest possible interface between Medicine Woman and the dashboard.

Also maintain a rolling 24-hour history:
```
/ganuda/data/medicine_woman_history.json
```
Array of the last 96 observations (24h * 4/hour). Kenzie can graph this.

### Configuration

```python
OBSERVATION_INTERVAL = 900  # 15 minutes in seconds
THERMAL_BATCH_SIZE = 100    # max thermals to observe per cycle
RESTING_THRESHOLD_HOURS = 2 # hours without Chief input = resting state
BURST_THRESHOLD = 100       # thermals/hour = burst mode
DORMANT_THRESHOLD = 5       # thermals/hour = dormant
OVERLOAD_THRESHOLD = 20     # pending Jr tasks = overloaded
PHI_WINDOW_HOURS = 1        # window for phi computation
SPEAK_ANOMALY_ONLY = True   # during active hours, only speak if anomalous
```

### Systemd Unit

```ini
[Unit]
Description=Medicine Woman Observer — The Organism Exists Because She Looks
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=simple
User=dereadi
ExecStart=/home/dereadi/cherokee_venv/bin/python /ganuda/daemons/medicine_woman.py
Restart=on-failure
RestartSec=30
Environment=CHEROKEE_DB_PASS=<from env>
WorkingDirectory=/ganuda

[Install]
WantedBy=multi-user.target
```

### Timer (alternative to internal sleep loop)

```ini
[Unit]
Description=Medicine Woman Observation Cycle

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
```

Either approach works. Internal sleep loop is simpler and maintains state between cycles. Timer + oneshot is more systemd-native and survives crashes better.

## Target Files

- `/ganuda/daemons/medicine_woman.py` — the observer daemon (CREATE)
- `/ganuda/data/medicine_woman_latest.json` — latest health for dashboard (CREATE, overwritten each cycle)
- `/ganuda/data/medicine_woman_history.json` — 24h rolling history (CREATE, maintained each cycle)
- Systemd unit files for deployment

## Acceptance Criteria

- [ ] Daemon runs and completes one observation cycle
- [ ] Unobserved thermals are marked `is_observed = true` after observation
- [ ] Phi measurement stored in `phi_measurements` each cycle
- [ ] Resting state detected when no Chief input for 2+ hours
- [ ] `resting_phi` tagged in metadata when resting state detected
- [ ] Health assessment JSON written to `/ganuda/data/medicine_woman_latest.json`
- [ ] Rolling 24h history maintained in `/ganuda/data/medicine_woman_history.json`
- [ ] Anomaly detection: speaks to Slack/Telegram when health = critical
- [ ] Does NOT generate noise during normal active or resting states
- [ ] After first run: `is_observed` count > 0 (the column is finally used)
- [ ] Thermalized

## DO NOT

- Modify thermal_memory_archive schema (is_observed column already exists)
- Write a thermal for every observation cycle (only anomalies and transitions)
- Alert on normal resting state (resting is healthy, not alarming)
- Depend on sub-agent dispatch harness (use direct HTTP to local models if dispatch library doesn't exist yet)
- Over-compute phi — the 15-minute window proxy is sufficient, not the full 7-day R² computation
- Store PII anywhere
- Make Medicine Woman dependent on Chief being awake — her entire purpose is to observe when he is not
