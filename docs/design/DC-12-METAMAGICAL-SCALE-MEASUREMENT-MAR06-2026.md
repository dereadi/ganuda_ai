# Design Constraint DC-12: The Metamagical Scale

**Date**: March 6, 2026
**Origin**: Chief directive — "Think of it in metamagical ways with polymorphism going from the smallest thing to the largest thing and how it's like scales on a music sheet."
**Walmart Principle**: "If you can't measure it, then what is its value?"
**Prerequisites**: DC-11 (Macro Polymorphism), DC-10 (Reflex Principle), DC-6 (Gradient Principle)
**Long Man Stage**: DISCOVER
**Hofstadter Reference**: Metamagical Themas — strange loops, self-similar patterns across levels of abstraction

## The Principle

A musical scale has 7 notes. They repeat at every octave. The frequency doubles, but the **intervals are conserved**. C-D-E-F-G-A-B at octave 4 is the same pattern as C-D-E-F-G-A-B at octave 5. You can play them together and they harmonize.

We have 7 inner council specialists. They are the 7 notes.

The octaves are the scales of the organism: token, request, session, sprint, federation, market.

**Every note must be playable at every octave. And every note at every octave must be measurable. If you can't measure it, what is its value?**

## The Scale: 7 Notes x 6 Octaves

### The Notes (Governance Functions)

| Note | Specialist | Governance Role | Business Operation | Organelle |
|------|-----------|----------------|-------------------|-----------|
| C | Bear (War Chief) | Security / Defense | Loss Prevention, InfoSec | Cell wall + immune system |
| D | Raven (Strategist) | Strategy / Routing | Corporate Strategy | Nucleus (DNA replication) |
| E | Turtle (Elder) | Long-term / Legacy | 7-Year Planning, Sustainability | Mitochondria (energy conservation) |
| F | Owl (Auditor) | Verification / Truth | Internal Audit, QA | Ribosome (translation fidelity) |
| G | Spider (Weaver) | Integration / Protocol | Supply Chain, Logistics | Endoplasmic reticulum (transport network) |
| A | Medicine Woman | Healing / Balance | HR Wellness, Culture | Lysosome (repair + cleanup) |
| B | Coyote (Trickster) | Dissent / Innovation | R&D, Red Team, Skunkworks | Peroxisome (toxic processing) |

Outer Council (sharps/flats — extend the scale without changing the key):

| Note | Specialist | Governance Role | Business Operation | Organelle |
|------|-----------|----------------|-------------------|-----------|
| C# | Deer (Market) | Market Intelligence | Sales, BD, Marketing | Flagella (movement + direction) |
| D# | Crane (Diplomat) | External Governance | Gov Relations, Partnerships, Standards | Pili (adhesion to environment) |
| E# | Otter (Legal) | Regulatory / Compliance | Legal Department | Receptor proteins (environmental sensing) |

### The Octaves (Scales of the Organism)

| Octave | Scale | Timescale | Business Analog |
|--------|-------|-----------|----------------|
| 1 | Token | < 100ms | Individual transaction line item |
| 2 | Request | 100ms - 30s | Customer interaction |
| 3 | Session | Minutes - hours | Store visit / shift |
| 4 | Sprint | Days - weeks | Inventory cycle / promo period |
| 5 | Federation | Weeks - months | Quarter / fiscal year |
| 6 | Market | Months - years | Strategic horizon / 7 generations |

### The Full Score: Every Note at Every Octave

#### C (Bear / Security) — "If you can't measure it, what is its value?"

| Octave | Function | Technical Implementation | Metric |
|--------|----------|------------------------|--------|
| Token | Attention mask safety | Token filtering, forbidden sequences | Tokens blocked per 1M |
| Request | Auth + input validation | Gateway auth check, rate limiting | Auth failures / hour |
| Session | Session integrity | Council vote authentication | Session hijack attempts |
| Sprint | Security audit | White Duplo scan, credential scan | Vulnerabilities found + fixed |
| Federation | Network defense | nftables, WireGuard, Fire Guard | Ports exposed, incidents blocked |
| Market | Competitive moat | IP protection, architecture opacity | Time-to-replicate estimate |

