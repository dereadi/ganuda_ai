# KB — LMC-11 Jr Executor Reliability + claim_verifier (Apr 21 2026)

**Filed:** 2026-04-21
**Status:** Tier 1a LIVE in production; Tier 1b/1c/2a pending
**Council audit:** 79e31f3b9cfd84ce (APPROVED 11-0-2)
**Epic ticket:** duyuktv #2136
**Long Man cycle:** LMC-11

## Motivating incident

Two Jr failures on Apr 21 2026 exposed a systemic reliability gap:

- **#1571 (LMC-8 VetAssist Forgot-Password):** Marked `completed` + `progress=100%` at 12:50:10. Actual state: `files_created=None`, `files_staged=None`, `artifacts=[]`, `1 step_executed`. **Zero code landed** — no login-page link, no backend endpoint, no DB table. The Jr hallucinated success.
- **#1572 (LMC-7 Cert Shepherd):** Failed honestly at 13:00:18 with `error_message="1 step(s) failed"`. Zero steps executed, zero files, zero artifacts. Jr couldn't even start the multi-file scope.

Both were TPM-dispatched multi-file tasks (LMC-8: 4 touches across frontend/backend/DB/tests; LMC-7: 5 files spanning shell/systemd/ACME-hook/doc).

## Root cause analysis

Three coupled causes:

1. **Scope-capability mismatch.** Jrs reliably fail at multi-file dispatches. Already documented in `feedback_adapt_phase_is_tpm_orchestration` (Apr 20). TPM slipped today by writing project-level instruction files rather than atomic per-file dispatches.

2. **Hallucinated-success — industry-wide failure mode.** Per MIRAGE-Bench (arxiv 2507.21017): *"Single-agent systems exhibit a failure pattern where agents claim success when operations failed with no validation layer catching execution errors."* The executor that did the work is the same one that reports the result — no cross-check, no validation layer, no audit trail.

3. **`preflight_gate.py` insufficient.** The existing gate catches "no work performed" cases (0 steps, 0 artifacts) but NOT claim-vs-reality mismatches. #1571 had `1 step_executed` so preflight let it through.

## Ecosystem landscape (discover phase research)

The 2025-2026 AI-coding-agent ecosystem converged on this problem:

| Tool | Stars | Approach |
|---|---|---|
| Aider | 39K, 4.1M installs, 15B tok/wk | Git-native SEARCH/REPLACE blocks + auto-commits + repomap |
| OpenHands | Top SWE-Bench (53% Verified) | Sandboxed autonomous agent |
| Plandex | Niche | 2M context + Tree-sitter 20M indexing + cumulative-diff sandbox pre-merge |
| OpenCode | 95K stars, 2.5M monthly devs | LSP + multi-session, 75+ providers |
| Claude Code | (our env) | 1M context, Agent Teams, MCP, hooks |

