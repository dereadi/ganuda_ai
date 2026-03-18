# EPIC: Consultation Ring Phase 2 — IP-Safe Multi-Model Consultation

**Epic ID**: CONSULT-RING-P2
**Date**: 2026-03-18
**TPM**: Claude Opus
**Total Story Points**: 13
**Council Vote**: #fa5922e4e1ae9d3a (APPROVED WITH CONDITIONS)
**Depends On**: Consultation Ring Phase 1 (LIVE on :9400), Domain Tokenizer, Frontier Adapters, UCB Bandit, Valence Gate
**Thermal Context**: Gemini triad study (temp 80), chirality research cooling period

## Problem Statement

The consultation ring (Phase 1) tokenizes infrastructure details — node names, IPs, internal jargon — before sending queries to frontier models. But it cannot tokenize IDEAS. When Partner ran the chirality hypothesis through Gemini in a blind triad study, Gemini received the full hypothesis. That is intellectual property leakage.

We need diverse cognitive DNA from frontier models to avoid monoculture brittleness (DC-11). But we need to protect novel IP — hypotheses, architectural patterns, strategic insights — that represent competitive advantage and patent-pending work.

The rule: **frontier models see the questions, never the connections between them.**

## Council Design Inputs

- **Coyote (DISSENT)**: Decomposed consultation creates false confidence. Models infer context from fragments. Enough related atomic claims to one provider = reconstruction risk. Need fragment correlation budget.
- **Turtle (7GEN)**: Shared ideas are irreversible — in the model's feedback loop forever. Patent filing before broad consultation is the only truly reversible pattern.
- **Crawdad (SECURITY)**: Synthesis must run in secure environment. Exposure log mandatory — audit every claim, every provider, every timestamp.
- **Eagle Eye (MONITORING)**: Watch for contextual clue leakage. Monitor response consistency — if a model's response implies knowledge of our broader framework, flag it.
- **Gecko (RESOURCES)**: Lightweight. +5ms per decomposed query. Feasible on existing infra.
- **Raven (STRATEGY)**: Don't rush. Queue behind in-flight P0 work.
- **Spider (DEPS)**: Synthesis engine is the new critical path component.

## Architecture

### Data Flow (Phase 2 Extension)

```
POST /consult (query, context, domain, ip_classification)
  → IPClassifier.classify() — operational / architectural / novel_ip
  │
  ├─ IF operational: Phase 1 flow (tokenize infra, send direct)
  │
  ├─ IF architectural: AnonymizationEngine.anonymize() — strip patterns to generic
  │   → Phase 1 flow with anonymized query
  │
  └─ IF novel_ip: DecompositionEngine.decompose()
      → FragmentRouter.route() — spread fragments across providers (correlation budget)
      → For each fragment: Phase 1 flow (tokenize + send to assigned provider)
      → SynthesisEngine.synthesize() — re-integrate on redfin (NEVER on frontier)
      → ExposureLog.record() — what went where, when
      → ValenceGate.score() — standard DC check on synthesized response
      → Return synthesized response + exposure metadata
```

### Component 1: IP Classifier (`lib/ip_classifier.py`)

Three-tier classification of outbound queries:

| Classification | Definition | Example | Action |
|---|---|---|---|
| `operational` | Infrastructure, status, troubleshooting | "How do I configure PgBouncer?" | Phase 1 direct (tokenize infra only) |
| `architectural` | Design patterns, topology, methodology | "What are the tradeoffs of star vs mesh topology for multi-agent systems?" | Anonymize to generic, then Phase 1 |
| `novel_ip` | Original hypotheses, patent-pending work, competitive insights | "Is biological chirality a framework for understanding AI governance?" | Decompose, distribute, synthesize locally |

**Implementation**: Pattern matching + keyword detection in v1. The classifier checks:
- Does the query reference internal project names, codenames, or branded concepts? → novel_ip
- Does the query describe our specific architecture without naming it? → architectural
- Is this a general technical question? → operational

Caller can override with explicit `ip_classification` parameter. Default: classifier decides.

### Component 2: Decomposition Engine (`lib/decomposition_engine.py`)

Breaks a novel_ip query into atomic claims that are individually innocuous.

