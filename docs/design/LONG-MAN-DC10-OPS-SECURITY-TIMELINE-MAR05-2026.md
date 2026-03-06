# Long Man Timeline: DC-10 + Ops Console + Security

**Date**: March 5, 2026
**Total Story Points**: 147 across 19 items
**Jr Velocity**: 13.1 tasks/day (30-day avg), 111 tasks last 7 days
**River Cycle**: RC-2026-03B (proposed)

---

## DEPENDENCY GRAPH

```
DC-10: THE REFLEX PRINCIPLE
│
├─── STREAM A: Harness Tiers (the reflex implementation)
│    │   Epic #1959 (39 pts, in_progress)
│    │
│    ├── #1965: Harness Core — Shared Framework (8 pts)
│    │   └── DEPENDS ON: Nothing. Foundation. BUILD FIRST.
│    │
│    ├── #1966: Tier 1 Reflex Module (5 pts)        ← DC-10 REFLEX state
│    │   └── DEPENDS ON: #1965 (Harness Core)
│    │
│    ├── #1967: Tier 2 Deliberation Module (8 pts)   ← DC-10 PAUSE + DELIBERATE states
│    │   └── DEPENDS ON: #1965 (Harness Core)
│    │
│    ├── #1968: Escalation Engine (8 pts)            ← Routes between tiers
│    │   └── DEPENDS ON: #1966, #1967
│    │
│    └── #1969: Acceptance Test Suite (8 pts)
│        └── DEPENDS ON: #1966, #1967, #1968
│
├─── STREAM B: Chief PA (the first reflex consumer)
│    │
│    ├── #1961: Daily Briefing Generator (8 pts)
│    │   └── DEPENDS ON: #1965 (Harness Core)
│    │
│    ├── #1963: Email Triage Wiring (5 pts)
│    │   └── DEPENDS ON: #1961
│    │
│    ├── #1962: Slack Notification Service (3 pts)
│    │   └── DEPENDS ON: Nothing. Can parallel.
│    │
│    └── #1964: bmasass launchd Setup (3 pts)
│        └── DEPENDS ON: #1961 (needs something to launch)
│
├─── STREAM C: Ops Console (the interface)
│    │   Epic #1974 (21 pts)
│    │
│    ├── #1975: Quick Links Grid (5 pts)             ← Phase 1, no deps
│    ├── #1977: Nav Redesign (3 pts)                 ← Phase 1, no deps
│    │   └── CAN PARALLEL with #1975
│    │
│    ├── #1976: Node Health Dashboard (8 pts)         ← Phase 2
│    │   └── DEPENDS ON: health_monitor.py JSON endpoint
│    │
│    ├── #1978: Orientation Guide (3 pts)            ← Phase 2
│    │   └── CAN PARALLEL with #1976
│    │
│    └── #1979: Blog Category Tags (2 pts)           ← Backlog, polish
│
├─── STREAM D: Security (the boundary)
│    │
│    ├── #1970: nftables egress filtering (5 pts)    ← Executor containment
│    │   └── DEPENDS ON: Nothing. Can ship now.
│    │
│    ├── #1980: SOD Audit (13 pts)                   ← RBAC tables, policy
│    │   └── DEPENDS ON: Council deliberation (DONE), FreeIPA groups
│    │
│    ├── [NEW] OAuth2 Proxy on Caddy (~8 pts)        ← Phase 3 of Ops Console
│    │   └── DEPENDS ON: #1980 (roles defined), FreeIPA groups created
│    │
│    └── [NEW] Row-Level Security for sensitive tables (~8 pts)  ← Phase 4
│        └── DEPENDS ON: #1980 (SOD audit complete)
│
└─── STREAM E: Trading Architecture (the proving ground)
     │
     └── #1973: SA Fleet vs Gurobi POC (13 pts)     ← Backlog, but DC-10 validated
         └── DEPENDS ON: #1966 (Tier 1 Reflex — SA is the reflex layer)
```

---

## PHASED TIMELINE