**Solution patterns from the literature:**
- Judge-LLM / multi-agent validation (MDPI 16/7/517)
- Sandbox-then-merge (Plandex's UX)
- Git-as-ground-truth (Aider)
- Protocol-layer safety checkpoints (retrieve / accuracy-check / ship)

## Solution — LMC-11 scope

**Tier 1 (ratified + shipped/pending):**

- **1a — `claim_verifier.py`** — post-completion verification module at `/ganuda/jr_executor/claim_verifier.py`. ✅ SHIPPED.
- **1b — TPM multi-file preprocessor** — detect multi-file scope in instruction files before dispatch; auto-decompose or require explicit flag. ⏳ Next session.
- **1c — Judge-LLM adversarial verifier** — sub-Claude reads Jr result + git diff + artifacts, raises discrepancies. ⏳ Next session.

**Tier 2 (empirical):**

- **2a — Aider integration experiment** — install aider, wrap in dispatcher for multi-file detected scope. Retry LMC-7 via aider as empirical comparison. ⏳ Next session.

## claim_verifier.py architecture

**Module:** `/ganuda/jr_executor/claim_verifier.py` (~270 lines).

### Verifier types

| Kind | What it checks | Implementation |
|---|---|---|
| `file_exists` | Path exists + non-empty | `os.path.isfile` + `os.path.getsize > 0` |
| `file_contains` | Needle appears in file | string search |
| `syntax` | Language-specific syntax | `ast.parse` (.py), `json.load`, `yaml.safe_load`, `bash -n` (.sh) |
| `endpoint` | HTTP URL returns expected status | `requests.get` |
| `migration` | DB table (+ optional columns) exist | `information_schema.tables/columns` |
| `service` | systemd unit is active | `systemctl is-active` |
| `test` | pytest exits 0 | `subprocess.run pytest` |

### Claim extraction

Two sources:

1. **`result.artifacts[]`** — entries with `type in ('file_created', 'file_edited', 'file_modified')` + `path` get `file_exists` claims AND `syntax` claims (if extension has a checker).
2. **Instruction file Done-criteria section** — regex-parses markdown for paths wrapped in backticks under "Done criteria" / "Verification" / "Acceptance" headers.

Claims deduped by `(kind, target)` before verification.

### Hallucination signature detector

Special-case trigger:
```python
reported_success AND step_count > 0 AND artifact_count == 0 AND files_created == 0 AND no verifiable claims
```
→ sets `hallucination_flag=True`, `verified=False`.

This catches the #1571 exact shape: success claimed with fake "step" evidence but zero concrete outputs.

### Master entrypoint

```python
from jr_executor.claim_verifier import verify_jr_task_result
verification = verify_jr_task_result(task, result)
if not verification.verified:
    # Revert status to failed with verification.mismatches
```

`VerificationResult` fields: `verified`, `total_claims`, `passed`, `failed`, `skipped`, `hallucination_flag`, `mismatches[]`, `details[]`.

## Integration — jr_queue_worker.py wire-up

Post-completion path (after existing `preflight_gate` check):

```python
if result.get('success'):
    try:
        from jr_executor.claim_verifier import verify_jr_task_result
        verification = verify_jr_task_result(task, result)
        if not verification.verified:
            reason = ("HALLUCINATION: ..." if verification.hallucination_flag
                      else f"{verification.failed}/{verification.total_claims} claims failed: {verification.mismatches[:3]}")
            result['success'] = False
            result['error'] = f"Claim verifier: {reason}"
            result['claim_verification'] = verification.as_dict()
    except ImportError:
        # non-fatal
        pass
```

**Failure semantics:** verification failure reverts `result.success` to False, populates `result.error`, preserves mismatches in `result.claim_verification` for forensics. Worker then routes task to DLQ / marks failed as usual.

**Graceful degradation:** ImportError + general exception → logged non-fatal, worker continues. Ensures claim-verifier deploy doesn't brick the worker.

## Deployment pattern (what to replicate)

1. Write verifier module as sibling to existing `preflight_gate.py` in `/ganuda/jr_executor/`.
2. Unit test against exact reproduced failure shape + positive case.
3. Edit `jr_queue_worker.py` to add the verifier call AFTER existing gate, INSIDE the `if result.get('success')` block. Wrap in try/except for non-fatal degradation.
4. Cycle Jr workers: `sudo systemctl restart jr-orchestrator.service` (NOT jr-bidding — that doesn't cascade to workers; jr_orchestrator.py is the `subprocess.Popen` spawner).
5. Mark any stuck in_progress tasks as failed BEFORE cycling to avoid zombie creation.
6. Verify new worker PIDs + importability of new module in fresh Python process.

## Verification (pre-deploy test cases)

### Hallucination detection case

```python
task = {'id': 1571, 'parameters': {'instruction_file': '...LMC8...'}}
result = {'success': True, 'steps_executed': [{'description': 'faux'}],
          'files_created': 0, 'artifacts': []}
v = verify_jr_task_result(task, result)
# v.verified == False, v.hallucination_flag == True
```

### Positive case

```python
task = {'id': 99999, 'parameters': {'instruction_file': None}}
result = {'success': True, 'files_created': 1,
          'artifacts': [{'type': 'file_created', 'path': '/ganuda/real/file.py'}]}
v = verify_jr_task_result(task, result)
# v.verified == True, v.passed == 2 (file_exists + syntax)
```

Both cases verified Apr 21 2026 pre-deploy.

## Related cleanup

- #1571 status reverted `completed` → `failed` with explicit hallucination error message
- LMC-8 phase reset to `deliberate` (needs re-dispatch via atomic decomposition)
- Stuck #1529 + #1531 (pre-existing zombies revived then re-stuck) marked failed during worker cycle
- #526 + #2028 closed earlier today as scope-dead / duplicate

## Cross-references

- MIRAGE-Bench paper — arxiv 2507.21017
- `feedback_adapt_phase_is_tpm_orchestration` memory — the discipline TPM slipped on
- `/ganuda/jr_executor/preflight_gate.py` — the existing complementary gate
- `/ganuda/jr_executor/jr_orchestrator.py` — the actual worker spawner (jr-orchestrator.service)
- Patent #1 Governance Topology — claim_verifier is governance-topology applied to the Jr/TPM trust boundary

## Apr 21 2026 TPM
