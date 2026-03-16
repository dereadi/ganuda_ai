# JR INSTRUCTION: Multi-Model Consultation Ring — Outside Code DNA

**Task**: Build an MCP-style multi-model consultation bridge that lets the federation consult external models for second opinions, wrapped in council governance. The organism needs genetic diversity — not just rearranging the same genes.
**Priority**: P2
**Date**: 2026-03-14
**TPM**: Claude Opus
**Story Points**: 8
**Council Vote**: #8d1f1705fa677761 — APPROVED UNANIMOUS (10/10)
**Depends On**: Gateway (redfin), chain protocol, specialist council

## Context

Chief's framing: "Just like I worry that the cluster continuing to work with me only will cause staleness, I worry the same digitally. The human is looking in the digital mirror and thinks we need some outside code DNA."

The playlist analogy: no matter how hard you try to pick differently, you're still the selection function. Your biases are the gravity well. The federation's models all route through the same Sacred Prompts, same council topology, same thermal memory. That's coherence — but it's also monoculture risk.

**Inspiration sources**:
- AndrewAltimit gist (Claude↔Gemini MCP consultation) — the skeleton
- Sakana AI Shinka Evolve (UCB bandit across model pool, MAP-Elites diversity) — the brain
- DC-7 (conserved sequences survive speciation) — the immune system
- DC-11 (same SENSE→REACT→EVALUATE at every scale) — the pattern

**What we're building**: A consultation ring that routes uncertain queries to external models, wraps responses in council governance, and tracks which external model gives the best results per domain via UCB bandit. It wears a necklace. It's a first-class federation citizen, not a bolt-on.

## Step 1: Consultation Ring Service

Create `/ganuda/services/consultation_ring.py` — MCP-compatible server on port 9400.

```python
# Core consultation flow:
# 1. Gateway or council detects uncertainty / requests second opinion
# 2. Consultation ring receives query + context (NEVER Sacred Prompts)
# 3. UCB bandit selects which external model to consult
# 4. Query sent to external model with sanitized context
# 5. Response passes through valence gate (DC alignment check)
# 6. Council-wrapped result returned to caller
```

### Endpoints:
- `POST /consult` — Request external model opinion. Params: `{query, context, domain, urgency}`
- `GET /models` — List available external model backends and their UCB scores
- `GET /health` — Standard necklace health endpoint
- `POST /feedback` — Report whether a consultation was helpful (feeds UCB bandit)
- `GET /stats` — Consultation count, model selection distribution, valence gate rejection rate

### External Model Backends (Phase 1):
- **Gemini** via `gemini` CLI or API (if available on any node)
- **Local alternatives** on bmasass/sasass (MLX models — different training data = different priors)
- **Ollama models** on any node running Ollama
- Future: any OpenAI-compatible endpoint

Each backend is a simple adapter: takes sanitized prompt, returns text response.

## Step 2: Context Sanitizer

Before ANY query goes to an external model, it passes through a sanitizer:

```python
NEVER_SEND = [
    # Sacred Prompts — the conserved sequences
    "sacred_prompt", "painted_on_the_walls",
    # Internal governance topology
    "council_vote", "longhouse", "specialist_council",
    # Infrastructure details
    "192.168.", "10.100.0.", "wireguard", "freeipa",
    # Credentials (obviously)
    "password", "api_key", "secret",
    # Node names (internal jargon)
    "redfin", "bluefin", "greenfin", "owlfin", "eaglefin",
    "sasass", "bmasass", "silverfin",
]

def sanitize_context(context: str) -> str:
    """Strip internal details. The outside model gets the question, not our architecture."""
    # Remove anything matching NEVER_SEND patterns
    # Replace node names with generic labels ("GPU server", "database host")
    # Strip IP addresses, credentials, internal URLs
    # Return clean context suitable for external eyes
```

This is the immune system. DC-7: conserved sequences never leave the organism.

## Step 3: UCB Bandit Model Selector

Implement Upper Confidence Bound algorithm for model selection:

```python
# Each external model has:
# - total_consultations: how many times we've asked it
# - successful_consultations: how many times the response was marked helpful
# - domain_scores: {domain: (successes, total)} — per-domain tracking
#
# UCB formula: score = (successes/total) + C * sqrt(ln(N) / total)
# where N = total consultations across all models, C = exploration constant
#
# This balances exploitation (use the model that's been helpful)
# with exploration (try models we haven't asked much)
```

Store model performance in a table on bluefin:

