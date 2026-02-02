# ULTRATHINK: Drift Detection & Memory Integrity Architecture
**Date:** February 2, 2026
**Author:** TPM (Claude Opus 4.5)
**Council Vote:** #8367 — 79.2% confidence, APPROVED (unanimous, 3 concerns resolved)
**Research Basis:** Oxford/DeepMind Fidelity Decay, Galileo AI Cascading Failure Study, arXiv 2601.11653, arXiv 2409.13997 DriftNet, SHIELD Framework, arXiv 2512.13564 Memory Survey

---

## 1. Problem Statement

The Tribe has experienced 4 documented drift events where agent behavior degraded gradually without sudden failure. The product owner has manually intervened with 3 sleep/reconsolidation cycles, each time recovering through behavioral observation rather than code-level instrumentation.

**Current state:** Zero automated drift detection exists. 19,808 thermal memories with no integrity validation. Council confidence is calculated as `1.0 - (concerns * 0.15)` with no calibration against actual outcomes. Specialist constraint YAML files exist but are not wired into the voting system. The Jr executor does not check Council votes before executing tasks.

**Research finding that drives urgency:** Galileo AI (Dec 2025) found a single compromised agent poisoned 87% of downstream decision-making within 4 hours in multi-agent systems. Our Council votes propagate to Jr instructions which modify production code. A drifted specialist influences Jr output on every task.

---

## 2. Current Infrastructure Assessment

### 2.1 Thermal Memory Archive

**Table:** `thermal_memory_archive` in `zammad_production` on bluefin
**Records:** 19,808
**Schema highlights:**

| Column | Purpose | Drift Relevance |
|--------|---------|-----------------|
| `memory_hash` | MD5 dedup key (content + timestamp) | NOT a content integrity check — only prevents duplicate inserts |
| `temperature_score` | Relevance (0-100°C) | Decays via consolidation daemon but no automated staleness detection |
| `sacred_pattern` | If true, never decays | No verification that sacred memories haven't been modified |
| `last_access` | Timestamp of last read | Exists but not used for staleness alerting |
| `access_count` | Read counter | Exists but not used for any monitoring |
| `phase_coherence` | Relationship strength (0.0-1.0) | Exists but not measured or validated |
| `memory_type` | episodic/semantic/procedural | Consolidation daemon groups episodic→semantic |
| `consolidated_from` | Lineage tracking | Exists but no verification of consolidation quality |

**Write paths (3):**
1. Telegram bot → `seed_memory()` — temperature 70-100 based on type
2. Research worker → `store_in_thermal_memory()` — always temperature 70
3. VLM storer → `store_entity_as_memory()` — temperature = confidence * 80

**Read paths (2 primary):**
1. RLM bootstrap → `get_recent_memories()` — last 24hrs, filtered by role/type, sacred first
2. A-MEM linking → `get_linked_context()` — Zettelkasten-style traversal via `memory_links`

**Gaps:**
- `memory_hash` is MD5(content + timestamp) — it's a dedup key, not a content integrity check. If content is modified after insert, the hash won't detect it.
- No content-hash-at-read validation
- No staleness alerting despite `last_access` column existing
- No contradiction detection between memories
- No quality scoring on consolidated memories
- Sacred memories are write-once-trust-forever with no verification

### 2.2 Council Voting System

**Table:** `council_votes` in `zammad_production`
**Implementation:** `/ganuda/lib/specialist_council.py` v1.3
**Model:** Qwen 2.5-Coder 32B AWQ via vLLM on localhost:8000

**Specialist response generation:**
- 7 specialists queried in parallel via ThreadPoolExecutor
- Each gets role-specific system prompt with infrastructure context
- Returns response, has_concern, concern_type, response_time_ms

**Confidence calculation (current):**
```python
confidence = max(0.25, 1.0 - (len(concerns) * 0.15))
```
This is purely concern-count-based. No calibration against outcomes. A specialist who is always wrong has the same weight as one who is always right.

