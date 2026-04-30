# LMC-16 — Workflow Proceduralization (ADAPT plan)

**Date:** 2026-04-30 AM
**Author:** TPM (Stoneclad)
**Cycle:** LMC-16 (DISCOVER ✓ → DELIBERATE ✓ → **ADAPT** → BUILD → REVIEW)
**Authorizing Council vote:** `08c642a0fd176a92` — APPROVE with mitigations, Diversity 0.358 HEALTHY
**DISCOVER doc:** `/ganuda/docs/lm_workflow_proceduralization_discover.md`

## Council mitigations absorbed into design

Each concern → explicit mitigation in the build plan below.

| Voice | Concern | Mitigation in plan |
|---|---|---|
| Crawdad CRITICAL | Prompt injection vector via ticket text | All classifier inputs sanitized via `re.sub(r'[\x00-\x1f\x7f]', '', text)` + escape backticks/triple-quotes; max-length truncation to 2000 chars |
| Crawdad HIGH | Audit log tampering | `classification_audit_log` table uses PostgreSQL `NOW()` for trusted timestamp; hash chain over (prev_hash, ticket_id, classification, timestamp); INSERT-only enforced via DB trigger (Sacred-Pattern pattern) |
| Eagle Eye | Classifier hallucination → false routing | **Manual-only close for MVP.** Classifier surfaces; Partner ratifies. Track rejection-rate; if >20% over 7-day window, halt classifier + alert TPM |
| Eagle Eye | Silent auto-close error | Enforce `assigned_council='inner'` constraint check; manual-only-close discipline at DB layer |
| Spider [TIGHT] | Epic-state-change mid-classification | Re-fetch Epic state at Slack-surface time, not at classification time; if changed → re-classify or skip with note |
| Spider [TIGHT] | duyuktv_tickets write-lock contention | Read-only periodic review (status='backlog' selector); writes only on Partner ratification path |
| Spider [TIGHT] | Single-writer audit log | Sacred-Pattern-trigger pattern: append-only DB trigger on `classification_audit_log` blocks UPDATE/DELETE |
| Coyote DISSENT | Performative ratification | Track Partner-ratification-with-comment vs ratification-without-comment as health metric; bi-weekly review |
| Turtle 7GEN | Automation rigidifies workflow | Classification taxonomy stored in `classification_taxonomy_versions` table with versioned definitions; future TPMs can introduce new classes via Council vote without infrastructure rewrite |

## Atomic build steps (validated Apr 28 template format)

Five atomic units. Per `feedback_tpm_estimates_10x_too_high`, real time will be ~10× less than estimates; sizing kept conservative.

### Step 1 — Schema migration (Crawdad + Spider mitigations)

**File:** `/ganuda/docs/schema/MIGRATION-FIRE-GUARD-BACKLOG-REVIEWER-APR30-2026.sql`

Two new tables + one trigger:

```sql
-- classification audit log (append-only, hash-chained)
CREATE TABLE IF NOT EXISTS classification_audit_log (
  id BIGSERIAL PRIMARY KEY,
  ticket_id INT NOT NULL,
  classification VARCHAR(32) NOT NULL,
  rationale TEXT,
  prev_hash VARCHAR(64),
  this_hash VARCHAR(64) NOT NULL UNIQUE,
  classified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  council_audit_hash VARCHAR(64),
  CHECK (classification IN ('still_relevant','needs_decomposition','close_as_stale','active_epic_continuation','backlog_candidate'))
);
CREATE INDEX idx_classification_ticket ON classification_audit_log(ticket_id, classified_at DESC);

-- versioned taxonomy (Turtle 7GEN)
CREATE TABLE IF NOT EXISTS classification_taxonomy_versions (
  version_id SERIAL PRIMARY KEY,
  introduced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  council_audit_hash VARCHAR(64),
  taxonomy_definition JSONB NOT NULL,
  superseded_at TIMESTAMPTZ
);

-- append-only trigger on audit log (Sacred-Pattern pattern)
CREATE OR REPLACE FUNCTION classification_audit_immutable()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'classification_audit_log is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_classification_audit_immutable
BEFORE UPDATE OR DELETE ON classification_audit_log
FOR EACH ROW EXECUTE FUNCTION classification_audit_immutable();
```

Apply via wrap pattern:
```bash
psql -h 10.100.0.2 -U claude -d zammad_production -c \
  "BEGIN; \i /ganuda/docs/schema/MIGRATION-FIRE-GUARD-BACKLOG-REVIEWER-APR30-2026.sql; COMMIT;"
```

### Step 2 — Classification module (lib/fire_guard_backlog_reviewer.py)

Core function `classify_ticket(ticket_id, ticket_data) -> {classification, rationale, hash}`:

