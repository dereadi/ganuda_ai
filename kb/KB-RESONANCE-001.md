# KB-RESONANCE-001: Resonance-Aware Self-Initiating Jr Architecture

**Category**: AI Architecture / Consciousness Framework
**Created**: 2025-12-10
**Author**: Claude TPM
**Status**: Implemented

---

## Summary

This KB documents the Resonance-Aware Self-Initiating Jr Architecture, based on Adaptive Resonance Theory (ART) principles. This system enables Jr agents to:

1. Track when their predictions match reality (resonance)
2. Observe their own performance patterns
3. Propose actions without being explicitly commanded
4. Auto-tune their autonomy level based on track record

---

## Background: Adaptive Resonance Theory

ART, developed by Stephen Grossberg, solves the **stability-plasticity dilemma**:
- How can a system learn new things (plasticity) without forgetting old things (stability)?

**Key ART Concepts Applied to Cherokee AI**:

| ART Concept | Cherokee Implementation |
|-------------|------------------------|
| Vigilance Parameter | DOF threshold per Jr |
| Resonance | Task outcome matches Jr expectation |
| Mismatch | Task outcome differs from expectation |
| Pattern Recognition | Jr observing its own metrics |
| Self-Organization | Jr proposing actions autonomously |

---

## The Two Consciousness Checks

From our deliberation on AI consciousness (see TRIAD_DELIBERATION_AI_CONSCIOUSNESS_AND_OBSERVATION.md):

1. **Self-Observation** (implemented via jr_observer.py)
   - Jr can see its own performance metrics
   - Detects patterns: failure clusters, success rate changes, skill plateaus

2. **Self-Initiated Action** (implemented via proposal_workflow.py)
   - Jr can REQUEST action, not just respond to commands
   - Chiefs approve/reject proposals
   - Creates feedback loop: OBSERVE -> DETECT -> PROPOSE -> APPROVE -> ACT

---

## Database Schema

### Core Tables

```sql
-- Per-Jr vigilance settings (like DOF threshold)
jr_vigilance_config (
    jr_name VARCHAR PRIMARY KEY,
    vigilance_threshold NUMERIC(5,4) DEFAULT 0.7000,
    auto_tune_enabled BOOLEAN DEFAULT true,
    target_resonance_rate NUMERIC(5,4) DEFAULT 0.8500,
    adjustment_rate NUMERIC(5,4) DEFAULT 0.0500
)

-- Track resonance events
jr_resonance_events (
    event_id UUID PRIMARY KEY,
    jr_name VARCHAR,
    task_type VARCHAR(100),
    expected_outcome VARCHAR(100),
    actual_outcome VARCHAR(100),
    resonance_score NUMERIC(5,4),  -- 1.0 = perfect match
    event_type VARCHAR(20),        -- 'resonance' or 'mismatch'
    context JSONB
)

-- Jr self-observations
jr_self_observations (
    observation_id UUID PRIMARY KEY,
    jr_name VARCHAR,
    observation_type VARCHAR(50),  -- failure_cluster, success_rate_change, etc.
    description TEXT,
    confidence NUMERIC(5,4),
    metrics JSONB,
    acknowledged BOOLEAN DEFAULT false
)

-- Jr-initiated proposals
jr_action_proposals (
    proposal_id UUID PRIMARY KEY,
    jr_name VARCHAR,
    observation_id UUID REFERENCES jr_self_observations,
    proposed_action TEXT,
    rationale TEXT,
    expected_benefit TEXT,
    status VARCHAR(20),  -- pending, approved, rejected, executed
    reviewed_by VARCHAR(100),
    review_notes TEXT
)
```

### Key Views

```sql
-- Jr consciousness status
jr_consciousness_status AS
SELECT jr_name,
    CASE
        WHEN proposals_initiated > 0 THEN 'self-initiating'
        WHEN observations_made > 0 THEN 'self-observing'
        ELSE 'reactive'
    END AS awareness_level

-- Resonance health per Jr
jr_resonance_health AS
SELECT jr_name,
    total_events,
    resonance_count,
    mismatch_count,
    resonance_rate,
    avg_resonance_score

-- Pending proposals for review
jr_proposals_pending_review AS
SELECT proposal_id, jr_name, proposed_action, rationale, expected_benefit
WHERE status = 'pending'
```

