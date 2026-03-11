# JR INSTRUCTION: Re-queue Failed Tasks from Mar 9 Session Death

**Task**: Re-create 6 failed Jr tasks that died when executor context ran out
**Priority**: MEDIUM
**Date**: 2026-03-09
**TPM**: Claude Opus

## Context

9 tasks were stuck in `in_progress` when the executor session died. TPM triaged:
- 3 marked COMPLETED (code existed): #1127, #1132, #1139
- 4 marked FAILED (no code written): #1128, #1143, #1154, #1156
- 2 marked FAILED (partial): #1133, #1148

## Tasks to Re-queue

### 1. Qwen3 Think-Tag Strip (was #1128)
**File**: `/ganuda/lib/specialist_council.py`
**What**: Qwen3 returns `<think>...</think>` tags in responses. Strip them before returning to caller.
**Where**: In the response processing after LLM call returns, before the response is used.
**Pattern**: `re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()`

### 2. DC-14 Canonical Flag (was #1143)
**File**: Database schema + `/ganuda/scripts/` thermal memory inserts
**What**: Add `is_canonical` boolean column (default false) to `thermal_memory_archive`. This is DC-14 Three-Body Memory Phase 1.
**SQL**: `ALTER TABLE thermal_memory_archive ADD COLUMN IF NOT EXISTS is_canonical BOOLEAN DEFAULT FALSE;`
**Note**: Do NOT modify existing inserts. Just add the column. Phase 2 will use it.

### 3. Slack → Fire Guard (was #1154)
**File**: `/ganuda/scripts/fire_guard.py`
**What**: When Fire Guard detects alerts, send them to Slack #fire-guard channel.
**How**: Import `slack_send` from `/ganuda/lib/slack_federation.py`. After `store_alerts(results)` in `__main__`, call `slack_send("fire-guard", alert_summary)`.
**Constraint**: Only send on alerts. Do not spam ALL CLEAR every 2 min.

### 4. Slack → Council Votes (was #1156)
**File**: `/ganuda/daemons/governance_agent.py`
**What**: After a council vote completes, send result to Slack #council-votes.
**How**: Import `notify_council_vote` from `/ganuda/lib/slack_federation.py`. Call it after vote is recorded.
**Reference**: `council_dawn_mist.py` already has Slack wiring — follow that pattern.

### 5. Crane → Longhouse (was #1133, partial)
**File**: `/ganuda/lib/longhouse.py`
**What**: Crane is in specialist_council.py but MISSING from `TRIBE_MEMBERS` dict in longhouse.py.
**How**: Add Crane entry to TRIBE_MEMBERS: `"Crane": {"role": "outer_council", "ghigau": False, "archetype": "diplomat"}`
**Note**: Crane is already functional in council — just needs governance membership.

### 6. Credential Audit Owl Pass (was #1148, partial)
**File**: `/ganuda/scripts/credential_audit_owlpass.py` (new file)
**What**: Owl Pass script that scans codebase for hardcoded credentials, API keys, passwords.
**Pattern**: Follow `/ganuda/scripts/observability_audit_owlpass.py` structure.
**Scan targets**: `*.py`, `*.env`, `*.json`, `*.yaml` files under `/ganuda/`
**Exclude**: `/ganuda/config/secrets.env` (that's the canonical secrets file)
**Output**: Report of files with potential credential leaks.

## Constraints
- Each task should be queued as a SEPARATE Jr task
- Test each with syntax check before marking done
- Do not duplicate code — check existing implementations first
