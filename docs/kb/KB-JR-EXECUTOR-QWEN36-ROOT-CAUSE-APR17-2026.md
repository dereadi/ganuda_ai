# KB: Jr Executor Root Cause Analysis — Qwen3.6 Model Swap

**Date**: April 17, 2026
**Severity**: P0 — All Jr task execution broken since model swap
**Root Cause**: Harness-model mismatch. Executor designed for Qwen2.5-72B structured output; Qwen3.6-35B-A3B produces fundamentally different output.

## The Execution Pipeline (10 stages)

```
Task Created → Claimed → Instructions Loaded → Smart Extract (regex)
    ↓ (if regex fails)
LLM Planning → Plan Parsed → Code Generated → PreFlect Safety Gate
    ↓
Step Execution → Verification → Reflection → SAGA Commit/Rollback
```

## Failure Map — Every Stage That Breaks

### Stage 1: Task Claiming
**Problem**: Dual dispatch systems. DB work queue (`jr_work_queue`) vs Gateway API.
- `it-jr-executor` polls DB, claims tasks with `assigned_jr = 'it_triad_jr'`
- `jr-executor` (gecko) polls Gateway at :8080, claims by task type
- Tasks dispatched with role names ("Research Jr.", "Software Engineer Jr.") → `it-jr-executor` ignores them
- Gecko executor crashes on startup (`No module named 'lib'` in its working directory)

**Fix**: Standardize on `it_triad_jr` tag for all dispatched tasks. Kill gecko or fix its working directory.

### Stage 2: Instruction Loading
**Problem**: Tasks created with `description` but no `instruction_file` or `instruction_content`.
- Executor requires one of these two fields
- Night shift tasks dispatched with descriptions only → "No instruction_file or instruction_content specified"

**Fix**: Dispatch function must copy `description` → `instruction_content` if no instruction file exists.

### Stage 3: Smart Extraction (Regex)
**Problem**: Regex looks for `<<<<<<< SEARCH / ======= / >>>>>>> REPLACE` blocks or explicit file paths in instructions.
- Most instructions are natural language, no SEARCH/REPLACE blocks
- Falls through to LLM planning every time

**Status**: Working as designed. Not a bug — LLM planning is the expected path for natural language instructions.

### Stage 4: LLM Planning
**Problem**: Qwen3.6 output format doesn't match plan parser expectations.

The planning prompt asks for:
```
```plan
PROJECT_NAME: ...
FILES_TO_CREATE:
- /ganuda/path/to/file.py: description
FILES_TO_MODIFY:
- /ganuda/path/to/file.py: description
STEPS:
- [ ] Step 1: ...
```​
```

**Qwen2.5-72B behavior**: Followed format instructions precisely. Output structured ```plan``` block 90%+ of the time.

**Qwen3.6-35B-A3B behavior**: 
1. Starts with reasoning/thinking (even with /no_think)
2. May produce the plan block but often with variations
3. Sometimes puts the plan AFTER extensive reasoning
4. Copies placeholder paths literally from prompt examples
5. Focus and project_name fields filled with template text "[name]", "[one sentence]"

**Evidence**: "Planning response received (7862 chars)" but "Files to create: 0, Files to modify: 0, Steps: 0" — 7862 chars of response, zero parsed content.

### Stage 5: Plan Parsing
**Problem**: `parse_planning_response()` in `/ganuda/lib/jr_plan_parser.py` is rigid.
- Requires exact section headers: `FILES_TO_CREATE:`, `FILES_TO_MODIFY:`, `STEPS:`
- File entries must match regex: `- /path/to/file: description`
- No fuzzy matching, no fallback patterns
- Prose extraction fallback is weak

**Fix needed**: Multi-strategy parser that handles Qwen3.6 output.

### Stage 6: Code Generation
**Problem**: Context overflow on large files.
- Code gen prompt includes the ENTIRE target file as context
- `specialist_council.py` = 14,385 tokens of input
- At 16K max context, leaves only 2K for output
- At 8K, it exceeded by 1 token

**Evidence**: "LLM API error 400: maximum context length is 16384 tokens. You requested 2000 output tokens and your prompt contains at least 14385 input tokens"

**Fix needed**: Chunk large files. For SEARCH/REPLACE mods, extract only the relevant section (±50 lines around the target code).