**Input**: Full query + context
**Output**: List of atomic claims, each tagged with:
- `claim_id`: unique identifier
- `claim_text`: the decomposed question
- `correlation_group`: which claims are related (for routing budget)
- `sensitivity_score`: 0-1, how much this claim alone reveals

**Decomposition strategies**:
1. **Literature decomposition**: Convert "Is X a framework for Y?" into separate questions about X and Y independently
2. **Component isolation**: Break architectural descriptions into individual pattern questions
3. **Adversarial reframing**: Convert validation questions into attack questions ("What are the weaknesses of X?")
4. **Domain generalization**: Strip domain-specific context, ask the general principle question

**Example**:
- INPUT: "Does the chirality framework explain why AI governance fails?"
- OUTPUT:
  - Claim A: "What is the current state of research applying chirality concepts outside biochemistry?" (correlation_group: 1)
  - Claim B: "What are the primary failure modes of institutional AI governance?" (correlation_group: 2)
  - Claim C: "Are there frameworks comparing biological and computational information processing as symmetric systems?" (correlation_group: 1)
  - Claim D: "What role does substrate asymmetry play in multi-agent system design?" (correlation_group: 2)

Claims A and C share correlation_group 1 — they MUST go to different providers.

### Component 3: Fragment Router (`lib/fragment_router.py`)

Enforces Coyote's constraint: no single provider gets enough correlated fragments to reconstruct the hypothesis.

**Rules**:
1. **Correlation budget**: Claims in the same correlation_group go to DIFFERENT providers
2. **Provider diversity**: Spread claims across all enabled providers (Anthropic, OpenAI, Gemini, local)
3. **Session isolation**: Each claim gets its own session/conversation. No multi-turn threading to a single provider.
4. **Maximum exposure per provider**: No provider sees more than ceil(N/providers) claims from one decomposition
5. **Local preference for sensitive claims**: Claims with sensitivity_score > 0.7 go to local models (sasass2/bmasass) — our DNA stays home

**Integration with UCB Bandit**: The bandit selects the best provider per claim, but the router can VETO a selection that violates the correlation budget. Bandit picks from the remaining eligible providers.

### Component 4: Synthesis Engine (`lib/synthesis_engine.py`)

Re-integrates decomposed responses locally. This is the critical path — synthesis NEVER happens on a frontier model.

**Input**: List of (claim, response) pairs from multiple providers
**Output**: Synthesized answer to the original query

**Implementation**:
- v1: Local model synthesis (Qwen-72B on redfin). Feed all claim/response pairs plus the original query to local vLLM. Local model connects the dots.
- v2: Template-based synthesis for common decomposition patterns (literature review, adversarial analysis)

**Security constraint**: The synthesis prompt includes the original un-decomposed query. This prompt NEVER leaves redfin. It goes to local vLLM only.

### Component 5: Exposure Log (`lib/exposure_log.py`)

Crawdad's requirement. Every outbound claim is logged.

**Schema** (new table: `consultation_exposure_log`):
```sql
CREATE TABLE consultation_exposure_log (
    id SERIAL PRIMARY KEY,
    consultation_id UUID NOT NULL,
    claim_id VARCHAR(64) NOT NULL,
    claim_text TEXT NOT NULL,
    correlation_group INTEGER,
    sensitivity_score FLOAT,
    provider VARCHAR(32) NOT NULL,
    ip_classification VARCHAR(16) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    original_query_hash VARCHAR(64) NOT NULL  -- hash of original, never the original itself
);
CREATE INDEX idx_exposure_provider ON consultation_exposure_log(provider);
CREATE INDEX idx_exposure_timestamp ON consultation_exposure_log(timestamp);
CREATE INDEX idx_exposure_query_hash ON consultation_exposure_log(original_query_hash);
```

**Queries this enables**:
- "What has Anthropic seen from us?" — filter by provider
- "How much of the chirality hypothesis is exposed?" — filter by query_hash
- "Are we over-exposing to one provider?" — aggregate by provider over time
- "What is our total exposure surface?" — count distinct claims by classification

### Component 6: Reconstruction Risk Monitor (`lib/reconstruction_monitor.py`)

Eagle Eye + Coyote's requirement. Monitors whether fragment distribution is safe.

