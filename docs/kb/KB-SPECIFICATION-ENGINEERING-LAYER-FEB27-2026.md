# KB: Specification Engineering Layer

**Date Deployed:** Feb 27 2026
**Council Vote:** #1d2ba22feb928108 (score: 0.743, APPROVED WITH CONDITIONS)
**Ultrathink:** /ganuda/docs/ultrathink/ULTRATHINK-SPECIFICATION-ENGINEERING-LAYER-FEB27-2026.md
**Status:** Live on bluefin

---

## Purpose

The Specification Engineering Layer provides a structured requirements framework that grounds Jr tasks in explicit, verifiable requirements before execution begins. Without specs, Jr tasks execute against implied requirements that exist only in the TPM's context window. With specs, acceptance criteria survive context compression and can be retrieved, audited, and verified independently of the originating conversation.

Inspired by Nate B. Jones' Four Disciplines framework (Prompt Craft, Context Engineering, Intent Engineering, Specification Engineering), which maps 1:1 to the federation's architecture. Specification Engineering is the fourth discipline — structuring intent before it hits the execution layer.

---

## Database Schema (deployed on bluefin)

### Table: `project_specifications`

Holds the specification documents themselves.

| Column | Type | Notes |
|---|---|---|
| id | serial PK | Auto-incremented |
| title | text | Short name for the spec |
| problem_statement | text | What problem are we solving? |
| acceptance_criteria | text | How do we know it is solved? |
| constraints | text | What boundaries must be respected? |
| decomposition | text | How does this break into steps? |
| evaluation_criteria | text | How do we verify quality? |
| target_files | text[] | Files expected to be modified |
| target_file_hashes | jsonb | SHA256 of each target file at spec write-time (drift detection) |
| framework_notes | text | Tech stack notes, patterns to follow |
| status | varchar | Status flow (see below) |
| created_by | text | Who authored the spec |
| created_at | timestamptz | Creation timestamp |
| updated_at | timestamptz | Last update timestamp |

**Status flow:** `draft` → `approved` → `in_progress` → `verified` → `closed`

### Table: `spec_task_links`

Links specifications to Jr work queue tasks. Allows a single spec to drive multiple tasks, and provides audit trail of which tasks were spawned from which spec.

- FK to `project_specifications`
- FK to `jr_work_queue`

### Column: `jr_work_queue.specification_id`

Nullable FK added to `jr_work_queue`. Allows a task to be linked directly to a spec at INSERT time, without requiring the join table.

---

## Five Primitives

These are the five required fields that constitute a complete specification. A spec is not actionable until all five are populated.

**1. problem_statement**
What problem are we solving? Describes the current state and why it is inadequate. Forces the TPM to articulate the gap before assigning work.

**2. acceptance_criteria**
How do we know it is solved? Specific, verifiable conditions. Owl uses these during debt reckoning to determine whether a task actually delivered what was intended. Without this field, verification is opinion-based.

**3. constraints**
What boundaries must be respected? Includes: files that must not be modified, services that cannot go down, performance thresholds, security requirements, backward-compatibility requirements. Prevents Jr tasks from solving the problem in ways that break adjacent systems.

**4. decomposition**
How does this break into steps? High-level task breakdown used by the TEG Planner and by the TPM when writing Jr instructions. Decomposition in the spec is advisory; the TEG Planner may further decompose at execution time.

**5. evaluation_criteria**
How do we verify quality beyond binary pass/fail? Includes performance benchmarks, code quality standards, test coverage expectations, review requirements. Distinct from acceptance_criteria in that it measures HOW WELL the solution was implemented, not just WHETHER it was implemented.

---

## Code Context Fields

These fields extend the spec to capture the technical surface area of the work.

**target_files**
Array of file paths expected to be created or modified. Written at spec-creation time. Used by Owl during debt reckoning to scope the verification sweep.

**target_file_hashes**
JSONB object mapping file path to SHA256 hash, captured at spec write-time. Enables drift detection: if a target file changes between spec approval and task execution, the executor can flag the divergence before proceeding. Protects against specs going stale while a task sits in the queue.

**framework_notes**
Free-text notes on tech stack, architectural patterns to follow, libraries already in use, patterns to avoid. Gives Jr executors context they cannot infer from the file contents alone.

---

## Pilot Specifications

Three pilot specs were approved alongside the layer deployment to validate the framework before general adoption.

| Spec # | Title | Purpose |
|---|---|---|
| #1 | Gateway Health | Async debounce and health check hardening for the redfin gateway |
| #2 | Self-Replication Audit | Security audit of self-replication vectors across the federation |
| #3 | Three Rivers KB | Knowledge base structure for the Three Rivers cultural memory system |

Pilot results feed the Coyote condition (see below).

---

## Coyote Condition

Council approved with the following condition attached:

> Measure DLQ reduction after pilots, 2-week review.

The hypothesis is that specs reduce failed/bounced Jr tasks by front-loading requirement clarity. DLQ (dead letter queue) volume is the measurable proxy. At the 2-week mark, compare DLQ rates for spec-linked tasks versus unlinked tasks. If DLQ reduction is not observed, revisit adoption mandate.

---

## Key Insight

Specs capture intent BEFORE execution. The TPM's context window does not persist across conversations. Requirements that exist only in the TPM's head at task-creation time are lost by the time the Jr executor runs, and certainly lost by the time Owl reviews the output days later.

With the Specification Engineering Layer:
- Acceptance criteria are durable (stored in DB, not in context)
- Owl can verify against the original intent, not a reconstructed approximation
- DLQ triage has a reference document to compare actual output against
- The Long Man RECORD step has a structured artifact to store, not just a thermal memory entry

This directly addresses the Anti-80/20 principle: specs force "does it actually work?" to be defined before the sprint, not after.

---

## Relationship to Other Systems

- **TEG Planner**: `decomposition` field feeds the TEG graph. If a spec has a decomposition, the TEG Planner can use it as the initial node structure.
- **Thermal Memory**: Spec titles and IDs should be referenced in thermal memory entries so that future context windows can locate the spec from a memory fragment.
- **Owl Debt Reckoning**: `target_files` and `acceptance_criteria` are the primary inputs for Owl verification sweeps.
- **Long Man RECORD step**: Approved specs are stored KB artifacts. This document IS the RECORD for the Specification Engineering Layer itself.
- **Drift Detection** (`lib/drift_detection.py`): `target_file_hashes` enables the drift detection library to flag stale specs before task execution.

---

## Operational Notes

- Specs should be written and moved to `approved` status BEFORE the corresponding Jr task is inserted into `jr_work_queue`.
- Set `specification_id` on the `jr_work_queue` INSERT when the spec exists. Do not retroactively link after execution begins.
- The `status` column on `project_specifications` is the source of truth for spec lifecycle, not the linked task status.
- Only the TPM or Council should move a spec from `draft` to `approved`. Jr executors do not author or approve specs.
- `target_file_hashes` must be captured at spec write-time, not at task execution time. The point is to detect drift, not to snapshot the execution state.
