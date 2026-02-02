# ULTRATHINK: Jr Executor Search-Replace Architecture

**Date:** January 31, 2026
**Triggered By:** P0 — File edit reliability crisis (7/11 sprint failures)
**Research Input:** Jr #492 research (minimal), TPM supplemental research (5 systems analyzed)

## Problem Statement

The Jr task executor cannot reliably edit existing files. In the Jan 30 sprint, every task that required modifying an existing Python or TypeScript file either failed or caused damage. The executor truncated `task_executor.py` from 2164 to 181 lines. Only SQL operations, new file creation, and bash commands work reliably.

### Failure Mode Summary

| Mode | Count | Severity | Root Cause |
|------|-------|----------|------------|
| File truncation | 2 | Catastrophic | LLM outputs snippet; executor writes it as full file |
| Guardrail blocks | 2 | Protective | LLM outputs new code only; >50% size reduction detected |
| Indentation corruption | 2 | Moderate | Partial edit insertion loses surrounding indentation context |
| Wrong working directory | 1 | Low | Relative paths in sed commands |

### Current Architecture (Why It Fails)

The executor's edit pipeline works like this:
1. **Parse instructions** — Regex extracts code blocks from markdown (` ```python...``` `)
2. **Detect intent from prose** — `_determine_edit_mode()` scans preceding 500 chars for words like "add", "modify", "replace"
3. **Route to handler** — Either `safe_file_write()` (full replacement) or `_apply_partial_edit()` (insert/append)
4. **Apply edit** — partial_edit tries to find an anchor function/method and insert after it

**The fundamental flaw**: The LLM generates a code block, and the executor must guess from prose context whether it's a full file or a partial snippet. This is ambiguous by design. When the LLM outputs a 7-line method to add to a 2164-line file, the executor either:
- Treats it as full file → 2164 lines become 7 lines (truncation)
- Correctly identifies partial edit → but can't find the right insertion point → syntax error
- Guardrail catches size mismatch → blocks the edit entirely

## Research Findings: Industry Consensus

### The Search-Replace Pattern Dominates

4 of 5 major agentic coding systems converge on **explicit search-and-replace** as the edit format:

**Aider** (SEARCH/REPLACE blocks):
```
path/to/file.py
<<<<<<< SEARCH
def old_function():
    return 42
=======
def new_function():
    return 43
>>>>>>> REPLACE
```
- 92.1% task completion with Claude Sonnet + diff format
- 97.8% edit format compliance with Claude 3.7 Sonnet (32k thinking)
- Search-replace outperforms unified diffs in Diff-XYZ benchmark

**SWE-Agent** (`str_replace_editor`):
- Exact string match — `old_str` must match one location
- Integrated linter auto-rejects syntactically invalid edits
- Auto-rollback on syntax error
- 74.4% on SWE-bench Verified (Claude 4.5 Opus)

**OpenHands** (`str_replace` via Anthropic tool):
- Same Anthropic-based str_replace tool
- Sandboxed execution, event stream tracking
- 53-60% on SWE-bench Verified (improving with critic models)

**Claude Code** (exact string replacement):
- `old_string` must be unique in the file (or use `replace_all`)
- Must Read file before Edit (enforced by tool)
- Zero silent wrong-location edits by design

**Cursor** (outlier — full file rewrite via fine-tuned apply model):
- Uses dedicated Llama-3-70b fine-tuned for file merging
- Requires specialized inference stack; not applicable to our architecture

### Key Design Principles

1. **Explicit over implicit**: The LLM must specify WHAT to find AND what to replace it with. No guessing from prose.
2. **Uniqueness enforcement**: The search string must match exactly one location. Ambiguous matches fail loudly.
3. **Post-edit validation**: Syntax check after every edit; auto-rollback on failure.
4. **Each edit is independent**: Errors in one search-replace block don't invalidate others.

## Council Consultation

### Crawdad (Security)
**Vote: APPROVE**
- Search-replace eliminates the most dangerous failure mode: silent file truncation
- Uniqueness enforcement prevents edits landing in the wrong location
- ADDENDUM: The backup system already exists (`_backup_file()` with timestamped copies). Ensure it's called BEFORE search-replace application, not just for writes.
- ADDENDUM: Rate-limit file edits per task (max 20 search-replace blocks per task execution) to prevent runaway modification.