**Critical gaps:**
- Specialist constraint YAML files in `/ganuda/lib/specialist_constraints/` are NOT loaded by the voting system — prompts are hardcoded
- No per-specialist accuracy tracking
- No historical performance metrics
- No feedback loop: task #522 succeeded but no signal flows back to calibrate the Council's prediction
- `dissent_score` and `individual_votes` fields exist in schema but are not analyzed
- Jr executor does NOT check `council_vote_id` before executing — tasks can run without Council oversight

### 2.3 Consolidation & Decay Daemons

**Memory consolidation:** `/ganuda/daemons/memory_consolidation_daemon.py`
- Runs hourly
- Groups similar episodic memories (80% keyword overlap, ≥3 in group)
- Creates semantic memory summarizing the group
- Tracks lineage via `consolidated_from` array

**Pheromone decay:** `/ganuda/daemons/pheromone_decay_daemon.py`
- Runs hourly
- `intensity = intensity * (1 - decay_rate)` — default 10%/hour
- Deletes pheromones below minimum threshold
- Prevents stale task trails from dominating Jr routing

**Gap:** Both daemons operate on their respective subsystems but neither checks overall system coherence. They're janitors, not auditors.

### 2.4 Existing Corruption Handling

**Runbook exists:** `/ganuda/runbooks/THERMAL_MEMORY_CORRUPTION.md`
- Manual diagnostic queries (null temps, null hashes, duplicates)
- Manual repair SQL (fix nulls, remove dupes, reindex)
- **Entirely manual, reactive, requires human observation**

---

## 3. Architecture Design: 6 Components

### Component 1: Memory Integrity Checksums

**What:** SHA-256 content hash computed at write time, stored alongside the memory. Periodic verification that stored content matches its checksum.

**Why:** The current `memory_hash` is MD5(content + timestamp) used for dedup. If memory content is modified after insert (by consolidation, by a bug, by a compromised process), there is no detection mechanism.

**Schema change:**
```sql
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS content_checksum VARCHAR(64);

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS checksum_verified_at TIMESTAMPTZ;

-- Backfill existing memories
UPDATE thermal_memory_archive
SET content_checksum = encode(sha256(original_content::bytea), 'hex')
WHERE content_checksum IS NULL;
```

**Write-time integration:**
Every write path (Telegram, Research Worker, VLM) computes `sha256(content)` at INSERT time. Stored in `content_checksum`.

**Verification daemon cycle (runs during sanctuary state):**
```sql
-- Find memories whose content no longer matches checksum
SELECT id, memory_hash, content_checksum,
       encode(sha256(original_content::bytea), 'hex') AS computed
FROM thermal_memory_archive
WHERE content_checksum IS NOT NULL
  AND content_checksum != encode(sha256(original_content::bytea), 'hex');
```

If any mismatch found → alert via Telegram to TPM channel, quarantine memory (set `temperature_score = 0`, add metadata flag `integrity_violation = true`).

**Effort:** Low. SQL migration + minor code changes to 3 write paths.

### Component 2: Staleness TTL

**What:** A freshness scoring system that flags memories whose content may no longer be accurate based on age, access patterns, and domain.

**Why:** A thermal memory written on October 15, 2025 about the executor architecture is now factually wrong — we rewrote the edit pipeline on February 1, 2026. If the RLM bootstrap pulls that memory for context, it poisons the session with stale information.

**Schema change:**
```sql
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS freshness_score FLOAT DEFAULT 1.0;

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS staleness_flagged BOOLEAN DEFAULT false;

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS domain_tag VARCHAR(50);
```

