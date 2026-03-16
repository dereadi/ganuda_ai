# JR INSTRUCTION: Wire the Council to the Consultation Ring Triad

**Task**: Connect the 9-specialist Council to the Consultation Ring so the Council can request parallel frontier model perspectives during deliberation.
**Priority**: P1
**Date**: 2026-03-14
**TPM**: Claude Opus
**Story Points**: 5
**Depends On**: Consultation Ring service (port 9400, LIVE), specialist_council.py, frontier_adapters.py
**Council Votes**: #722d822dd3bda167 (1-pass parallel — APPROVED), #05ed7f5f4caa9c17 (architecture wiring — APPROVED)

## Context

The Consultation Ring launched today with 4 frontier adapters (Anthropic Claude, OpenAI GPT-4o, Google Gemini, Local Qwen). It tokenizes queries, scrubs outbound, dispatches to frontier models, valence-gates responses, and detokenizes. But it's a standalone service — nothing inside the federation calls it. The Council's 9 specialists can only reach local models (Qwen on redfin vLLM, Qwen3/Llama on bmasass).

Partner proposed: the Triad makes exactly ONE pass — sending the tokenized query to all 3 frontier models in parallel simultaneously. Each model returns its perspective — not disagreeing, just incomplete. Three sides of the same picture. The Council then synthesizes the three views with its 9 specialists.

**DC-10 mapping**: Triad = reflex layer (fast, parallel, one shot). Council = deliberation layer (synthesize, narrow, clarify).

## Binding Conditions (from Council votes)

These are non-negotiable. The Council voted on them:

1. **Trigger authority**: Only **Raven** (strategy) or **Peace Chief** (consensus) can trigger a frontier consultation. No other specialist can autonomously dispatch to external models.
2. **Coyote veto**: Coyote retains veto power over any external dispatch. If Coyote dissents on sending a query outside, the query stays local.
3. **Weighting**: Frontier responses weighted **30%**, local specialist knowledge weighted **70%**. The Council's own reasoning is primary. Frontier provides signal, not authority.
4. **Opt-in, not automatic**: The Council decides when outside signal is needed. No automatic frontier dispatch on Tier 3 queries. A specialist must explicitly request consultation.
5. **Synthesis mechanism**: Weighted merge with local bias. NOT majority vote across frontier responses. The Council synthesizes — it doesn't outsource judgment.
6. **Dependency prevention**: Quarterly internal-only deliberation drills. The Council must practice reasoning without frontier input to prevent capability atrophy.
7. **Observability**: Eagle Eye logs every frontier consultation — domain, cost, latency, whether frontier signal changed the Council's outcome. This data feeds back into the UCB bandit.

## Architecture

### New Function: `council_consult_triad()`

Add to `/ganuda/lib/specialist_council.py`:

```python
async def council_consult_triad(query: str, context: str, domain: str = "general") -> dict:
    """
    Dispatch query to all 3 frontier models in parallel via consultation ring.
    Returns dict with three perspectives for Council synthesis.

    Only callable by Raven or Peace Chief. Coyote can veto.
    """
```

### Flow

```
Council receives Tier 3 query
  → Raven or Peace Chief determines outside signal needed
  → Coyote veto check (if Coyote dissents, stay local)
  → DomainTokenizer.tokenize(query) — PII + infra → opaque tokens
  → chain_protocol.outbound_scrub() — NEVER_SEND enforcement
  → asyncio.gather(
      anthropic_adapter.send(tokenized_query),
      openai_adapter.send(tokenized_query),
      gemini_adapter.send(tokenized_query),
    )  — ONE pass, all 3 in parallel
  → For each response:
      → web_ring.sanitize_inbound() — strip injection patterns
      → valence_gate.score() — DC alignment check
  → DomainTokenizer.detokenize() — restore original terms in all 3
  → Package as triad_perspectives = {
      "anthropic": {"text": ..., "valence": ..., "latency_ms": ...},
      "openai":    {"text": ..., "valence": ..., "latency_ms": ...},
      "gemini":    {"text": ..., "valence": ..., "latency_ms": ...},
    }
  → Council specialists receive triad_perspectives as additional context
  → Each specialist weighs: 70% own reasoning + 30% frontier signal
  → Council synthesizes unified response
  → Eagle Eye logs: consultation_id, domain, cost, latency, outcome_changed
  → Thermalize with source="council_triad_consultation"
```

### Key Design Decisions

1. **Do NOT call the consultation ring HTTP endpoint internally.** Import `frontier_adapters.get_adapters()` directly and call adapters in-process. Avoids HTTP overhead, rate limit contention, and double-tokenization. The consultation ring HTTP service is for external callers (Telegram, gateway). The Council uses the same adapters directly.

2. **Parallel dispatch via `asyncio.gather()`**. All 3 frontier calls happen simultaneously. Total latency = max(individual latencies), not sum. Typical: 15-45 seconds for all 3.

3. **Valence gate on EACH response independently.** A rejected frontier response is replaced with `{"text": "[REJECTED: {reason}]", "valence": score}`. The Council sees the rejection reason but not the rejected content. This is a feature — the Council learns which providers produce DC-misaligned responses for which domains.

