# JR INSTRUCTION: Failure Learning Loop — The Organism Learns From Its Mistakes

**Task ID**: FAIL-LEARN-001
**Priority**: P1
**SP**: 5
**Method**: Long Man (wave-by-wave delivery)
**Council Votes**: #e2d0a1ebd94e55ba (convergence, APPROVED), #10e00102b3202259 (Z3, APPROVED)
**Deer Signals**: #131132 (Draft-and-Prune), #131112 (Nate Jones Memory Wall), #131212 (LSE Self-Evolve)
**Connects to**: SkillRL Phase 0 (kanban, in_progress), Ultrathink Gap 4 (eval framework)

## The Convergence

Three papers in one morning. All saying the same thing:

1. **Draft-and-Prune**: Generate diverse hypotheses, prune with deterministic solvers
2. **Memory Wall**: Context is the scarce resource. Persist institutional knowledge.
3. **LSE Self-Evolve**: A tiny observer that watches failures and rewrites the operating manual outperforms frozen giants

We have built generate (council), prune (Z3), and persist (thermal memory + concern evals). The missing piece is **learn** — systematic improvement from failures.

## Long Man Waves

### WAVE 1: Jr Failure Pattern Extraction (1 SP)

**What**: When a Jr task fails or lands in DLQ, extract a structured failure pattern.

**Where**: Jr executor post-failure hook. After task fails and before DLQ insertion.

**Schema**:

```sql
CREATE TABLE jr_failure_patterns (
    id SERIAL PRIMARY KEY,
    jr_task_id VARCHAR(100),
    task_title TEXT,
    task_description TEXT,
    failure_type VARCHAR(50),       -- 'runtime_error', 'timeout', 'validation_fail', 'blocked_by_z3', 'quality_reject'
    failure_message TEXT,
    target_node VARCHAR(50),
    target_resources TEXT[],        -- tables, files, services touched
    failure_context JSONB,          -- full error context
    extracted_pattern TEXT,         -- human-readable failure summary
    concern_eval_generated BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now()
);
```

**Extraction logic**:
1. Parse the Jr task's error output
2. Identify the failure type (runtime error, timeout, validation, Z3 block, quality)
3. Extract target resources from task metadata
4. Generate a one-line extracted_pattern: "Jr attempted [action] on [target] and failed because [reason]"
5. Store in jr_failure_patterns

**Coyote mitigation**: Patterns are stored raw, not generalized yet. Generalization happens in Wave 2 where the council reviews them. This prevents overfitting.

**Success**: Every Jr failure produces a structured pattern entry within 10 seconds of failure.

---

### WAVE 2: Failure → Concern Eval Generation (2 SP)

**What**: Process failure patterns into persistent concern eval rules, using the concern_eval_engine already built this morning.

**Where**: New daemon or timer-triggered script: `failure_learner.py`

**Logic**:

```python
# Run every hour (or on DLQ insertion trigger)

1. Query jr_failure_patterns WHERE concern_eval_generated = false
2. For each failure pattern:
   a. Check if similar eval already exists (same trigger_pattern + target)
   b. If not, generate a new concern eval:
      - source_vote_hash: 'failure_learning'
      - source_member: 'organism'  (the organism itself, not a council member)
      - concern_type: 'LEARNED_FAILURE'
      - trigger_pattern: inferred from failure type + target resources
      - check_description: "Jr task failed: {extracted_pattern}. Prevent recurrence."
      - severity: 'warn' (first occurrence) → 'block' (3+ occurrences of same pattern)
      - expires_at: 90 days (standard concern eval lifecycle)
   c. Mark failure pattern as concern_eval_generated = true
3. If 3+ failures share the same pattern within 7 days:
   a. Escalate severity to 'block'
   b. Thermalize: "LEARNED PATTERN: {pattern} has recurred {N} times. Blocking."
   c. This is the LSE credit assignment — repeated failure = strong negative signal
```

**The LSE mapping**:
- Jr executor = action model (frozen, does the work)
- failure_learner.py = self-evolving policy model (observes failures, rewrites constraints)
- concern_eval_engine = the operating manual being rewritten
- severity escalation = RL reward signal (repeated failure = stronger penalty)