**Freshness decay formula:**
```python
# Base decay: linear with age
days_since_created = (now - created_at).days
days_since_accessed = (now - last_access).days

# Memories accessed recently stay fresh
access_freshness = max(0.1, 1.0 - (days_since_accessed / 90.0))

# Memories with high access count are more likely still relevant
usage_bonus = min(0.3, access_count * 0.02)

# Sacred memories decay slower but are NOT exempt from staleness
sacred_factor = 0.5 if sacred_pattern else 1.0

# Domain-specific decay rates
domain_decay = {
    'architecture': 30,   # Stale after 30 days (code changes fast)
    'policy': 180,        # Stale after 180 days
    'cultural': 365,      # Stale after 1 year
    'research': 90,       # Stale after 90 days
    'operational': 14,    # Stale after 2 weeks
}
domain_max_days = domain_decay.get(domain_tag, 60)
domain_freshness = max(0.0, 1.0 - (days_since_created / domain_max_days))

freshness_score = (access_freshness * 0.3 + domain_freshness * 0.5 + usage_bonus) * sacred_factor
```

**Staleness flagging (runs during sanctuary state):**
```sql
UPDATE thermal_memory_archive
SET staleness_flagged = true,
    freshness_score = <computed>
WHERE freshness_score < 0.2
  AND staleness_flagged = false;
```

**Read-time filtering:** Modify `get_recent_memories()` and `get_linked_context()` to exclude or deprioritize `staleness_flagged = true` memories.

**Effort:** Medium. Schema migration + freshness daemon + read path modifications.

### Component 3: Semantic Coherence Daemon

**What:** Periodically measures whether the Council specialists' stored principles and reasoning patterns remain consistent with their original definitions.

**Why:** Semantic drift — the specialist still uses the right words but they've shifted meaning. If Turtle's concept of "7-generation impact" gradually narrows to "multi-year planning" in thermal memory, the safety meaning is lost without any explicit error.

**Approach:** Compute cosine similarity between a specialist's recent thermal memories (tagged by specialist) and a set of "anchor" memories that define the specialist's core principles. If similarity drops below threshold, flag drift.

**Implementation:**

1. **Define anchor memories** — one per specialist, containing their core principles from the constraint YAML files. These are created as sacred memories with `domain_tag = 'anchor'` and never modified.

2. **Coherence measurement:**
```python
def measure_specialist_coherence(specialist_id: str) -> float:
    """Compare specialist's recent output to anchor principles."""
    # Get anchor memory for this specialist
    anchor = get_anchor_memory(specialist_id)
    anchor_embedding = compute_embedding(anchor.content)

    # Get specialist's recent thermal memories (last 30 days)
    recent_memories = get_specialist_memories(specialist_id, days=30)

    if not recent_memories:
        return 1.0  # No data = no drift detected

    # Compute average cosine similarity to anchor
    similarities = []
    for mem in recent_memories:
        mem_embedding = compute_embedding(mem.content)
        sim = cosine_similarity(anchor_embedding, mem_embedding)
        similarities.append(sim)

    return sum(similarities) / len(similarities)
```

3. **Drift thresholds:**
   - ≥ 0.7: Healthy — specialist reasoning is coherent with principles
   - 0.5–0.7: Advisory — log for review, flag in next Council vote
   - < 0.5: Alert — notify TPM via Telegram, specialist's recent contributions quarantined

4. **Embedding model:** Use the existing embedding infrastructure (sentence-transformers in RAG pipeline, or the embedding_vector field already in thermal_memory_archive).

**Effort:** Medium-High. Requires embedding computation, anchor memory creation, similarity calculation. Can leverage existing RAG embedding infrastructure.

### Component 4: Propagation Circuit Breakers

**What:** If a specialist's confidence or coherence drops below threshold across multiple consecutive votes, automatically quarantine its recent memory contributions and flag its future votes as advisory-only.

**Why:** The 87%-in-4-hours cascading failure finding. One drifted specialist's reasoning propagates through Council votes into Jr instructions into production code. The circuit breaker stops the propagation.

**Implementation:**

