# ULTRATHINK: Jr Executor 95% Solution — Why Tasks Fail and How to Fix Them

**Date:** 2026-02-03
**Author:** TPM (Claude Opus 4.5)
**Trigger:** Tasks #547-553 all exhibited false completion — files went to staging, content was hallucinated, success reported falsely
**Council Vote:** 38a517d5c204a4e7 (7/7 approve architecture upgrade)
**Objective:** Achieve 95%+ true task completion rate

---

## The Failure We Keep Watching

Every Jr task we've monitored in the last 48 hours follows the same pattern:

1. Task queued with detailed instruction file
2. Worker picks up task, sends to RLM executor
3. LLM generates code — but generates WRONG code
4. RLM executor's path protection catches the target files
5. Files go to staging instead of target paths
6. Worker reports `success=True` because `files_staged > 0`
7. TPM discovers actual files untouched, staging contains hallucinated garbage

**Observed on:** Tasks #547, #548, #550, #551 (and likely #552, #553)

---

## The Six Root Causes (Ordered by Impact)

### Root Cause 1: THE LLM GENERATES FROM SCRATCH, NOT FROM EXISTING CODE

**This is the #1 cause of failure.**

When we say "Modify `/ganuda/jr_executor/jr_queue_client.py` — replace `get_pending_tasks()`", the instruction file contains the exact new code. But the LLM doesn't receive the EXISTING file as context. It generates a brand new file from scratch.

**Evidence:** Task #550 staged `jr_queue_client.py` — 34 lines, uses `self.db_config` (wrong pattern), references a `tasks` table (doesn't exist). The actual file is 311 lines using `DB_CONFIG` dict and references `jr_work_queue` table.

Task #550 staged `jr_queue_worker.py` — 23 lines, imports Celery and uses Redis broker. **We don't use Celery. We don't use Redis.** The actual file is 199 lines using a custom poll-based worker loop.

The LLM read the instruction's CONCEPTS (atomic locking, worker lifecycle) and hallucinated generic implementations instead of modifying the real files.

**Where in code:** `rlm_executor.py:294-343` — `_build_execution_prompt()` builds the LLM prompt with task instructions but NEVER includes existing file contents. The prompt says "Generate the complete file contents" which tells the LLM to write from scratch.

### Root Cause 2: STAGING COUNTED AS SUCCESS

The success condition in `rlm_executor.py` treats staged files the same as created files:

```python
# Line 247
actual_success = (files_created + files_staged) > 0
```

```python
# Line 807
files_created = len([a for a in artifacts if a.get('type') in ('file_created', 'file_staged')])
```

Staging means the file was BLOCKED from the target path. That is NOT success — it's a controlled failure. The file was not deployed. The task is not done.

The worker's P0 validation (line 128) checks `steps and artifacts and files_created` — but `files_created` includes staged files, so the validation passes.

### Root Cause 3: jr_executor/*.py IS PROTECTED WITH NO OVERRIDE

`rlm_protected_paths.yaml` line 32:
```yaml
- "/ganuda/jr_executor/*.py"
```

The `allowed_overrides` section only covers VetAssist backend paths. There is NO override for `jr_executor/*.py`. So every task that modifies the executor itself will ALWAYS be staged, ALWAYS.

This is correct from a safety perspective — Jrs should not modify their own executor. But it means Jr instructions to upgrade the executor are STRUCTURALLY IMPOSSIBLE to complete via the Jr system.

**This is a category error, not a technical bug.** We wrote Jr instructions for tasks that Jrs cannot perform.

### Root Cause 4: THE CHICKEN-AND-EGG PROBLEM

The task "fix worker contention in jr_queue_client.py" requires modifying `jr_queue_client.py`. But `jr_queue_client.py` is loaded by the worker at process startup. Even if the Jr DID write the file correctly:

- The currently running worker loaded the OLD code
- The new code wouldn't take effect until worker restart
- If the new code has a bug, the worker dies and can't process the fix

Self-referential modification through the system being modified is inherently fragile.

### Root Cause 5: NO CONTENT QUALITY VALIDATION

When the LLM generates a 34-line replacement for a 311-line file, nothing catches this. The existing "destructive overwrite" check (`rlm_executor.py:506-523`) blocks overwrites where `existing_size > new_size * 2`, but this only applies to files that PASS protection checks. Protected files are staged before this check runs.

Even for non-protected files, there's no validation that:
- The generated code imports the correct modules
- The generated code references correct table/column names
- The generated code follows the existing patterns in the file
- The generated code is syntactically and semantically correct for the codebase

### Root Cause 6: DUAL-MODEL STILL HALLUCINATES FILE STRUCTURE

The dual-model approach (PM + Coder, `rlm_executor.py:731-827`) was added Jan 28 to fix "0 files created." It improved FILE EXTRACTION (patterns 1-8 for parsing), but the Coder model still generates from scratch without existing-file context. The PM creates a plan, the Coder generates new files — neither reads the files being "modified."

