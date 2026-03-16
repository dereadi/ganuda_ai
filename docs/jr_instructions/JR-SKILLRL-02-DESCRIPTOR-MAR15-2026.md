# Jr Instruction: SkillRL — Skill Descriptor Dataclass

**Task ID**: To be assigned
**Priority**: P1
**Story Points**: 2
**Node**: redfin
**Blocked by**: JR-SKILLRL-01 (schema must exist for integration tests)
**Blocks**: JR-SKILLRL-03 (extractor), JR-SKILLRL-05 (selector), JR-SKILLRL-07 (SkillToolSet)
**Epic**: SkillRL (Council vote `#b91e297a508525c3`)

## What This Delivers

The `SkillDescriptor` dataclass — the atomic unit of learned capability. After this task, the federation has a standard format for representing skills, composing them, hashing them, and converting them for tool injection.

## Implementation

**File**: `/ganuda/lib/skill_descriptor.py`

Create a Python dataclass with the following:

### SkillDescriptor fields
- `name` (str) — human-readable name
- `intent` (str) — WHY the pattern works (reasoning principle)
- `method` (str) — HOW to apply the pattern (construction procedure)
- `difficulty` (int, 1-10) — complexity rating
- `tool_hints` (list[str]) — which tools/APIs this skill uses
- `domain` (str) — "code", "research", "ops", "legal", "general"
- `is_compound` (bool) — whether this was composed from other skills
- `parent_skills` (list[str]) — skill_ids of parent skills if compound
- `source_task_id` (Optional[int]) — Jr task that spawned this skill

### Properties
- `skill_id` — deterministic: `SHA256(intent + "||" + method)[:16]`. Same pattern = same skill ID.
- `content_hash` — `SHA256(intent + "||" + method + "||" + "|".join(sorted(tool_hints)))`. For integrity validation (Eagle Eye condition).

### Methods
- `to_tool_description()` — convert to OpenAI function-calling format for context injection
- `to_context_block()` — render as skill MD block for context window
- `to_db_row()` — dict ready for INSERT into skill_library
- `from_db_row(row)` — classmethod, reconstruct from DB row

### Composition function
- `compose_skills(skills, name, intent, method)` — combine 2+ atomic skills into a compound skill. Difficulty = max(parent difficulties) + len(parents) - 1, capped at 10. Tool hints merge. Parent skill_ids recorded.

## Testing

**File**: `/ganuda/tests/test_skill_descriptor.py`

1. **Deterministic skill_id**: Same intent+method always produces same skill_id
2. **Different content = different id**: Changing intent changes skill_id
3. **Content hash includes tool_hints**: Changing tool_hints changes content_hash but NOT skill_id
4. **Composition**: Two difficulty-3 skills compose into difficulty-4 compound with both parent IDs
5. **Round-trip**: `from_db_row(skill.to_db_row())` produces identical descriptor
6. **Tool description format**: `to_tool_description()` returns valid OpenAI function format

## Definition of Done

- [ ] `/ganuda/lib/skill_descriptor.py` created
- [ ] All 6 unit tests pass
- [ ] SkillDescriptor importable from `lib.skill_descriptor`