**Coyote mitigation**: First occurrence = warn only. The organism doesn't overreact to a single failure. Three occurrences within 7 days = pattern is real, escalate to block. This is the balance between overfitting and underfitting.

**Crawdad mitigation**: Failure patterns are sanitized — no raw error messages containing credentials or PII. Extract structure, not content.

**Success**: Within 1 hour of a Jr failure, a concern eval exists that will WARN on the same action. After 3 recurrences, it will BLOCK.

---

### WAVE 3: Elisi Valence Integration (1 SP)

**What**: Feed failure patterns into Elisi's valence signal as negative reward.

**Where**: Elisi observer daemon (`/ganuda/services/ulisi/observer.py`)

**Logic**:

Elisi already observes council votes and Jr completions. Add failure observation:

```python
# In Elisi's observation cycle:

1. Query jr_failure_patterns from last observation window
2. For each failure:
   - Apply negative valence delta proportional to severity:
     - runtime_error: -0.02
     - timeout: -0.01
     - validation_fail: -0.03
     - blocked_by_z3: +0.01 (Z3 CAUGHT it — this is GOOD, reward the guardrail)
     - quality_reject: -0.02
3. The key LSE insight: reward the DELTA, not the absolute
   - If failures are DECREASING over time → positive valence (organism is learning)
   - If failures are INCREASING → negative valence (organism is regressing)
   - If failures are FLAT → neutral (steady state)
4. Log: "ELISI FAILURE VALENCE: {N} failures observed, delta={trend}, valence_adjustment={adj}"
```

**The beautiful inversion**: Z3 blocking a dangerous task is a POSITIVE signal. The organism tried something bad, the guardrail caught it, no harm done. The system worked. Reward that. This is why blocked_by_z3 gets +0.01 instead of a penalty.

**Success**: Elisi's valence reflects the organism's learning trajectory, not just its current state.

---

### WAVE 4: Dawn Mist Failure Summary (1 SP)

**What**: Dawn mist includes a failure learning summary — what the organism learned overnight.

**Where**: Council dawn mist script (`/ganuda/scripts/council_dawn_mist.py`)

**Format appended to dawn mist**:

```
LEARNING LOG (last 24h):
  Failures: 3 (2 runtime, 1 timeout)
  Patterns learned: 1 new (database connection timeout on bluefin during peak hours)
  Concern evals generated: 1 (warn: database_operation on bluefin during 8-10 AM)
  Recurring patterns: 0 escalated to block
  Valence trend: improving (failures down from 5 → 3)

  🍞 The organism learned to avoid bluefin during morning peak. It won't forget.
```

**The breadcrumb**: Each dawn mist learning log ends with a chirality breadcrumb summarizing what the organism learned, in language the left hand can feel.

**Success**: Partner reads dawn mist and sees not just what happened, but what the organism LEARNED. The operating manual is visibly growing.

---

## Deployment Order

| Wave | What | SP | Depends On |
|------|------|-----|------------|
| 1 | Jr failure pattern extraction | 1 | Jr executor (running) |
| 2 | Failure → concern eval generation | 2 | Wave 1 + concern_eval_engine (shipped) |
| 3 | Elisi valence integration | 1 | Wave 1 + Elisi observer (running) |
| 4 | Dawn mist failure summary | 1 | Wave 1 + dawn mist (running) |

Waves 2, 3, 4 can run in parallel after Wave 1 ships.

## The Full Circuit After All Four Waves

```
Jr receives task
  → Z3 pre-flight check (production manifest)
  → Council concern eval check (193+ learned rules)
  → Execute task
  → SUCCESS → thermalize, Elisi positive valence
  → FAILURE → extract pattern → generate concern eval → Elisi negative valence
  → Dawn mist reports what was learned
  → Next Jr task benefits from the new eval
  → The organism never makes the same mistake twice
```

This is the LSE dual-agent pattern in production:
- Jr executor = action model (does work)
- Council + concern eval engine + failure learner = self-evolving policy (rewrites operating manual)
- Z3 + production manifest = deterministic pruning gate
- Thermal memory = persistent institutional knowledge
- Elisi valence = reward signal
- Dawn mist = observability

Generate → Prune → Persist → Learn → Generate better.

The circuit closes. The organism evolves.