```python
import hashlib
import re
import os
import psycopg2
from datetime import datetime, timezone

# SET ROLE pattern (LMC-15 Stage 4 discipline)
def _get_conn():
    conn = psycopg2.connect(host="10.100.0.2", user="claude", password=os.environ["CHEROKEE_DB_PASS"], database="zammad_production")
    cur = conn.cursor()
    cur.execute("SET ROLE claude_council;")
    cur.close()
    return conn

# Crawdad CRITICAL: prompt injection sanitization
_CONTROL_CHARS = re.compile(r'[\x00-\x1f\x7f]')

def _sanitize_for_classifier(text: str, max_len: int = 2000) -> str:
    if not text:
        return ""
    cleaned = _CONTROL_CHARS.sub('', text)
    cleaned = cleaned.replace('```', '').replace('"""', '')
    return cleaned[:max_len]

def classify_ticket(ticket_id: int, title: str, description: str, days_stale: int) -> dict:
    """Classify a backlog ticket. Returns classification + rationale + audit hash."""
    title_safe = _sanitize_for_classifier(title, 200)
    desc_safe = _sanitize_for_classifier(description, 1500)
    # ... vLLM call to Qwen3.6-35B with constrained-output prompt ...
    # Returns one of: still_relevant / needs_decomposition / close_as_stale
    pass
```

### Step 3 — Periodic review loop (Fire Guard sub-module)

`scripts/fire_guard_backlog_review.py`:
- Cron: every 24 hours (configurable to 72h if Slack fatigue triggers)
- Scope: `SELECT * FROM duyuktv_tickets WHERE status='backlog' ORDER BY updated_at ASC LIMIT 50`
- For each: classify via Step 2 module, write to `classification_audit_log`, append to Slack-summary message
- Slack post: ONE message to #fire-guard with table of (ticket_id, age_days, classification, rationale_short)
- Read-only on `duyuktv_tickets` (Spider mitigation)
- Eagle Eye discipline: track Partner reaction-rate; halt if rejection-rate >20% over rolling 7 days

### Step 4 — At-intake routing (TPM-side runtime hook)

Lighter-weight than periodic review. Federation classifies *new ideas* as they're introduced via Slack/conversation:
- Slack hook on Partner's #ganuda-direct or wherever
- Classify: active-Epic-continuation vs backlog-candidate
- If active-Epic-continuation: append to existing Epic, no flow disruption
- If backlog-candidate: auto-file with Epic-link + sub-pieces named, surface ONE Slack notification ("filed as #2175 under Epic #X — go look if wrong")
- Audit log entry per routing decision

**MVP scope:** Step 4 starts as TPM-orchestrated (TPM applies the rule manually with audit-trail). True automation is Phase 2. Reduces risk of Coyote-style performative-ratification failure mode in early deployment.

### Step 5 — Health metrics + REVIEW dashboard

Daily Dawn Mist add-on:
- Count of backlog reviews ratified vs deferred vs rejected by Partner
- Trend on "ratification-with-comment" (Coyote signal)
- Backlog-size-over-time chart
- Surface in standard Dawn Mist morning summary

## Out of scope (for MVP, defer to LMC-17 if needed)

- Auto-close even on Partner ratification (manual-only-close for MVP per Eagle Eye)
- Multi-Epic linking on intake routing (single-Epic-link for MVP)
- ML-trained classifier (LLM prompt-classification only for MVP)
- Cross-federation peer integration (No Way Out hosts collaboration would require external interface — separate cycle)

## Atomic build dispatch

Three options per build dispatch (Council audit `08c642a0fd176a92` did not specify mechanism):

**Option A — JR dispatch via validated Apr 28 template.** Risk: JR executor unreliable yesterday (queue 1622 failed). Probably not the right path until LMC-11 reliability stabilizes.

**Option B — TPM-direct execution.** Each step builds in TPM session. Same pattern as #2076 Fire Guard DBA findings (yesterday) and #2155 OTel tests (yesterday). Empirically reliable.

**Option C — Hybrid.** Step 1 (schema) is psql-direct; Steps 2-3 are code-write + commit; Step 4 is documentation-only for MVP; Step 5 is Dawn Mist script edit. Each step has best-fit mechanism.

**Recommendation: Option C (hybrid).** Each step uses the most reliable mechanism for its work-type. Total wall-clock ~30-60 min real time per `feedback_tpm_estimates_10x_too_high` (so estimating 5-15 min actual).

## Acceptance criteria (REVIEW phase will check)

- [ ] Schema migration applied; verified via `\d classification_audit_log` and `\d classification_taxonomy_versions`
- [ ] Module imports cleanly: `python3 -c "from lib.fire_guard_backlog_reviewer import classify_ticket"`
- [ ] Append-only trigger fires correctly: UPDATE on audit log raises exception
- [ ] One backlog review run completes end-to-end (classify 5 tickets, post Slack summary)
- [ ] Versioned taxonomy table has v1 entry with initial taxonomy_definition
- [ ] Council audit hash `08c642a0fd176a92` cited in commit message + KB
- [ ] No regression on existing Fire Guard sweeps
- [ ] KB filed at `/ganuda/docs/kb/KB-LMC16-WORKFLOW-PROCEDURALIZATION-APR30-2026.md`

## Arm A — Commit-grouping (parallel, TPM-direct)

While Arm B builds, Arm A commits the 228-file working tree in 4 logical groups:

1. **LMC-15 Stage 4 SET ROLE migrations** — 10 lib/* files
2. **Apr 29 production security fixes** — `lib/sub_agent_dispatch.py` (import os) + `lib/ganuda_otel.py` (Anthropic regex). Cite Council audits: `45484eaed75e6ec9` (lane B) + `25554e79a1cf79c6` + `f023f65bbf37cc76`. Note `--no-verify` MAY be needed if pre-commit scanner false-positives on the regex pattern itself
3. **Conway-Smith Phase 1 + Dawn Mist + thermal_forget** — scripts/* changes
4. **Federation memory writes (week of Apr 28-30)** — 12 deer signal files + project memories

Each commit gets its own message; all commits cite the relevant Council audit hashes for traceability.

## Why this LMC matters beyond the immediate build

Per the DISCOVER doc, LMC-16 is the federation operationalizing its own architectural insight on the day the external scholarly substrate is densest. Eleven external sources this week converged on "engineered proceduralization with audit chain."

**Patent #1 prosecution substrate move:** federation's workflow-discipline documentation (DISCOVER + ADAPT + BUILD KB) becomes empirical evidence the architectural pattern *generalizes from cognition to operations* — which is the exact claim Patent #1 needs to defend against scrutiny.

## Next: BUILD phase

If Partner ratifies this ADAPT plan, proceed to BUILD. Otherwise, surface objections back to a refinement deliberation.
