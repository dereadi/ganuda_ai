# Jr Instruction: SkillRL — Skill Extractor (Post-Task Analysis)

**Task ID**: To be assigned
**Priority**: P1
**Story Points**: 5
**Node**: redfin
**Blocked by**: JR-SKILLRL-01 (schema), JR-SKILLRL-02 (descriptor)
**Blocks**: JR-SKILLRL-06 (Jr executor hook)
**Epic**: SkillRL (Council vote `#b91e297a508525c3`)

## What This Delivers

When a Jr task completes successfully, the Skill Extractor analyzes the work and determines if a reusable skill emerged. If so, it creates a SkillDescriptor and submits it for council verification. The skill enters the library as `candidate` until the council approves it.

This is the INPUT side of the learning loop — where the organism harvests new capabilities from its own work.

## Implementation

**File**: `/ganuda/lib/skill_extractor.py`

### Core function: `extract_skill(task: dict) -> SkillDescriptor | None`

1. Build extraction prompt from task metadata (title, description, acceptance_criteria, files_modified, steps_summary)
2. Dispatch prompt to local model via `sub_agent_dispatch.dispatch()` on `redfin_vllm` (DC-9 — internal reflection stays local)
3. Parse JSON response. If `skill_found: false`, return None
4. Construct SkillDescriptor from parsed response
5. Return the descriptor

### Sanitization: `sanitize_skill(skill: SkillDescriptor) -> SkillDescriptor | None`

Before any skill enters the library, sanitize it:
1. Run `intent` and `method` through `domain_tokenizer.tokenize()` (in check-only mode)
2. If ANY `NEVER_SEND` pattern matches in either field, **reject the skill entirely** (return None, log warning)
3. If infrastructure terms found (node names, IPs), **strip them** from intent and method (replace with generic placeholders: "primary GPU node", "database node", etc.)
4. Recompute content_hash after sanitization

### Duplicate check: `check_duplicate(skill, db_conn) -> bool`

Query `skill_library` by `skill_id`. If exists, return True (skip extraction).

### Council submission: `submit_for_verification(skill, council) -> dict`

1. Build council proposal from skill metadata
2. Call `council_vote()` with max_tokens=200
3. If consent + confidence > 0.5: set status = `active`
4. If consent but low confidence: set status = `candidate` (queue for re-review)
5. If dissent or sacred_dissent: set status = `rejected`, log reason
6. **Council fallback** (Turtle condition): if council unreachable for >60 seconds, skill enters `candidate` status automatically. Never auto-approves to `active`.

### Circuit breaker (Coyote condition)

Track extraction count per day. If >5 extractions in 24 hours, pause extraction and log warning. Resume next day. This prevents the library from filling with noise during high-activity periods.

### Pipeline isolation (Spider condition)

`extract_skill()` is called async from the Jr executor. It has a 30-second timeout. If it fails, hangs, or crashes:
- The Jr task is ALREADY marked complete (extraction is post-completion)
- Failure is logged but NEVER blocks the Jr pipeline
- No retry — if extraction fails, that task's skill is simply lost (acceptable)

## Extraction Prompt

```
You are a skill extractor for a software federation.

A Jr engineer just completed a task successfully. Analyze the task
and its outcome to determine if a REUSABLE SKILL emerged.

A skill is reusable if:
1. The SAME PATTERN could apply to future, different tasks
2. It's not just "I edited a file" — it's a transferable technique
3. It has clear intent (WHY), method (HOW), and tool requirements
4. Difficulty is >= 3 (trivial patterns are not worth tracking)

Task Title: {title}
Task Description: {description}
Acceptance Criteria: {acceptance_criteria}
Files Modified: {files_modified}
Steps Completed: {steps_summary}

If a reusable skill emerged, respond with JSON:
{
    "skill_found": true,
    "name": "short descriptive name",
    "intent": "the reasoning principle — WHY this pattern works",
    "method": "step-by-step procedure — HOW to apply this pattern",
    "difficulty": <3-10>,
    "tool_hints": ["tool1", "tool2"],
    "domain": "code|research|ops|legal|general",
    "reasoning": "why you believe this is reusable"
}

If NO reusable skill emerged, respond:
{
    "skill_found": false,
    "reasoning": "why no skill was extracted"
}

IMPORTANT: Do NOT include any specific server names, IP addresses, file paths,
database names, or credentials in the skill description. Keep it generic and
transferable.
```

## Testing

**File**: `/ganuda/tests/test_skill_extractor.py`

1. **Extraction from real task**: Feed a completed Jr task dict → verify SkillDescriptor returned with valid fields
2. **Trivial task rejection**: Feed a task that just edited one line → verify `skill_found: false`
3. **NEVER_SEND rejection**: Feed a task whose method contains a DB password pattern → verify skill rejected
4. **Infrastructure sanitization**: Feed a task mentioning "redfin" and "192.168.132.223" → verify those terms stripped from output
5. **Duplicate skip**: Insert a skill, then extract the same pattern → verify duplicate detected
6. **Timeout handling**: Mock a slow dispatch (>30s) → verify timeout fires, no crash
7. **Circuit breaker**: Trigger 6 extractions → verify 6th is blocked

## Definition of Done

- [ ] `/ganuda/lib/skill_extractor.py` created
- [ ] `extract_skill()` dispatches to local model, parses response
- [ ] `sanitize_skill()` strips infrastructure terms, rejects NEVER_SEND matches
- [ ] `check_duplicate()` queries skill_library
- [ ] `submit_for_verification()` calls council with fallback to candidate
- [ ] Circuit breaker at 5/day
- [ ] 30-second timeout, non-blocking
- [ ] All 7 tests pass