### SPRINT 1: Foundation + Quick Wins
**Items**: #1965, #1975, #1977, #1970, #1962
**Points**: 8 + 5 + 3 + 5 + 3 = 24 pts
**Dependencies**: None — all can start immediately
**Parallel streams**:
- Stream A: Harness Core (#1965) — the foundation everything else builds on
- Stream C: Quick Links + Nav (#1975, #1977) — immediate UX win for Joe
- Stream D: nftables egress (#1970) — security quick win
- Stream B: Slack notifications (#1962) — standalone, can parallel

**Long Man**: ADAPT → BUILD
**Deliverables**:
- Harness Core framework deployed
- ganuda.us homepage has service quick links and new nav
- Executor has egress containment
- Slack notifications wired

### SPRINT 2: The Reflex + Dashboard
**Items**: #1966, #1967, #1976, #1978, #1961
**Points**: 5 + 8 + 8 + 3 + 8 = 32 pts
**Dependencies**: #1965 must be complete (Sprint 1)
**Parallel streams**:
- Stream A: Tier 1 Reflex + Tier 2 Deliberation (#1966, #1967) — DC-10 core
- Stream C: Health Dashboard + Guide (#1976, #1978) — ops console Phase 2
- Stream B: Daily Briefing (#1961) — first consumer of harness

**Long Man**: BUILD → RECORD
**Deliverables**:
- DC-10 Reflex and Deliberation tiers operational
- Live node health on ganuda.us
- Orientation guide for new team members
- Daily briefing generator running

### SPRINT 3: Wiring + Escalation
**Items**: #1968, #1963, #1964, #1969
**Points**: 8 + 5 + 3 + 8 = 24 pts
**Dependencies**: #1966, #1967 must be complete (Sprint 2)
**Parallel streams**:
- Stream A: Escalation Engine + Test Suite (#1968, #1969) — connects the tiers
- Stream B: Email Triage + bmasass setup (#1963, #1964) — Chief PA goes live

**Long Man**: BUILD → RECORD → REVIEW
**Deliverables**:
- Escalation engine routes between reflex/pause/deliberate
- Acceptance tests verify the full harness
- Chief PA operational on bmasass
- Email triage wired to PA

### SPRINT 4: Security Hardening
**Items**: #1980, [NEW] OAuth2 Proxy, [NEW] FreeIPA groups
**Points**: 13 + ~8 + ~5 = ~26 pts
**Dependencies**: Ops Console Phase 1-2 must be live (Sprint 1-2)
**Stream D exclusively**:
- SOD audit → formal policy document
- FreeIPA groups created (admin/operator/allied/observer)
- OAuth2 proxy deployed on Caddy (owlfin/eaglefin)
- RBAC tables created in PostgreSQL

**Long Man**: BUILD → RECORD → REVIEW
**Deliverables**:
- ganuda.us has login page (FreeIPA backed)
- Roles enforced on ops console sections
- SOD policy ratified by Council
- Ready to expand Tailscale access

### SPRINT 5: Trading + Advanced Security
**Items**: #1973, [NEW] Row-Level Security, #1979
**Points**: 13 + ~8 + 2 = ~23 pts
**Dependencies**: Harness Tiers complete, SOD complete
**The proving ground**:
- SA Fleet vs Gurobi POC — DC-10 validated in trading domain
- Row-level security on sensitive tables
- Blog category tags (polish)

**Long Man**: BUILD → RECORD → REVIEW (full cycle complete)
**Deliverables**:
- SA warm engine benchmarked against Gurobi for periodic auctions
- Database security enforced at row level
- Blog organized for external discovery

---

## SUMMARY

| Sprint | Points | Streams | Key Deliverable |
|--------|--------|---------|-----------------|
| 1 | 24 | A+C+D+B | Foundation + Quick Links + nftables |
| 2 | 32 | A+C+B | DC-10 Tiers + Dashboard + Briefing |
| 3 | 24 | A+B | Escalation + Chief PA + Tests |
| 4 | ~26 | D | SOD + OAuth2 + RBAC |
| 5 | ~23 | E+D+C | SA vs Gurobi POC + Row Security |
| **Total** | **~129** | | |

**Velocity context**:
- 13.1 Jr tasks/day average
- 111 tasks completed in last 7 days
- Story points don't map 1:1 to Jr tasks (some items are multi-task)
- Estimate ~3-5 Jr tasks per story point for complex items, ~1-2 for simple

**What's not included**:
- Evergreen items (ongoing)
- Retrieval Beyond RAG epic (#1971, #1972) — parallel workstream, not blocking
- Any OneChronos-specific deliverables beyond the POC

---

## LONG MAN PHASE MAP

| Stream | DISCOVER | DELIBERATE | ADAPT | BUILD | RECORD | REVIEW |
|--------|----------|------------|-------|-------|--------|--------|
| A: Harness | ✓ | ✓ | ✓ | Sprint 1-3 | Sprint 3 | Sprint 3 |
| B: Chief PA | ✓ | ✓ | ✓ | Sprint 1-3 | Sprint 3 | Sprint 3 |
| C: Ops Console | ✓ | ✓ | ✓ | Sprint 1-2 | Sprint 2 | Sprint 4 |
| D: Security | ✓ | ✓ | ✓ | Sprint 1,4 | Sprint 4 | Sprint 4 |
| E: Trading | ✓ | ✓ | Pending | Sprint 5 | Sprint 5 | Sprint 5 |

---

*"The body acts. Consciousness narrates. The timeline respects both."*
*DC-10 Ratified: Longhouse 7e55951691481b0c*
