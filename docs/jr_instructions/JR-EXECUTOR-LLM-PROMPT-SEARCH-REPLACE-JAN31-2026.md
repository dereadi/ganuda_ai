# JR-EXECUTOR-LLM-PROMPT-SEARCH-REPLACE-JAN31-2026

## Metadata
- **Priority:** P1
- **Jr Type:** Engineering
- **Target Node:** sasass2 (192.168.132.200)
- **Category:** Executor Architecture — LLM Prompt Update for Search-Replace
- **Depends On:** JR-EXECUTOR-WIRE-SEARCH-REPLACE-JAN31-2026
- **Council Vote:** ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026 (7/7 APPROVE)

## Objective

Update the LLM prompts in `jr_llm_reasoner.py` and `jr_planning_prompt.py` so that Qwen 32B generates SEARCH/REPLACE format for file edits instead of raw code blocks.

**CRITICAL: This task uses ONLY bash commands with absolute paths.**

## Pre-Flight Check

```bash
# Verify search-replace is wired into executor
python3 -c "
import sys
sys.path.insert(0, '/ganuda/jr_executor')
from search_replace_editor import SearchReplaceEditor
print('OK: SearchReplaceEditor available')
"
```

```bash
# Backup files before modification
cp /ganuda/lib/jr_llm_reasoner.py /ganuda/lib/jr_llm_reasoner.py.backup_pre_sr_$(date +%Y%m%d_%H%M%S)
cp /ganuda/lib/jr_planning_prompt.py /ganuda/lib/jr_planning_prompt.py.backup_pre_sr_$(date +%Y%m%d_%H%M%S)
```

## Step 1: Update jr_llm_reasoner.py — get_code_for_step() Prompt

The current prompt asks the LLM to output a code block with `# filepath:` marker. We need to change it to request SEARCH/REPLACE format for file modifications.

```bash
# Find the current prompt in get_code_for_step
grep -n "CRITICAL: Your response MUST start with a code block" /ganuda/lib/jr_llm_reasoner.py
```

```bash
# Replace the code generation prompt section
# The old prompt says "Format your response EXACTLY like this: ```python # filepath: ..."
# Replace with search-replace format instruction
sed -i '/CRITICAL: Your response MUST start with a code block containing a filepath comment/,/Generate the complete implementation:/c\
CRITICAL RULES FOR FILE MODIFICATIONS:\
\
If you are CREATING A NEW FILE, use this format:\
```python\
# filepath: {target}\
# Complete file content here\
```\
\
If you are MODIFYING AN EXISTING FILE, use SEARCH/REPLACE blocks.\
Each block finds exact text in the file and replaces it:\
\
**File:** `{target}`\
\
<<<<<<< SEARCH\
[exact existing code to find - copy it precisely, including indentation]\
=======\
[replacement code - with your changes applied]\
>>>>>>> REPLACE\
\
Rules for SEARCH/REPLACE:\
1. The SEARCH text must match EXACTLY what exists in the file (whitespace matters)\
2. Include enough surrounding context (3-5 lines) to make the match unique\
3. Use multiple SEARCH/REPLACE blocks for multiple changes to the same file\
4. NEVER put the entire file in a SEARCH block - only the specific section to change\
5. Preserve indentation exactly as it appears in the original file\
\
Generate the implementation:' /ganuda/lib/jr_llm_reasoner.py
```

## Step 2: Update jr_planning_prompt.py — CODE_GENERATION_PROMPT

```bash
# Find the current CODE_GENERATION_PROMPT
grep -n "CODE_GENERATION_PROMPT" /ganuda/lib/jr_planning_prompt.py
```

```bash
# Add search-replace guidance to the rules section
# Find "The code must be complete and runnable" and add after it
sed -i '/The code must be complete and runnable/a\
8. For MODIFYING existing files: Use SEARCH/REPLACE blocks instead of full file content\
9. SEARCH/REPLACE format: <<<<<<< SEARCH\\n[exact old code]\\n=======\\n[new code]\\n>>>>>>> REPLACE\
10. Each SEARCH block must match exactly ONE location in the target file' /ganuda/lib/jr_planning_prompt.py
```

## Step 3: Verify Syntax

```bash
python3 -c "
import py_compile
try:
    py_compile.compile('/ganuda/lib/jr_llm_reasoner.py', doraise=True)
    print('PASS: jr_llm_reasoner.py syntax valid')
except py_compile.PyCompileError as e:
    print(f'FAIL: {e}')

try:
    py_compile.compile('/ganuda/lib/jr_planning_prompt.py', doraise=True)
    print('PASS: jr_planning_prompt.py syntax valid')
except py_compile.PyCompileError as e:
    print(f'FAIL: {e}')
"
```

## Rollback (manual only — do NOT execute automatically)

To undo: restore from the backups created in pre-flight:
- `cp $(ls -t /ganuda/lib/jr_llm_reasoner.py.backup_pre_sr_* | head -1) /ganuda/lib/jr_llm_reasoner.py`
- `cp $(ls -t /ganuda/lib/jr_planning_prompt.py.backup_pre_sr_* | head -1) /ganuda/lib/jr_planning_prompt.py`
