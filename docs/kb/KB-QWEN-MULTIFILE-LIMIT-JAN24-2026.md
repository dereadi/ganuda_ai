# KB Article: Qwen2.5-Coder-32B Multi-File Task Limit

**KB ID:** KB-QWEN-MULTIFILE-001
**Date:** January 24, 2026
**Category:** Research / Task Design
**Model:** Qwen2.5-Coder-32B-AWQ

---

## Executive Summary

**Maximum reliable files per task: 2-3**

Tasks requesting 4+ file modifications have inconsistent success rates (33-67%). Break complex multi-file work into chunks of ≤3 files.

---

## Experiment Results

| Files per Task | Success Rate | Recommendation |
|----------------|--------------|----------------|
| 1 | 100% | ✅ Always safe |
| 2 | 100% | ✅ Always safe |
| 3 | ~80% | ✅ Recommended max |
| 4 | 67% | ⚠️ Risky |
| 6 | 33% | ❌ Avoid |
| 8 | 67% | ❌ Avoid |
| 12 | 33% | ❌ Avoid |

---

## Task Decomposition Pattern

### Before (Will Fail ~67% of time)
```
Task: Update 12 files to use centralized config
- wizard.py
- research.py
- export.py
- family.py
- workbench.py
- conditions.py
- evidence_analysis.py
- rag.py
- evidence_service.py
- rag_ingestion.py
- rag_query.py
- database.py
```

### After (Reliable)
```
Task 1: Update wizard.py, research.py, export.py (3 files)
Task 2: Update family.py, workbench.py, conditions.py (3 files)
Task 3: Update evidence_analysis.py, rag.py, evidence_service.py (3 files)
Task 4: Update rag_ingestion.py, rag_query.py, database.py (3 files)
```

---

## Why Multi-File Fails

1. **Output format confusion**: Model struggles to clearly separate multiple file outputs
2. **Context tracking**: Loses track of which file it's generating after 3-4 files
3. **Syntax validation**: Single syntax error in any file fails the whole task
4. **Incomplete generation**: Often generates first few files completely, truncates later ones

---

## Jr Instruction Template for Multi-File Tasks

When creating Jr instructions that modify multiple files:

```markdown
## Files to Modify (MAX 3)

1. `/path/to/file1.py` - Brief description of change
2. `/path/to/file2.py` - Brief description of change
3. `/path/to/file3.py` - Brief description of change

## Change Pattern

For each file, make this specific change:
[Clear, unambiguous instruction]

## Output Format

Generate each file with clear separator:
# FILE: /path/to/file.py
<complete file content>
```

---

## Thermal Memory Integration

This finding should be checked when:
- Creating Jr instructions with multiple file modifications
- Task executor encounters multi-file failures
- TPM reviews task decomposition

Query: `multifile limit 3 files task decomposition`

---

## Related KB Articles

- KB-QWEN-CONTEXT-001: Context size limits (12K+ chars OK)
- KB-JR-COMPLEX-001: Task complexity patterns

---

**FOR SEVEN GENERATIONS** - Small batches, reliable results.