### Stage 7: PreFlect Safety Gate
**Problem**: False-positive FLAG on thinking content.
- Qwen3.6 writes "I should check for ACTION: FLAG... actually this looks fine, ACTION: PASS"
- Old code searched for "ACTION: FLAG" anywhere in text → false positive
- FIXED: Now takes LAST ACTION: match

### Stage 8: Think-Tag Contamination (Cross-Cutting)
**Problem**: Qwen3.6 produces `<think>...</think>` blocks in every response.
- With `--reasoning-parser qwen3`: content=null, reasoning=text → downstream code crashes on None
- Without parser: content includes `<think>...</think>` inline → pollutes plan parsing, code gen, preflect
- FIXED in critical paths by adding `strip_think_tags()` and `clean_response()` from `/ganuda/lib/llm_config.py`
- NOT FIXED everywhere — 50+ files still have direct `["content"]` extraction

## The Five Fixes

### Fix 1: Executor System Prompt (NEW)
Add a dedicated system prompt for ALL Jr executor LLM calls:
```python
EXECUTOR_SYSTEM_PROMPT = """You are a code executor. Output ONLY what is requested.
Do not explain. Do not reason. Do not think out loud.
Follow the exact output format specified in each prompt.
If asked for a ```plan block, output ONLY that block.
If asked for code, output ONLY the code.
No preamble. No postscript. No thinking."""
```
This goes in every `simple_completion()` call from the executor. Suppresses thinking mode at the prompt level.

### Fix 2: Flexible Plan Parser
Replace rigid `parse_planning_response()` with multi-strategy:

**Strategy 1**: Original ```plan``` block format (unchanged)
**Strategy 2**: Markdown extraction — find `## FILES` or `## MODIFY` headers
**Strategy 3**: Path extraction — regex scan for any `/ganuda/...` paths mentioned anywhere
**Strategy 4**: JSON extraction — try `json.loads()` on the response
**Strategy 5**: Last resort — if instructions contain `MODIFY FILE: /path`, use that directly (skip LLM plan entirely)

### Fix 3: File Chunking for Code Gen
For files over 500 lines:
1. Read the target file
2. Search for the relevant section using keywords from the modification description
3. Extract that section ± 50 lines of context
4. Send only the chunk to the LLM with line numbers
5. Apply the resulting SEARCH/REPLACE to the full file

This keeps code gen prompts under 4K tokens regardless of file size.

### Fix 4: Universal Response Cleaning
Every LLM response in the executor goes through `clean_response()`:
- Strip `<think>...</think>` (complete and unclosed)
- Handle `content: null` with reasoning fallback
- Strip markdown formatting artifacts
- Return clean text

Already implemented in `/ganuda/lib/llm_config.py`. Needs to be wired into every response extraction point (50+ locations across the codebase).

### Fix 5: Dispatch Standardization
All tasks dispatched to `assigned_jr = 'it_triad_jr'`. The gecko executor is deprecated until its working directory issue is fixed. Add a dispatch helper:

```python
def dispatch_jr_task(title, instruction_content, priority=2, tags=None):
    """Standard Jr task dispatch — always uses it_triad_jr."""
    cur.execute("""INSERT INTO jr_work_queue 
        (title, instruction_content, assigned_jr, status, priority, tags, created_at, updated_at)
        VALUES (%s, %s, 'it_triad_jr', 'pending', %s, %s, NOW(), NOW())""",
        (title, instruction_content, priority, tags or []))
```

## Implementation Priority

| Fix | Effort | Impact | Priority |
|-----|--------|--------|----------|
| Fix 1: Executor system prompt | 30 min | High — suppresses thinking | Do now |
| Fix 5: Dispatch standardization | 15 min | High — tasks actually get claimed | Do now |
| Fix 3: File chunking | 2 hrs | High — unblocks large file mods | Do today |
| Fix 2: Flexible parser | 1 hr | Medium — handles format variance | Do today |
| Fix 4: Universal response cleaning | 1 hr | Medium — hardens all paths | Do this week |

## Harness Engineering Principle

> "The orchestration code wrapping a language model now drives more performance variation than the model itself." — Stanford meta-harness paper, March 2026

The Jr executor IS the harness. The model swap exposed every assumption the harness made about model behavior. The fixes above don't change the model — they change the harness to be model-agnostic. Next model swap should require only `models.env` update, not code changes.