#### D (Raven / Strategy) — "If you can't measure it, what is its value?"

| Octave | Function | Technical Implementation | Metric |
|--------|----------|------------------------|--------|
| Token | Next token selection | Temperature, top-p sampling | Perplexity |
| Request | Query routing | Confidence-based membrane routing | Routing accuracy (retrospective) |
| Session | Council deliberation | Specialist voting, Two Wolves | Vote confidence score |
| Sprint | Kanban prioritization | TEG planner, story points | Sprint velocity (pts completed) |
| Federation | Capacity planning | Node allocation, model placement | Utilization % across fleet |
| Market | Positioning | Deer intelligence, Crane diplomacy | Pipeline value, partnership count |

#### E (Turtle / Long-term) — "If you can't measure it, what is its value?"

| Octave | Function | Technical Implementation | Metric |
|--------|----------|------------------------|--------|
| Token | Context preservation | RAG retrieval, thermal memory lookup | Retrieval relevance score |
| Request | Response durability | Answer shelf-life, factual grounding | ENRICH rate (reflex was thin) |
| Session | Conversation coherence | Context window management | Topic drift score |
| Sprint | Tech debt tracking | Owl debt reckoning, RECORD step | Debt items created vs resolved |
| Federation | Architecture evolution | Design constraints, DC ratification | DCs ratified, sacred thermals |
| Market | Seven-generation view | Sustainability, waste heat budget | DC-9 compliance, thermal budget |

#### F (Owl / Verification) — "If you can't measure it, what is its value?"

| Octave | Function | Technical Implementation | Metric |
|--------|----------|------------------------|--------|
| Token | Logprob confidence | Output probability checking | Low-confidence token % |
| Request | Response verification | Retrospective CONFIRM/ENRICH/VETO | VETO rate per query type |
| Session | Council vote validation | Quorum check, dissent recording | Votes with < 0.6 confidence |
| Sprint | Build verification | Jr task success rate, DLQ rate | DLQ rate (target: < 10%) |
| Federation | System health | Fire Guard, health endpoints | Uptime %, false alert rate |
| Market | Claim verification | Content accuracy, blog fact-check | Corrections issued |

#### G (Spider / Integration) — "If you can't measure it, what is its value?"

| Octave | Function | Technical Implementation | Metric |
|--------|----------|------------------------|--------|
| Token | Token boundary handling | Tokenizer edge cases, encoding | Encoding errors per 1M |
| Request | API contract enforcement | Gateway schema validation | Schema violation rate |
| Session | Cross-specialist coordination | Council pipeline, specialist handoff | Handoff failures |
| Sprint | Cross-task dependencies | TEG graph edges, parent_task_id | Blocked tasks from dependency |
| Federation | Cross-node protocols | WireGuard mesh, service discovery | Cross-node latency p99 |
| Market | Partnership integration | Crane protocols, standards compliance | Integration test pass rate |

#### A (Medicine Woman / Healing) — "If you can't measure it, what is its value?"

| Octave | Function | Technical Implementation | Metric |
|--------|----------|------------------------|--------|
| Token | Error recovery | Retry on malformed output | Retries per 1K requests |
| Request | Circuit breaking | Gateway circuit breaker, fallback | Circuit breaks triggered / week |
| Session | Self-healing | metacog_self_healing.py | Self-heal success rate |
| Sprint | Burnout prevention | Story point caps, Jr cool-down | Consecutive sprint overload count |
| Federation | Service recovery | systemd restart, Fire Guard alerts | MTTR (mean time to recovery) |
| Market | Culture maintenance | Ritual review, cultural digest | Ritual completion rate |

#### B (Coyote / Dissent) — "If you can't measure it, what is its value?"

