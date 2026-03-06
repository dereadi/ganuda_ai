# Jr Instruction: Wire Chief PA Through Harness

**Task**: Modify Chief PA daily briefing to route through the Graduated Harness instead of raw LLM calls
**Kanban**: #1961 (Daily Briefing Generator)
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**DC-10 Alignment**: Chief PA is the first consumer of the reflex arc

## Context

Chief PA (`services/chief_pa/daily_briefing.py`) currently makes direct LLM calls.
It should route through the Harness so that:
- Simple status queries use Tier 1 (fast, cheap)
- Complex analysis escalates to Tier 2 (multi-specialist)
- Sacred/constitutional topics reach Tier 3 (full Council)

The harness handles all routing automatically. Chief PA just needs to send a HarnessRequest.

## Steps

### Step 1: Add harness helper to Chief PA

File: `/ganuda/services/chief_pa/daily_briefing.py`

Find the import section at the top and add:

<<<<<<< SEARCH
import logging
=======
import logging
from lib.harness.core import HarnessRequest
from lib.harness.config import load_harness_config
from lib.harness.escalation import EscalationEngine
from lib.harness.tier1_reflex import Tier1Reflex
from lib.harness.tier2_deliberation import Tier2Deliberation
>>>>>>> REPLACE

Then find any function that makes a direct LLM call (look for `requests.post` to a `/v1/chat/completions` endpoint) and add a harness-aware alternative. Do NOT remove the existing direct call -- add a `use_harness` flag so we can toggle.

Find the class or module-level initialization area and add:

```python
# Harness integration (DC-10)
_harness_engine = None

def _get_harness():
    global _harness_engine
    if _harness_engine is not None:
        return _harness_engine
    config = load_harness_config()
    engine = EscalationEngine(config)
    if config.tier1.enabled:
        engine.register_tier(1, Tier1Reflex(config.tier1))
    if config.tier2.enabled:
        engine.register_tier(2, Tier2Deliberation(config.tier2))
    _harness_engine = engine
    return _harness_engine


def harness_query(query, context=None, user_id="chief_pa"):
    """Route a query through the graduated harness."""
    engine = _get_harness()
    req = HarnessRequest(
        query=query,
        context=context or {},
        user_id=user_id,
    )
    resp = engine.handle_request(req)
    return resp.answer, resp.tier_used, resp.confidence
```

Note: We intentionally skip Tier 3 in Chief PA. Daily briefings should never trigger a full Council vote. If the query needs Council-level deliberation, the briefing should flag it for human review instead.

## Verification

```text
python3 -c "
from services.chief_pa.daily_briefing import harness_query
answer, tier, conf = harness_query('What are the top 3 priorities for today?')
print(f'Tier: {tier}, Confidence: {conf:.3f}')
print(f'Answer: {answer[:200]}')
"
```

Expected: Returns an answer from Tier 1 or Tier 2. No Tier 3 invocation.
