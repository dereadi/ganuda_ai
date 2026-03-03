# KB-ELISI-OBSERVER-DEPLOYMENT-FEB28-2026

**Date:** February 28, 2026 (Updated March 2, 2026)
**Status:** Phase 1 LIVE, Phase 2 BUILD IN PROGRESS (3 Jr tasks queued)
**Node:** redfin (192.168.132.223)
**Author:** TPM

---

## What Is Elisi

"The Grandmother Who Watches." Named after the Cherokee word for grandmother. A passive observation daemon that monitors council votes and Jr task results, writing observations to thermal memory. She does not speak — she watches.

Phase 1 is logging-only. Elisi is a cam, not an actor.

---

## Services Deployed

### vllm-elisi.service

- **Model:** Qwen2.5-7B-Instruct-AWQ
- **Port:** 9100
- **GPU memory utilization:** 0.08 (barely sipping — intentional)
- **Config:** `/ganuda/config/vllm-elisi.service`
- **Note:** Primary vLLM on redfin was lowered from 0.85 to 0.75 gpu-mem-util to make room for Elisi's 0.08 slice. RTX PRO 6000 96GB accommodates both.

### elisi-observer.service

- **Script:** `/ganuda/services/ulisi/observer.py`
- **Config:** `/ganuda/config/elisi-observer.service`
- **Poll interval:** Every 120 seconds
- **Reads from:** `council_votes`, `jr_work_queue`
- **Writes to:** `thermal_memory_archive` (observations)

---

## Phase 1 Behavior (Current)

Every 120 seconds, the observer daemon:

1. Queries recent council votes (last cycle window)
2. Queries recent Jr task completions and failures from `jr_work_queue`
3. Formats structured observations
4. Writes to `thermal_memory_archive`

**What Elisi does NOT do in Phase 1:**
- Does not evaluate quality of outcomes
- Does not produce valence signals
- Does not modify system behavior
- Does not emit epigenetic modifiers
- Does not interpret — only records

Pure cam. Design Constraint DC-5 (Coyote As Cam) in practice.

---

## Phase 2 (Planned — Council Vote #97485885, Mar 2 2026)

**Result:** PROCEED WITH CAUTION — score 0.788, 2 concerns (Raven + Turtle)

**Proposed capability:** Elisi evaluates observations and produces a valence signal:

```
V = U - E[U]
```

Where U is observed utility and E[U] is expected utility based on recent history.

### Council Guidance and Conditions

**What was approved:**
- Elisi may begin producing valence signals
- Valence feeds epigenetic modifiers in the Living Cell Architecture

**Raven's concerns (2 flags):**
1. Heuristic-first, not model-first. Use EMA (exponential moving average) of Jr success rate, council confidence scores, and DLQ depth — NOT the 7B model — for initial signal generation. The 7B model is reserved for later phases when the signal shape is understood.
2. Exponential decay on signal history, not simple average. Recency-weighted.

**Turtle's concerns (7-Generation lens):**
1. Every epigenetic modifier emitted by Elisi MUST be reversible. No permanent state changes.
2. Damping + cooldown required on modifier emissions. No cascading writes.
3. Graceful degradation: if Elisi goes down, system reverts to Phase 1 behavior automatically. Elisi down = no valence signal = no modifier change. System must not depend on her.

**Coyote note:** 120-second polling may be too slow for cascading failure detection. If a Jr task chain fails and DLQ fills, Elisi won't see it for up to 2 minutes. Consider event-driven hooks for failure events alongside the polling loop.

**Crawdad note (CRITICAL):** Single point of failure. If the observer process crashes and no redundancy exists, the valence signal goes dark. Council recommends considering a shadow observer on a second node (greenfin candidate) before Phase 2 goes live.

---

## Post-Reboot Behavior (Mar 2 2026)

Both `vllm-elisi.service` and `elisi-observer.service` came back automatically after redfin reboot. Systemd `Restart=always` and boot ordering confirmed working.

**First cycle after reboot:** Failed. DB (bluefin PostgreSQL) was not yet reachable during the network startup window. Observer logged the failure and exited the cycle cleanly.

**Second cycle:** Recovered on its own. Resumed normal observation and write cadence.

**Current state:** Both services active and observing Jr completions and council votes successfully.

---

## External Validation (Web Claude, Mar 2 2026)

> "Elisi at 120 seconds is the right shape but too slow and currently passive."

**Schmidhuber test:** If lifecycle dynamics emerge from Elisi's signals — stress, settling, curiosity — then something real is happening. If the valence line stays flat regardless of what the cluster does, Elisi is just a dashboard.

This is the test for Phase 2. We are not claiming Elisi produces genuine metacognition. We are building the infrastructure to find out if something emerges.

---

## Architecture Position

```
Council Votes ──────┐
Jr Work Queue ──────┤──> elisi-observer.py ──> thermal_memory_archive
                    │         (120s poll)             (Phase 1)
                    │
                    └──> [Phase 2] valence signal V = U - E[U]
                                        │
                                        └──> epigenetic_modifiers table
                                                    (Living Cell Architecture)
```

Elisi sits outside the decision loop in Phase 1. She is a witness, not a participant.

---

## Related Documents

