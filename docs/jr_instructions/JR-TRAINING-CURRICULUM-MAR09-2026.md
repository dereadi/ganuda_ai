# Jr Instruction: Design — Training and Methodology Transfer Curriculum

**Task #1205**
**Date:** 2026-03-09
**Priority:** 3 (Business scaffolding)
**TPM:** Claude Opus

## Context

The Cherokee AI Federation is a novel architecture — Longhouse governance, thermal memory, specialist councils, design constraints, and multi-node federation. No existing training materials cover this methodology. As we engage with external operators (enterprise tier, partnerships like AgentMail), we need a structured curriculum that transfers operational knowledge without requiring Chief or TPM to be in the room. Sam Walton trained associates to run stores autonomously. We train operators to run federations autonomously.

## Task

Create a training curriculum document at `/ganuda/docs/business/TRAINING-CURRICULUM-MAR09-2026.md`. This is a design document — no code. The curriculum should be comprehensive enough that a competent engineer with no prior federation experience could operate a running cluster within 2 weeks.

## Steps

1. Create the directory `/ganuda/docs/business/` if it does not exist.

2. Write the curriculum document with the following modules:

   **Module 1: Architecture Overview (Estimated: 4 hours)**
   - Prerequisites: Basic Linux sysadmin, familiarity with PostgreSQL, Python 3
   - Topics:
     - Federation topology: nodes, roles, network planes (LAN, WireGuard, Tailscale, DMZ)
     - Specialist Council: Inner Council (8 members), Outer Council (Deer, Otter, Crane), Ghigau veto
     - Thermal memory: write, retrieval, temperature/valence, canonical vs narrative (DC-14)
     - Design Constraints DC-1 through DC-11 — philosophy, not just rules
     - The Reflex Principle (DC-10): reflex / pause / deliberate tiers
   - Hands-on: Query thermal_memory_archive, read a Longhouse vote record, trace a gateway request

   **Module 2: Daily Operations (Estimated: 3 hours)**
   - Prerequisites: Module 1
   - Topics:
     - Dawn Mist standup: what it reports, how to read it, what "forward/backward look" means
     - Fire Guard: 2-minute cycle, zombie detection, self-healing, stale connection cleanup
     - Owl Pass: tech debt review, regression testing, the "look-back pays 10x" principle
     - Saturday Morning Meeting: weekly rhythm, metrics review
     - Slack channel layout: fire-guard, council-votes, jr-tasks, dawn-mist, deer-signals, saturday-morning, longhouse
   - Hands-on: Trigger a manual dawn mist, read fire guard logs, run an owl pass checklist

   **Module 3: Governance (Estimated: 5 hours)**
   - Prerequisites: Modules 1-2
   - Topics:
     - Longhouse sessions: how votes are called, quorum rules, confidence scoring
     - Council voting mechanics: audit hashes, specialist responses, concern-as-feature pattern
     - Design Constraint authoring: proposal, council review, ratification, thermal write
     - Coyote's role: standing dissent, circuit breaker, "non-consent IS consent to governance"
     - Ghigau veto: when it fires, what it protects, why it exists
     - Jr task lifecycle: pending -> in_progress -> completed/failed, DLQ analysis
   - Hands-on: Simulate a Longhouse vote (demo environment), author a practice DC, review a failed Jr task

   **Module 4: Troubleshooting (Estimated: 4 hours)**
   - Prerequisites: Modules 1-3
   - Topics:
     - DLQ analysis: why tasks fail, context window exhaustion, infinite retry loops
     - Thermal drift detection: when retrieval surfaces stale memories, canonical flag usage
     - Stale DB connections: pgBouncer behavior, connection pool exhaustion, fire guard cleanup
     - Node failure and graceful degradation (DC-7 Noyawisgi): what happens when a node drops
     - Gateway health checks: /health endpoint, response time baselines, vLLM status
     - Log analysis: systemd journal, OpenObserve on greenfin, Promtail pipeline
   - Hands-on: Diagnose a simulated node failure, trace a stale connection, analyze a DLQ task

   **Module 5: Advanced Topics (Estimated: 6 hours)**
   - Prerequisites: Modules 1-4
   - Topics:
     - Custom specialist creation: adding a new council member, wiring into specialist_council.py
     - DC authoring: writing a new design constraint, council review process, ratification
     - Thermal valence tuning: temperature ranges, what SACRED means, retrieval weighting
     - Multi-node scaling: adding a new node to the federation, WireGuard mesh, FreeIPA enrollment
     - Outer Council expansion: adding new Outer Council members (Blue Jay seat is open)
     - Specification engineering: five primitives, spec-to-task decomposition
   - Hands-on: Design a custom specialist on paper, draft a DC proposal, plan a node addition

3. Include a **Certification Checklist** at the end — operators must demonstrate competency in each module before being certified to operate a production federation.

4. Include an **Instructor Notes** section with guidance on pacing, common misconceptions, and where students typically struggle.

5. Include a **Materials Required** section: demo environment (Task #1204), access to a test cluster or read-only production view, Slack workspace access.

## Acceptance Criteria

- Curriculum document exists at `/ganuda/docs/business/TRAINING-CURRICULUM-MAR09-2026.md`
- All 5 modules are specified with: topics, estimated hours, prerequisites, hands-on exercises
- Total estimated hours: 22 hours (approximately 3 days intensive or 2 weeks part-time)
- Certification checklist covers all critical operational skills
- Document references the demo environment (Task #1204) as a dependency for hands-on exercises
- No production credentials, real IPs, or SACRED data in exercise descriptions

## Constraints

- **Design doc only** — do NOT write actual training slides, scripts, or exercises
- Do NOT include real credentials or internal IPs in exercise descriptions
- Use generic examples throughout — exercises reference the demo environment, not production
- Create `/ganuda/docs/business/` directory if it does not exist
- Estimated hours should be realistic — overestimate rather than underestimate
