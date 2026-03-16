# Jr Instruction: SkillRL — Proficiency Tracker (Curriculum Learning)

**Task ID**: To be assigned
**Priority**: P1
**Story Points**: 2
**Node**: redfin
**Blocked by**: JR-SKILLRL-01 (schema)
**Blocks**: JR-SKILLRL-05 (selector needs proficiency scores)
**Epic**: SkillRL (Council vote `#b91e297a508525c3`)

## What This Delivers

The EMA proficiency tracker — tracks how good the organism is at each skill category. Weak categories get more attention from the curriculum selector. The organism focuses training time where it's weakest, not where it's already strong.

From the Agentic Proposing paper: `M(t+1) = (1-α) * M(t) + α * success_rate`

## Implementation

**File**: `/ganuda/lib/skill_proficiency.py`

### Class: `SkillProficiency`

**Constructor**: Takes a DB connection.

**Constants**:
- `ALPHA = 0.3` — smoothing factor. Responsive to recent results while respecting history.

**Methods**:

1. `get_score(domain, category) -> float`
   - Returns current proficiency score (0.0 = weak, 1.0 = mastered)
   - Returns 0.5 for unseen categories (uncertain)

2. `update(domain, category, reward, success)`
   - EMA update: `new_score = (1 - ALPHA) * old_score + ALPHA * new_signal`
   - `new_signal = reward` if success, `reward * 0.5` if failure
   - Upserts into `skill_proficiency` table

3. `get_weakest(domain, limit=5) -> list[dict]`
   - Returns lowest proficiency categories with `total_attempts >= 3`
   - These are the curriculum targets

4. `get_vector(domain) -> dict[str, float]`
   - Full proficiency vector for a domain
   - Used for curriculum sampling probability: `P(category) ∝ (1 - proficiency)`

## Testing

1. **EMA convergence**: Update 10 times with reward=1.0 → score approaches 1.0
2. **EMA decay**: Start at 0.8, update with reward=0.2 five times → score drops
3. **New category**: get_score for unknown → returns 0.5
4. **Weakest sorting**: Insert 5 categories with different scores → get_weakest returns lowest first
5. **Proficiency vector**: Insert 3 categories → get_vector returns all three with correct scores

## Definition of Done

- [ ] `/ganuda/lib/skill_proficiency.py` created
- [ ] EMA update working with α=0.3
- [ ] get_weakest and get_vector return correct results
- [ ] All 5 tests pass
