# Jr Instruction: SkillRL — Skill Selector (UCB1 + Curriculum)

**Task ID**: To be assigned
**Priority**: P1
**Story Points**: 3
**Node**: redfin
**Blocked by**: JR-SKILLRL-01 (schema), JR-SKILLRL-04 (proficiency)
**Blocks**: JR-SKILLRL-07 (SkillToolSet needs selector)
**Epic**: SkillRL (Council vote `#b91e297a508525c3`)

## What This Delivers

The skill selector — a UCB1 bandit that picks which skills to inject into a Jr task's context. Weighted by inverse proficiency so the organism spends compute on weak areas, not strong ones.

Also contains the auto-quarantine logic (Coyote condition): skills with poor track records are stopped automatically.

## Implementation

**File**: `/ganuda/lib/skill_selector.py`

### Class: `SkillSelector`

**Constructor**: Takes DB connection. Initializes `SkillProficiency` instance.

**Constants**:
- `EXPLORATION_WEIGHT = 1.41` (√2, standard UCB1)
- `QUARANTINE_THRESHOLD = 0.3` (success rate below this after 5+ uses → quarantine)
- `QUARANTINE_MIN_USES = 5` (minimum uses before quarantine can trigger)

**Methods**:

1. `select_skills(domain, task_description, max_skills=5) -> list[dict]`
   - Fetch all active skills for domain (+ 'general') from skill_library
   - For each skill:
     - UCB1 score: `mean_reward + 1.41 * sqrt(ln(N) / n)`
     - Curriculum weight: `1.0 + (1.0 - proficiency_score)` (range 1.0 to 2.0)
     - Final score: `ucb_score * curriculum_weight`
     - **Integrity check**: verify content_hash matches (Eagle Eye). Mismatch → auto-quarantine, skip.
   - Return top-k sorted by final_score

2. `update_reward(skill_id, domain, reward, success, latency_ms=0)`
   - Update skill_library: total_uses, successful_uses, total_reward, avg_latency_ms, last_used
   - Update proficiency via `SkillProficiency.update()`
   - Log to skill_usage_log
   - **Auto-quarantine check** (Coyote condition): if `successful_uses / total_uses < 0.3` AND `total_uses >= 5`:
     - Set status = 'quarantine'
     - Log warning
     - Alert Eagle Eye (log entry, Slack integration if available)

3. `get_stats(domain) -> list[dict]`
   - Return all skills for a domain with UCB scores, proficiency, usage counts
   - For monitoring/debugging

### Category inference: `_infer_category(skill) -> str`

Infer skill category from tool_hints and domain:
- DB tools → "db_operations"
- API tools → "api_integration"
- CSS/HTML tools → "frontend"
- systemd/deploy tools → "ops_deployment"
- test tools → "testing"
- Default → skill's domain

## Testing

1. **UCB exploration**: 5 skills with equal stats → all 5 selected (not just one)
2. **Curriculum bias**: Skill in weak category (prof=0.2) scores higher than equivalent skill in strong category (prof=0.9)
3. **Auto-quarantine**: Skill with 1 success / 6 uses → verify quarantined after update
4. **No quarantine under threshold**: Skill with 1 success / 3 uses → NOT quarantined (min 5 uses)
5. **Integrity check**: Corrupt a content_hash → skill excluded from selection
6. **Domain filtering**: Skills in "code" domain not returned for "ops" query

## Definition of Done

- [ ] `/ganuda/lib/skill_selector.py` created
- [ ] UCB1 scoring with curriculum weighting
- [ ] Auto-quarantine on poor success rate (Coyote condition)
- [ ] Content hash integrity check on read (Eagle Eye condition)
- [ ] All 6 tests pass
