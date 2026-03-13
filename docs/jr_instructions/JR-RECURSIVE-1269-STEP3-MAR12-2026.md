# [RECURSIVE] Chain Protocol: Associate/Temp Ring Registry + Dispatch Library - Step 3

**Parent Task**: #1269
**Auto-decomposed**: 2026-03-12T18:03:02.138066
**Original Step Title**: Seed Associate Rings in Registry

---

### Step 3: Seed Associate Rings in Registry

**File:** `/ganuda/scripts/migrations/chain_protocol_schema.sql`

```sql
-- Seed Associate rings (permanent)
INSERT INTO duplo_tool_registry (name, ring_type, provider, ring_status, canonical_schema)
VALUES
('claude_opus', 'associate', 'anthropic', 'active', '{"input": "text", "output": "text", "tier": "strategic"}'),
('claude_sonnet', 'associate', 'anthropic', 'active', '{"input": "text", "output": "text", "tier": "content"}'),
('claude_haiku', 'associate', 'anthropic', 'active', '{"input": "text", "output": "text", "tier": "screening"}'),
('qwen_72b', 'associate', 'local_redfin', 'active', '{"input": "text", "output": "text", "tier": "reasoning"}'),
('qwen_vl_7b', 'associate', 'local_bluefin', 'active', '{"input": "image+text", "output": "text", "tier": "vision"}'),
('qwen3_30b', 'associate', 'local_bmasass', 'active', '{"input": "text", "output": "text", "tier": "fast_reasoning"}'),
('llama_70b', 'associate', 'local_bmasass', 'active', '{"input": "text", "output": "text", "tier": "direct_reasoning"}'),
('bge_large', 'associate', 'local_greenfin', 'active', '{"input": "text", "output": "vector_1024", "tier": "embedding"}')
ON CONFLICT DO NOTHING;
```

## Constraints

- **Coyote condition**: Provenance tagging is IMMUTABLE. No process can upgrade external-sourced thermal to sacred. Independent Associate must re-verify and create new internal thermal.
- **Coyote condition**: Adversarial test suite for Outbound Scrub Ring must pass before any external ring goes live.
- **Ring Budget**: Max 20% external rings. Enforced in `check_ring_budget()`. Longhouse vote to expand.
- **DC-9**: Ring Metering auto-throttles on daily cost budget exceeded.
- **DC-7**: Chain protocol is a conserved sequence. Ring implementations speciate; the chain interface does not.
- **Schema versioning**: Lock v1 canonical schema before first external ring dispatch.
- No API keys in this code. External ring credentials stored in secrets.env or provider-specific config.

## Target Files

- `/ganuda/scripts/migrations/chain_protocol_schema.sql` — DB schema (CREATE)
- `/ganuda/lib/chain_protocol.py` — dispatch library (CREATE)
- `/ganuda/docs/kb/KB-CHAIN-PROTOCOL-ASSOCIATE-TEMP.md` — architecture doc (CREATE)

## Acceptance Criteria

- `python3 -c "import py_compile; py_compile.compile('lib/chain_protocol.py', doraise=True)"` passes
- Migration creates `ring_health` and `scrub_rules` tables
- `duplo_tool_registry` has new columns: `ring_type`, `provider`, `canonical_schema`, `removal_procedure`, `calibration_schedule`, `cost_budget_daily`, `ring_status`, `schema_version`, `last_calibration`, `drift_score`
- 8 Associate rings seeded in registry
- `outbound_scrub("the redfin server at 192.168.132.223")` returns violations
- `outbound_scrub("AI governance patterns in distributed systems")` returns empty list
- `check_ring_budget()` returns correct counts
- `tag_provenance()` returns correct trust_tier (1 for associate, 3 for temp)
- No API keys in any file
- Scrub rules table seeded with all blocked terms from `deer_linkedin_drafts.py`

## DO NOT

- Store API keys in scripts or config files checked into git
- Allow external-sourced thermals to reach sacred status without Associate re-verification
- Dispatch to external rings without passing outbound scrub
- Add external rings that would exceed the 20% budget without Longhouse vote
- Remove the provenance tag from any thermal after it is written