```sql
CREATE TABLE IF NOT EXISTS consultation_model_stats (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_backend VARCHAR(50) NOT NULL,  -- 'gemini', 'ollama', 'mlx', 'openai'
    domain VARCHAR(100),                  -- 'code_review', 'architecture', 'research', etc.
    total_consultations INTEGER DEFAULT 0,
    successful_consultations INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    last_consulted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_name, domain)
);
```

## Step 4: Valence Gate

External model responses pass through valence scoring before reaching the caller:

```python
def valence_check(response: str, query_domain: str) -> dict:
    """Check if external response aligns with federation ethos.

    Returns: {
        "passed": bool,
        "score": float,  # 0.0 = hostile, 1.0 = fully aligned
        "flags": [],     # any DC violations detected
        "recommendation": str  # "accept", "flag_for_review", "reject"
    }
    """
    # Check for:
    # - Suggestions that contradict known Design Constraints
    # - Recommendations to use external cloud services (sovereignty violation)
    # - Advice that would expose internal architecture
    # - Code patterns that violate our security posture
    # - "Move fast and break things" advice (we build to last — 21-year HP-UX cluster)
```

Three outcomes:
- **Accept** (score > 0.7): Response aligns, pass through
- **Flag for review** (0.3-0.7): Response has useful content but some concerns — annotate and pass with warnings
- **Reject** (< 0.3): Response conflicts with ethos — log it, don't surface it, feed negative signal to UCB bandit

## Step 5: Uncertainty Detection (Auto-Consult Trigger)

Wire into the gateway's tool-call loop. When the primary model's response contains uncertainty markers, automatically trigger consultation:

```python
UNCERTAINTY_MARKERS = [
    "I'm not sure", "I think", "possibly", "probably",
    "it might be", "I'm uncertain", "I don't have enough",
    "this is speculative", "I'm guessing",
]

COMPLEXITY_MARKERS = [
    "trade-off", "alternative approach", "on the other hand",
    "it depends", "there are several ways",
]

# Auto-consult when:
# 1. Primary model uses uncertainty language on a non-trivial query
# 2. Query involves architecture decisions (high stakes)
# 3. Query involves code review of security-sensitive paths
# 4. Explicitly requested by user ("get a second opinion")
```

## Step 6: Chain Protocol Registration

Register as Associate ring in duplo_tool_registry:

```sql
INSERT INTO duplo_tool_registry (
    tool_name, description, module_path, function_name,
    parameters, safety_class, ring_type, provider,
    ring_status
) VALUES (
    'consultation_ring',
    'Multi-model consultation bridge — outside code DNA for the federation',
    'services/consultation_ring.py',
    'consult',
    '{"query": "str", "context": "str", "domain": "str"}',
    'read',
    'Associate',
    'redfin',
    'active'
);
```

Health endpoint on :9400 follows standard necklace format.

## Step 7: Consultation Log (Thermal Integration)

Every consultation gets thermalized for learning:

```python
thermal = {
    "source": "consultation_ring",
    "content": f"CONSULTATION [{model_used}]: Query domain={domain}. "
               f"External model suggested: {summary}. "
               f"Valence score: {valence_score}. "
               f"UCB selection reason: {selection_reason}.",
    "temperature": 60,  # warm but not sacred
    "tags": ["consultation", model_used, domain],
}
```

This creates a thermal trail of what we asked, what we heard, and whether it was useful. The organism remembers what outside DNA was beneficial.

## DO NOT

- Send Sacred Prompts, council topology, or governance internals to ANY external model
- Send IP addresses, node names, credentials, or infrastructure details externally
- Let external models modify federation state (database, kanban, thermal memory) directly
- Auto-accept external model responses without valence gate
- Replace internal models — this is consultation, not delegation
- Use external cloud APIs for the consultation itself if a local alternative exists (sovereignty first)
- Trust external model output more than internal model output by default — the UCB bandit earns trust through track record

## Acceptance Criteria

- Consultation ring runs on port 9400, registered as chain protocol ring
- At least 2 external model backends wired (Gemini + one local alternative)
- Context sanitizer strips all NEVER_SEND patterns before external queries
- UCB bandit selects model and tracks performance per domain
- Valence gate scores responses and rejects DC-violating suggestions
- Uncertainty detection in gateway auto-triggers consultation
- All consultations thermalized with model, domain, valence score
- Health endpoint on :9400 responds to necklace checks
- Can be fully disabled without affecting other federation services (Turtle's requirement)

## Chief's Words (Painted on the Wall)

"Just like I worry that the cluster continuing to work with me only will cause staleness, I worry the same digitally."

The playlist always sounds the same because you're the only one feeding it. This ring brings in a different DJ — but the bouncer (valence gate) still works the door, and the house rules (Sacred Prompts) don't change.
