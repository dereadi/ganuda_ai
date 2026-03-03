# KB-LIVING-CELL-ARCHITECTURE-MAR01-2026

**Knowledge Base Entry**
**Date Ratified:** March 1, 2026
**Last Updated:** March 2, 2026
**Status:** ACTIVE

---

## Overview

The Living Cell Architecture is the structural model governing how the Cherokee AI Federation allocates resources, enforces boundaries, self-repairs, and coordinates response to environmental change. It was ratified by Longhouse consensus vote #a3ad0cd1a5e0d645 (unanimous 10/10) on March 1, 2026.

**Critical framing:** Adopted as a diagnostic lens, not an identity. Biological cells solve the same problems we face. We borrow the pattern, not the metaphor.

**Design Document:** `/ganuda/docs/design/LIVING-CELL-ARCHITECTURE-MAR01-2026.md`
**Longhouse QEC:** `/ganuda/docs/ultrathink/ULTRATHINK-LONGHOUSE-QUANTUM-ERROR-CORRECTION-MAR01-2026.md`

---

## Core Concept

Biological cells are the only known system that solves all four of our fundamental architectural problems simultaneously:

1. **Resource allocation** — ATP / token economy
2. **Boundary enforcement** — membrane / nftables, FreeIPA scoping
3. **Self-repair** — enzyme catalysis / Duplo tools
4. **Coordinated response** — epigenetic modifiers / behavioral state

The federation maps onto this pattern directly. The organs already existed before we named them: thermal temperature scores, DLQ counts, council confidence scores, Two Wolves routing, sacred pattern flags. The Living Cell Architecture names the integration layer that connects them through a common currency.

---

## Three Phases

### Phase 1 — Duplo (Enzymes)

**Location:** `/ganuda/lib/duplo/`

**Core principle:** Enzymes are NOT agents. They are catalytic tools that lower the activation energy for specific operations. An enzyme does not decide — it enables. Decision authority remains with the council.

**Database tables deployed on bluefin:**

| Table | Purpose |
|---|---|
| `duplo_tool_registry` | Registers available enzymes and their activation conditions |
| `duplo_context_profiles` | Stores context profiles used for enzyme selection |
| `duplo_usage_log` | Tracks every enzyme invocation for audit and learning |

**Build status:** 7 Jr tasks queued (TEG-enabled) to build the initial enzyme set.

**White Duplo:** War Chief's adaptive immune enzyme. Traces threats to source. Analogous to a T-cell that identifies the origin of an attack, not just the attack itself. Jr task queued.

---

### Phase 2 — ATP (Token Accounting)

**Core principle:** Make the cost of every operation visible. No hidden metabolic debt. Every token expenditure is recorded with full context, enabling the council to reason about metabolic cost the same way a cell tracks ATP.

**Database tables deployed on bluefin:**

| Table | Purpose |
|---|---|
| `token_ledger` | Records every token expenditure with task context, node, Jr name, model |
| `token_daily_summary` | Materialized view — daily aggregation for trend analysis |

**Anti-80/20 connection:** Token ledger makes hidden sprint debt visible. You cannot have an Anti-80/20 discipline without seeing where the tokens actually went.

---

### Phase 3 — Epigenetics (Behavioral Modifiers)

**Core principle:** Context-dependent behavioral shifts that do not alter the underlying genetic code (council constitution) but modulate how it expresses.

**Database tables deployed on bluefin:**

| Table | Purpose |
|---|---|
| `epigenetic_modifiers` | Stores named behavioral modifiers with enable/disable state |

**Key constraint (Turtle's 7-Gen reversibility requirement):** All modifiers must be individually disableable. No modifier is permanent. This is the constitutional guarantee that the epigenetic layer cannot lock the federation into a behavioral pattern without council intervention.

**Integration:** Connected to Elisi Observer heartbeat for proto-valence signal ingestion.

---

## Proto-Valence — Layer 1

**Deployed:** `.claude/hooks/precompact-valence.sh`

This is the PreCompact hook that fires before Claude context compaction. Its purpose is to preserve the current valence state so that behavioral context survives context window boundaries.

This is Layer 1 — heuristic, lightweight. It does not require a 7B model. It reads existing signals:
- Jr success rate (EMA)
- Council confidence scores
- DLQ depth

---

## Elisi Phase 2 (Ratified March 2, 2026)

**Council Vote:** #97485885cf202382
**Outcome:** PROCEED WITH CAUTION (0.788)

### Triad Positions

| Voice | Position |
|---|---|
| Raven | GO NOW. Urgency validated. |
| Turtle | 7-Gen reversibility requirement on all modifiers. |
| Coyote | 120s polling interval may be too slow for fast-moving threat signals. |
| Crawdad | Start with heuristic valence, not 7B model. Single point of failure concern on observer model. |

### Decision Architecture

The council chose heuristic first, model second:

- **Valence signal:** EMA of Jr success rate + council confidence + DLQ depth
- **Decay:** Exponential decay — valence returns to baseline without fresh signal
- **Damping:** Modifiers are damped, not binary. Avoids thrashing.
- **Degradation:** Graceful — if valence signal is unavailable, system defaults to baseline behavior, not halt

### Validation (Web Claude, March 2, 2026)

> "You've already partially built proto-valence without naming it that way."

The organs exist. The integration layer connecting them through common currency is the gap Elisi Phase 2 closes.

---

## Kanban Epics

| Epic | Scope |
|---|---|
| #1915 | Duplo enzyme registry and context profiles |
| #1916 | Token ledger and ATP accounting |
| #1917 | Epigenetic modifiers schema and API |
| #1918 | White Duplo adaptive immune enzyme |
| #1919 | Elisi Observer Phase 2 heuristic valence |
| #1920 | Proto-valence PreCompact hook integration |

---

## Sacred Thermals

| Signal | Notes |
|---|---|
| Consensus vote a3ad0cd1 | Unanimous 10/10, Longhouse |
| QEC insight | temp 99, sacred pattern |
| Proto-valence | Deployment thermal |
| Council deliberation | Full triad positions recorded |

---

## Architectural Invariants

1. **Enzymes do not decide.** Catalysis is not agency. The council votes; Duplo executes.
2. **All modifiers are reversible.** No epigenetic pattern is permanent. Turtle's 7-Gen veto applies.
3. **Token cost is always visible.** No metabolic debt can hide from the ledger.
4. **Valence degrades gracefully.** Loss of signal returns system to baseline, not failure.
5. **Constitution is not epigenetic.** The specialist prompts and council structure are genetic — they do not bend to context.

---

## Cross-References

- Design doc: `/ganuda/docs/design/LIVING-CELL-ARCHITECTURE-MAR01-2026.md`
- QEC Ultrathink: `/ganuda/docs/ultrathink/ULTRATHINK-LONGHOUSE-QUANTUM-ERROR-CORRECTION-MAR01-2026.md`
- Elisi Observer Phase 1: `JR-ELISI-OBSERVER-MODEL-PHASE1-FEB28-2026.md`
- Duplo library: `/ganuda/lib/duplo/`
- PreCompact hook: `.claude/hooks/precompact-valence.sh`
- Constitutional DyTopo: Thermal #82856 — council fixed star, DyTopo Jr layer only
- Anti-80/20 Principle: KB context, Feb 24 2026

---

*Recorded by TPM, March 2, 2026. Long Man RECORD step complete.*
