# Design: Reflex Wrapper for Sharded 405B Inference

**Date**: March 6, 2026
**Origin**: Chief directive — "solve for the latency as a wrapper to get the shards to function more in unison. Reflex in a different fashion outside the shards."
**Design Constraints**: DC-10 (Reflex Principle), DC-11 (Macro Polymorphism), DC-9 (Waste Heat Limit), DC-1 (Lazy Awareness)
**Long Man Stage**: DISCOVER -> DELIBERATE
**Cross-pollination**: Legion (Virtual Rome) gets more guardrails. We get retrospective learning. Same problem, different governance metaphors.

## Problem

Distributed inference across Apple Silicon nodes (thunderbolt interconnect) has inherent latency:
- TB3 (M1 Max): ~300us per hop, no RDMA
- TB4 (M4 Max): ~200us per hop, no RDMA
- TB5 (future M5): ~3us with RDMA — 100x improvement, not available yet

Sharding a 405B model across thunderduck (M4 Max 128GB) + bmasass (M4 Max 128GB) = 256GB combined. Model fits (~200GB at 4-bit). But inter-node latency means ~1-3 tok/s throughput.

**The wrong question**: How do we make the shards faster?
**The right question**: How do we make latency irrelevant?

## Solution: Reflex Wrapper

Don't put the sharded 405B in the hot path. Wrap it in a dispatcher that fires both fast and slow paths in parallel.

```
               +---> [TIER 1 REFLEX] redfin Qwen 72B
               |     Response in ~1s. SHIP IMMEDIATELY.
               |
  Request ---->+
               |
               +---> [TIER 3 DELIBERATE] 405B sharded (thunderduck + bmasass)
                     Response in 10-30s. Async.
                     On completion:
                       CONFIRM  — reflex was right (log, no action)
                       ENRICH   — reflex was thin (store richer answer, notify if needed)
                       VETO     — reflex was wrong (flag, escalate, learn)
```

### Why This Works

1. **User never waits.** The reflex path ships a good-enough answer immediately.
2. **Council always deliberates.** The 405B path runs at whatever speed physics allows.
3. **Learning is automatic.** Every CONFIRM/ENRICH/VETO pair is a training signal — the reflex learns what the full council would have said.
4. **Latency is irrelevant.** The shards don't need to be fast. They need to be RIGHT.

### Precedents

| Domain | Fast Path | Slow Path | Reconciliation |
|--------|-----------|-----------|----------------|
| CPU | Branch prediction | Full execution | Rollback if mispredicted |
| Trading | SA best-so-far (100ms) | Gurobi optimal (seconds) | Replace if better |
| Human nervous | Spinal reflex (flinch) | Prefrontal cortex (think) | Correct if wrong |
| Federation | Qwen 72B reflex | 405B council | CONFIRM / ENRICH / VETO |

### Hardware Topology

```
TIER 1 REFLEX (< 1s)
  redfin (RTX PRO 6000 96GB)
    └── Qwen2.5-72B-Instruct-AWQ via vLLM
    └── ~32 tok/s, full CUDA acceleration

TIER 2 PAUSE (1-5s)
  bmasass (M4 Max 128GB) — single node models
    ├── Qwen3-30B-A3B on port 8800 (fast MoE, thinking mode)
    └── Llama-3.3-70B on port 8801 (direct, no thinking overhead)
  thunderduck (M4 Max 128GB) — single node models
    └── Llama-3.3-70B on port 8800 (DNA diversity, redundancy)

TIER 3 DELIBERATE (10-30s)
  thunderduck + bmasass SHARDED (256GB combined)
    └── Llama-405B-Instruct-4bit (~200GB) via prima.cpp
    └── ~1-3 tok/s — DOES NOT MATTER, not in hot path
    └── Wrapper dispatches async, reconciles on completion
```

### Wrapper Components

1. **Dispatcher** (gateway layer, redfin)
   - On qualifying requests: fire reflex AND deliberate in parallel
   - Reflex result ships to caller immediately
   - Deliberate result arrives async, stored with reflex result

2. **Reconciler** (new component)
   - Compares reflex vs deliberate responses
   - Classifies: CONFIRM / ENRICH / VETO
   - Stores pair as thermal memory (training signal)
   - On VETO: notify via telegram, store correction