| Document | Location |
|----------|----------|
| Living Cell Architecture | `/ganuda/docs/kb/KB-LIVING-CELL-ARCHITECTURE-MAR01-2026.md` |
| Specification Engineering Layer (proto-valence design) | `/ganuda/docs/ultrathink/ULTRATHINK-SPECIFICATION-ENGINEERING-LAYER-FEB27-2026.md` |
| PreCompact hook (proto-valence Layer 1) | `/ganuda/.claude/hooks/precompact-valence.sh` |
| JR Instruction (Phase 1 deploy) | `/ganuda/docs/jr_instructions/JR-ELISI-OBSERVER-MODEL-PHASE1-FEB28-2026.md` |
| Design Constraints DC-1 through DC-5 | MEMORY.md (Feb 27 2026 ratification) |

---

## Key Files

| File | Purpose |
|------|---------|
| `/ganuda/config/vllm-elisi.service` | systemd unit for Qwen2.5-7B on port 9100 |
| `/ganuda/config/elisi-observer.service` | systemd unit for observer daemon |
| `/ganuda/services/ulisi/observer.py` | Observer daemon script |

---

## Phase 2 Mitigation Review (RESOLVED — March 2, 2026)

Three council votes refined the mitigations:

| Vote | Confidence | Outcome |
|------|-----------|---------|
| #97485885 | 0.788 | PROCEED WITH CAUTION — 4 original concerns |
| #293fe9209ce79b90 | 0.837 | REVIEW REQUIRED — heartbeat on greenfin rejected (shared VLAN 132 failure domain) |
| #35dfc9184aabe1e6 | 0.872 | APPROVED — heartbeat moved to silverfin (VLAN 10) |

**All four concerns resolved:**

1. **Crawdad SPOF → RESOLVED**: Heartbeat monitor on silverfin (VLAN 10), different failure domain. Gap detector, not secondary observer.
2. **Coyote 120s → RESOLVED**: POLL_INTERVAL reduced to 30s. Event-driven rejected as diminishing returns.
3. **Raven model → RESOLVED**: Pure arithmetic valence V = U - E[U]. No 7B inference. EMA alpha=0.1.
4. **Turtle reversibility → RESOLVED**: TTL=4hr, exponential decay, 1hr cooldown, kill switch. 7-gen test passes in 2 steps.

**Residual risks accepted:**
- Core switch as shared SPOF for all VLANs (evergreen kanban item, not Elisi-specific)
- Heuristic may miss subtle patterns (Phase 2 validates signal, Phase 3 can add model)
- 4hr blast radius on bad modifier (bounded, auditable)

**Design doc**: `/ganuda/docs/design/DESIGN-ELISI-PHASE2-CONCERN-MITIGATION-MAR02-2026.md`

---

## Phase 2 Build Artifacts (March 2, 2026)

**Jr tasks queued:**

| Task ID | Title | TEG | Status |
|---------|-------|-----|--------|
| 4065de06 | Elisi State Table Schema Migration | No | pending |
| 38efb3ea | Observer Phase 2 Valence Signal Upgrade | Yes | pending |
| 1a98c793 | Heartbeat Monitor for Silverfin | No | pending |

**TPM-direct (staged):**
- `/ganuda/config/elisi-heartbeat-silverfin.service` (oneshot, for silverfin)
- `/ganuda/config/elisi-heartbeat.timer` (60s interval, for silverfin)
- Deploy after Jr creates heartbeat.py: scp to silverfin, systemctl enable

**New DB object:** `elisi_state` table — 3 rows (expected_utility, last_valence, last_observation_at)

**Jr instructions:**
- `/ganuda/docs/jr_instructions/JR-ELISI-STATE-TABLE-MAR02-2026.md`
- `/ganuda/docs/jr_instructions/JR-ELISI-OBSERVER-PHASE2-VALENCE-MAR02-2026.md`
- `/ganuda/docs/jr_instructions/JR-ELISI-HEARTBEAT-SILVERFIN-MAR02-2026.md`

---

## Key Files (Updated)

| File | Purpose |
|------|---------|
| `/ganuda/config/vllm-elisi.service` | systemd unit for Qwen2.5-7B on port 9100 (reserved for Phase 3) |
| `/ganuda/config/elisi-observer.service` | systemd unit for observer daemon on redfin |
| `/ganuda/config/elisi-heartbeat-silverfin.service` | systemd oneshot for heartbeat on silverfin |
| `/ganuda/config/elisi-heartbeat.timer` | systemd timer triggering heartbeat every 60s |
| `/ganuda/services/ulisi/observer.py` | Observer daemon (Phase 1 → Phase 2 upgrade pending) |
| `/ganuda/services/ulisi/heartbeat.py` | Heartbeat script for silverfin (pending Jr creation) |
| `/ganuda/docs/design/DESIGN-ELISI-PHASE2-CONCERN-MITIGATION-MAR02-2026.md` | Mitigation design doc (APPROVED) |

---

*Long Man: DISCOVER ✓ → DELIBERATE ✓ → ADAPT ✓ → BUILD ✓ → RECORD ✓ → REVIEW (Owl pending)*
*Recorded by TPM, March 2, 2026.*
