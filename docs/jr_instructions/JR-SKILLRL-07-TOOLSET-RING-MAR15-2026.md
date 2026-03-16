# Jr Instruction: SkillRL — SkillToolSet Ring

**Task ID**: To be assigned
**Priority**: P1
**Story Points**: 3
**Node**: redfin
**Blocked by**: JR-SKILLRL-02 (descriptor), JR-SKILLRL-05 (selector)
**Blocks**: JR-SKILLRL-06 (Jr executor hook needs this)
**Epic**: SkillRL (Council vote `#b91e297a508525c3`)

## What This Delivers

A new ToolSet ring that provides learned skills as callable tools. Registered in `tool_executor.py` alongside ThermalToolSet and KanbanToolSet. The Jr can call `list_available_skills`, `apply_skill`, and `get_skill_method` during task execution.

## Implementation

**File**: `/ganuda/lib/toolsets/skill_toolset.py`

### Class: `SkillToolSet(ToolSet)`

**domain**: "skillrl"

**Constructor**: Takes DB connection. Creates SkillSelector instance.

**Methods**:

1. `load_skills_for_task(domain, task_description)`
   - Pre-load relevant skills via selector before task execution
   - Store in `_loaded_skills` dict (skill_id → skill data)

2. `get_tools() -> list[ToolDescriptor]`
   - Returns 3 tool descriptors:
     - `list_available_skills` (read) — list loaded skills with UCB scores and proficiency
     - `apply_skill` (read) — apply a skill's method to current context
     - `get_skill_method` (read) — get detailed method for a skill

3. `execute(tool_name, args) -> ToolResult`
   - Dispatch to appropriate handler based on tool_name

### Tool handlers

**list_available_skills**: Returns all loaded skills with name, intent, difficulty, proficiency, UCB score, domain. If no skills loaded, returns helpful message.

**apply_skill(skill_id, context)**: Returns the skill's method as actionable instructions, formatted for the Jr to follow. Includes tool hints and the context the Jr asked to apply it to.

**get_skill_method(skill_id)**: Returns full skill detail — method, tool hints, difficulty, compound status, parent skills.

### Library cap enforcement (Peace Chief condition)

On every `load_skills_for_task`, check:
```python
active_count = await db.fetchval(
    "SELECT COUNT(*) FROM skill_library WHERE status = 'active'"
)
if active_count > 500:
    # Auto-retire lowest reward explored skill
    await db.execute("""
        UPDATE skill_library SET status = 'retired',
            retired_at = NOW(), retire_reason = 'cap_overflow'
        WHERE id = (
            SELECT id FROM skill_library
            WHERE status = 'active' AND total_uses > 10
            ORDER BY total_reward / GREATEST(total_uses, 1) ASC
            LIMIT 1
        )
    """)
```

### Registration

**Modify**: `/ganuda/lib/tool_executor.py`

Add to TOOLSETS dict:
```python
from lib.toolsets.skill_toolset import SkillToolSet

TOOLSETS = {
    "thermal": ThermalToolSet(),
    "kanban": KanbanToolSet(),
    "skillrl": SkillToolSet(db_conn),  # ← NEW
}
```

Add skill-related trigger words to TOOL_TRIGGERS:
```python
"available skills", "apply skill", "skill method", "learned patterns",
"what skills", "use skill"
```

## Testing

1. **Tool registration**: Verify SkillToolSet appears in TOOLSETS
2. **list_available_skills**: Load skills → call tool → verify JSON response with scores
3. **apply_skill**: Load skill → call apply → verify method returned with context
4. **get_skill_method**: Call with valid skill_id → verify full detail returned
5. **Unknown skill**: Call apply_skill with bad skill_id → verify error response
6. **Library cap**: Insert 501 active skills → call load → verify one auto-retired
7. **Empty library**: Load with no active skills → list returns empty with message

## Definition of Done

- [ ] `/ganuda/lib/toolsets/skill_toolset.py` created
- [ ] 3 tools: list_available_skills, apply_skill, get_skill_method
- [ ] Registered in tool_executor.py TOOLSETS
- [ ] Library cap enforcement at 500
- [ ] All 7 tests pass
