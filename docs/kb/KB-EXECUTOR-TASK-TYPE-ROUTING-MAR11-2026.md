# KB: Executor Task-Type Routing + Artifact Verification

**Date**: 2026-03-11
**Category**: Jr Executor Architecture
**Council Votes**: #1c14b3cf65e95fcd (quality issue), #328507ea46a247d2 (notification)
**Status**: Approved, queued for implementation

## Problem Discovered

On Mar 10 2026, 5 Jr tasks were queued (14 SP). Three "completed" within minutes but produced no actual deliverables:
- standing_dissent bug fix: test file created but all `pass` bodies, no code fix
- Executor security audit: 1 SQL query ran, no report file
- Eaglefin post-mortem: 3 bash commands ran, no post-mortem document

**Root cause**: Executor checks "did steps run" not "did deliverables land."
**Secondary cause**: Builder Jrs (SE Jr, Infra Jr) assigned investigative work they're not suited for.

## Solution: Two-in-One Executor Upgrade

### Feature 1: Task-Type Routing (DC-6 Gradient Principle)

Semantic classification of tasks into three archetypes:

| Archetype | Jr Pool | Example Tasks |
|-----------|---------|---------------|
| BUILD | SE Jr, Infra Jr | Write scripts, deploy services, fix bugs |
| THINK | Research Jr, Synthesis Jr | Audits, investigations, risk assessments |
| DOCUMENT | Document Jr, Synthesis Jr | Post-mortems, reports, specifications |

**Implementation**: Embed task description via greenfin (192.168.132.224:8003), compare against route exemplars using cosine similarity. Keyword fallback if greenfin is down.

**Reference architectures researched**:
- aurelio-labs/semantic-router — semantic vector routing, no LLM in loop (BEST FIT)
- lm-sys/RouteLLM — cost-based model routing (not our use case)
- ulab-uiuc/LLMRouter — 16+ strategies, embedding-based (overkill but good ideas)

**Key principle**: Routing is gravity, not a wall. Jrs CAN do work outside their archetype. Routing determines where they REST (DC-6).

### Feature 2: Artifact Verification

Before marking complete, executor checks:
1. Parse instruction file for expected output paths
2. Verify each file exists, is non-empty, was modified after task start
3. Missing deliverables → status=failed, not completed

### Council Binding Conditions
- **Coyote**: Embedding drift fallback — keyword routing if embeddings misclassify
- **Crawdad**: Strip credentials from task descriptions before embedding
- **Raven**: Greenfin latency cap (< 2s or fallback to keywords)
- **Turtle**: No vendor lock-in — embedding service is swappable

## Related KBs
- KB-JR-EXECUTOR-FALSE-COMPLETION-PATTERNS-JAN31-2026.md — same problem seen in January
- KB-EXECUTOR-95-PERCENT-SOLUTION-DEPLOYMENT-FEB03-2026.md — previous executor fix
- KB-TWO-WOLVES-DATA-SOVEREIGNTY-COUNCIL-ROUTING-FEB08-2026.md — earlier routing discussion

## Impact on "913 Completed Tasks"

Chief's question: how many of those 913 actually delivered? A sampling audit (50 random tasks) is recommended as Track 3. The false-completion KB from January shows this is a known pattern, not new.

## Files
- Jr Instruction: `/ganuda/docs/jr_instructions/JR-EXECUTOR-ROUTING-VERIFICATION-MAR11-2026.md`
- Executor: `/ganuda/jr_executor/task_executor.py`
- New module: `/ganuda/lib/task_router.py` (to be created)
