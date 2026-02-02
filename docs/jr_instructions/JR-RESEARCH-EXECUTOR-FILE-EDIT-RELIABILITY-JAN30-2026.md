# JR-RESEARCH-EXECUTOR-FILE-EDIT-RELIABILITY-JAN30-2026

## Metadata
- **Priority:** P0
- **Jr Type:** Research
- **Target Node:** Any
- **Category:** Architecture Research — Jr Executor File Edit Reliability

## Research Objective

The Jr task executor has a critical reliability gap: **it cannot safely edit existing files.** Out of 11 tasks in the Jan 30 sprint, every task that required modifying an existing Python or TypeScript file either failed or caused damage. Tasks that created new database tables or resources succeeded.

**Your job:** Research how other agentic coding systems solve reliable file editing, analyze our specific failure modes, and propose concrete solutions the council can evaluate.

## Failure Data (From Sprint Jan 30, 2026)

### Failure Mode 1: File Truncation (Catastrophic)
- **Task #488** reported "completed" but truncated `task_executor.py` from 2164 lines to 181 lines
- **Task #484** created incomplete try block, syntax check caught it but partial write already damaged file
- The executor wrote a small code snippet and it replaced the entire file content
- **Root cause hypothesis:** The file write operation replaces the entire file rather than inserting at a specific location

### Failure Mode 2: Guardrail Blocks (Protective but Unproductive)
- **Task #482** tried to edit `__init__.py` (134 lines) but the proposed content was only 11 lines → guardrail blocked it as ">50% loss"
- **Task #487** tried to edit `task_executor.py` (182 lines at that point) with 7 lines → guardrail blocked
- **Root cause hypothesis:** The Jr generates the NEW content but not the surrounding EXISTING content, so the write operation looks like a replacement

### Failure Mode 3: Indentation Corruption
- **Task #489** edited `user.py`, introduced IndentationError at line 89
- **Task #490** edited `va_auth.py`, introduced IndentationError in `va_oauth_service.py` at line 155
- **Root cause hypothesis:** Partial edit insertion doesn't preserve the indentation context of the surrounding code

### Failure Mode 4: Wrong Working Directory
- **Task #483** ran `sed -i 's/claim_id: int/claim_id: str/g' app/api/v1/endpoints/workbench.py` but the file wasn't at that relative path from the executor's working directory
- **Root cause hypothesis:** Instructions use relative paths, executor runs from a different directory

### What Works Reliably
- SQL operations (CREATE TABLE, INSERT, ALTER TABLE)
- New file creation (when the file doesn't exist yet)
- Bash commands (when paths are absolute)
- Web research and content fetching

## Research Questions

### Q1: How do other agentic coding systems handle file edits?

Research these systems and their approaches:
- **Aider** (https://aider.chat) — How does it handle code edits? What edit format does it use?
- **OpenHands/OpenDevin** — How does it modify existing files?
- **SWE-Agent** (Princeton) — What edit action space does it use?
- **Cursor/Windsurf** — How do IDE-integrated agents apply code changes?
- **Claude Code** (Anthropic) — How does it handle the edit/apply cycle?

For each, document:
- Edit format (whole file replacement, diff/patch, search-and-replace, AST manipulation)
- Validation approach (syntax check before/after, diff review)
- Rollback strategy (backup, git, undo)
- Success rate data if available

### Q2: What edit formats have the highest reliability?

Compare these approaches:
1. **Whole file replacement** — Generate entire new file content (our current approach, causes truncation)
2. **Search-and-replace blocks** — Find exact string, replace with new string (Aider's approach)
3. **Unified diff/patch** — Generate standard diff, apply with `patch` command
4. **Line-range insertion** — Specify "insert after line N" or "replace lines N-M"
5. **AST-based edits** — Parse to AST, modify nodes, regenerate code (preserves formatting)
6. **Marker-based insertion** — Use unique comment markers (e.g., `# EDIT_POINT_001`) as anchors

### Q3: What validation pipeline prevents silent corruption?

Research best practices for:
- Pre-edit file hash capture
- Post-edit syntax validation (AST parse)
- Post-edit semantic validation (import check, test run)
- Automatic rollback on validation failure
- File size sanity checks (our guardrail catches >50% loss, but what about growth?)

### Q4: What is the minimum viable fix for our executor?

Given our current architecture (`task_executor.py`, 2164 lines, Python, uses Qwen 32B for LLM reasoning):
- What is the smallest change that would make file edits reliable?
- Can we implement search-and-replace as the primary edit mode?
- Should we use `diff` + `patch` instead of direct file writes?
- Should the LLM generate the diff rather than the full file content?

## Deliverables

Write a research report to `/ganuda/docs/reports/RESEARCH-EXECUTOR-FILE-EDIT-RELIABILITY-JAN30-2026.md` containing:

1. **Comparison table** of how 5+ agentic coding systems handle file edits
2. **Ranked list** of edit format approaches by estimated reliability
3. **Proposed solution** for our executor (specific, implementable, with code examples)
4. **Risk assessment** for each approach
5. **Recommended implementation order** (what to fix first for maximum impact)

## Constraints

- This is a RESEARCH task — do NOT modify any code files
- Do NOT edit task_executor.py or any executor code
- Write findings to the report file only
- Use web search to gather information about the systems listed above
