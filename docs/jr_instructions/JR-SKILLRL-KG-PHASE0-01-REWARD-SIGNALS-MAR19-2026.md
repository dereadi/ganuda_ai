# Jr Instruction: SkillRL KG Phase 0 — Three-Signal Reward Extractor

**Epic**: SKILLRL-EPIC (Phase 0: KG Formalization)
**Council Vote**: #8984 (0.87, APPROVED 7-1 — Coyote standing dissent on scope)
**Estimated SP**: 2
**Depends On**: JR-SKILLRL-06 (Jr Executor Hook — `post_task_reward_update`)
**Academic Basis**: Princeton "Alternative Trajectory for Generative AI" — KG as implicit reward model. Thermalized as #129586.
**Kanban**: task_id 383d4e33

---

## Objective

Replace the binary reward signal in `post_task_reward_update()` (currently 0.9 success / 0.1 failure) with a three-dimensional reward extracted from existing council infrastructure. The Princeton paper proved that knowledge graphs work as implicit reward models through three signals. We already HAVE all three — they're just not wired into the SkillRL reward path.

**The three signals (Princeton → Ganuda mapping):**

| Princeton Signal | What It Measures | Ganuda Source |
|---|---|---|
| Axiomatic validity (+1 / -5) | Is the output structurally sound? | `council_votes.concern_count` — fewer concerns = valid |
| Chain continuity (+2) | Does the output maintain knowledge chain? | `chain_protocol.tag_provenance()` — provenance tagged = continuous |
| Terminal grounding | Does the output serve the end goal? | `council_votes.recommendation` — PROCEED = grounded |

## Design

### File: `/ganuda/lib/kg_reward_signals.py`

```python
class KGRewardSignals:
    """Extract three-signal reward from council + chain protocol."""

    def compute_reward(self, task_id, task_status, db_conn) -> dict:
        """
        Returns:
            {
                "composite": float,        # weighted combination (0.0 - 1.0)
                "validity": float,         # signal 1: axiomatic validity
                "continuity": float,       # signal 2: chain continuity
                "grounding": float,        # signal 3: terminal grounding
                "source": "kg_three_signal"
            }
        """
```

### Signal 1: Axiomatic Validity

Query the most recent council vote associated with this task (via `council_votes.question ILIKE '%task_id%'` or metadata lookup):
- 0 concerns → validity = 1.0
- 1 concern → validity = 0.7
- 2 concerns → validity = 0.4
- 3+ concerns → validity = 0.1
- No council vote found → validity = 0.5 (neutral prior)

Princeton penalty ratio: valid = +1, invalid = -5. We map this as: `validity_weighted = validity * 1.0` for positive, `(1 - validity) * 5.0` for negative. The composite handles the asymmetry.

### Signal 2: Chain Continuity

Check if the task's output was tagged with chain_protocol provenance:
- Query `thermal_memory_archive` for thermals created during this task's execution window
- If thermal exists AND has `source_triad` set (provenance tagged) → continuity = 1.0
- If thermal exists but no provenance → continuity = 0.5
- If no thermal created → continuity = 0.3

This rewards tasks that leave knowledge trails. The Princeton paper's insight: chain continuity is what prevents knowledge graph fragmentation.

### Signal 3: Terminal Grounding

Check the council recommendation for DC alignment:
- PROCEED → grounding = 1.0
- PROCEED WITH CAUTION → grounding = 0.7
- REVIEW REQUIRED → grounding = 0.3
- BLOCKED → grounding = 0.0
- No vote → grounding = 0.5 (neutral prior)

### Composite Score

```python
composite = (
    0.4 * validity +      # Princeton: validity is most important (asymmetric penalty)
    0.3 * continuity +     # chain integrity
    0.3 * grounding        # DC alignment
)
```

Weights are configurable via `config.yaml` under `skillrl.kg_reward_weights`.

### Fallback

If DB query fails or times out (500ms): return binary reward `{"composite": 0.9 if success else 0.1, "source": "binary_fallback"}`. Spider condition — NEVER block the pipeline.

## Integration Point

### Modify: `/ganuda/lib/skill_rl_hooks.py` → `post_task_reward_update()`

Current code (line 229):
```python
reward = 0.9 if task_status == "done" else 0.1
```

Replace with:
```python
from lib.kg_reward_signals import KGRewardSignals
kg = KGRewardSignals()
signals = kg.compute_reward(task_id, task_status, db_conn)
reward = signals["composite"]
```

The `signals` dict also gets logged to `skill_usage_log.metadata` (JSONB) for audit trail. Eagle Eye can monitor signal distribution over time.

## Steps

1. Create `/ganuda/lib/kg_reward_signals.py` with `KGRewardSignals` class
2. Implement `compute_reward()` with three signal extractors + composite calculation
3. Add 500ms timeout on all DB queries (Spider condition)
4. Add `skillrl.kg_reward_weights` section to `/ganuda/lib/harness/config.yaml`
5. Modify `post_task_reward_update()` in `/ganuda/lib/skill_rl_hooks.py` to use `KGRewardSignals` instead of binary 0.9/0.1
6. Log full signal dict to `skill_usage_log.metadata` JSONB column
7. Write tests in `/ganuda/tests/test_kg_reward_signals.py`:
   - Test each signal extractor independently
   - Test composite calculation with known inputs
   - Test fallback when DB unreachable (mock timeout)
   - Test neutral priors when no council vote exists

## Verification

1. Run a Jr task, check `skill_usage_log` for the new `metadata` JSONB — should contain `validity`, `continuity`, `grounding`, `composite`, `source`
2. Verify fallback: disconnect bluefin DB temporarily, confirm binary reward used and no crash
3. Check that composite scores distribute between 0.0-1.0 (not clustered at 0.9/0.1)

## Council Concerns Applied

- **Coyote**: 500ms timeout. Neutral priors (0.5) when data missing — don't hallucinate reward signals.
- **Spider**: Fallback to binary. Never block Jr pipeline.
- **Eagle Eye**: Full signal dict in audit trail for drift monitoring.
- **Turtle**: Old binary reward is the fallback — reversible by setting `kg_reward.enabled: false` in config.