### Gecko (Technical Feasibility)
**Vote: APPROVE with conditions**
- The executor already has `_apply_partial_edit()` at lines 414-567 and `_determine_edit_mode()` at lines 329-412. These become OBSOLETE under search-replace — they should be replaced, not supplemented.
- The regex extraction (`_extract_steps_via_regex()` lines 1395-1516) currently parses ` ```language...``` ` blocks. Under search-replace, it must also parse `<<<<<<< SEARCH...=======...>>>>>>> REPLACE` blocks.
- CONDITION: The LLM prompt in `jr_llm_reasoner.py` must change to instruct Qwen 32B to output search-replace format instead of code blocks. This is a prompt engineering change, not a code change.
- CONDITION: Existing instruction format (markdown code blocks) must continue to work for SQL and bash — only file edits change to search-replace.

### Turtle (Seven Generations)
**Vote: APPROVE**
- This is foundational infrastructure. Every future Jr task that modifies files depends on this working.
- Investment in reliable file editing pays compound returns across all sprints.

### Eagle Eye (Monitoring & Observability)
**Vote: APPROVE**
- ADDENDUM: Log every search-replace attempt: search string (first 80 chars), match count, success/fail, file path, lines affected.
- ADDENDUM: Track metrics: search_match_rate, syntax_pass_rate, rollback_count, edits_per_task.
- ADDENDUM: If match_rate drops below 70% across a sprint, surface an alert to the council.

### Spider (Cultural Integration)
**Vote: APPROVE**
- Search-replace aligns with the principle of precision over volume.
- The Jr instructions should be updated to use search-replace format as a documented standard.

### Peace Chief (Coordination)
**Vote: APPROVE**
- This is the chicken-and-egg problem: fixing the executor requires editing the executor.
- RESOLUTION: The TPM (Claude Opus 4.5 running in Claude Code) implements Phase 1 directly, since Claude Code already has the exact-string-replacement Edit tool. Once Phase 1 is working, Phase 2+ can be done by Jrs.
- ADDENDUM: All existing Jr instruction templates must be updated to show search-replace format for file edits.

### Raven (Strategic Architecture)
**Vote: APPROVE**
- STRATEGIC NOTE: This is the single highest-leverage fix available. It converts the executor from ~30% file-edit success rate to an estimated 85-90%, based on industry data.
- PHASED APPROACH:
  - **Phase 1**: Add `_apply_search_replace()` method to `task_executor.py`. This is a new method, not editing an existing one, so it's safe for the TPM to implement directly.
  - **Phase 2**: Modify `_extract_steps_via_regex()` to detect and parse SEARCH/REPLACE blocks. Route them to the new method.
  - **Phase 3**: Update the LLM prompt to request search-replace format for file edits.
  - **Phase 4**: Add post-edit syntax validation with auto-rollback.
  - **Phase 5**: Update Jr instruction templates.

## Council Vote

| Specialist | Vote | Confidence |
|-----------|------|-----------|
| Crawdad | APPROVE | 0.92 |
| Gecko | APPROVE with conditions | 0.88 |
| Turtle | APPROVE | 0.95 |
| Eagle Eye | APPROVE | 0.90 |
| Spider | APPROVE | 0.87 |
| Peace Chief | APPROVE | 0.91 |
| Raven | APPROVE | 0.93 |

**Consensus: 7/7 APPROVE** | Composite Confidence: 0.91

## Proposed Solution

### New Search-Replace Instruction Format

Jr instructions for file edits will use this format:

```
**File:** `/ganuda/vetassist/backend/app/models/user.py`

<<<<<<< SEARCH
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
=======
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    # VA Account Linking
    va_icn = Column(String(50), unique=True, nullable=True)
    va_linked_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
>>>>>>> REPLACE
```

### New Executor Method: `_apply_search_replace()`

