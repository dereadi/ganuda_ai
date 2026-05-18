# KB: Jr Research Pipeline — `research_topic` Step Failure Mode

**Filed:** 2026-05-17 ~21:25 CDT
**Author:** Stoneclad (TPM)
**Severity:** P2 — blocks all Research-Jr dispatch (deer-research, Substack research, Kauffman synthesis)
**Affects:** Mode D failures in `KB-JR-SEV1-DISARM-AND-VERIFY-PLAYBOOK-MAY17-2026.md`; 5 active failures in last 24h

## Problem statement

Tasks assigned to `Research Jr.` fail with one of two error signatures:

1. `Partial-success bug fix May 12: 1/2 step(s) failed: ['research_topic']` — explicit step-name failure
2. `Research task failed` — catch-all from the research executor

Both originate in `jr_executor/research_task_executor.py`.

## Failures triggering this KB (last 7d)

| ID | Title | Error |
|---|---|---|
| 1652 | DEER-PUB-KAUFFMAN-CONSTRAINT-CLOSURE-MAY10 | `1/2 step(s) failed: ['research_topic']` |
| 1653 | DEER-PUB-JONES-LILY-MCKINSEY-MAY10 | Research task failed |
| 1636 | INFRA-JR-CURRICULUM-FAILURE-MAPPING-MAY12-2026 | `1/2 step(s) failed: ['research_topic']` |
| 1624 | SUBSTACK-EAI-PART-III-MAY12-2026 | Research task failed |
| 1635 | INFRA-CODE-REPO-REDUNDANCY-MAY12-2026 | HALLUCINATED SUCCESS (caught by TPM, separate mode) |

## Code surface

- `jr_executor/research_task_executor.py:62` — `execute_research_task(task)` entry point
- `jr_executor/research_task_executor.py:171` — `topic_results = sync_research_topic(topic, [wiki_url])`
- `jr_executor/research_task_executor.py:187` — step type tag `'type': 'research_topic'`
- `jr_executor/web_research.py` — `sync_fetch_url`, `sync_research_topic` (the actual research primitives)
- `jr_executor/research_task_executor.py:575` — `is_research_task(task, instructions)` — the dispatcher gate

## Root cause hypothesis (NOT yet confirmed — investigation required)

The `research_topic` step calls `sync_research_topic()` which fetches external URLs. Three plausible failure paths:

1. **External-fetch failure** — `sync_research_topic` hits a URL that times out, returns non-200, or returns empty content. Failure not caught with informative error → bubbles up as "Research task failed."
2. **Wiki URL contract** — `[wiki_url]` argument expects a specific shape (federation internal wiki vs external Wikipedia vs site-specific). Mismatch produces silent zero-result, treated as failure.
3. **Topic-extraction failure** — `topic` is extracted from the instruction file but the extraction logic doesn't handle the deer/substack instruction shape. Empty topic → empty result → "failed" verdict.

**Most likely** based on the failures clustering on deer-publication tasks (#1652 Kauffman, #1653 Jones, #1624 Substack EAI-III): cause 3 (topic-extraction mismatch on deer/substack instruction patterns). Deer instructions are conversational/multi-source; `sync_research_topic` may expect single-topic single-source.

## What needs investigation (open follow-ups)

1. **Read `web_research.py`** — understand actual contract of `sync_research_topic(topic, [wiki_url])`
2. **Read one failing instruction file** — e.g. `/ganuda/docs/jr_instructions/JR-DEER-PUB-KAUFFMAN-CONSTRAINT-CLOSURE-MAY10-2026.md` — see what topic gets extracted
3. **Trace one execution end-to-end** — manually run `execute_research_task()` on #1652's task dict, log every step, find the actual exception
4. **Check `is_research_task()` over-fires** — per `EXECUTION-MODE-ROUTER-AUDIT-MAY17-2026.md`, this function over-fires on RAG-augmented instructions. Some "research" tasks may actually be content-generation tasks mis-routed.

## Stopgap (until root cause confirmed)

**Do NOT dispatch new Research-Jr tasks** until investigation completes. The 5 failures above are inert in `failed` state and DLQ entries are blocked by `MAX_AGE_DAYS=3` cutoff. Safe.

For deer-pub work meanwhile: **TPM-inline research** is the alternative (TPM does the research as orchestration work per `feedback_tpm_can_code_but_teach`). Slower but correct.

## Connection to broader architecture

- **DUPLO frame** ([[project_duplo_jr_layer_extension_may17_2026]]): the Research-Jr is currently a monolithic generalist. Under the DUPLO Ring architecture, research should decompose into Rings (URL-fetcher Ring, content-summarizer Ring, citation-extractor Ring, topic-synthesizer Ring), each independently testable. Current monolithic failure-shape ("Research task failed" with no detail) is exactly the symptom of missing Ring decomposition.
- **FWPL Phase 1 (#2563)**: doesn't directly help Research-Jr, but FWPL's pre-write hook would catch any stub-shaped research output before it pollutes deer-pipeline files.
- **Execution-mode router** (`EXECUTION-MODE-ROUTER-AUDIT-MAY17-2026.md`): `is_research_task()` over-fires; some Research-Jr failures may be content tasks misrouted. Router refinement is a sibling fix.

## Lineage

- KB-JR-SEV1-DISARM-AND-VERIFY-PLAYBOOK-MAY17-2026 (parent — Mode D)
- KB-JR-CAPABILITY-GAPS-EXECUTION-MODE-PLAN-PARSER-MAY15-2026 (router over-fire mentioned)
- KB-JR-CONTENT-GENERATION-OVER-EAGER-CODE-MAY16-2026 (sibling routing-error pattern)
- `docs/audit/EXECUTION-MODE-ROUTER-AUDIT-MAY17-2026.md` (router audit)
- Kanban candidate: INFRA-RESEARCH-PIPELINE-DRILLDOWN-MAY18 (to open)

## When this KB graduates

Convert findings to a fix-KB when investigation completes. This KB stays as the failure-mode record; new KB will document the actual root cause + patch.