---

## The Interaction Effects

These root causes compound each other in a deadly cascade:

```
Instruction says "Modify file X"
    → LLM doesn't see file X's contents (RC1)
    → LLM generates file X from scratch (wrong patterns, wrong tables, wrong framework)
    → RLM executor sees path is protected (RC3)
    → File goes to staging (not target)
    → Staging counted as success (RC2)
    → Worker reports "completed" (RC2)
    → TPM discovers garbage in staging
    → Even if we merge staging → target, the content is WRONG (RC1)
    → Even if content were right, worker is stale and won't use it (RC4)
```

Every layer of protection (path checking, staging, validation) is working as designed, but the FUNDAMENTAL FAILURE — wrong content — means even perfect deployment infrastructure would deploy broken code.

---

## The 95% Solution: Five Interventions

### Intervention 1: TPM DEPLOYS SELF-REFERENTIAL CHANGES (Immediate — Eliminates RC3, RC4)

**Tasks that modify the Jr executor, queue client, queue worker, or RLM executor must be deployed by the TPM directly, not through the Jr system.**

This is not a workaround — it's the correct architectural boundary. A factory robot doesn't upgrade its own firmware while running.

**Implementation:**
- TPM writes the code changes directly (or reviews staging and applies manually)
- Jr instructions for executor changes become TPM WORK ORDERS, not Jr tasks
- The `jr_executor/*.py` protection pattern stays — it's correct
- TPM deploys, then restarts workers: `sudo systemctl restart jr-queue-worker`

**Success rate impact:** Eliminates 100% of self-referential failures (tasks #550-553 and any future executor tasks).

### Intervention 2: INJECT EXISTING FILE CONTENTS INTO LLM PROMPT (P0 — Fixes RC1, RC6)

**When the instruction says "Modify file X", the LLM must see file X's current contents.**

Modify `rlm_executor.py` `_build_execution_prompt()` to:
1. Parse `files_to_modify` from the task
2. Read each file's current contents
3. Include them in the prompt as "CURRENT FILE CONTENTS"

```python
# In _build_execution_prompt():
existing_files_context = ""
for filepath in task.get('files_to_modify', []):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        existing_files_context += f"\n--- CURRENT CONTENTS OF {filepath} ---\n{content}\n--- END ---\n"

# Add to prompt:
"""
{existing_files_context}

IMPORTANT: You are MODIFYING existing files, not creating new ones.
Preserve all existing code structure, imports, class names, and patterns.
Only change the specific parts described in the instructions.
Output the COMPLETE modified file contents.
"""
```

**Success rate impact:** Eliminates the #1 failure mode. LLM sees the actual code and can make targeted modifications instead of hallucinating from scratch.

**Risk:** Long files may exceed Qwen 32B's context window (32K tokens). Mitigate by truncating to most relevant sections or summarizing.

### Intervention 3: STAGING ≠ SUCCESS (P0 — Fixes RC2)

**Staged files must NOT count toward success.**

Change in `rlm_executor.py`:

```python
# Line 247: Change from
actual_success = (files_created + files_staged) > 0
# To
actual_success = files_created > 0

# Line 807: Change from
files_created = len([a for a in artifacts if a.get('type') in ('file_created', 'file_staged')])
# To
files_created = len([a for a in artifacts if a.get('type') == 'file_created'])
files_staged = len([a for a in artifacts if a.get('type') == 'file_staged'])
```

Add a new result status for staged-only outcomes:

```python
if files_staged > 0 and files_created == 0:
    result["success"] = False
    result["status"] = "staged_for_review"
    result["error"] = f"All {files_staged} file(s) were staged (protected paths). TPM review required."
```

Worker should mark these as `blocked` instead of `completed`:

```python
# In jr_queue_worker.py, after result check:
if result.get('status') == 'staged_for_review':
    self.client.block_task(task['id'], f"Files staged for TPM review: {result.get('files_staged', 0)} file(s)")
```

**Success rate impact:** Eliminates false positives entirely. Tasks that need TPM review are correctly flagged.

### Intervention 4: CONTENT QUALITY GATE (P1 — Fixes RC5)

Before writing a file (or staging it), validate the generated content against the existing file:

```python
def _validate_generated_content(self, file_path, new_content, task):
    """Validate LLM-generated content before writing."""
    issues = []

    if os.path.exists(file_path):
        with open(file_path) as f:
            existing = f.read()

        # Size regression check
        if len(new_content) < len(existing) * 0.3:
            issues.append(f"Size regression: {len(new_content)} bytes vs {len(existing)} existing")

        # Import preservation check (Python files)
        if file_path.endswith('.py'):
            existing_imports = set(re.findall(r'^(?:import|from)\s+\S+', existing, re.MULTILINE))
            new_imports = set(re.findall(r'^(?:import|from)\s+\S+', new_content, re.MULTILINE))
            lost_imports = existing_imports - new_imports
            if len(lost_imports) > len(existing_imports) * 0.5:
                issues.append(f"Lost {len(lost_imports)} imports: {list(lost_imports)[:3]}")

        # Class/function preservation check
        existing_defs = set(re.findall(r'(?:def|class)\s+(\w+)', existing))
        new_defs = set(re.findall(r'(?:def|class)\s+(\w+)', new_content))
        lost_defs = existing_defs - new_defs
        if lost_defs and len(lost_defs) > len(existing_defs) * 0.3:
            issues.append(f"Lost definitions: {lost_defs}")

    return issues
```

**Success rate impact:** Catches LLM hallucination before files are written. ~20% of remaining failures.

### Intervention 5: WORKER RESTART AFTER EXECUTOR DEPLOYMENT (Operational — Fixes RC4)

After any TPM deployment to `jr_executor/*.py`:

```bash
sudo systemctl restart jr-queue-worker
```

Add this to a TPM deployment checklist. The Jr instruction system can't do this itself (it's a systemd operation requiring sudo). This is TPM operational responsibility.

