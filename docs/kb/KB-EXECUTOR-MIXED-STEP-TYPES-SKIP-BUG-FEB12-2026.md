# KB: Executor Skips SEARCH/REPLACE When Mixed with Create Blocks

**Date**: February 12, 2026
**Jr Tasks**: #713, #714, #715 (all partial — only Create step executed)
**River Cycle**: RC-2026-02A

## Bug

When a Jr instruction file contains BOTH `Create` blocks (new file creation) AND `<<<<<<< SEARCH` / `>>>>>>> REPLACE` blocks, the executor only processes the first Create block and reports "1/1 steps succeeded". All SEARCH/REPLACE blocks are silently skipped.

## Evidence

| Task | Instruction Steps | Executed | Skipped |
|------|-------------------|----------|---------|
| #713 | 3 SEARCH/REPLACE + 1 Create | Create only (credential_migration.py) | 3 SEARCH/REPLACE |
| #714 | 1 Create + 2 SEARCH/REPLACE | Create only (create_dlq_table.py) | 2 SEARCH/REPLACE |
| #715 | 1 Create + 2 SEARCH/REPLACE | Create only (create_checkpoint_tables.py) | 2 SEARCH/REPLACE |

## Root Cause (Suspected)

The executor's step parser finds the first Python code fence (the Create block) and treats it as the complete task. The `<<<<<<< SEARCH` / `=======` / `>>>>>>> REPLACE` markers inside subsequent code fences are not parsed as additional steps.

This may be a step extraction issue in `task_executor.py` — the regex or parser that identifies steps from the instruction markdown likely stops after finding the first valid code block.

## Workaround

**One instruction per edit operation.** Never mix Create blocks and SEARCH/REPLACE blocks in the same instruction file.

Recursive approach: If a multi-step instruction partially executes, re-queue the skipped steps as individual single-operation instructions.

## Fix Needed

Investigate the step extraction logic in `task_executor.py` (likely in the `_parse_instruction_file()` or equivalent method). The parser needs to:
1. Extract ALL code blocks from the markdown
2. Classify each as Create vs SEARCH/REPLACE
3. Execute them in order

## Related

- KB-JR-INSTRUCTION-FORMAT-REGEX-COMPATIBILITY-FEB08-2026 (SEARCH/REPLACE format spec)
- Jr #692 (earlier DLQ attempt, failed on SEARCH_NOT_FOUND — different bug, same area)
