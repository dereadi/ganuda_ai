# KB: Jr Instruction File Authoring Patterns — Executable vs Design-Doc Confusion

**Filed:** 2026-05-17 ~21:30 CDT
**Author:** Stoneclad (TPM)
**Severity:** P2 — recurrent dispatcher confusion; #1497 has failed 6+ times with same root cause
**Affects:** Mode C residual in `KB-JR-SEV1-DISARM-AND-VERIFY-PLAYBOOK-MAY17-2026.md` after plan-parser fix shipped

## Problem statement

Some instruction files under `/ganuda/docs/jr_instructions/` are **design documents** (long-form prose with implicit work) rather than **executable step-lists**. The plan parser correctly returns "No executable steps found" — and the failure cascades into infinite DLQ retry loops. Plan-parser fix (commit `39160b7`, 5-strategy cascade) does not help: there genuinely are no executable steps in the file.

## Triggering case study: #1497 GAAS-MVP-WEEK1

`/ganuda/docs/jr_instructions/JR-GAAS-MVP-WEEK1-APR07-2026.md` — 173 lines, dispatched 6+ times, failed 6+ times.

Structure of the file:
- Lines 1-30: Title + Council vote refs + Coyote/Turtle safeguards
- Lines 9-30: **Design Constraints (DC-15/16/17)** — governance theory
- Line 32+: `## Day 1-2: Content + Outreach`
- Line 34+: `### Task A: Substack Article — "The Model Is Free..."`
- (Continues with Task B, Task C as long-form prose)

Why parser returns empty:
- No `## Step 1`, `## Step 2` header pattern (Strategy 2 finds nothing actionable)
- No JSON `steps: [...]` block (Strategy 3 finds nothing)
- No absolute paths to write/modify (Strategy 4 finds nothing)
- No instruction-text override (`# steps:` block etc., Strategy 5 finds nothing)
- The "Task A/B/C" structure isn't recognized — and even if it were, the content is week-scoped strategic work (write an essay, do outreach), not atomic Jr-executable operations

**The instruction file is a Partner-authored design document, not a Jr instruction set.** A Jr cannot execute "Day 1-2: Content + Outreach" — that's a week of human strategic work.

## The pattern (so you recognize it next time)

A file is a **design doc, not an executable instruction set**, when ANY of these is true:

1. Headers use **time-scoped** scope (`## Day 1-2`, `## Week 1`, `## Phase 2`) — implies multi-day human work
2. Tasks reference **strategic content production** ("write a Substack article", "draft outreach email", "negotiate with X") — requires Partner voice/judgment
3. Steps reference **Council/governance work** ("Council vote on Y", "Crawdad review of Z") — requires Council convocation
4. Body is **long-form prose argument** rather than imperative steps (compare: "Write a defense of governance-as-differentiator" vs "Run pytest in /ganuda/lib/ and report failures")
5. **No file paths to write/modify, no commands to run, no concrete acceptance criteria** — the file describes WHAT and WHY but not HOW

## Executable instruction file pattern (for contrast)

A file IS Jr-executable when:

1. Headers are **step-scoped** (`## Step 1`, `### Atomic Operation`)
2. Each step has an **imperative verb + concrete object** ("Add column X to table Y", "Move file from A to B", "Run script Z and capture output to W")
3. **Concrete file paths**, **runnable commands**, **specific tests/acceptance criteria** are present
4. Estimated complexity is **single-Jr-session** (<2-3 hours wall time, not "Week 1")
5. **No need for Partner judgment, Council convocation, or external negotiation**

Recent good examples in the tree:
- `/ganuda/docs/jr_instructions/JR-PLAN-PARSER-MULTI-STRATEGY-MAY15-2026.md` (one parser to build, defined surface area)
- `/ganuda/docs/jr_instructions/MORNING-BUILD-BOBCATFIN-MAY14-2026.md` (numbered phases, each with concrete commands)
- `/ganuda/docs/jr_instructions/JR-EXECUTION-MODE-ROUTER-INVESTIGATION-MAY15-2026.md` (defined deliverable, code surface to read)

## Why this matters at scale

Without classification, every design doc that gets dispatched becomes:
- 1+ failed Jr execution (wasted GPU time + tokens)
- 1+ DLQ entry that retries 3x (3x more wasted tokens)
- Cascading retry attempts every poll cycle while poller is on
- For #1497 specifically: **6+ failures recorded** despite plan-parser fix being correct

Result: shared resources (GPU, model context, queue capacity, RAG pollution) wasted on tasks no Jr can ever complete.

## Stopgap (immediate)

### A. Triage #1497 and similar persistent-failure tasks

For each task that's failed >2 times with "No executable steps":
1. Read the instruction file
2. Decide: **cancel** (instruction is a design doc — Partner needs to either write executable steps OR do the work themselves) OR **rewrite** (genuine Jr-executable work mis-formatted)
3. Update kanban accordingly

#1497 specifically: **recommend CANCEL** — the GAAS-MVP-WEEK1 content is week-scoped strategic work, not Jr-executable. The Substack article authoring, governance positioning, and outreach require Partner voice. The file should live as a Partner planning doc, not a Jr instruction.

Other candidates to check (Mode C residual): query `SELECT id, instruction_file FROM jr_work_queue WHERE error_message ILIKE '%No executable steps%' GROUP BY 1,2;`

### B. Pre-dispatch classifier (proposed)

Add a `classify_instruction_file()` step BEFORE dispatch:
- Run the same 5-strategy parser
- If empty → **mark task `requires_rewrite`** rather than dispatching to Jr
- Operator (Partner or TPM) reviews and either rewrites or cancels
- Saves 1 wasted Jr execution per design-doc-mistakenly-dispatched

### C. Instruction-file authoring template

Create `/ganuda/docs/jr_instructions/TEMPLATE-EXECUTABLE.md` with the executable pattern above. Reference in CLAUDE.md so new TPM/Partner-authored instructions follow the executable convention by default.

## Connection to broader architecture

- **DUPLO frame** ([[project_duplo_jr_layer_extension_may17_2026]]): If we have Ring-specialists, the dispatcher can route based on instruction type. Design docs would route to a "design-doc-Ring" that flags for Partner review; executable steps would route to operation-specific Rings. Pre-dispatch classifier IS the Ring router.
- **FWPL Phase 1 (#2563)**: pre-write hook is the file-write parallel; pre-dispatch classifier is the task-input parallel. Same architectural pattern at different points in the pipeline.

## Lineage

- KB-JR-SEV1-DISARM-AND-VERIFY-PLAYBOOK-MAY17-2026 (parent — Mode C)
- KB-JR-CAPABILITY-GAPS-EXECUTION-MODE-PLAN-PARSER-MAY15-2026 (sibling — parser strategies that don't help here)
- KB-JR-RESEARCH-PIPELINE-FAILURE-MAY17-2026 (sibling — Mode D)
- Council vote target: pre-dispatch classifier + instruction-file template adoption

## Open follow-ups

1. **#1670 (parser-fix re-fail) drill-down** — `result` JSON empty + only "1 step(s) failed" reported. Likely no-op dispatch (TPM had already shipped the fix inline) but needs confirmation
2. **Pre-dispatch classifier ticket** — kanban + Council vote
3. **Instruction-file template** — `/ganuda/docs/jr_instructions/TEMPLATE-EXECUTABLE.md`
4. **Audit all current instruction files** in `/ganuda/docs/jr_instructions/` for the design-doc pattern; flag for review