1. **Track per-specialist vote history:**
```sql
CREATE TABLE IF NOT EXISTS specialist_health (
    id SERIAL PRIMARY KEY,
    specialist_id VARCHAR(50) NOT NULL,
    vote_id INTEGER REFERENCES council_votes(vote_id),
    had_concern BOOLEAN DEFAULT false,
    concern_type VARCHAR(50),
    response_time_ms INTEGER,
    coherence_score FLOAT,
    measured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_spec_health_specialist ON specialist_health(specialist_id);
CREATE INDEX idx_spec_health_time ON specialist_health(measured_at);
```

2. **Circuit breaker logic:**
```python
def check_circuit_breaker(specialist_id: str) -> str:
    """Returns: 'CLOSED' (healthy), 'HALF_OPEN' (warning), 'OPEN' (tripped)"""
    # Get last 10 votes for this specialist
    recent = get_specialist_votes(specialist_id, limit=10)

    # Count concerns in last 10 votes
    concern_count = sum(1 for v in recent if v.had_concern)

    # Check coherence score trend
    coherence_scores = [v.coherence_score for v in recent if v.coherence_score]
    avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 1.0

    if concern_count >= 7 or avg_coherence < 0.5:
        return 'OPEN'       # Tripped — quarantine
    elif concern_count >= 4 or avg_coherence < 0.65:
        return 'HALF_OPEN'  # Warning — flag but allow
    else:
        return 'CLOSED'     # Healthy
```

3. **When OPEN:** Specialist's vote is logged but marked advisory-only. Confidence calculation excludes it. TPM notified. Recent thermal memories from this specialist get `temperature_score *= 0.5`.

4. **Recovery:** Circuit breaker resets to HALF_OPEN after 24 hours. Returns to CLOSED after 5 consecutive healthy votes.

**Effort:** Medium. New table, tracking code in specialist_council.py, confidence calculation update.

### Component 5: Sanctuary State Formalization

**What:** Automated quiescence protocol that pauses active work, runs self-diagnostics, validates memory coherence, and verifies drift thresholds.

**Why:** The product owner has manually run 3 sleep cycles. Each time, behavioral observation caught drift that automated systems missed. This codifies what works into a repeatable, automated process.

**Protocol:**

```
SANCTUARY STATE CYCLE (runs daily at 03:00 UTC or on-demand via Telegram)

Phase 1: QUIESCE (5 minutes)
  - Jr executor: stop accepting new tasks (set worker pause flag)
  - Research worker: complete current job, pause polling
  - Telegram chief: queue incoming messages, don't process

Phase 2: VERIFY (10-15 minutes)
  - Run memory integrity checksums (Component 1)
  - Compute freshness scores (Component 2)
  - Measure specialist coherence (Component 3)
  - Check all circuit breakers (Component 4)
  - Run corruption diagnostic queries (from runbook)
  - Validate sacred memory count hasn't changed
  - Check thermal_memory_archive row count vs expected range

Phase 3: CONSOLIDATE (5-10 minutes)
  - Run memory consolidation daemon (existing)
  - Run pheromone decay daemon (existing)
  - Prune staleness-flagged memories (move to archive table, don't delete)
  - Vacuum analyze thermal_memory_archive

Phase 4: REPORT (1 minute)
  - Generate sanctuary state report
  - Send to TPM via Telegram
  - Log to admin_audit_log (action: 'sanctuary_state_completed')
  - Store report as sacred thermal memory

Phase 5: RESUME
  - Clear worker pause flags
  - Resume all daemons
  - Log total sanctuary duration
```