```python
def _apply_search_replace(self, filepath: str, search_text: str, replace_text: str) -> dict:
    """
    Apply a single search-and-replace edit to a file.

    Rules:
    1. search_text must match EXACTLY ONE location in the file
    2. If zero matches: fail with 'SEARCH_NOT_FOUND'
    3. If multiple matches: fail with 'SEARCH_AMBIGUOUS' + count
    4. Create backup BEFORE modification
    5. After replacement, validate Python syntax if .py file
    6. On syntax error, restore from backup and fail

    Returns: {success: bool, error: str, lines_changed: int, backup_path: str}
    """
    import os
    import shutil
    from datetime import datetime

    result = {'success': False, 'error': '', 'lines_changed': 0, 'backup_path': ''}

    # Validate path
    is_valid, error = self._validate_path(filepath)
    if not is_valid:
        result['error'] = f'Invalid path: {error}'
        return result

    # Read current file
    if not os.path.exists(filepath):
        result['error'] = f'File not found: {filepath}'
        return result

    with open(filepath, 'r') as f:
        content = f.read()

    # Count matches (must be exactly 1)
    count = content.count(search_text)

    if count == 0:
        result['error'] = f'SEARCH_NOT_FOUND: The search text was not found in {filepath}'
        return result

    if count > 1:
        result['error'] = f'SEARCH_AMBIGUOUS: Found {count} matches in {filepath}. Provide more context to make the match unique.'
        return result

    # Create backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{filepath}.backup_{timestamp}"
    shutil.copy2(filepath, backup_path)
    result['backup_path'] = backup_path

    # Apply replacement
    new_content = content.replace(search_text, replace_text, 1)

    # Write new content
    with open(filepath, 'w') as f:
        f.write(new_content)

    # Syntax validation for Python files
    if filepath.endswith('.py'):
        try:
            compile(new_content, filepath, 'exec')
        except SyntaxError as e:
            # RESTORE from backup
            shutil.copy2(backup_path, filepath)
            result['error'] = f'SYNTAX_ERROR at line {e.lineno}: {e.msg} — restored from backup'
            return result

    # Count lines changed
    old_lines = search_text.count('\n')
    new_lines = replace_text.count('\n')
    result['lines_changed'] = abs(new_lines - old_lines)
    result['success'] = True

    # Audit log
    print(f"[SEARCH-REPLACE] {filepath}: matched, replaced, {result['lines_changed']} lines changed")

    return result
```

### Updated Regex Extraction

Add parsing for SEARCH/REPLACE blocks in `_extract_steps_via_regex()`:

```python
# Parse SEARCH/REPLACE blocks
sr_pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'
for match in re.finditer(sr_pattern, instructions, re.DOTALL):
    search_text = match.group(1)
    replace_text = match.group(2)

    # Find filepath from preceding prose (same existing logic)
    block_start = match.start()
    preceding_text = instructions[max(0, block_start-500):block_start]
    filepath = self._extract_filepath_from_prose(preceding_text)

    if filepath:
        steps.append({
            'type': 'search_replace',
            'args': {
                'path': filepath,
                'search': search_text,
                'replace': replace_text
            }
        })
```

### Updated Execute Method

In `execute()`, add the new step type:

```python
elif step_type == 'search_replace':
    exec_result = self._apply_search_replace(
        step['args']['path'],
        step['args']['search'],
        step['args']['replace']
    )
```

## Implementation Plan

### Phase 1: Add search-replace method (TPM implements directly)
- Add `_apply_search_replace()` method to `task_executor.py`
- Add `search_replace` step type to `execute()` method
- Add SEARCH/REPLACE block parsing to `_extract_steps_via_regex()`
- This is SAFE: adds new code, does not modify existing code

### Phase 2: Update LLM prompt (Jr instruction)
- Modify `jr_llm_reasoner.py` prompt to instruct Qwen 32B to output SEARCH/REPLACE format
- Update `jr_planning_prompt.py` code generation prompt

### Phase 3: Post-edit validation pipeline (Jr instruction)
- Add TypeScript/JavaScript syntax validation (currently only Python)
- Add import verification for Python files
- Add file size growth cap (prevent accidental doubling)

### Phase 4: Metrics and monitoring (Jr instruction)
- Log search-replace metrics to `triad_shared_memories`
- Dashboard integration for Eagle Eye

### Phase 5: Template migration (Jr instruction)
- Update all Jr instruction templates to use SEARCH/REPLACE format
- Create template guide document

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Qwen 32B struggles with search-replace format | Medium | High | Prompt engineering + few-shot examples in prompt |
| Search text doesn't match due to whitespace | Medium | Low | Add whitespace-normalized fallback matching |
| Existing markdown code block instructions break | Low | Medium | Keep existing code block parser; add search-replace as additional format |
| task_executor.py edit causes new breakage | Low | Critical | TPM tests locally before committing; backup exists |

## Decision: Phase 1 Implementation Approach

Per Peace Chief's recommendation: **The TPM (Claude Opus 4.5 in Claude Code) implements Phase 1 directly.** This resolves the chicken-and-egg problem — we can't ask Jrs to fix the executor using a broken executor.

Phase 2-5 can be queued as Jr tasks once Phase 1 is working, since the new search-replace format will be available for those tasks to use.
