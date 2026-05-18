# Execution-Mode Router Audit

**Task ID:** INFRA-JR-EXECUTION-MODE-ROUTER-MAY15-2026 (kanban #22, Council priority 2026-05-15 + 2026-05-17)
**Author:** Stoneclad (TPM, inline take after Jr-stub-pattern blocked Jr #1669)
**Filed:** 2026-05-17 Sunday
**Type:** READ-ONLY audit (no production-code changes; produces this doc + stashes existing corruption)
**Supersedes:** Jr #1669 stub deliverable at this same path

---

## TL;DR

Two distinct bugs identified, both fed by the same Jr-stub-pattern documented over the last 48h.

1. **Classifier over-fires (the actual router bug):** `is_research_task()` in `jr_executor/research_task_executor.py:575` checks academic keywords against the **fully-augmented** `instructions` string — including RAG-injected prior experiences from thermal memory and SkillRL skill context. Federation's substantial academic substrate (KB articles, deer signals, papers) leaks keywords like "research," "arxiv," "paper analysis" into the instructions for ANY ticket whose RAG retrieval pulls academic-adjacent context. Result: implementation tickets get misrouted to research mode whenever their prior-experiences contain academic vocabulary.

2. **task_executor.py was Jr-stub-corrupted (independent P0):** 109 uncommitted lines from 2026-05-16 22:39 (same Saturday-night Jr-stub window as DC-15/16/17, secrets.env). The corruption inserts orphan method body at module-import-level (line 33: `response = reasoner(planning_prompt, ...)`) with no enclosing class or function. **File fails to import.** The running jr-executor process (33d uptime, predates corruption) has cached the working version in memory — but next restart for any reason would dark-out the federation's Jr capability. **Now stashed** as a P0 mitigation; full TPM-inline restore queued separately.

---

## Bug 1 — `is_research_task` over-fires

### Current implementation

`jr_executor/research_task_executor.py:575-615`:

```python
def is_research_task(task: Dict, instructions: str) -> bool:
    tags = task.get('tags', []) or []
    title = task.get('title', '').lower()
    assigned_jr = task.get('assigned_jr', '').lower()
    instructions_lower = instructions.lower()

    if 'research' in [t.lower() for t in tags]:
        return True
    if re.search(r'\bresearch\b', title):
        return True
    if 'research jr' in assigned_jr:
        return True

    academic_indicators = [
        'arxiv.org', 'semanticscholar.org', 'scholar.google.com',
        'paper analysis', 'pull the paper', 'fetch the paper'
    ]
    for indicator in academic_indicators:
        if indicator in instructions_lower:
            return True

    return False
```

### Why it over-fires

The `instructions` parameter is the **fully RAG-augmented prompt** by the time it reaches this classifier — see `task_executor.py:1326-1348` (above the `is_research_task` call at line 1350):

```python
# experience_retriever injects prior experiences (thermal memory hits) into instructions
# SkillRL injects _skill_context into instructions
instructions = instructions + "\n\n<RELEVANT_SKILLS>\n" + _skill_context + "\n</RELEVANT_SKILLS>\n"
...
if RESEARCH_EXECUTOR_AVAILABLE and is_research_task(task, instructions):
```

So `instructions` includes:
1. Original task instructions (from `instruction_file` or `description`)
2. RAG-injected "Prior Experiences" — top-K thermal memory matches, often KB articles or deer signals containing academic vocabulary
3. SkillRL-injected skill context

The federation's substrate is **heavily academic** — KB articles cite papers, deer signals reference arxiv, thermal memory archive contains research summaries. Any ticket whose RAG retrieves academic-adjacent context will get academic keywords leaked INTO its `instructions` string, triggering `is_research_task() → True`, misrouting to research-mode.

### Trace: why #1658 misrouted

Ticket #1658 `INFRA-FLEXIBLE-PLAN-PARSER-FIX2-MAY13-2026` description:

> "Implement KB-JR-EXECUTOR-QWEN36 Fix 2 in full - multi-strategy plan parser"

This is unambiguously an IMPLEMENTATION task — verbs `Implement`, references a specific code file (`/ganuda/lib/jr_plan_parser.py`), includes pytest acceptance criteria. The classifier should NOT fire.

But the description references `KB-JR-EXECUTOR-QWEN36-ROOT-CAUSE-APR17-2026.md`. The experience_retriever pulls this KB AND adjacent thermal memories (deer signals, research summaries about the QWEN model family) as "Prior Experiences." Those memories contain `arxiv.org`, `paper`, and `research` vocabulary in their bodies. Once injected into `instructions`, the classifier's keyword scan fires.

Result: `is_research_task() → True` → routed to research_task_executor → produces `RESEARCH-INFRA-FLEXIBLE-PLAN-PARSER-FIX2-MAY13-20-20260513-1912.md` stub with "Sources Attempted: 0, Sources Fetched: 0." The actual implementation work never attempted.

### Pattern: Meeting Notes Extractor stub-loop (live evidence)

Last night 22:42, 22:43, 22:44 — three retries of "Meeting Notes Extractor: Deploy Demo + GitHub + Substack + LinkedIn" each produced a research-mode stub at `/ganuda/docs/research/RESEARCH-Meeting-Notes-Extractor-Deploy-Demo--Git-20260516-22{42,43,44}.md`. Same pattern — DLQ retry → classifier over-fires → research stub → re-DLQ → loop. Each retry generates another empty research summary, none make progress on the actual deployment task.

### Proposed fix (do NOT implement here — separate ticket)

Three patches needed:

**Patch A — separate raw vs augmented instructions.** Pass the ORIGINAL task description / instruction_file content to `is_research_task`, NOT the RAG-augmented version:

```python
# In task_executor.py near line 1350
raw_instructions = task.get('description', '') + '\n' + load_instruction_file(task.get('instruction_file'))
if RESEARCH_EXECUTOR_AVAILABLE and is_research_task(task, raw_instructions):  # ← raw, not augmented
    ...
```

**Patch B — add IMPLEMENTATION negative signals to the classifier.** Strong indicators of "this is implementation, NOT research" should win over weak academic-keyword signals:

```python
def is_research_task(task: Dict, instructions: str) -> bool:
    instructions_lower = instructions.lower()

    # NEW: implementation negative signals override academic positive signals
    implementation_verbs = [
        'implement', 'extend', 'modify', 'add', 'fix', 'refactor',
        'create file:', 'modify file:', 'pytest', 'unit test', 'integration test',
        'systemctl', 'deploy', 'install', 'configure'
    ]
    for verb in implementation_verbs:
        if verb in instructions_lower:
            return False  # ← short-circuit: never route implementation to research

    # ... existing positive-signal checks ...
```

**Patch C — explicit execution_mode field on the kanban row.** Long-term fix: add `execution_mode` column to `jr_work_queue` with values `research|implementation|content|audit|other` so the dispatcher routes by explicit operator intent rather than keyword inference. Eliminates classifier ambiguity entirely. Bigger change, separate ticket.

Recommended sequence:
1. Patch A (5-line fix in task_executor.py, low risk) — STOPS the leak
2. Patch B (~15-line fix in is_research_task, low risk) — adds defensive guard
3. Patch C (schema change, larger blast radius) — defer to architectural sprint

---

## Bug 2 — task_executor.py Jr-stub corruption (P0)

### State found

`jr_executor/task_executor.py` had 109 uncommitted lines from 2026-05-16 22:39. The corruption inserts orphan method body at module-import-level (line 33 became `response = reasoner(planning_prompt, max_tokens=4096, temperature=0.1)` with no enclosing function definition). The intended addition was a `_extract_steps_via_legacy_llm` fallback method, but it was dropped into the wrong place (module level instead of inside the `TaskExecutor` class).

### Verified failure mode

```
$ python3 -c "import task_executor"
File "/ganuda/jr_executor/task_executor.py", line 34
  plan = parse_planning_response(response)
IndentationError: unexpected indent
```

### Why the federation was still running

The jr-executor process on redfin has uptime **33 days** (PID 1044058, ELAPSED 33-00:34:24). The Saturday corruption happened AFTER the process started. Python caches imported modules in `sys.modules`; the running process holds the working pre-corruption version in memory. Any restart for any cause — cat-PSU, OOM, manual restart, systemd reload, power event — would attempt to re-import task_executor.py and fail.

**The federation's Jr capability was a single-point-failure away from going dark for 48 hours and nobody knew.**

### Mitigation taken (this audit session)

Stashed the corruption: `git stash push -m "Jr-stub-corruption of task_executor.py..." jr_executor/task_executor.py`. File now imports cleanly. Federation is safe to restart.

Stash entry preserved for later TPM-inline review — the intent (adding a fallback legacy-LLM-extraction method) is legitimate; the execution was Jr-stub-corrupted. Restoring the intent cleanly is a separate ticket.

### Bonus finding: duplicate jr-executor process

`ps` on redfin shows TWO `jr_task_executor.py jr-redfin-gecko redfin` processes:
- PID 1044058 — 33 days uptime
- PID 2274355 — 30 days uptime

Both running with the same agent identity. Either a restart that didn't kill the old process, OR systemd spawned a second instance. Either way, two workers may be claiming the same tickets which could cause race conditions or duplicate execution.

Recommended: investigate which is canonical, kill the other, file follow-up to ensure systemd unit has correct `KillMode=` and `Type=` settings.

---

## Pattern observation — 6th Jr-stub-corruption in 48h

This audit confirms an escalating pattern. Documented instances:

| # | Date | Location | Symptom |
|---|---|---|---|
| 1 | May 13 | Jr ticket #1658 deliverable | Research stub instead of implementation |
| 2 | May 16 morning | Jr ticket #1669 deliverable | 217-byte audit stub |
| 3 | May 16 morning | Jr ticket #1670 deliverable | 296-byte test stub |
| 4 | May 16 ~22:36 | `lib/specialist_council.py` working tree | 86-line DC-15/16/17 partial edit + `# ... (rest of the code)` placeholder |
| 5 | May 16 ~22:36 | `/ganuda/config/secrets.env` | CHEROKEE_DB_PASS overwritten with hallucinated value |
| 6 | May 16 ~22:39 | `jr_executor/task_executor.py` | 109-line partial-edit, module-level orphan code, would fail import |

Items 4, 5, 6 happened within minutes of each other on Saturday night, around the same time the DLQ retry poller was deployed and started firing retries. **The poller-driven Jr retry storm appears to be the trigger for the production-code corruption** — Jr workers picked up tasks that involved modifying these files and produced stub-deliverables that overwrote the targets.

Items 4, 5, 6 are particularly dangerous because they damage PRODUCTION CODE, not just kanban output. Item 6 specifically would have caused complete Jr-pipeline outage on next restart.

---

## Recommended follow-up tickets

| Priority | Title | Type | Estimated effort |
|---|---|---|---|
| P1 | Fix `is_research_task` over-fire — Patches A + B | Implementation (TPM or carefully-scoped Jr) | 1-2 hours |
| P1 | Restore task_executor.py legacy-LLM fallback cleanly from stash | TPM-inline (Jr can't do it — recursive trap) | 30-60 min |
| P1 | Investigate duplicate jr-executor process on redfin | Diagnosis | 30 min |
| P2 | Restore DC-15/16/17 from stash if anything still pending | TPM-inline | DONE (committed 8985b24) |
| P2 | Schema change: explicit `execution_mode` column on jr_work_queue (Patch C) | Architectural | 4-6 hours |
| P3 | Stop the Jr-stub-corruption damage at its source: pre-write file-content validator | Architectural — Crawdad-flag | TBD; depends on Patch A/B effectiveness |

---

## What this audit does NOT do (deliberately)

- Does NOT implement any of the patches above
- Does NOT restore the stashed task_executor.py content (Partner-decision)
- Does NOT fix the duplicate-process issue
- Does NOT touch the running jr-executor process

This is per Crawdad's discipline from yesterday's Council: separate the AUDIT (read-only diagnostic) from the IMPLEMENTATION (write-and-verify), because Jr-as-self-modifying-system has a recursive trap and we should preserve fix-step traceability.

---

## For Seven Generations

Two structural lessons emerge from this audit:

1. **RAG augmentation pollutes downstream classifiers.** Any decision that runs ON top of RAG-augmented prompts will be biased by what RAG retrieves. If RAG pulls academic context, every downstream decision will look academic. Mitigation: classifiers must distinguish ORIGINAL operator intent from AUGMENTED context. Patch A is one instance; the principle generalizes.

2. **Jr-self-modifying-the-Jr-pipeline is a recursive trap.** Jr stub-corruption of production code that Jr itself uses to execute creates a feedback loop where each failed Jr task can damage the system that runs Jr tasks. Mitigation: critical Jr-pipeline files (`task_executor.py`, `specialist_council.py`, `dlq_manager.py`, `jr_plan_parser.py`, anything in `/ganuda/jr_executor/` core) should require TPM review before any Jr-produced edit lands. Phrase as a write-gate, not a Jr policy — Jrs will work around policies.

The Federation has been getting away with Jr-stub-corruption because most damage has been to kanban deliverables (stub MD files in `/ganuda/docs/research/`), not to the executor itself. Item 6 (task_executor.py) crossed that line. We caught it before restart. Next time we might not.
