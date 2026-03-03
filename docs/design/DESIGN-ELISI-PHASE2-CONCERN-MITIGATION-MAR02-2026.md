# Elisi Phase 2 — Concern Mitigation Design

**Date**: March 2, 2026
**Status**: APPROVED (Iteration 2, TPM Finalized)
**Author**: TPM (Claude Opus 4.6)
**Original Vote**: #97485885 (0.788 confidence, PROCEED WITH CAUTION)
**Iteration 1 Vote**: #293fe9209ce79b90 (0.837 confidence, REVIEW REQUIRED — 5 concerns)
**Kanban**: Elisi Observer epic (#1918)
**Long Man Phase**: DELIBERATE → ADAPT (this document) → BUILD (pending council approval)

---

## Problem Statement

Council Vote #97485885 approved Elisi Phase 2 with four conditions. Phase 2 transitions Elisi from passive observation (logging council votes and Jr results) to active valence signaling — computing a health metric `V = U - E[U]` and using it to activate epigenetic modifiers that adjust system behavior.

This transition carries risk. Four specialists identified specific concerns during deliberation. This document proposes engineering mitigations for each concern, assesses the residual risk after mitigation, and identifies the diminishing returns boundary for each — the point where further mitigation costs more than the risk it reduces.

**The council decides whether these mitigations are sufficient.** If they are not, we iterate. If iteration reaches diminishing returns, we present the residual risk as an accept/reject/redirect decision.

---

## The Four Concerns

Quoted from Council Vote #97485885 deliberation (March 2, 2026):

| # | Specialist | Concern | Severity |
|---|-----------|---------|----------|
| 1 | **Crawdad** | Single point of failure — Elisi runs only on redfin. If redfin goes down, observation goes blind. | **CRITICAL** |
| 2 | **Coyote** | 120s polling interval is too slow to detect cascading failures. | HIGH |
| 3 | **Raven** | Start with heuristic and EMA, not the 7B model. Prove the signal before adding inference cost. | HIGH |
| 4 | **Turtle** | Every modifier must be reversible. Graceful degradation required. Damping on emissions. 7-generation test. | HIGH |

---

## Mitigation Engineering

### Concern 1: Crawdad — Single Point of Failure (CRITICAL)

**What could go wrong**: Redfin reboots (as happened March 2), crashes, or loses network. Elisi stops observing. No one notices. System runs blind — valence signals go stale, modifiers decay to neutral, but the *gap in observation* is invisible.

**Iteration 1 review feedback**: Council Vote #293fe9209ce79b90 placed the heartbeat monitor on greenfin. Coyote dissented (2x weight): greenfin is on the same VLAN (132) as redfin — a switch failure, VLAN misconfiguration, or power event affecting the 132 subnet takes both down simultaneously. The heartbeat monitor shared redfin's failure domain. Crawdad suggested a secondary heartbeat on a different node.

**Iteration 2 mitigation — Heartbeat Monitor on Silverfin (VLAN 10)**:

Deploy the heartbeat checker on **silverfin** (192.168.10.10, VLAN 10) — the FreeIPA identity authority. Silverfin is:
- **Always on**: If silverfin goes down, SSSD breaks on every node and sudo stops working federation-wide. Its uptime is the highest-priority SLA in the cluster.
- **Different failure domain**: VLAN 10, isolated from the compute VLAN 132 where redfin and greenfin live. No shared switch ports, no shared power strip, no common mode failure.
- **Network path to bluefin proven**: Every node's SSSD client connects through silverfin already. The route from VLAN 10 to bluefin (VLAN 132) is established and tested daily by every sudo invocation.
- **Minimal footprint**: FreeIPA is a lightweight identity server. A cron job or systemd timer adding one SQL query every 60s is invisible overhead.

The checker queries bluefin's `thermal_memory_archive` for recent Elisi observations:

```sql
SELECT COUNT(*) FROM thermal_memory_archive
WHERE metadata->>'source' = 'elisi_observer'
AND created_at > NOW() - INTERVAL '240 seconds';
```

If count = 0 (no observation in 2x POLL_INTERVAL):
1. Log "BLIND SPOT: Elisi has not reported in 240s" to thermal memory (temp 85, source: elisi_heartbeat)
2. Send Telegram alert to TPM channel
3. Continue checking every 60s until Elisi resumes

**Alternative considered — goldfin (VLAN 20)**: Goldfin is also on an isolated VLAN and always on. Either goldfin or silverfin would work. Silverfin is preferred because its network path to bluefin is already proven by SSSD traffic, and its uptime is already the highest-priority SLA.

This remains a **gap detector**, not a secondary observer. Silverfin detects the absence of observation — it does not replace it.

**Why NOT a full secondary observer**: Running observer.py on a second node doubles the maintenance surface, creates duplicate thermal writes requiring dedup logic, and adds cross-node coordination complexity. The failure mode we're mitigating is *not knowing Elisi is down*, not *Elisi being down*. A 30-line heartbeat script solves the actual problem.

**Residual risk**: If redfin (observer) AND bluefin (database) are simultaneously down, the heartbeat check fails because the DB is unreachable. **Accepted** — simultaneous loss of redfin + bluefin is a federation-level catastrophe that takes down council, Jr execution, and all DB-backed services. Elisi's blindness is the least of the problems. Silverfin's heartbeat will correctly detect this (connection refused) and can still send a Telegram alert (outbound internet via its own route) even if bluefin is down.

**Diminishing returns boundary**: Moving the heartbeat from greenfin (same VLAN) to silverfin (isolated VLAN) eliminates the common-mode failure that Coyote identified, at zero additional engineering cost — same script, different node. Adding a THIRD heartbeat (e.g., goldfin) provides marginal additional coverage for a two-VLAN-simultaneous-failure scenario that is already extremely improbable. **Stop here.**

---

### Concern 2: Coyote — 120s Polling Too Slow

**What could go wrong**: A cascade (3+ Jr failures in rapid succession, or a council vote triggering bad routing) starts and finishes within one poll interval. Elisi never sees it. The valence signal reports "all clear" during an active incident.

**Proposed mitigation — Reduce POLL_INTERVAL to 30s**:

Change `POLL_INTERVAL = 120` to `POLL_INTERVAL = 30` in observer.py. This is a one-line config change.

30s rationale:
- Matches web materializer cadence (proven sustainable for DB polling)
- A 3-failure cascade at typical Jr task duration (~60-120s per task) spans 3-6 minutes. At 30s polling, Elisi observes it within the first 30s of the cascade — in time to detect the trend.
- 4x faster than current, for zero engineering cost
- DB cost: one SELECT every 30s on two tables with indexed columns = negligible

**Why NOT event-driven (LISTEN/NOTIFY)**: PostgreSQL LISTEN/NOTIFY requires persistent connections, reconnection logic on network flaps, new triggers on council_votes and jr_work_queue, and testing for missed notifications during reconnection windows. It solves a problem that 30s polling already handles. Coyote's concern is *speed*, not *architecture*.

**Residual risk**: A sub-30s incident (start to resolution in <30s) could be missed entirely. **Accepted** — Elisi is a trend indicator, not a circuit breaker. The gateway health check (5s interval) and systemd restart policies handle real-time recovery. Elisi's job is to notice patterns across minutes and hours, not react within seconds.

**Diminishing returns boundary**: 120s → 30s = config change (zero cost, 4x improvement). 30s → event-driven = week of work (high cost, ~2x improvement over 30s for edge cases only). **Stop at 30s.**

---

### Concern 3: Raven — Heuristic First, No Model

**What could go wrong**: Using the 7B model (vllm-elisi on port 9100) for valence computation burns 8GB VRAM continuously, adds inference latency to every observation cycle, and introduces an AI-evaluating-AI loop before we've proven the underlying signal has value.

**Proposed mitigation — Pure Arithmetic Valence Signal**:

Phase 2 valence is computed with no model inference:

```
V = U - E[U]
```

**U (Observed Utility)** — composite score from existing DB fields:

| Component | Source | Weight | Calculation |
|-----------|--------|--------|-------------|
| Jr success rate | jr_work_queue | 0.4 | completed / (completed + failed) over last 10 tasks |
| Council confidence | council_votes | 0.3 | Mean confidence of last 5 votes |
| DLQ depth | jr_work_queue | 0.2 | Inverse of count WHERE status = 'failed' AND retry_count >= 3 |
| Thermal write rate | thermal_memory_archive | 0.1 | Count of non-Elisi writes in last hour (system activity indicator) |

**E[U] (Expected Utility)** — Exponential Moving Average:

```
E[U]_new = α * U + (1 - α) * E[U]_old
```

- α = 0.1 (slow adaptation — 10% weight to new observation, 90% to history)
- Stored in a single DB row: `elisi_state` table (new, 1 row only)
- Initialized to first observed U value

**V (Valence Signal)** — the delta:

- V > 0.1 → system performing above expectations (no action)
- -0.1 ≤ V ≤ 0.1 → neutral zone (no action)
- V < -0.1 → degradation detected → activate `high_load` modifier with 4-hour TTL
- V < -0.3 → significant degradation → activate `high_load` + send Telegram alert

**Why NOT the 7B model**: Raven's wisdom — prove the signal first. If the arithmetic valence correctly detects degradation patterns over 2 weeks of Phase 2 operation, then Phase 3 can layer in model-based narrative summaries for human consumption. If the arithmetic signal has no predictive value, the model won't save it.

**The 7B model stays deployed** on port 9100. It just isn't called. Zero cost to keep it warm for Phase 3.

**Residual risk**: Heuristic misses subtle correlations that a model would catch (e.g., specific specialist response patterns predicting future failures). **Accepted** — this is Phase 2 validation. We need to know if the signal structure works before we optimize signal extraction.

**Diminishing returns boundary**: This concern is fully mitigated by design choice. No further mitigation needed. The mitigation IS the approach. **Stop here.**

---

### Concern 4: Turtle — Reversibility & Graceful Degradation

**What could go wrong**: Elisi emits a bad valence signal → activates a modifier → modifier changes specialist behavior → bad council vote or failed Jr task → damage that's hard to trace back to Elisi.

**Proposed mitigation — Four Layers of Reversibility**:

**Layer 1: TTL on all Elisi-activated modifiers**

Every modifier activated by Elisi gets `expires_hours=4`. The `epigenetics.py:activate_modifier()` API already supports this. After 4 hours, the modifier auto-deactivates on next read (existing `get_active_modifiers()` auto-expire logic). No permanent system changes from automated signals.

**Layer 2: Valence decay to neutral**

If Elisi produces no new observations for 3x POLL_INTERVAL (90s at 30s interval), V decays toward 0:

```
V_decayed = V * (0.5 ^ (elapsed / POLL_INTERVAL))
```

After ~5 missed cycles, V ≈ 0. After ~10, V ≈ 0.001 (effectively zero). Stale signals don't persist.

**Layer 3: Activation cooldown**

Elisi cannot activate the same condition_name more than once per hour. Implementation: check `activated_at` on the condition before re-activating. If `NOW() - activated_at < 1 hour`, skip. Prevents oscillation loops (V dips → activate → V recovers → deactivate → V dips → activate...).

**Layer 4: Kill switch**

One SQL statement disables everything Elisi has ever activated:

```sql
UPDATE epigenetic_modifiers SET active = FALSE
WHERE activated_by LIKE 'elisi_%';
```

Alternatively, stop the service: `systemctl stop elisi-observer`. System immediately reverts to pre-Elisi behavior. No schema changes, no data loss, no state corruption.

**7-Generation Test**: Can this be undone in 7 iterations?
- Iteration 1: Stop elisi-observer service
- Iteration 2: Kill switch query
- Iteration 3: System operates normally without Elisi
- Iterations 4-7: Not needed. Reversibility achieved in 2 steps.

**Residual risk**: Between a bad signal and TTL expiry (worst case 4 hours), one or more council votes or Jr tasks could be affected by a modifier that shouldn't be active. **Accepted** — 4 hours bounds the blast radius. The affected operations are themselves logged with full audit trails (council_votes.metacognition, jr_work_queue.result), so the impact is traceable.

**Diminishing returns boundary**: TTL + decay + cooldown + kill switch = four independent safety layers. Adding a fifth (e.g., council approval gate before each modifier activation) would make Elisi's response time ~minutes instead of seconds, defeating the purpose of automated observation. The 4-hour blast radius is acceptable for a trend indicator. **Stop here.**

---

## Integrated Phase 2 Architecture

With all four mitigations composed:

```
          ┌──────────────────────────────────────────────┐
          │        SILVERFIN (VLAN 10 — isolated)         │
          │  ┌────────────────────────────────────────┐  │
          │  │  Heartbeat Monitor (60s cron/timer)     │  │
          │  │  "Is Elisi still writing to thermal?"   │  │
          │  │  Alert on 240s silence → Telegram       │  │
          │  │  Different failure domain from redfin   │  │
          │  └────────────────────────────────────────┘  │
          └─────────────────────┬────────────────────────┘
                                │ reads thermal_memory_archive
                                │ (route: VLAN 10 → VLAN 132)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BLUEFIN (PostgreSQL)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │council_votes │  │jr_work_queue │  │thermal_memory_archive │ │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘ │
│         │                  │                      │              │
│  ┌──────┴──────────────────┴──────┐  ┌───────────┴───────────┐ │
│  │          elisi_state           │  │ epigenetic_modifiers   │ │
│  │  (1 row: E[U], last_V, ts)    │  │ (TTL, activated_by)    │ │
│  └────────────────────────────────┘  └───────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▲ reads (30s poll) / writes
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                          REDFIN                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Elisi Observer v2                        │ │
│  │                                                            │ │
│  │  1. Query council_votes + jr_work_queue (every 30s)       │ │
│  │  2. Compute U (weighted composite)                         │ │
│  │  3. Update E[U] via EMA (α=0.1)                           │ │
│  │  4. Compute V = U - E[U]                                   │ │
│  │  5. If V < -0.1: activate modifier (cooldown: 1hr)        │ │
│  │  6. If V < -0.3: activate + Telegram alert                │ │
│  │  7. Log observation to thermal_memory_archive              │ │
│  │                                                            │ │
│  │  Safety: TTL=4hr | Decay on silence | Cooldown=1hr | Kill │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  vllm-elisi (port 9100) — DEPLOYED, NOT CALLED in Phase 2 │ │
│  │  Reserved for Phase 3 narrative summaries                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### New DB Object: `elisi_state` table

```sql
CREATE TABLE IF NOT EXISTS elisi_state (
    key         VARCHAR(64) PRIMARY KEY,
    value       NUMERIC(10,6),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Seed with initial values
INSERT INTO elisi_state (key, value) VALUES
    ('expected_utility', 0.5),    -- E[U] starts at neutral
    ('last_valence', 0.0),        -- V starts at 0
    ('last_observation_at', 0.0); -- epoch timestamp of last observation
```

One table, three rows. No schema complexity.

---

## Acceptance Criteria

Each mitigation has an operational verification:

| Mitigation | Verification | Method |
|-----------|-------------|--------|
| Heartbeat on silverfin (VLAN 10) | Stop elisi-observer on redfin. Within 240s, silverfin logs blind spot alert to thermal memory and sends Telegram. | `systemctl stop elisi-observer` on redfin, then query thermal from silverfin + check Telegram |
| 30s polling | Observer logs show ~2 observations per minute during active period | `journalctl -u elisi-observer --since "5 min ago" \| grep "Observed"` |
| Heuristic valence | V computed without any HTTP call to port 9100. No vLLM logs from Elisi during Phase 2. | `journalctl -u vllm-elisi --since "1 hour ago"` shows no inference requests |
| TTL on modifiers | Activate a test modifier via Elisi. Wait 4 hours. Confirm auto-deactivated. | `SELECT active, expires_at FROM epigenetic_modifiers WHERE activated_by LIKE 'elisi_%'` |
| Decay to neutral | Stop feeding events. After 90s, V should approach 0. | Read elisi_state after quiet period |
| Cooldown | Trigger two activations within 60 min. Second should be skipped with log. | Check observer logs for "cooldown" message |
| Kill switch | Run kill query. All Elisi modifiers immediately inactive. | `UPDATE ... WHERE activated_by LIKE 'elisi_%'` then verify |

---

## Kill Criteria — When to Stop Elisi Phase 2

If any of these conditions are met after 2 weeks of Phase 2 operation, the project should be halted and the council should deliberate on whether to continue, redirect, or abandon:

1. **Valence signal is noise**: V oscillates randomly with no correlation to actual system health events (Jr failures, DLQ spikes, council disagreements). Signal has no predictive or diagnostic value.
2. **Modifier activations cause harm**: A modifier activated by Elisi is traced as the root cause of a council vote failure or Jr task failure that would not have occurred otherwise.
3. **Observation overhead degrades performance**: 30s polling measurably impacts bluefin PostgreSQL performance (query latency increase >10% on other services).
4. **Heartbeat creates false alarms**: Greenfin heartbeat fires repeatedly during normal operation due to timing jitter, creating alert fatigue.

---

## What This Is NOT

- **This is NOT a Phase 3 design.** Phase 3 (model-based narrative summaries) is a separate future decision.
- **This is NOT a circuit breaker.** Elisi is a trend indicator. Real-time response remains with gateway health checks and systemd restart policies.
- **This is NOT autonomous governance.** Elisi activates predefined, time-limited modifiers. She does not create new modifiers, change council specialist prompts, or override council votes.
- **This is NOT permanent.** Every change Elisi makes auto-expires. The system returns to pre-Elisi behavior by stopping one service.

---

## Council Question (Iteration 2)

**MITIGATION REVIEW — ITERATION 2**: Vote #293fe9209ce79b90 (Iteration 1) returned REVIEW REQUIRED with 5 concerns. The primary gap was Concern 1: Coyote dissented that placing the heartbeat on greenfin (same VLAN 132 as redfin) created a shared failure domain. This iteration moves the heartbeat to **silverfin (VLAN 10)** — an always-on infrastructure node on an isolated VLAN with proven network path to bluefin. Concerns 2-4 were largely accepted in Iteration 1.

Do these revised mitigations sufficiently address all concerns? Specifically: does the silverfin heartbeat placement resolve Coyote's shared-failure-domain dissent and Crawdad's secondary monitor recommendation?