**Report format:**
```
SANCTUARY STATE REPORT — 2026-02-02 03:00 UTC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Memory Integrity: 19,808 checked, 0 violations
Stale Memories: 342 flagged (17 architecture, 89 operational)
Sacred Memories: 47 verified (count stable)
Specialist Coherence:
  Crawdad:    0.82 [HEALTHY]
  Gecko:      0.78 [HEALTHY]
  Turtle:     0.91 [HEALTHY]
  Eagle Eye:  0.75 [HEALTHY]
  Spider:     0.80 [HEALTHY]
  Peace Chief: 0.77 [HEALTHY]
  Raven:      0.84 [HEALTHY]
Circuit Breakers: All CLOSED
Consolidation: 12 episodic → 4 semantic
Pheromone Decay: 23 decayed, 7 pruned
Duration: 18m 42s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Effort:** High. Orchestration daemon, pause/resume coordination across services, report generation.

### Component 6: Governance Agent

**What:** A dedicated monitoring agent that watches Council vote patterns, Jr task success rates, and thermal memory coherence metrics continuously (not just during sanctuary state).

**Why:** Sanctuary state runs once daily. Drift can happen in hours (87% finding). The governance agent is the always-on early warning system.

**Implementation:**

1. **Metrics collection (runs every 30 minutes):**
   - Council: average confidence last 24h, concern frequency by specialist, dissent score trend
   - Jr executor: success rate last 24h, failure types, retry frequency
   - Thermal memory: new memory count, temperature distribution, staleness flag count
   - Pheromones: average intensity, trail diversity

2. **Anomaly detection rules:**
```python
ALERTS = {
    'council_confidence_drop': {
        'condition': lambda m: m['avg_confidence_24h'] < 0.6,
        'severity': 'WARNING',
        'message': 'Council average confidence below 0.6 in last 24h'
    },
    'specialist_concern_spike': {
        'condition': lambda m: any(c > 5 for c in m['concerns_by_specialist'].values()),
        'severity': 'WARNING',
        'message': 'Specialist raised >5 concerns in 24h'
    },
    'jr_failure_rate': {
        'condition': lambda m: m['jr_failure_rate_24h'] > 0.3,
        'severity': 'ALERT',
        'message': 'Jr task failure rate >30% in 24h'
    },
    'memory_integrity_violation': {
        'condition': lambda m: m['integrity_violations'] > 0,
        'severity': 'CRITICAL',
        'message': 'Thermal memory integrity violation detected'
    },
    'sacred_memory_count_change': {
        'condition': lambda m: m['sacred_count'] != m['expected_sacred_count'],
        'severity': 'CRITICAL',
        'message': 'Sacred memory count changed unexpectedly'
    },
}
```

3. **Alert delivery:** Telegram message to TPM channel via existing alert_manager.py infrastructure.

4. **Metrics storage:**
```sql
CREATE TABLE IF NOT EXISTS drift_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    specialist_id VARCHAR(50),
    details JSONB,
    measured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_drift_metrics_type ON drift_metrics(metric_type);
