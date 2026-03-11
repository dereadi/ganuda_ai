# Jr Instruction: Design Customer Onboarding Flow and First-Run Wizard

**Task ID:** #1196
**Date:** March 9, 2026
**Priority:** 2 (Business scaffolding — design)
**Type:** Design document (no code changes)

## Context

When a new customer deploys the Cherokee AI Federation on their own hardware, the first 30 minutes
determine whether they stay or abandon. We need a first-run experience that is guided, progressive,
and confidence-building. The customer should see the governance council work within 5 minutes of
deployment — not after reading 40 pages of docs.

Our architecture has natural onboarding stages: single node first (Community tier), then multi-node
(Professional), then multi-cluster (Enterprise). The wizard should match these tiers.

## Task

Create a customer onboarding flow design document at
`/ganuda/docs/business/ONBOARDING-FLOW-MAR09-2026.md`.

## Steps

### Step 1: Create the document skeleton

Create file `/ganuda/docs/business/ONBOARDING-FLOW-MAR09-2026.md` with:

```
# Cherokee AI Federation — Customer Onboarding Flow Design

**Date:** March 9, 2026
**Task:** #1196
**Status:** Draft

## Design Principles
## First-Run Wizard Flow
## Progressive Disclosure Strategy
## Health Check Dashboard
## Demo Mode
## ASCII Wireframes
## Edge Cases and Error Handling
## Open Questions
```

### Step 2: Populate Design Principles

Document the guiding principles for onboarding:

1. **Time to first value < 5 minutes** — customer sees council voting work before they understand
   the full architecture.
2. **Progressive disclosure** — start with one node, one specialist, one vote. Complexity unlocks
   as confidence grows.
3. **No silent failures** — every step shows success/failure with actionable next steps.
4. **Demo mode available** — customer can explore with sample data before committing their own.
5. **Reversible** — every setup step can be undone or reconfigured.
6. **Offline-capable** — onboarding works without internet (sovereign deployment).

### Step 3: Design First-Run Wizard Flow

Document each wizard step as a numbered stage:

**Stage 1: System Check (automatic, ~30 seconds)**
- Detect hardware: GPU (type/VRAM), CPU cores, RAM, disk
- Detect OS and prerequisites (Python, PostgreSQL, systemd)
- Show compatibility report: green/yellow/red for each requirement
- Suggest optimal configuration based on hardware

**Stage 2: Node Registration (~1 minute)**
- Name this node (default: hostname)
- Set node role: primary / worker / DMZ
- Configure network interfaces (LAN IP, optional WireGuard)
- Write node identity to `/ganuda/config/node.json`

**Stage 3: Database Initialization (~2 minutes)**
- Create or connect to PostgreSQL instance
- Run schema migrations (thermal_memory_archive, jr_work_queue, council tables)
- Verify connectivity with test write/read
- Show: "Database ready. 0 thermal memories. Let's make the first one."

**Stage 4: Council Initialization (~1 minute)**
- Select council size: Minimal (4 seats) or Full (12 seats, Professional+)
- Initialize specialist definitions
- Run first health check — each specialist reports ready/not-ready
- Show council status table

**Stage 5: First Thermal Memory Write (~30 seconds)**
- Guided prompt: "Describe something important about your deployment"
- Write to thermal_memory_archive with temperature 50
- Show the stored memory with ID, hash, timestamp
- Explain: "This is how your cluster remembers. Every decision, every event."

**Stage 6: First Longhouse Vote (~1 minute)**
- Propose a simple governance question: "Should this node join the federation?"
- Each initialized specialist casts a vote
- Show vote tally, confidence score, resolution
- Explain the governance model in context of what just happened

**Stage 7: Completion**
- Summary of what was configured
- Links to next steps: add another node, configure Fire Guard, set up notifications
- Option to enter demo mode for exploration

### Step 4: Document Progressive Disclosure Strategy

Map feature visibility to customer maturity:

| Customer Stage | What They See | What Is Hidden |
|---|---|---|
| First hour | Single node, basic council, thermal memory, health check | Multi-node, Jr tasks, dawn mist, valence |
| First week | Fire Guard, basic notifications, Jr task queue | Drift detection, specification engineering, sacred patterns |
| First month | Full specialist council, scheduled rituals, observation levels | Multi-cluster, cross-cluster memory, custom specialists |
| Established | Everything unlocked for their tier | Only higher-tier features gated |

Describe the mechanism: feature flags in config, not hidden code. Customer can always see
what exists and what their tier includes.

### Step 5: Design Health Check Dashboard

Design a first-boot health dashboard showing:

```
+--------------------------------------------------+
|  CHEROKEE AI FEDERATION — Node: redfin           |
|  Status: HEALTHY          Uptime: 4m 32s         |
+--------------------------------------------------+
|                                                    |
|  Services            Status    Last Check          |
|  ─────────────────── ───────── ──────────          |
|  PostgreSQL          [GREEN]   12s ago             |
|  Council Gateway     [GREEN]   12s ago             |
|  Thermal Memory      [GREEN]   12s ago             |
|  Fire Guard          [GREEN]   12s ago             |
|  vLLM Backend        [YELLOW]  12s ago (loading)   |
|                                                    |
|  Council Seats       4/4 active                    |
|  Thermal Memories    1                             |
|  Longhouse Votes     1                             |
|  Jr Tasks            0 queued / 0 running          |
|                                                    |
|  [View Logs]  [Run Health Check]  [Open Console]   |
+--------------------------------------------------+
```

This is a CLI dashboard (TUI), not a web UI. Specify it should use a library like `rich` or
`textual` for Python, or plain formatted output as fallback.

### Step 6: Design Demo Mode

Demo mode pre-populates:

- 50 sample thermal memories across different domains (fire_guard, council, market)
- 10 sample Longhouse votes with varying confidence scores
- 3 sample Jr tasks (1 completed, 1 in progress, 1 failed)
- Sample Fire Guard history with one simulated alert recovery
- Sample dawn mist report

Demo mode flag: `--demo` on first-run wizard or `GANUDA_DEMO=1` env var.
All demo data is tagged with `demo=true` metadata and can be purged with one command.

### Step 7: Document Edge Cases and Error Handling

Cover these scenarios:

1. **No GPU detected** — Wizard continues, warns about performance. CPU-only mode is valid.
2. **PostgreSQL not installed** — Offer to install via package manager (apt/brew) or connect to remote.
3. **Port conflicts** — Detect and suggest alternatives for 8080, 5432, 8000.
4. **Previous installation detected** — Offer: resume, reconfigure, or fresh start.
5. **Network unreachable** — Proceed in offline/single-node mode. Multi-node setup deferred.
6. **Insufficient disk space** — Warn and show estimated requirements per tier.

## Acceptance Criteria

- [ ] Document exists at `/ganuda/docs/business/ONBOARDING-FLOW-MAR09-2026.md`
- [ ] All 7 wizard stages are described with timing estimates
- [ ] Progressive disclosure table maps customer maturity to feature visibility
- [ ] Health check dashboard has an ASCII wireframe
- [ ] Demo mode is specified with sample data counts and purge mechanism
- [ ] At least 6 edge cases are documented with handling strategies
- [ ] Design principles are stated upfront
- [ ] Document is at least 1000 words

## Constraints

- **No code changes.** This is a design document only.
- Create parent directory `/ganuda/docs/business/` if it does not exist.
- ASCII wireframes should be readable in any terminal or markdown renderer.
- Design should work for all three tiers (Community, Professional, Enterprise).
- The onboarding flow must work offline — no external service dependencies during setup.
- Reference existing architecture (Fire Guard, council, thermal memory) by their real names.
