# Jr Instruction: PM Jr Training — Task Decomposition Standards

**Ticket**: PM-JR-001
**Council Vote**: Turtle slate vote, 5-2
**Estimated SP**: 5
**Assigned**: TPM
**Depends On**: None

---

## Objective

Standardize how Jr tasks are decomposed. After 1,418 Jr instructions and 188 completed tasks, patterns have emerged for what works and what fails. This instruction codifies those patterns into a template library and quality rubric so that future Jr instructions are consistent, executable, and verifiable.

This is a TRAINING artifact — it creates templates and documentation, not runtime code.

## Problem Statement

Current Jr task quality varies because:
1. No standard template — instructions range from 20 lines to 400 lines
2. Step headers inconsistent — `### Step 1:`, `## Step 1`, `Phase 1:`, `Implementation:` all used
3. Verification criteria often missing — Jr completes steps but can't prove they worked
4. Risk assessment ad hoc — some instructions have rollback plans, most don't
5. `decompose_task()` in sub_agent_dispatch.py exists but isn't called in the main executor
6. Specification layer (project_specifications table) underutilized — only 3 specs exist

## Implementation

### Step 1: Create Template Library

Create `/ganuda/docs/jr_templates/` directory with these templates:

**`/ganuda/docs/jr_templates/TEMPLATE-CODE-CHANGE.md`**:
```markdown
# Jr Instruction: [TITLE]

**Ticket**: [TICKET-ID]
**Council Vote**: [vote hash, confidence, outcome]
**Estimated SP**: [number]
**Assigned**: [specialist or Jr type]
**Depends On**: [ticket IDs or "None"]

---

## Objective

[2-3 sentences: what this task accomplishes and why it matters]

## Current State

[What exists today. File paths, line numbers, current behavior.]

## Implementation

### Step 1: [Verb] [Object]

**File**: `[absolute path]`

[Description of change]

<<<<<<< SEARCH
[exact text to find — include enough context for unique match]
=======
[replacement text]
>>>>>>> REPLACE

### Step 2: [Verb] [Object]

[repeat pattern]

## Verification

1. [Specific test command or query]
2. [Expected output or assertion]
3. [Regression check — verify nothing else broke]

## Rollback

[How to undo this change if verification fails]

## What NOT To Do

- [Specific anti-pattern relevant to this task]
```

**`/ganuda/docs/jr_templates/TEMPLATE-SQL-MIGRATION.md`**:
```markdown
# Jr Instruction: [TITLE]

**Ticket**: [TICKET-ID]
**Estimated SP**: [number]
**Target DB**: [bluefin/zammad_production or specific database]

---

## Objective

[What this migration accomplishes]

## Pre-Flight

```sql
-- Verify current state before migration
[SELECT query showing current state]
```

## Migration

### Step 1: [Create/Alter/Insert]

```sql
[SQL statement]
```

### Step 2: [repeat]

## Verification

```sql
-- Verify migration succeeded
[SELECT query showing new state]
```

## Rollback

```sql
-- Undo migration if needed
[DROP/ALTER/DELETE statements]
```

## What NOT To Do

- Do NOT run on production without pre-flight check
- Do NOT drop columns without backing up data first
```

**`/ganuda/docs/jr_templates/TEMPLATE-SERVICE-DEPLOY.md`**:
```markdown
# Jr Instruction: [TITLE]

**Ticket**: [TICKET-ID]
**Estimated SP**: [number]
**Target Node**: [redfin/bluefin/greenfin/etc]
**Port**: [service port]

---

## Objective

[What service is being deployed and why]

## Prerequisites

- [ ] Code exists at [path]
- [ ] Dependencies installed: [list]
- [ ] Config in place: [config file path]
- [ ] Port [NNNN] not in use

## Implementation

### Step 1: Create systemd unit file

**File**: `/etc/systemd/system/[service-name].service`

```ini
[Unit]
Description=[Service description]
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=[path]
ExecStart=[command]
Restart=on-failure
RestartSec=5
Environment=[KEY=VALUE]

[Install]
WantedBy=multi-user.target
```

### Step 2: Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable [service-name]
sudo systemctl start [service-name]
```

### Step 3: Add to Fire Guard

In `/ganuda/scripts/fire_guard.py`, add health check for port [NNNN].

## Verification

```bash
# Service running
systemctl is-active [service-name]

# Health endpoint
curl -s http://localhost:[PORT]/health | python3 -m json.tool

# Logs clean
journalctl -u [service-name] --no-pager -n 20
```

## Rollback

```bash
sudo systemctl stop [service-name]
sudo systemctl disable [service-name]
```
```

**`/ganuda/docs/jr_templates/TEMPLATE-RESEARCH.md`**:
```markdown
# Jr Instruction: [TITLE]

**Ticket**: [TICKET-ID]
**Estimated SP**: [number]
**Assigned**: [Raven/Deer/specialist]

---

## Objective

[What question are we answering and why it matters to the federation]

## Research Scope

- **Sources**: [arxiv, web, thermal memory, codebase]
- **Time budget**: [max hours or token budget]
- **Output format**: [thermal entry, Jr instruction, ultrathink doc, blog post]

## Research Questions

1. [Specific question]
2. [Specific question]
3. [Specific question]