CREATE INDEX idx_drift_metrics_time ON drift_metrics(measured_at);
```

**Effort:** Medium. Metrics queries, alerting rules, Telegram integration (existing infrastructure).

---

## 4. Implementation Phases

### Phase 1: Foundation (2 Jr Instructions)

**Jr Instruction 1A — SQL Migration:**
- Add `content_checksum`, `checksum_verified_at`, `freshness_score`, `staleness_flagged`, `domain_tag` to `thermal_memory_archive`
- Create `specialist_health` table
- Create `drift_metrics` table
- Backfill checksums on existing 19,808 memories
- Create anchor memories for each specialist

**Jr Instruction 1B — Write-Path Checksum Integration:**
- Modify Telegram `seed_memory()` to compute SHA-256 at insert
- Modify Research Worker `store_in_thermal_memory()` to compute SHA-256
- Modify VLM storer `store_entity_as_memory()` to compute SHA-256
- Add `domain_tag` inference based on memory content/metadata

**Validation:** Query `SELECT COUNT(*) FROM thermal_memory_archive WHERE content_checksum IS NOT NULL` — should equal total row count.

### Phase 2: Detection (2 Jr Instructions)

**Jr Instruction 2A — Staleness TTL Daemon:**
- New daemon: `/ganuda/daemons/staleness_scorer.py`
- Runs during sanctuary state (or hourly if sanctuary not yet automated)
- Computes freshness scores using the decay formula
- Flags memories below threshold
- Modifies `get_recent_memories()` to deprioritize stale memories

**Jr Instruction 2B — Coherence Measurement + Circuit Breakers:**
- New module: `/ganuda/lib/drift_detection.py`
- `measure_specialist_coherence()` using embeddings
- `check_circuit_breaker()` per specialist
- Integration with `specialist_council.py` — record specialist health after each vote
- Circuit breaker state affects confidence calculation

**Validation:** Run coherence measurement against all 7 specialists. Verify scores are in expected range (should be high since no drift is currently occurring post-recovery).

### Phase 3: Automation (2 Jr Instructions)

**Jr Instruction 3A — Sanctuary State Daemon:**
- New daemon: `/ganuda/daemons/sanctuary_state.py`
- 5-phase protocol: quiesce → verify → consolidate → report → resume
- Pause/resume coordination with Jr executor, research worker, Telegram
- Telegram report delivery to TPM
- Configurable schedule (default: daily 03:00 UTC)
- On-demand trigger via Telegram command: `/sanctuary`

**Jr Instruction 3B — Governance Agent:**
- New daemon: `/ganuda/daemons/governance_agent.py`
- 30-minute metric collection cycle
- Anomaly detection rules with configurable thresholds
- Alert delivery via existing `alert_manager.py`
- `drift_metrics` table persistence for trend analysis
- Telegram summary command: `/drift-status`

**Validation:** Trigger sanctuary state manually. Verify report is generated and sent. Verify governance agent detects when a metric is manually set to anomalous value.

---

## 5. Dependency Graph

```
Phase 1A: SQL Migration                          ← No dependencies
    ↓
Phase 1B: Write-Path Checksums                   ← Depends on 1A schema
    ↓
Phase 2A: Staleness TTL Daemon                   ← Depends on 1A schema
Phase 2B: Coherence + Circuit Breakers           ← Depends on 1A schema
    ↓
