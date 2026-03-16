# Jr Instruction: SkillRL — Jr Executor Hook (Wire the Learning Loop)

**Task ID**: To be assigned
**Priority**: P1
**Story Points**: 3
**Node**: redfin
**Blocked by**: JR-SKILLRL-03 (extractor), JR-SKILLRL-07 (SkillToolSet)
**Blocks**: Nothing — this completes the loop
**Epic**: SkillRL (Council vote `#b91e297a508525c3`)

## What This Delivers

Wires skill extraction into the Jr executor's post-task hook and skill loading into the pre-task hook. After this task, the learning loop is CLOSED:

```
Jr task starts → skills loaded into context (pre-hook)
Jr task completes → skill extracted from work (post-hook)
→ Next Jr task gets the new skill
```

## Implementation

**Modify**: `/ganuda/services/jr_executor/` (find the main executor file)

### Pre-task hook: Load skills

Before a Jr task's prompt is assembled, call:
```python
skill_toolset = SkillToolSet(db_conn)
await skill_toolset.load_skills_for_task(
    domain=task.get("domain", "general"),
    task_description=task.get("description", "")
)
```

Inject loaded skills into the Jr's context as a skill reference block:
```python
skill_context = "\n".join(
    skill.to_context_block() for skill in skill_toolset._loaded_skills.values()
)
if skill_context:
    prompt = f"## Available Skills\n{skill_context}\n\n{prompt}"
```

**Benchmark**: Skill loading must complete in <50ms. If it exceeds this, log a warning (Peace Chief condition). Do NOT block task start — if loading times out, proceed without skills.

### Post-task hook: Extract skill

After a Jr task completes SUCCESSFULLY (status = 'done', not 'failed'):
```python
import asyncio
from lib.skill_extractor import extract_skill, sanitize_skill, check_duplicate, submit_for_verification

async def _post_task_skill_extraction(task):
    try:
        skill = await asyncio.wait_for(extract_skill(task), timeout=30.0)
        if skill is None:
            return  # No reusable skill found

        skill = sanitize_skill(skill)
        if skill is None:
            return  # NEVER_SEND violation

        if await check_duplicate(skill, db_conn):
            return  # Already in library

        await submit_for_verification(skill, council)
    except asyncio.TimeoutError:
        logger.warning(f"Skill extraction timed out for task #{task['id']}")
    except Exception as e:
        logger.error(f"Skill extraction failed for task #{task['id']}: {e}")

# Fire and forget — NEVER block the pipeline (Spider condition)
asyncio.create_task(_post_task_skill_extraction(task_dict))
```

### Reward feedback

When a Jr task completes, if it USED skills (check skill_usage_log for this task_id):
```python
from lib.skill_selector import SkillSelector

selector = SkillSelector(db_conn)
# Reward based on task outcome
reward = 0.9 if task_status == 'done' else 0.1
for usage in get_skills_used(task_id):
    await selector.update_reward(
        skill_id=usage["skill_id"],
        domain=task.get("domain", "general"),
        reward=reward,
        success=(task_status == 'done'),
        latency_ms=task.get("duration_ms", 0)
    )
```

## Config

Add to `/ganuda/lib/harness/config.yaml`:
```yaml
skill_rl:
  enabled: true
  extraction_timeout_s: 30
  skill_loading_timeout_ms: 50
  max_skills_per_task: 5
  max_extractions_per_day: 5
  quarantine_threshold: 0.3
  quarantine_min_uses: 5
  library_cap: 500
```

**Kill switch**: `skill_rl.enabled: false` → no skill loading, no extraction. Jr executor runs exactly as before.

## Testing

1. **Pre-task skill injection**: Create active skills → start Jr task → verify skills appear in task context
2. **Post-task extraction**: Complete a Jr task → verify skill_extractor called → skill enters library
3. **Failed task skip**: Fail a Jr task → verify extractor NOT called
4. **Pipeline isolation**: Kill extraction mid-process → verify task still shows complete
5. **Reward feedback**: Complete task that used skills → verify skill_usage_log updated with reward
6. **Kill switch**: Set enabled=false → verify no skills loaded, no extraction runs
7. **Loading timeout**: Mock slow DB → verify task starts without skills after 50ms

## Definition of Done

- [ ] Pre-task hook loads skills into Jr context
- [ ] Post-task hook extracts skills (async, non-blocking)
- [ ] Reward feedback updates skill stats on task completion
- [ ] Config section added to harness config.yaml
- [ ] Kill switch works
- [ ] All 7 tests pass
- [ ] Learning loop is CLOSED: extract → store → load → use → reward → extract