4. **Token map stays in specialist_council.py process memory.** Same security boundary as the consultation ring. Never persisted, never transmitted.

5. **The `triad_perspectives` dict is passed as additional context to each specialist's prompt.** Format:
   ```
   FRONTIER CONSULTATION (weight: 30% — your own analysis carries 70%):

   [Claude]: {anthropic response or REJECTED}
   [GPT-4o]: {openai response or REJECTED}
   [Gemini]: {gemini response or REJECTED}

   Synthesize these perspectives with your own expertise. Note where they agree,
   where they differ, and where they are each incomplete. Your specialist knowledge
   takes priority.
   ```

## Files to Modify

| File | Change |
|------|--------|
| `/ganuda/lib/specialist_council.py` | Add `council_consult_triad()` async function. Add `_should_consult_triad()` decision function. Import frontier_adapters, domain_tokenizer, valence_gate. Modify council deliberation flow to optionally include triad perspectives. |
| `/ganuda/lib/harness/tier3_council.py` | Pass `allow_triad=True` flag to specialist_council when query context suggests outside signal needed. |
| `/ganuda/services/sag-v2/gateway.py` | Add `consult_triad: bool` optional parameter to council vote endpoint. Default false. |

## New Table (Migration)

```sql
-- Track when the Council uses frontier consultation and whether it changed outcomes
CREATE TABLE IF NOT EXISTS council_triad_consultations (
    id SERIAL PRIMARY KEY,
    vote_audit_hash VARCHAR(64),
    domain VARCHAR(50) DEFAULT 'general',
    query_hash VARCHAR(64),
    providers_called TEXT[] DEFAULT '{}',
    providers_succeeded TEXT[] DEFAULT '{}',
    providers_rejected TEXT[] DEFAULT '{}',
    total_cost NUMERIC(10,6) DEFAULT 0,
    total_latency_ms INTEGER DEFAULT 0,
    outcome_changed BOOLEAN DEFAULT false,
    outcome_changed_how TEXT,
    triggered_by VARCHAR(50),  -- 'raven' or 'peace_chief'
    coyote_vetoed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ctr_domain ON council_triad_consultations(domain);
CREATE INDEX idx_ctr_changed ON council_triad_consultations(outcome_changed) WHERE outcome_changed = true;
```

## DO NOT

- Call the consultation ring HTTP endpoint from inside the federation — use adapters directly
- Allow any specialist other than Raven or Peace Chief to trigger frontier consultation
- Skip the Coyote veto check
- Weight frontier responses above 30%
- Make frontier consultation automatic — it must be opt-in
- Persist token maps beyond the request lifecycle
- Skip valence gate on any frontier response

## Acceptance Criteria

- [ ] `council_consult_triad()` dispatches to all 3 frontier models in parallel
- [ ] Only Raven or Peace Chief can trigger (other specialists get "unauthorized" error)
- [ ] Coyote veto prevents dispatch (logged, query stays local-only)
- [ ] Each frontier response passes through valence gate independently
- [ ] Specialists receive triad_perspectives with 30% weighting instruction
- [ ] Eagle Eye logs every consultation to council_triad_consultations table
- [ ] Rejected frontier responses show reason but not content
- [ ] Token map never leaves process memory
- [ ] Council can deliberate normally (local-only) when triad not requested
- [ ] End-to-end test: query with `consult_triad=true` returns synthesized response with provenance showing all 3 providers
- [ ] Quarterly drill mechanism: config flag `triad_drill_mode: true` disables frontier calls for practice periods

## Council Specialist Input (from vote #05ed7f5f4caa9c17)

**Raven**: Only Raven and Peace Chief should trigger. Weight frontier 30%, local 70%. Regular internal deliberation drills to prevent dependency.

**Coyote**: [DISSENT] "What if the frontier models are influenced by external biases or have their own agenda? We need a mechanism to vet and validate the external signals before they influence our internal deliberations." → Addressed by valence gate + Coyote veto power.

**Turtle**: [7GEN CONCERN] "Will this architecture ensure that the Council remains self-sufficient and wise, or does it risk creating a dependency?" → Addressed by 70/30 weighting, opt-in only, quarterly drills.

**Spider**: Flagged tight coupling risk with frontier model availability. → Addressed by graceful degradation — if a frontier model fails, Council proceeds with remaining responses (or local-only).

**Crawdad**: CRITICAL threat — data sovereignty. → Addressed by domain tokenizer + NEVER_SEND + chain protocol outbound scrub. Token map never crosses boundary.

**Eagle Eye**: Failure mode table provided. Key SLAs: frontier unavailability <10min recovery, valence gate failure <15min. → Observability table tracks all of this.

**Gecko**: Network overhead estimate: ~1.2KB per query across 3 models. Tokenization overhead <10ms. Manageable.

**Peace Chief**: Consensus on unified answer, weighting mechanism, and dependency prevention. Gaps: synthesis mechanism (now specified as weighted merge) and frequency limits (now opt-in).
