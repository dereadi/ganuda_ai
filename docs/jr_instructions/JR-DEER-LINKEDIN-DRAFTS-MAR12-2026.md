# Jr Instruction: Deer LinkedIn Draft Generation from Thermal Fuel

**Task ID**: #1284
**Priority**: 3
**Story Points**: 5
**Council Owner**: Deer (Outer Council)
**Supersedes**: JR-DEER-LINKEDIN-DRAFT-GENERATOR-MAR06-2026.md (v1)

## Context

The v1 LinkedIn draft generator (`deer_linkedin_drafts.py`, Mar 6) had limitations:
- Rolled its own DB connection instead of using `ganuda_db`
- Direct HTTP to vLLM only, no fallback model routing
- Excluded sacred thermals entirely
- No CLI arguments (hours, limit, dry-run)
- No sub_agent_dispatch integration

This Jr task upgrades the script to use the federation's standard patterns:
`ganuda_db` for connections, `sub_agent_dispatch` for model dispatch with fallback,
expanded thermal fuel queries (sacred + high-temp business/market thermals),
content screening, and CLI controls.

## What Changed (v1 -> v2)

1. **DB**: `ganuda_db.get_connection()` replaces manual psycopg2 connection logic
2. **LLM**: `sub_agent_dispatch.SubAgentDispatch.dispatch_with_fallback()` replaces direct HTTP. Primary: bmasass Qwen3-30B (creative work). Fallback chain: redfin vLLM, sasass Ollama.
3. **Thermal query**: Now includes sacred thermals (opt-in via `--include-sacred`), business/market domains at temp >= 70, any domain at temp >= 85. Deduplicates against existing `linkedin_drafts` table rows.
4. **Content screening**: Expanded blocked terms list (Tailscale, Caddy, keepalived, internal lib names). Added word-boundary matching for short terms (TEG, SAG, DLQ).
5. **CLI**: `--hours`, `--limit`, `--dry-run`, `--include-sacred` flags.
6. **Notifications**: Slack deer-signals channel (best-effort). Pending count logged.
7. **Fallback**: JSONL file fallback at `/ganuda/logs/linkedin_drafts_fallback.jsonl` if DB write fails.

## Files

- **Script**: `/ganuda/scripts/deer_linkedin_drafts.py`
- **Migration**: `/ganuda/scripts/migrations/linkedin_drafts_schema.sql` (unchanged, reused from v1)
- **Dependencies**: `ganuda_db`, `sub_agent_dispatch`, `slack_federation` (optional)

## Steps

### Step 1: Verify the script runs in dry-run mode

```bash
cd /ganuda && python3 scripts/deer_linkedin_drafts.py --dry-run --hours 72
```

Expected: Lists thermal fuel candidates with id, temperature, domain, and content preview. No LLM calls made.

### Step 2: Run a single draft generation

```bash
cd /ganuda && python3 scripts/deer_linkedin_drafts.py --limit 1 --hours 72
```

Expected: One draft generated, screened for internal terms, saved to `linkedin_drafts` table with `status = 'pending'`.

### Step 3: Verify draft in database

```sql
SELECT id, source_type, status, LEFT(draft_content, 100),
       metadata->>'thermal_id' as thermal_id,
       metadata->>'model_node' as model_node
FROM linkedin_drafts
WHERE metadata->>'jr_task' = '1284'
ORDER BY created_at DESC LIMIT 5;
```

### Step 4: Verify content screening

Manually inspect drafts for any internal terms. The `screen_content()` function should have blocked any drafts containing terms from `BLOCKED_TERMS` or `BLOCKED_WORDS`.

### Step 5: Full run

```bash
cd /ganuda && python3 scripts/deer_linkedin_drafts.py --hours 48 --limit 5
```

## Verification Checklist

- [ ] `--dry-run` lists fuel without calling LLM
- [ ] Drafts saved to `linkedin_drafts` with `status = 'pending'`
- [ ] No internal terms in any saved draft
- [ ] `metadata` contains `thermal_id`, `model_node`, `latency_ms`, `jr_task`
- [ ] Dedup works: re-running does not create duplicate drafts for same thermals
- [ ] Fallback to file works if DB is unreachable
- [ ] Slack notification sent to deer-signals (if Slack is wired)

## Safety

- NEVER auto-posts. All drafts require manual Chief review.
- Sacred thermals excluded by default (opt-in only).
- Content screening blocks 30+ internal terms from appearing in drafts.
- No credentials in code — uses `ganuda_db` secret resolution chain.

## Design Constraints

- **DC-9**: Uses local models (bmasass/redfin), not expensive external APIs.
- **DC-10**: Sub-agent dispatch handles reflex-tier fallback automatically.
- **DC-11**: Same SENSE (query thermals) -> REACT (generate draft) -> EVALUATE (screen content) pattern.
