# Jr Instruction: SkillRL — Seed Library from Historical Jr Tasks

**Task ID**: To be assigned
**Priority**: P2
**Story Points**: 2
**Node**: redfin
**Blocked by**: JR-SKILLRL-01 (schema), JR-SKILLRL-02 (descriptor), JR-SKILLRL-03 (extractor)
**Blocks**: Nothing — but makes the library useful immediately (Raven's cold start concern)
**Epic**: SkillRL (Council vote `#b91e297a508525c3`)

## What This Delivers

Seeds the skill library with 10-15 hand-crafted skills extracted from the federation's most successful Jr tasks. Solves Raven's cold start problem — the library is useful from day one instead of waiting for 50+ tasks to populate it organically.

## Implementation

### Step 1: Identify top Jr tasks

Query `jr_work_queue` for completed tasks with the clearest patterns:
```sql
SELECT id, title, description, acceptance_criteria, status, completed_at
FROM jr_work_queue
WHERE status = 'done'
ORDER BY completed_at DESC
LIMIT 50;
```

From these 50, manually select 10-15 that represent distinct, reusable patterns.

### Step 2: Extract skills

For each selected task, run the skill extractor:
```python
from lib.skill_extractor import extract_skill, sanitize_skill
from lib.skill_descriptor import SkillDescriptor

task = {
    "id": task_id,
    "title": "...",
    "description": "...",
    "acceptance_criteria": "...",
    "files_modified": [...],
    "steps_summary": "..."
}

skill = await extract_skill(task)
if skill:
    skill = sanitize_skill(skill)
    if skill:
        # Insert directly as 'active' — these are hand-verified seed skills
        insert_seed_skill(skill, db_conn)
```

### Step 3: Hand-verify and insert

Each seed skill must be verified by TPM before insertion:
- Intent is clear and generic (no project-specific jargon)
- Method is actionable and step-by-step
- No infrastructure terms (node names, IPs, paths)
- Difficulty rating is appropriate
- Domain is correct

Insert with `status = 'active'` and `council_vote_id = 'seed_library'`.

### Expected Seed Skill Categories

Based on the kinds of Jr tasks the federation runs:

| Category | Example Skill | Difficulty |
|----------|--------------|------------|
| db_operations | "Add column to existing table with migration" | 3 |
| api_integration | "Create FastAPI endpoint with health check" | 4 |
| frontend | "Fix CSS layout with scoped DOM queries" | 4 |
| ops_deployment | "Create systemd service with timer" | 5 |
| testing | "Write integration test for API endpoint" | 4 |
| security | "Run NEVER_SEND pattern scan on file" | 3 |
| monitoring | "Add health check to fire guard necklace" | 3 |
| config | "Add config section with kill switch" | 3 |
| refactoring | "Extract shared logic into base class" | 5 |
| governance | "Submit proposal to council with concerns" | 6 |

## Verification

```sql
-- Verify seed skills inserted
SELECT skill_id, name, domain, difficulty, status
FROM skill_library
WHERE council_vote_id = 'seed_library'
ORDER BY domain, difficulty;

-- Should return 10-15 rows, all status='active'
```

## Definition of Done

- [ ] 10-15 seed skills inserted into skill_library
- [ ] All skills have status='active', council_vote_id='seed_library'
- [ ] No infrastructure terms in any skill intent or method
- [ ] At least 5 different categories represented
- [ ] Content hashes valid