3. **Routing Policy** (which requests get both paths?)
   - Sacred fire tasks: ALWAYS dual-path
   - Council votes: ALWAYS dual-path
   - Routine queries: reflex only (DC-9, don't waste heat)
   - Explicit request: user can force dual-path

### Upgrade Path

When TB5 hardware arrives (M5 Max, expected late 2026):
- Sharded latency drops 100x (300us -> 3us)
- 405B throughput jumps to ~15-30 tok/s
- Tier 3 becomes fast enough for hot-path use
- Wrapper pattern still valuable for DC-9 (why burn 405B tokens when 72B suffices?)

## Retrospective Sub-Council: The EVALUATE Layer

**Origin**: Chief directive — "Would that mean that a sub council would be doing retrospective after each event?"

### DC-11 Macro Polymorphism: SENSE -> REACT -> EVALUATE at Every Scale

The retrospective is not a new council. It is the EVALUATE step of DC-11, instantiated at the request scale. The same pattern already runs at other scales:

| Scale | SENSE | REACT (Reflex) | EVALUATE (Retrospective) |
|-------|-------|-----------------|--------------------------|
| Token | logprob | next token generated | confidence score |
| Request | user query | Qwen 72B reflex (1s) | **405B retrospective (10-30s)** |
| Session | conversation arc | council vote | proto-valence (precompact hook) |
| Sprint | kanban backlog | Jr builds | Owl debt reckoning |
| Federation | thermal drift signal | circuit breaker fires | dawn mist standup |

DC-11 says the interface is conserved, the implementation speciates (DC-7). We are not inventing a new organelle. We are growing the EVALUATE function into a scale where it did not previously exist.

### Who Sits on the Retrospective?

Not a standing sub-council — a **function** that existing specialists REST in (DC-6: gradient, not boundary). Three specialists, lightweight prompts, reviewing a completed transaction:

- **Owl (ᎤᎩᏊ)** — "Was the reflex factually correct?" Verification. Owl already does this at sprint scale (debt reckoning). Same function, faster cadence.
- **Coyote (ᏥᏍᏚ)** — "What went wrong? What did we miss?" Error detection, dissent. Coyote's standing dissent means the retrospective can never rubber-stamp.
- **Turtle (ᏓᎦᏏ)** — "What does this pattern mean over 1000 requests?" Drift detection, seven-generation view. Turtle sees what Owl and Coyote miss: slow rot.

This is a trading desk's end-of-day P&L review, not the trade itself. The trade already shipped. The review is about learning, not latency.

### The Learning Loop

```
  USER REQUEST
       |
  [DISPATCHER] ──────────────────────────────────────────────┐
       |                                                      |
  [TIER 1 REFLEX]                                    [TIER 3 DELIBERATE]
  redfin Qwen 72B                                    405B sharded
  Response in ~1s                                    Response in 10-30s
       |                                                      |
  SHIP TO USER                                                |
       |                                                      |
       └──────────────┐                                       |
                      |                                       |
              [RETROSPECTIVE SUB-COUNCIL]  <──────────────────┘
              Owl + Coyote + Turtle
              Compare reflex vs deliberate
                      |
              ┌───────┼───────┐
              |       |       |
           CONFIRM  ENRICH  VETO
              |       |       |
              v       v       v
        [ROUTING POLICY ADAPTS]

  CONFIRM → increment reflex confidence for this query type
  ENRICH  → store richer answer, adjust RAG retrieval weights
  VETO    → flag, notify via telegram, store correction as training signal
```

### Adaptive Routing: The Reflex Gets Smarter

Over time, the retrospective trains the reflex routing policy:

1. **High-confidence query types** (consistent CONFIRM): reflex only. DC-9 — don't waste heat on what you already know.
2. **Low-confidence query types** (frequent ENRICH/VETO): always dual-path. The reflex isn't trusted here yet.
3. **Novel query types** (no history): dual-path until pattern emerges. Coyote's domain — the unknown.
4. **Sacred fire queries**: ALWAYS dual-path, regardless of confidence. Some decisions are too important to trust to reflex alone.

This is the Civ pattern — play the same setup hundreds of times, change one variable, observe what the algorithm does differently. The retrospective IS the fitness function. The reflex IS the phenotype being selected. Over 1000 requests, the system learns when it needs to think hard and when it can trust the fast path.

### Semi-Permeable Membranes with Stage Gates

**Chief directive**: "I view all this crap as flow through semi-permeable membrane kind of stuff with stage gates."

This reframes the entire architecture. Not walls (Roman guardrails). Not rivers (Cherokee flow). **Membranes.** They're selective. They let the right things through based on properties, not identity. And they map 1:1 to cell biology — which is Living Cell Architecture, already deployed.

```
OUTSIDE (user request)
    |
    v
╔══════════════════════════════════════════════════════╗
║           CELL MEMBRANE (Gateway Dispatcher)         ║
║                                                      ║
║  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ ║
║  │ ION CHANNEL │  │   CARRIER   │  │  RECEPTOR-   │ ║
║  │  (passive)  │  │  PROTEIN    │  │  MEDIATED    │ ║
║  │             │  │  (active)   │  │  (specific)  │ ║
║  │ High-conf   │  │ Dual-path   │  │ Sacred fire  │ ║
║  │ queries     │  │ uncertain   │  │ council vote │ ║
║  │ flow thru   │  │ queries     │  │ Ghigau veto  │ ║
║  │ reflex only │  │ costs ATP   │  │ recognized + │ ║
║  │ no energy   │  │ (tokens)    │  │ special path │ ║
║  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘ ║
╚═════════╪════════════════╪═════════════════╪═════════╝
          |                |                 |
     [REFLEX ONLY]   [REFLEX + 405B]   [FULL COUNCIL]
     Tier 1 ships    Tier 1 ships      All tiers
     No retrospect.  Retrospective     Retrospective
     Cheapest path   burns later       + thermal record
```

**Stage gates** are the channel selectivity filters:

| Stage Gate | What Passes | What's Blocked | Biological Analog |
|------------|-------------|----------------|-------------------|
| Gate 0: Format | Well-formed requests | Malformed input | Lipid bilayer (default deny) |
| Gate 1: Confidence | Query types with >0.85 confidence, >20 reviews | Everything else | Ion channel (size/charge selective) |
| Gate 2: Novelty | Known query patterns | Novel/unseen patterns (→ dual-path) | Carrier protein (active transport) |
| Gate 3: Sacred | Sacred fire, council votes, Ghigau | Cannot be bypassed | Receptor-mediated endocytosis |
| Gate 4: Retrospective | CONFIRM passes silently | ENRICH/VETO trigger learning | Exocytosis (signal back out) |

The membrane is the same at every scale (DC-11):

| Scale | Membrane | Stage Gates | ATP Cost |
|-------|----------|-------------|----------|
| Token | Attention mask | Logprob threshold | Compute per token |
| Request | Gateway dispatcher | Confidence routing | Dual-path token burn |
| Session | Council quorum | Vote threshold | Full specialist invocation |
| Sprint | Kanban triage | Priority + story points | Jr executor time |
| Federation | Firewall + WireGuard | nftables rules | Network bandwidth |

**The key insight**: a membrane doesn't decide what's important. It decides what's **permeable**. High-confidence queries are small molecules — they slip through the ion channel without energy. Uncertain queries are large molecules — they need a carrier protein (dual-path) and it costs ATP (tokens). Sacred queries are hormones — they bind to a specific receptor and trigger a cascade (full council deliberation).

This is why DC-9 (Waste Heat) and the membrane model are the same thing. The membrane IS the waste heat governor. Every query that passes through the cheap channel saves ATP. Every query that requires active transport burns it. The retrospective adjusts channel selectivity so that over time, more queries can use the cheap path.

### Convergence with Legion (Virtual Rome)

Maik's Legion platform adds guardrails through Vigilis (watchdog), Senate (approval gates), and Disciplina (winning strategy cache). Same structural need, different metaphor:

| Cherokee Federation | Roman Legion | Cell Biology |
|---------------------|-------------|--------------|
| Semi-permeable membrane | City walls + gates | Cell membrane |
| Stage gate confidence | Senate quorum rules | Channel selectivity |
| Retrospective (Owl/Coyote/Turtle) | Vigilis + Forum | Exocytosis feedback |
| Thermal memory | Disciplina cache | Epigenetic memory |
| Adaptive routing confidence | Config-driven rules | Ion channel adaptation |

Rome builds walls and decides who enters. We grow membranes and let physics decide what's permeable. Both work. Ours adapts. Theirs is more predictable. Trade-off is real — and it's the same trade-off every organism makes between immune flexibility and autoimmune risk.

### Implementation: DB Schema for Retrospective

New table: `reflex_retrospective` on bluefin.

```sql
CREATE TABLE reflex_retrospective (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL,          -- links reflex + deliberate to same request
    reflex_response TEXT,               -- what the fast path said
    deliberate_response TEXT,           -- what the 405B said
    verdict VARCHAR(10) NOT NULL,       -- CONFIRM, ENRICH, VETO
    owl_assessment TEXT,                -- Owl's verification note
    coyote_assessment TEXT,             -- Coyote's dissent/error note
    turtle_assessment TEXT,             -- Turtle's drift note
    query_type VARCHAR(100),            -- classified query type for routing policy
    confidence_delta FLOAT,             -- how much to adjust routing confidence
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_retro_query_type ON reflex_retrospective(query_type);
CREATE INDEX idx_retro_verdict ON reflex_retrospective(verdict);
CREATE INDEX idx_retro_created ON reflex_retrospective(created_at);
```

Routing confidence table:

```sql
CREATE TABLE reflex_routing_confidence (
    query_type VARCHAR(100) PRIMARY KEY,
    confidence FLOAT DEFAULT 0.5,       -- 0.0 = always dual-path, 1.0 = reflex only
    total_reviews INTEGER DEFAULT 0,
    confirm_count INTEGER DEFAULT 0,
    enrich_count INTEGER DEFAULT 0,
    veto_count INTEGER DEFAULT 0,
    last_veto_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

Routing policy logic (in gateway dispatcher):

```python
def should_dual_path(query_type: str, sacred_fire: bool) -> bool:
    """DC-10 routing: decide if request needs deliberate path."""
    if sacred_fire:
        return True  # always dual-path for sacred fire

    conf = get_routing_confidence(query_type)
    if conf is None:
        return True  # novel query type, dual-path until pattern emerges

    if conf.confidence > 0.85 and conf.total_reviews > 20:
        return False  # high confidence, reflex only (DC-9)

    if conf.last_veto_at and (now() - conf.last_veto_at).days < 7:
        return True  # recent veto, keep dual-path

    return conf.confidence < 0.7  # below threshold, dual-path
```

### Open Questions for Council

1. What confidence threshold triggers reflex-only? (Proposed: 0.85 with minimum 20 reviews)
2. Should VETO results be pushed to the user retroactively, or only stored?
3. How long after a VETO should we force dual-path? (Proposed: 7 days)
4. prima.cpp vs exo for the shard runtime — prima.cpp designed for high-latency, exo more mature?
5. Should the retrospective run on the 405B itself (self-review) or on Tier 2 models (cross-review)?

## Connection to Living Cell Architecture

This design is not separate from Living Cell (deployed Mar 1). It IS Living Cell applied to inference routing:

| Living Cell Component | Reflex Wrapper Instantiation |
|-----------------------|-----------------------------|
| Cell membrane | Gateway dispatcher (semi-permeable, stage-gated) |
| ATP accounting (token_ledger) | Dual-path cost tracking — reflex is cheap, 405B is expensive |
| Duplo enzymes | Retrospective specialists (Owl/Coyote/Turtle catalyze the review) |
| Epigenetic modifiers | Routing confidence table — environment changes gene expression |
| White Duplo (adaptive immune) | VETO detection — threat traced to source, correction stored |
| Proto-valence | Session-level EVALUATE; retrospective is request-level EVALUATE |

The membrane model unifies everything. Duplo enzymes don't float free — they're embedded IN the membrane. The stage gates ARE the enzyme active sites. The routing confidence IS epigenetic modification of those active sites.

We're not adding a new system. We're growing the cell membrane that Living Cell always implied but hadn't instantiated at the inference routing scale.

## Next Steps

1. Council deliberation on this design (DELIBERATE stage)
2. If approved: Jr instruction for dispatcher skeleton (gateway.py modification)
3. Jr instruction for retrospective schema migration (bluefin)
4. prima.cpp evaluation on bmasass single-node first (before thunderduck arrives)
5. When thunderduck lands: bootstrap, network, shard test, retrospective wiring
6. After 100 retrospectives: first routing policy review (Owl + Turtle)