---

## Success Rate Projection

| Intervention | Failure Mode Eliminated | Est. Impact |
|---|---|---|
| 1. TPM deploys executor changes | Self-referential impossibility | +30% |
| 2. Inject existing file contents | LLM generates from scratch | +35% |
| 3. Staging ≠ success | False positive completions | +15% |
| 4. Content quality gate | Hallucinated garbage deployed | +10% |
| 5. Worker restart after deploy | Stale code | +5% |
| **Total** | | **~95%** |

The remaining 5% comes from:
- LLM context window overflow on very large files
- Tasks with ambiguous instructions that confuse the LLM
- Intermittent vLLM inference failures
- Edge cases in partial edit detection

---

## Implementation Plan

### Phase A: Immediate TPM Action (Today)

1. **TPM deploys P0 task locking directly** — Apply the changes from the Jr instruction file to the actual `jr_queue_client.py` and `jr_queue_worker.py` manually
2. **Restart all Jr workers** — `sudo systemctl restart jr-queue-worker`
3. **Reset tasks #550-553** back to pending after deployment

### Phase B: Code Changes (Jr Instruction — non-self-referential)

1. **Modify `rlm_executor.py`** — Inject existing file context into LLM prompt (Intervention 2)
2. **Modify `rlm_executor.py`** — Change staging ≠ success (Intervention 3)
3. **Add content quality gate to `rlm_executor.py`** (Intervention 4)

**IMPORTANT:** These changes to `rlm_executor.py` are ALSO self-referential (modifying the executor). The TPM must deploy these directly too. After these changes land, FUTURE non-executor tasks will benefit from the improvements.

### Phase C: Operational (Ongoing)

1. Any task modifying `jr_executor/*.py` or `lib/rlm_executor.py` → TPM work order, not Jr task
2. Worker restart after every executor deployment
3. Monitor staging directory for false completions: `ls /ganuda/staging/`
4. The Jr instruction queue should tag executor tasks with `tpm_deploy_required: true`

---

## Subab Principle Applied

> "Slow down so the rest can catch up. So we can stay together, because that way we are stronger."

We've been running too fast — writing Jr instructions for tasks the Jr system can't perform, trusting success reports without verification, layering improvements on a broken foundation. The 95% solution is about slowing down:

- **Accept the architectural boundary:** Jrs should not modify their own executor. The TPM deploys executor changes.
- **Stop counting staging as success:** Be honest about what actually happened.
- **Give the LLM what it needs:** If you want it to modify a file, show it the file.
- **Verify before declaring victory:** Content quality gates catch hallucination before it reaches disk.

---

## Files That Need Changing

| File | Change | Who Deploys |
|---|---|---|
| `/ganuda/jr_executor/jr_queue_client.py` | P0: FOR UPDATE SKIP LOCKED | TPM (self-referential) |
| `/ganuda/jr_executor/jr_queue_worker.py` | P0: max-tasks-per-child | TPM (self-referential) |
| `/ganuda/lib/rlm_executor.py` | Inject existing file context, staging ≠ success, quality gate | TPM (self-referential) |
| `/ganuda/config/rlm_protected_paths.yaml` | No change needed — protection is correct | N/A |
| Future non-executor Jr tasks | Will benefit from Interventions 2-4 automatically | Jr system |

---

## Key Insight

**The Jr executor system works for deploying code to TARGET APPLICATIONS (VetAssist, Telegram bot, etc.). It does NOT work for modifying ITSELF.**

This is not a bug to fix — it's a design constraint to respect. A compiler can compile other programs but cannot recompile itself while running. The TPM is the "build system" for the executor. The Jr is the "build system" for everything else.

Once we accept this boundary and deploy Interventions 2-4 (which improve the Jr's ability to modify non-executor code), the remaining non-self-referential tasks should hit 95%+ success.

---

*For Seven Generations*
*Cherokee AI Federation — Architecture Team*