## Deliverables

1. [Thermal memory entry with tags and temperature]
2. [Summary document at path]
3. [Council briefing if findings warrant architectural change]

## What NOT To Do

- Do NOT thermalize raw paper abstracts — synthesize into federation context
- Do NOT exceed time budget — partial findings are better than none
- Do NOT recommend architectural changes without council vote
```

### Step 2: Create Quality Rubric

Create `/ganuda/docs/jr_templates/QUALITY-RUBRIC.md`:

```markdown
# Jr Instruction Quality Rubric

Score each instruction 0-2 per criterion. Minimum 8/14 to submit.

| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| **Objective** | Missing or vague | Present but no "why" | Clear what AND why |
| **Steps** | No step headers | Inconsistent headers | `### Step N: [Verb] [Object]` |
| **File paths** | Relative or missing | Absolute but no line refs | Absolute with line numbers |
| **SEARCH/REPLACE** | Prose description only | Partial diff blocks | Complete SEARCH/REPLACE blocks |
| **Verification** | None | "Check it works" | Specific commands with expected output |
| **Rollback** | None | "Undo the changes" | Specific reversal steps |
| **What NOT To Do** | None | Generic warnings | Task-specific anti-patterns |

### Step Header Standard

ALWAYS use: `### Step N: [Verb] [Object]`

Examples:
- `### Step 1: Add search terms to SEARCH_QUERIES list`
- `### Step 2: Create systemd unit file`
- `### Step 3: Verify noise ratios after 7 days`

NOT:
- `## Implementation` (too vague)
- `Phase 1:` (not parseable by recursive_decomposer)
- `Step 1` without `###` (won't match regex extraction)

### Maximum Steps

- **Target**: 3-7 steps per instruction
- **Hard limit**: 10 steps — if more needed, decompose into sub-tasks with parent_task_id linkage
- **Minimum**: 1 step — but if only 1 step, consider whether a Jr instruction is overkill
```

### Step 3: Create Decomposition Guide

Create `/ganuda/docs/jr_templates/DECOMPOSITION-GUIDE.md`:

```markdown
# Task Decomposition Guide

## When to Decompose

| Total SP | Action |
|----------|--------|
| 1-3 | Single Jr instruction, 1-5 steps |
| 5-8 | Single Jr instruction, 5-7 steps, OR 2 linked instructions |
| 8-13 | 2-3 linked Jr instructions with blocking dependencies |
| 13-21 | Epic with 3-5 Jr instructions, council review required |
| 21+ | Break into multiple epics first |

## Dependency Types

- **Blocking**: Task B cannot start until Task A completes. Use `Depends On: [TASK-A-ID]`
- **Informing**: Task B benefits from Task A's output but can proceed without it. Note in description, don't block
- **Independent**: No relationship. Can execute in parallel

## Decomposition Checklist

Before submitting a Jr instruction:
1. Can each step be executed independently? (If step 3 needs step 2's output, is that explicit?)
2. Are file paths absolute? (`/ganuda/lib/foo.py`, not `lib/foo.py`)
3. Does verification prove the task succeeded, not just that it ran?
4. If this task fails, does the rollback leave the system in a known state?
5. Is SP estimate realistic? (1 SP ≈ 1-2 hours of Jr work including verification)

## Common Decomposition Mistakes

1. **God instruction**: 15+ steps, 400 lines, tries to do everything. Break it up.
2. **Orphan steps**: Step 4 creates a file that nothing references. Why?
3. **Implicit dependencies**: Step 3 assumes step 2's database migration ran. Make it explicit.
4. **Missing verification**: "Deploy the service" with no health check.
5. **Wrong granularity**: A 1 SP task split into 5 sub-tasks. Overhead > work.
```

### Step 4: Wire decompose_task() into Task Executor

In `/ganuda/jr_executor/task_executor.py`, the `_extract_steps_from_instructions()` method uses regex to find step headers. Verify it matches the standard header format:

```python
# Ensure this regex matches: ### Step N: [description]
step_pattern = r'###\s+Step\s+(\d+)[:\s]+(.+)'
```

If the current regex is different, update it to match the standard. Do NOT change the function signature or return type.

## Verification

1. **Templates exist**: `ls /ganuda/docs/jr_templates/` shows 4 templates + rubric + guide
2. **Rubric scoring**: Score 3 recent Jr instructions against the rubric. Note gaps
3. **Step header regex**: Verify `_extract_steps_from_instructions()` parses `### Step N: [text]` correctly
4. **Template usability**: Write one new Jr instruction using TEMPLATE-CODE-CHANGE.md. Verify it's faster and more consistent than freeform

## Acceptance Criteria

1. Four templates exist (code-change, sql-migration, service-deploy, research)
2. Quality rubric exists with scoring criteria
3. Decomposition guide exists with SP-based sizing
4. Step header format standardized across templates
5. Task executor regex matches standard format

## What NOT To Do

- Do NOT retroactively reformat 1,418 existing instructions — too much churn, too little value
- Do NOT make templates mandatory for trivial tasks (<2 SP) — overhead not worth it
- Do NOT add template validation to the executor — templates are guidance, not enforcement
- Do NOT create a "Jr training course" — learn by doing, templates are the rails