**Checks**:
1. **Per-provider reconstruction score**: Given all claims a provider has seen (across all consultations), could they reconstruct a novel_ip hypothesis? Score based on correlation group coverage.
2. **Cross-session inference risk**: If provider X saw claim A in January and claim C in March, and A+C are in the same correlation group — flag it. Even across sessions, fragments accumulate.
3. **Response inference detection**: If a provider's response to an atomic claim references concepts from a DIFFERENT claim we sent them — the provider is connecting dots. Immediate flag.

**Alert thresholds**:
- Provider has seen >50% of correlation groups for any novel_ip query → WARNING
- Provider response references unsent context → CRITICAL
- Any single provider has >60% of all novel_ip claims in 30 days → WARNING

## Jr Tasks (Long Man Decomposition)

### P-3: Foundation

| Task | Title | SP | Deps |
|---|---|---|---|
| #1 | DB Migration: consultation_exposure_log table + indexes | 1 | PostgreSQL (bluefin) |
| #2 | IP Classifier: three-tier classification (operational/architectural/novel_ip) | 2 | consultation_ring.py |
| #3 | Exposure Log: write/query functions + audit trail | 1 | Task #1 |

### P-2: Decomposition

| Task | Title | SP | Deps |
|---|---|---|---|
| #4 | Decomposition Engine: break queries into atomic claims with correlation groups | 3 | Task #2 |
| #5 | Fragment Router: correlation budget enforcement + provider diversity + local preference | 2 | Task #4, UCB Bandit |

### P-1: Synthesis + Monitoring

| Task | Title | SP | Deps |
|---|---|---|---|
| #6 | Synthesis Engine: local-only re-integration via vLLM | 2 | Task #5 |
| #7 | Reconstruction Risk Monitor: per-provider scoring + cross-session tracking + alerts | 2 | Task #3, Task #5 |

### P-Day: Integration

| Task | Title | SP | Deps |
|---|---|---|---|
| #8 | Wire Phase 2 into consultation_ring.py: /consult endpoint with ip_classification routing | 0 | Tasks #2-#7 |

**Total: 13 SP, 8 Jr tasks, P-3 through P-Day**

## Verification

1. **Decomposition round-trip**: Submit a novel_ip query. Verify decomposed claims are individually innocuous — a human reading any single claim cannot identify the parent hypothesis.
2. **Correlation budget enforcement**: Submit a query with 4 claims in 2 correlation groups. Verify no provider receives both claims from the same group.
3. **Local preference**: Submit a claim with sensitivity_score > 0.7. Verify it routes to local model, not frontier.
4. **Exposure log audit**: After 10 consultations, query the exposure log. Verify complete audit trail — every claim, every provider, every timestamp.
5. **Reconstruction risk alert**: Artificially send related claims to the same provider. Verify the monitor flags the reconstruction risk.
6. **Response inference detection**: If a provider's response to claim A mentions concepts only present in claim C (sent separately), verify the monitor fires CRITICAL.
7. **Synthesis locality**: Verify the synthesis prompt (containing the original query) NEVER appears in any outbound network traffic. It stays on redfin.

## Design Constraints Satisfied

- **DC-1 (Sovereignty)**: Novel IP stays local. Synthesis on redfin only. Token map never crosses.
- **DC-3 (Security)**: Exposure log audits all outbound claims. Reconstruction monitor watches for accumulation.
- **DC-7 (Build to Last)**: Decomposition strategies and variation templates are JSON configs. Framework is disposable; pattern is permanent.
- **DC-9 (Waste Heat)**: Fragment router respects rate limits. Decomposed queries cost more tokens but spread across providers.
- **DC-11 (Interface Conservation)**: Phase 2 extends Phase 1 /consult endpoint. Same API, new ip_classification parameter. Backwards compatible.

## Coyote's Standing Challenge

"Decomposed consultation creates false confidence." This is addressed by the Reconstruction Risk Monitor, but Coyote's deeper point stands: we are in an arms race with model intelligence. As models get better at inferring context, our decomposition must get better at obscuring it. The reconstruction risk thresholds should be reviewed quarterly and tightened as model capabilities increase.

The ultimate answer remains Turtle's: file the patent. Then exposure becomes marketing.