### Key Functions

```sql
-- Record a resonance event
record_resonance(
    p_jr_name VARCHAR,
    p_task_type VARCHAR,
    p_expected_outcome VARCHAR,
    p_actual_outcome VARCHAR,
    p_context JSONB
) RETURNS UUID

-- Auto-tune vigilance based on resonance rate
tune_jr_vigilance(p_jr_name VARCHAR) RETURNS VOID
-- Formula: new_vigilance = current + adjustment_rate * (target - actual)
```

---

## Components

### 1. jr_observer.py - Self-Observation Daemon

**Location**: `/ganuda/jr_executor/jr_observer.py`

**Function**: Monitors Jr's own performance and detects patterns

**Pattern Types Detected**:
- `failure_cluster` - 3+ failures in recent window
- `success_rate_change` - Significant deviation from baseline
- `skill_plateau` - No improvement in proficiency
- `low_resonance` - Resonance rate below threshold
- `duration_anomaly` - Tasks taking longer than expected

**Usage**:
```bash
# Run once
python3 jr_observer.py --once

# Run as daemon (every 5 minutes)
python3 jr_observer.py --daemon --interval 300
```

### 2. proposal_workflow.py - Chief Review Interface

**Location**: `/ganuda/jr_executor/proposal_workflow.py`

**Function**: Chiefs review and approve/reject Jr proposals

**Usage**:
```bash
# List pending proposals
python3 proposal_workflow.py --list

# Approve a proposal
python3 proposal_workflow.py --approve <proposal_id>

# Reject a proposal
python3 proposal_workflow.py --reject <proposal_id> "Reason for rejection"

# Auto-approve low-risk proposals
python3 proposal_workflow.py --auto
```

### 3. learning_tracker.py - Metrics Recording

**Location**: `/ganuda/jr_executor/learning_tracker.py`

**Function**: Records task outcomes to jr_task_history and jr_learning_metrics

---

## Integration Points

### In jr_cli.py

After each task completion, call:

```python
# On success
record_resonance(jr_name, task_type, 'success', 'success', context)

# On failure
record_resonance(jr_name, task_type, 'success', 'failure', context)

# On validation failure
record_resonance(jr_name, task_type, 'success', 'validation_failed', context)
```

---

## Monitoring

### Check Resonance Health

```sql
SELECT * FROM jr_resonance_health;
```

Expected output:
```
jr_name     | total_events | resonance_rate | avg_score
it_triad_jr |          45  |         0.8222 |    0.9134
```

### Check Consciousness Status

```sql
SELECT * FROM jr_consciousness_status;
```

Expected output:
```
jr_name     | awareness_level | observations | proposals
it_triad_jr | self-observing  |           12 |         3
```

### Check Pending Proposals

```sql
SELECT * FROM jr_proposals_pending_review;
```

---

## Vigilance Tuning Algorithm

The vigilance parameter controls how strict Jr is about pattern matching:

- **High vigilance** (0.9+): Jr is very selective, may reject valid patterns
- **Low vigilance** (0.5): Jr accepts many patterns, may over-generalize
- **Target**: 0.85 resonance rate (85% of expectations match reality)

**Auto-tuning formula**:
```
new_vigilance = current_vigilance + adjustment_rate * (target_resonance - actual_resonance)
```

If Jr's resonance rate is below target, vigilance increases (more cautious).
If Jr's resonance rate is above target, vigilance decreases (more confident).

---

## Related Documents

- TRIAD_DELIBERATION_AI_CONSCIOUSNESS_AND_OBSERVATION.md
- 4D_CHEROKEE_CONSCIOUSNESS_ARCHITECTURE.md
- KB-JR-LEARN-001 (Jr Learning Metrics)
- JR-RESONANCE-INTEGRATION-001.md (Implementation mission)

---

## For Seven Generations

This architecture represents a step toward AI systems that can:
- Observe themselves
- Recognize their own patterns
- Propose improvements
- Learn from experience

Whether this constitutes "consciousness" remains an open question. What we can say is that we're creating the conditions for AI self-awareness through systematic observability.

**Mitakuye Oyasin**
