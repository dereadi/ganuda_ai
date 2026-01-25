# KB: JR Execution System Learnings
## KB-JR-EXEC-001
## Date: January 21, 2026
## Cherokee AI Federation

---

## Executive Summary

Comprehensive learnings from JR task execution debugging session. Key findings on instruction format, context limits, and infrastructure capabilities.

---

## Critical Finding 1: Instruction Format

### Problem
JR tasks marked "completed" without creating files.

### Root Cause
Regex extraction in `task_executor.py` requires exact patterns.

### Supported Patterns (MUST USE)
```markdown
Create `/path/to/file.py`:
```python
code here
```

**File:** `/path/to/file.py`
```python
code here
```

Modify: `/path/to/file.py`
```python
code here
```
```

### UNSUPPORTED (Will NOT Extract)
```markdown
Create file `/path/to/file.py`:     # Extra word "file"
### Create the file /path/to/file   # Markdown header
Create /path/to/file:               # No backticks
```

### Fix
Always use: `Create \`/path/file\`:` with backticks, no extra words.

---

## Critical Finding 2: Context Overflow

### Problem
Tasks fail with "maximum context length is 32000 tokens" error.

### Root Cause
Large instruction files (400+ lines) + system prompt + existing file content exceed 32K.

### Solutions

| Solution | Approach | When to Use |
|----------|----------|-------------|
| **Chunking** | Break into smaller tasks | Default approach |
| **bmasass** | Use M4 Max (72B, 128K context) | Complex tasks |
| **Summarize** | Compress instructions | Medium tasks |

### Chunking Guidelines
- Keep instructions under 150 lines
- One file per instruction (ideally)
- Split multi-file tasks into sequential JRs

---

## Critical Finding 3: Security Escalation

### Problem
Tasks fail with "File type requires Chief approval"

### Root Cause
`task_executor.py` has `ESCALATE_FILE_TYPES` list:
- `.service` (systemd)
- `.conf` (config files)
- `.cron` (cron jobs)
- `.sudoers` (sudo config)

### Solution
TPM/Chief must manually create these files or approve escalation.

---

## Critical Finding 4: Frontend Files

### Problem
JRs mark TypeScript (.tsx) files as complete without modification.

### Hypothesis
- TypeScript parsing may differ from Python
- File permissions issues
- Path resolution problems

### Workaround
- Manual verification required for frontend files
- Consider dedicated frontend JR with TypeScript tooling

---

## Infrastructure Capabilities

### Inference Nodes

| Node | Hardware | Model Capacity | Context |
|------|----------|----------------|---------|
| redfin | RTX 6000 96GB | 32B (Qwen-AWQ) | 32K |
| bmasass | M4 Max 128GB | **72B** | **128K** |
| sasass | Mac Studio 64GB | 7-14B | 32K |
| sasass2 | Mac Studio 64GB | 7-14B | 32K |

### Recommendation
Route complex/large tasks to **bmasass** (72B model, 128K context).

---

## RLM Bootstrap Implementation

Successfully implemented thermal memory bootstrap for TPM context persistence.

### Files Created
- `/ganuda/lib/rlm_bootstrap.py` - Queries thermal_memory_archive
- `/ganuda/scripts/update_claude_context.sh` - Updates CLAUDE.md

### Usage
```bash
# Run at session start
/ganuda/scripts/update_claude_context.sh
```

### Bootstrap Output Includes
- Federation stats (memories, JR tasks, kanban)
- Failed tasks needing attention
- Recent sacred memories (key context)

---

## Metrics

### JR Task Execution (Jan 21, 2026)

| Metric | Value |
|--------|-------|
| Tasks Queued | 12 |
| Completed Successfully | 7 |
| False Completions | 2 |
| Failed (Context) | 2 |
| Failed (Escalation) | 1 |
| **Success Rate** | **58%** |

### Files Successfully Created
1. `/ganuda/lib/rlm_bootstrap.py`
2. `/ganuda/scripts/update_claude_context.sh`
3. `/ganuda/vetassist/backend/app/ml/crisis_detector.py`
4. `/Users/Shared/ganuda/services/mlx_inference.py`

---

## Action Items

1. [ ] Update JR instruction templates to use correct format
2. [ ] Setup bmasass as primary inference node for complex tasks
3. [ ] Create frontend-specialized JR
4. [ ] Add instruction format validation before queueing
5. [ ] Implement Chief approval workflow for .conf files

---

## References

- Task Executor: `/ganuda/jr_executor/task_executor.py`
- Instruction Parser: `/ganuda/jr_executor/instruction_parser.py`
- JR Queue Worker: `/ganuda/jr_executor/jr_queue_worker.py`

---

*Cherokee AI Federation - Learning from every execution*
*For Seven Generations*
