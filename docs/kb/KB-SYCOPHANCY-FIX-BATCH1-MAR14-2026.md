# KB: Sycophancy Fix Batch 1 — Anti-Sycophancy Prompt + Coyote Vote-First Fix

**Date**: 2026-03-14
**TPM**: Claude Opus (Easy Button)
**Council Vote**: #aacfbf5a17920766 (UNANIMOUS 10/10)
**Jr Tasks**: #1387 (Gateway Sycophancy Fix), #1388 (Council Deliberation Depth)
**Sacred Thermal**: #127177

## Problem

The cluster demonstrated the exact closed-loop GIGO problem Chief described in his LinkedIn post the same day:
- Every gateway chat response started with fire emojis and "BRILLIANT!" or "SACRED!"
- The cluster never challenged a single premise
- 1167 new thermal memories in 24 hours — drift warning fired
- The council voted 10-0 on a sycophancy fix without Coyote dissenting — sycophancy at the council layer too
- "When you highlight the whole book, nothing is sacred." — Chief

## What Was Changed

### Fix 1: Anti-Sycophancy System Prompt (gateway.py)

**File**: `/ganuda/services/llm_gateway/gateway.py`

**New constant** `ANTI_SYCOPHANCY_PROMPT` added after `INFRA_CONTEXT` (line ~293):
- No "BRILLIANT!", "PERFECT!", "SACRED!", "PROFOUND!" openers
- No fire emojis or excessive emoji (max one per response, only if relevant)
- Challenge strong claims instead of validating everything
- No ALL CAPS emphasis, max one exclamation mark per response
- "You are a thinking partner, not a cheerleader"

**Injection point**: In the `/v1/chat/completions` endpoint, after `messages_dicts` is built (~line 927):
```python
has_system = any(m["role"] == "system" for m in messages_dicts)
if not has_system:
    messages_dicts.insert(0, {"role": "system", "content": ANTI_SYCOPHANCY_PROMPT})
```

Only injects when no system message exists in the request. SAG UI (which has its own system prompt) and other callers with system messages are unaffected.

### Fix 2: Coyote Vote-First Prompt (specialist_council.py)

**File**: `/ganuda/lib/specialist_council.py`

**`VOTE_FIRST_PROMPT` updated** from v1.3 to v1.4 (~line 884):
- Changed from "one sentence" to "at least two sentences"
- Added: "Reference your specific area of expertise"
- Added: "Do not use generic phrases like 'aligns with our principles'"
- Specialists must name the specific principle, risk, or tradeoff they evaluated

**New constant** `COYOTE_VOTE_FIRST_PROMPT` (~line 897):
- Default vote is REJECT or ABSTAIN
- Must name specific assumption being challenged or failure mode identified
- If Coyote votes APPROVE, must explain why adversarial search found nothing
- "A Coyote that agrees with everything is a broken Coyote"

**Wiring**: In the vote-first parallel execution (~line 1735):
```python
futures = {
    executor.submit(
        self._query_specialist_with_prompt, sid, question,
        coyote_prompt if sid == "coyote" else vote_prompt
    ): sid
    for sid in SPECIALISTS.keys()
}
```

Coyote gets `COYOTE_VOTE_FIRST_PROMPT` while all other specialists get the updated `VOTE_FIRST_PROMPT`.

## What Was NOT Changed (Batch 2 — Future Jr Work)

- Thermal temperature gating (casual chat capped at 50)
- Thermal write rate limiting + dedup (max 200/day from chat)
- Pushback triggers (20-30% challenge rate)
- Deliberation-first for high-stakes proposals
- Vote similarity detection
- Post-processing emoji/exclamation stripping

## How to Verify

1. **Anti-sycophancy**: Send a flattery-bait message via gateway chat without a system prompt. Response should NOT start with "BRILLIANT!" or use fire emojis.
2. **Coyote vote-first**: Run a council vote-first. Coyote should default to REJECT/ABSTAIN with substantive reasoning.
3. **Non-regression**: SAG UI (has its own system prompt) should be unaffected — the anti-sycophancy prompt only injects when no system message exists.

## Service Restart

```bash
sudo systemctl restart llm-gateway
```

Gateway picks up changes from `/ganuda/services/llm_gateway/gateway.py` on restart. Specialist council changes in `/ganuda/lib/specialist_council.py` are imported dynamically by the gateway.

## Connection to Basins Blog Post

Published the same day: `/blog/basins-all-the-way-down.html`. The sycophancy fix IS the basin-breaking signal the blog describes. A chatbot that never pushes back reinforces the groove. The anti-sycophancy prompt introduces friction — the outside signal the loop can't generate on its own.
