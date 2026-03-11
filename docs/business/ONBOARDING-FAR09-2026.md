# Cherokee AI Federation — Customer Onboarding Flow Design

**Date:** March 9, 2026
**Task:** #1196
**Status:** Draft

## Design Principles

1. **Time to first value < 5 minutes** — customer sees council voting work before they understand the full architecture.
2. **Progressive disclosure** — start with one node, one specialist, one vote. Complexity unlocks as confidence grows.
3. **No silent failures** — every step shows success/failure with actionable next steps.
4. **Demo mode available** — customer can explore with sample data before committing their own.
5. **Reversible** — every setup step can be undone or reconfigured.
6. **Offline-capable** — onboarding works without internet (sovereign deployment).

## First-Run Wizard Flow

### Stage 1: System Check (automatic, ~30 seconds)
- Detect hardware: GPU (type/VRAM), CPU cores, RAM, disk
- Detect OS and prerequisites (Python, PostgreSQL, systemd)
- Show compatibility report: green/yellow/red for each requirement
- Suggest optimal configuration based on hardware

### Stage 2: Node Registration (~1 minute)
- Name this node (default: hostname)
- Set node role: primary / worker / DMZ
- Configure network interfaces (LAN IP, optional WireGuard)
- Write node identity to `/ganuda/config/node.json`

### Stage 3: Database Initialization (~2 minutes)
- Create or connect to PostgreSQL instance
- Run schema migrations (thermal_memory_archive, jr_work_queue, council tables)
- Verify connectivity with test write/read
- Show: "Database ready. 0 thermal memories. Let's make the first one."

### Stage 4: Council Initialization (~1 minute)
- Select council size: Minimal (4 seats) or Full (12 seats, Professional+)
- Initialize specialist definitions
- Run first health check — each specialist reports ready/not-ready
- Show council status table

### Stage 5: First Thermal Memory Write (~30 seconds)
- Guided prompt: "Describe something important about your deployment"
- Write to thermal_memory_archive with temperature 50
- Show the stored memory with ID, hash, timestamp
- Explain: "This is how your cluster remembers. Every decision, every event."

### Stage 6: First Longhouse Vote (~1 minute)
- Propose a simple governance question: "Should this node join the federation?"
- Each initialized specialist casts a vote
- Show vote tally, confidence score, resolution
- Explain the governance model in context of what just happened

### Stage 7: Completion
- Summary of what was configured
- Links to next steps: add another node, configure Fire Guard, set up notifications
- Option to enter demo mode for exploration

## Progressive Disclosure Strategy

| Customer Stage | What They See | What Is Hidden |
|---|---|---|
| First hour | Single node, basic council, thermal memory, health check | Multi-node, Jr tasks, dawn mist, valence |
| First week | Fire Guard, basic notifications, Jr task queue | Drift detection, specification engineering, sacred patterns |
| First month | Full specialist council, scheduled rituals, observation levels | Multi-cluster, cross-cluster memory, custom specialists |
| Established | Everything unlocked for their tier | Only higher-tier features gated |

The mechanism for progressive disclosure is feature flags in the configuration. Customers can always see what exists and what their tier includes.

## Health Check Dashboard