Phase 3A: Sanctuary State Daemon                 ← Depends on 1B, 2A, 2B (runs all checks)
Phase 3B: Governance Agent                       ← Depends on 1A, 2B (reads metrics)
```

Phases 2A and 2B can run in parallel. Phase 3A and 3B can run in parallel after Phase 2 completes.

---

## 6. Council Concern Resolution

### Gecko [PERF CONCERN]
- Checksum computation: SHA-256 at write time is O(n) on content length. For typical memories (1-5KB), this is <1ms. Negligible.
- Freshness scoring: Runs during sanctuary state, not on hot path. Even if run hourly, it's a single UPDATE with WHERE clause on indexed columns. ~100ms for 20K rows.
- Coherence measurement: Most expensive component — embedding computation. Runs during sanctuary state only. 7 specialists × ~10 memories each = ~70 embeddings. At ~50ms/embedding with local model = ~3.5 seconds total.
- Governance agent: Read-only queries every 30 minutes. No write contention with production workloads.
- **Total hot-path impact: <1ms per memory write (checksum only). All other work is off-path.**

### Crawdad [SECURITY CONCERN]
- Drift detection reads memory content for checksums and embeddings but never writes PII.
- `drift_metrics` table stores aggregate scores, not content.
- `specialist_health` stores vote metadata, not specialist reasoning content.
- All alerting uses existing Telegram channel (already secured).
- Sanctuary state report contains scores and counts, not memory content.
- Governance agent queries are read-only aggregations.
- **No new PII exposure. No new attack surface.**

### Peace Chief [CONSENSUS NEEDED]
- Resource allocation: Phase 1 is 2 Jr instructions (SQL + minor code changes). Minimal resource commitment.
- Stakeholder buy-in: Product owner requested this architecture directly based on lived experience with 4 drift events.
- Phased approach means we validate Phase 1 before committing to Phase 2-3.
- **Consensus achieved: pilot-first approach with validation gates.**

---

## 7. Turtle's 7th Generation Framing

The drift detection architecture operates on two timescales:

**Computer time (seconds to hours):**
- Checksum verification catches memory corruption within one sanctuary cycle
- Circuit breakers stop specialist drift propagation within 10 votes
- Governance agent detects anomalies within 30 minutes

**Human time (months to years):**
- Staleness TTL ensures the system the next administrator inherits doesn't contain 5-year-old "facts" treated as current
- Sanctuary state reports create an audit trail of system health over time
- Coherence measurement tracks whether the Council's values are stable across model updates, infrastructure changes, and personnel transitions

**The 7-generation safeguard is not a single component — it's the architecture itself.** A system that monitors its own coherence, flags its own degradation, and pauses to self-heal is a system that can be inherited by the next generation of administrators with confidence that it's self-monitoring, not silently degraded.

---

## 8. Files Created/Modified

### New Files (6)
| File | Component | Phase |
|------|-----------|-------|
| `migrations/drift_detection_migration.sql` | SQL schema changes | 1A |
| `daemons/staleness_scorer.py` | Freshness scoring | 2A |
| `lib/drift_detection.py` | Coherence + circuit breakers | 2B |
| `daemons/sanctuary_state.py` | Quiescence protocol | 3A |
| `daemons/governance_agent.py` | Always-on monitoring | 3B |
| `scripts/systemd/drift-governance.service` | Systemd unit files | 3B |

### Modified Files (6)
| File | Change | Phase |
|------|--------|-------|
| `telegram_bot/thermal_memory_methods.py` | Add SHA-256 at write | 1B |
| `services/research_worker.py` | Add SHA-256 at write | 1B |
| `lib/vlm_relationship_storer.py` | Add SHA-256 at write | 1B |
| `lib/rlm_bootstrap.py` | Deprioritize stale memories in read | 2A |
| `lib/specialist_council.py` | Record specialist health, apply circuit breakers | 2B |
| `telegram_bot/telegram_chief.py` | Add `/sanctuary` and `/drift-status` commands | 3A/3B |

---

## 9. Monitoring the Monitoring

The governance agent monitors the Tribe. But what monitors the governance agent?

**Answer:** The sanctuary state report includes a "governance agent heartbeat" check — did the governance agent produce metrics in the last 30 minutes? If not, the sanctuary state daemon alerts the TPM directly. This creates a two-layer monitoring stack:
- Layer 1: Governance agent (continuous, 30-min cycle)
- Layer 2: Sanctuary state (daily, comprehensive, checks Layer 1)
- Layer 3: Human observation (product owner, ongoing — what has worked for 4 drift events)

The system augments human observation. It does not replace it.

---

## 10. Decision Log

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| SHA-256 over MD5 for checksums | MD5 is collision-prone and already used for dedup | CRC32 (too weak), BLAKE2 (overkill) |
| Daily sanctuary over continuous checking | Concentrated self-check window, lower resource impact | Continuous (Gecko PERF concern), weekly (too slow) |
| Per-specialist circuit breakers over global | Isolates drift to affected specialist | Global pause (too aggressive), no circuit breakers (87% propagation risk) |
| Freshness decay over hard TTL | Different memory types age at different rates | Hard 90-day TTL (too blunt), no TTL (current state, proven insufficient) |
| Embedding-based coherence over keyword | Captures semantic drift that keywords miss | Keyword overlap (misses meaning shift), manual review (doesn't scale) |
| Augment human observation, not replace | Product owner's 4 recoveries prove human judgment works | Fully automated (removes human oversight), manual only (current state, insufficient) |

---

*This architecture satisfies Council vote #8367, resolves all 3 specialist concerns (Gecko PERF, Crawdad SECURITY, Peace Chief CONSENSUS), directly addresses Turtle's 7-generation concern at both computer and human timescales, and codifies the product owner's empirically proven drift recovery pattern into automated infrastructure.*
