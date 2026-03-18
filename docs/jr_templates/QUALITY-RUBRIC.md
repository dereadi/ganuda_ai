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

## Step Header Standard

ALWAYS use: `### Step N: [Verb] [Object]`

Examples:
- `### Step 1: Add search terms to SEARCH_QUERIES list`
- `### Step 2: Create systemd unit file`
- `### Step 3: Verify noise ratios after 7 days`

NOT:
- `## Implementation` (too vague)
- `Phase 1:` (not parseable by recursive_decomposer)
- `Step 1` without `###` (won't match regex extraction)

## Maximum Steps

- **Target**: 3-7 steps per instruction
- **Hard limit**: 10 steps — if more needed, decompose into sub-tasks with parent_task_id linkage
- **Minimum**: 1 step — but if only 1 step, consider whether a Jr instruction is overkill