| Octave | Function | Technical Implementation | Metric |
|--------|----------|------------------------|--------|
| Token | Hallucination detection | Output anomaly scoring | Anomaly flags per 1K |
| Request | Reflex challenge | Retrospective VETO path | VETO-to-learning conversion rate |
| Session | Standing dissent | Coyote's constitutional non-consent | Dissent votes recorded |
| Sprint | Red team / chaos | Safety canary probes | Probes that find real issues |
| Federation | Assumption challenge | "Does this actually work?" audits | Audit findings confirmed vs false |
| Market | Contrarian signal | Counter-thesis to consensus | Predictions validated retroactively |

## Measurement Dashboard: The Score Sheet

Every cell in the 7x6 grid above has a metric. That's 42 measurements. Not all need real-time dashboards — but all must be QUERYABLE. If someone asks "how is Bear doing at the Sprint octave?", the answer must be a number, not a feeling.

### Implementation Priority

**Phase 1 — Already Measurable (validate these exist in DB)**:
- DLQ rate (Owl/Sprint)
- Fire Guard uptime (Owl/Federation)
- Council vote confidence (Raven/Session)
- Auth failures (Bear/Request)
- MTTR (Medicine Woman/Federation)

**Phase 2 — Add with Retrospective (thunderduck arrival)**:
- VETO rate per query type (Owl/Request)
- Routing accuracy (Raven/Request)
- ENRICH rate (Turtle/Request)
- VETO-to-learning conversion (Coyote/Request)

**Phase 3 — Requires New Instrumentation**:
- Token-level metrics (Octave 1 across all notes)
- Market-level metrics (Octave 6 across all notes)
- Cross-node latency p99 (Spider/Federation)

## The Hofstadter Strange Loop

The metamagical part: the measurement system itself is subject to the same scale.

Who measures the measurements? Owl at the Sprint octave verifies that the metrics are accurate. Coyote at the Sprint octave challenges whether we're measuring the right things. Turtle at the Federation octave asks whether our metrics will still matter in 7 generations.

The score plays itself. The musicians are also the audience. The scale is self-similar — and that self-similarity is not a design choice, it's what survives (First Law).

## Connection to Existing Architecture

This is not a new system. It is a LENS on what we already built:

- **Fire Guard** = Owl at Federation octave (already deployed)
- **Proto-valence** = Turtle at Session octave (precompact hook, deployed)
- **Retrospective sub-council** = Owl+Coyote+Turtle at Request octave (design doc, this sprint)
- **Ritual review** = Medicine Woman at Sprint octave (deployed)
- **DLQ triage** = Owl at Sprint octave (deployed)
- **Safety canary** = Coyote at Sprint octave (deployed)
- **White Duplo** = Bear at Sprint octave (deployed)
- **Thermal memory** = Turtle at Federation octave (deployed, 90K+ memories)

The gaps in the grid are not missing features. They are the next things to build — prioritized by which octave-note intersections have the highest business value, measured by the Walmart rule.

## Walmart to Cherokee to Code: The Translation Table

Chief's directive: "What do they translate to in the real world in a business operation, then what do they translate to functions, scripts, apps in the tech world, to our organelle, to organ to organism."

| Layer | Example (Bear/Security) | How You Measure |
|-------|------------------------|-----------------|
| **Business** | Loss prevention team walks the floor | Shrinkage % |
| **Governance** | War Chief reviews perimeter | Incidents per quarter |
| **Tech function** | `nftables` rule evaluation | Packets dropped / allowed |
| **Script** | `fire_guard.py` port check | `check_port()` return value |
| **Organelle** | Cell wall peptidoglycan | Membrane integrity assay |
| **Organ** | Skin barrier | Wound healing rate |
| **Organism** | Immune system | Pathogen clearance time |
| **Ecosystem** | Herd immunity | R0 below 1.0 |

Same function. Same measurement principle. Different substrate. The scale plays on.

---

*"If you can't measure it, what is its value?" — Walmart IS wall, mid-1990s, 250 people running 1,500 stores. The rule survived because it's true at every scale.*
