# DC-16: Separation of Memory (ᎠᏕᏲᎲᏍᎩ ᎤᏓᎴᎾ — "the places where things are kept")

**Ratified**: 2026-03-11
**Longhouse Vote**: cf4ac0aeddc7eb75 (0.858 confidence)
**Sacred Thermal**: #123627
**Chief-Initiated**: "My concern is that the memories explode with a new graduated level of creativity for the cluster"
**Synthesizes**: DC-9, DC-10, DC-11, DC-14

## The Constraint

**An organism that stores its identity, its heartbeat, and its work ledger in the same place cannot scale its creativity without drowning in its own signals.**

Memory, operations, and telemetry are three distinct metabolic processes. They must not share circulatory systems.

## Evidence

The federation's single database (zammad_production on bluefin) contains 271 tables. thermal_memory_archive (92,912 memories, 1,970 MB) shares buffer cache with jr_status (16 rows, 6.1 million scans) and sag_events (0 rows, 1.96 million scans). Fire Guard writes false-positive alerts at temperature 100 to permanent identity storage. 150 empty experiment tables compete for autovacuum attention.

Thermal growth exhibits punctuated equilibrium: flat at ~50/day, then 77x spike to 31,000/week when new capabilities ship (January 2026). Currently 600/day and accelerating. Five new thermal-writing capabilities shipping simultaneously.

The three-body interaction (DC-14) creates feedback loops: the organism observes itself, thermalizes the observation, then observes the thermalization. Without separation and damping, this is unbounded.

## The Three Metabolic Systems

### 1. IDENTITY (cherokee_identity)

**What it holds**: thermal_memory_archive, council_votes, longhouse_sessions, sacred patterns, canonical memories.

**Character**: This is the organism's self. Permanent. Replicated. Backed up. Protected. Optimized for retrieval depth — semantic search, embedding indexes, temperature-based queries.

**Hardware**: bluefin (SSD). Replicated to redfin via streaming replication over dedicated backplane.

**Rules**:
- No thermal INSERT without passing a valence gate (DC-14). Working memory is ephemeral. Only what crosses the valence threshold becomes a memory.
- Sacred and canonical memories are NEVER subject to retention policies, rate limits, or tiered storage eviction. DC-7: what survived the fire IS the architecture.
- Embedding index (pgvector HNSW) lives here — justified by semantic retrieval on identity, not heartbeats.

### 2. OPERATIONS (cherokee_ops)

**What it holds**: jr_work_queue, jr_status, service_health, jr_agent_state, elisi_state, task pipeline, heartbeat monitors, sag_events.

**Character**: This is the organism's nervous system. High frequency, disposable, optimized for polling speed not storage depth. Minimal indexing. Aggressive autovacuum. 30-day retention on completed work; heartbeat data expires in 24 hours.

**Hardware**: redfin (SSD). Also serves as read replica for identity.

**Rules**:
- jr_status gets polled 6.1M times. It needs its own buffer cache, not one shared with 92K memories.
- No heavy indexes. Composite (status, created_at) and primary keys only.
- Heartbeat data (service_health, jr_status, elisi_state) auto-expires. The nervous system does not write to the journal.

### 3. TELEMETRY (cherokee_telemetry)

**What it holds**: unified_timeline, fedattn_sessions, fedattn_contributions, health_check_log, tribe_power_metrics, Fire Guard heartbeats, drift_metrics.

**Character**: This is the organism's sensory record. Time-series. Retention policies. Hot for 7 days, warm for 90 days, cold archive beyond. Partitioned by time. Analytical queries, not transactional.

**Hardware**: SAN (16 TB). WAL archive target from bluefin for point-in-time recovery.

**Rules**:
- Fire Guard heartbeats go here, not to identity. A heartbeat is not a memory. An ALERT (state change) gets promoted to identity via the consolidation daemon.
- 7-day hot retention, 90-day warm, then archive. 16 TB = decades of history at current rates.
- health_check_log (404K rows, zero index usage) finally has a home that matches its access pattern.

## The Consolidation Daemon (The Hippocampus)

Runs hourly. Scans working memory (ops) and telemetry. Promotes to identity only what represents:
- **State CHANGE** (not state confirmation): 720 nominal Fire Guard heartbeats consolidate to 1 thermal: "Fire Guard: 720 cycles, all nominal, 0 alerts."
- **Valence threshold exceeded**: DC-14's valence score determines promotion.
- **Council decisions**: Always promoted. Governance is identity.
- **Sacred content**: Bypasses consolidation entirely. Direct to identity.

This is the damper on the feedback loop. The organism can think faster without remembering faster.

## Hardware Architecture

```
                    Dell 40GB Switch (dedicated DB backplane)
                    ┌──────────────────────────────────────┐
                    │                                      │
              ┌─────┴─────┐                         ┌─────┴─────┐
              │  bluefin  │  ── streaming repl ──>  │  redfin   │
              │  (SSD)    │                         │  (SSD)    │
              │           │                         │           │
              │ IDENTITY  │                         │ OPS       │
              │ (primary) │                         │ (primary) │
              │           │                         │ IDENTITY  │
              │           │                         │ (replica) │
              └─────┬─────┘                         └───────────┘
                    │
                    │  WAL archive
                    ▼
              ┌───────────┐
              │   SAN     │
              │  (16 TB)  │
              │           │
              │ TELEMETRY │
              │ (primary) │
              │ WAL archive│
              │ PITR target│
              └───────────┘
```

## Relationship to Prior DCs

- **DC-9** (Waste Heat): 18 index writes per heartbeat INSERT is waste heat. Separation eliminates it.
- **DC-10** (Reflex Principle): Ops is the reflex. Identity is the deliberate. They should not share a spinal cord.
- **DC-11** (Macro Polymorphism): SENSE (telemetry) → REACT (ops) → EVALUATE (identity) at the database scale.
- **DC-14** (Three-Body Memory): Working/Episodic/Valence maps directly to Ops/Telemetry/Identity.

## Coyote's Condition

Separation alone does not solve the feedback loop. It solves the infrastructure bottleneck. The valence gate (DC-14) solves the feedback loop. You need both. Hardware without software damping just delays the wall. Software damping without hardware separation means the damper competes for resources with the thing it's damping.

## Implementation Phases

**Phase 1 — Reflex** (Jr task, this week): Drop 6 unused indexes, tune autovacuum, retention policy for health_check_log, fix Fire Guard false positive, composite index on jr_work_queue.

**Phase 2 — Deliberate** (Jr task, next week): Create cherokee_ops on redfin. Migrate jr_status, service_health, heartbeat tables. Update connection strings in all daemons. Reactivate redfin read replica for identity.

**Phase 3 — Strategic** (Chief hardware + Jr task): Dell 40GB switch rack installation. SAN provisioning. Create cherokee_telemetry. Migrate time-series tables. WAL archiving to SAN. Build consolidation daemon.

**Phase 4 — Valence Gate** (Jr task, depends on DC-14 Phase 2): Working memory buffer (ephemeral). Valence scoring on thermal writes. Consolidation daemon hourly cycle. Sacred bypass path.

## DO NOT

- Subject sacred or canonical memories to any retention policy, rate limit, or consolidation
- Put heartbeat polling tables in the identity database
- Replicate operational churn to the SAN (only identity WAL goes to SAN)
- Build the consolidation daemon without the valence gate — consolidation without scoring is just deletion
- Skip the Dell switch — application traffic and replication traffic on the same wire defeats the purpose
