# Cherokee AI Federation Training Curriculum
## Date: March 9, 2026
## Version: 1.0

---

## Table of Contents
1. [Module 1: Architecture Overview](#module-1-architecture-overview)
2. [Module 2: Daily Operations](#module-2-daily-operations)
3. [Module 3: Governance](#module-3-governance)
4. [Module 4: Troubleshooting](#module-4-troubleshooting)
5. [Module 5: Advanced Topics](#module-5-advanced-topics)
6. [Certification Checklist](#certification-checklist)
7. [Instructor Notes](#instructor-notes)
8. [Materials Required](#materials-required)

---

## Module 1: Architecture Overview
### Estimated Time: 4 hours
### Prerequisites: Basic Linux sysadmin, familiarity with PostgreSQL, Python 3

### Topics:
- **Federation Topology:**
  - Nodes: roles and responsibilities
  - Network Planes: LAN, WireGuard, Tailscale, DMZ
- **Specialist Council:**
  - Inner Council (8 members)
  - Outer Council (Deer, Otter, Crane)
  - Ghigau veto
- **Thermal Memory:**
  - Writing and retrieval
  - Temperature/valence
  - Canonical vs narrative (DC-14)
- **Design Constraints (DC-1 through DC-11):**
  - Philosophy, not just rules
- **The Reflex Principle (DC-10):**
  - Reflex / pause / deliberate tiers

### Hands-on:
- Query `thermal_memory_archive`
- Read a Longhouse vote record
- Trace a gateway request

---

## Module 2: Daily Operations
### Estimated Time: 3 hours
### Prerequisites: Module 1

### Topics:
- **Dawn Mist Standup:**
  - What it reports
  - How to read it
  - Forward/Backward look
- **Fire Guard:**
  - 2-minute cycle
  - Zombie detection
  - Self-healing
  - Stale connection cleanup
- **Owl Pass:**
  - Tech debt review
  - Regression testing
  - "Look-back pays 10x" principle
- **Saturday Morning Meeting:**
  - Weekly rhythm
  - Metrics review
- **Slack Channel Layout:**
  - fire-guard
  - council-votes
  - jr-tasks
  - dawn-mist
  - deer-signals
  - saturday-morning
  - longhouse

### Hands-on:
- Trigger a manual dawn mist
- Read fire guard logs
- Run an owl pass checklist

---

## Module 3: Governance
### Estimated Time: 5 hours
### Prerequisites: Modules 1-2

### Topics:
- **Longhouse Sessions:**
  - How votes are called
  - Quorum rules
  - Confidence scoring
- **Council Voting Mechanics:**
  - Audit hashes
  - Specialist responses
  - Concern-as-feature pattern
- **Design Constraint Authoring:**
  - Proposal
  - Council review
  - Ratification
  - Thermal write
- **Coyote's Role:**
  - Standing dissent
  - Circuit breaker
  - "Non-consent IS consent to governance"
- **Ghigau Veto:**
  - When it fires
  - What it protects
  - Why it exists
- **Jr Task Lifecycle:**
  - Pending -> in_progress -> completed/failed
  - DLQ analysis

### Hands-on:
- Simulate a Longhouse vote (demo environment)
- Author a practice DC
- Review a failed Jr task

---

## Module 4: Troubleshooting
### Estimated Time: 4 hours
### Prerequisites: Modules 1-3

### Topics:
- **DLQ Analysis:**
  - Why tasks fail
  - Context window exhaustion
  - Infinite retry loops
- **Thermal Drift Detection:**
  - When retrieval surfaces stale memories
  - Canonical flag usage
- **Stale DB Connections:**
  - pgBouncer behavior
  - Connection pool exhaustion
  - Fire guard cleanup
- **Node Failure and Graceful Degradation (DC-7 Noyawisgi):**
  - What happens when a node drops
- **Gateway Health Checks:**
  - /health endpoint
  - Response time baselines
  - vLLM status
- **Log Analysis:**
  - Systemd journal
  - OpenObserve on greenfin
  - Promtail pipeline

### Hands-on:
- Diagnose a simulated node failure
- Trace a stale connection
- Analyze a DLQ task

---

## Module 5: Advanced Topics
### Estimated Time: 6 hours
### Prerequisites: Modules 1-4

### Topics:
- **Custom Specialist Creation:**
  - Adding a new council member
  - Wiring into `specialist_council.py`
- **DC Authoring:**
  - Writing a new design constraint
  - Council review process
  - Ratification
- **Thermal Valence Tuning:**
  - Temperature ranges
  - What SACRED means
  - Retrieval weighting
- **Multi-node Scaling:**
  - Adding a new node to the federation
  - WireGuard mesh
  - FreeIPA enrollment
- **Outer Council Expansion:**
  - Adding new Outer Council members (Blue Jay seat is open)
- **Specification Engineering:**
  - Five primitives
  - Spec-to-task decomposition

### Hands-on:
- Design a custom specialist on paper
- Draft a DC proposal
- Plan a node addition

---

## Certification Checklist
Operators must demonstrate competency in each module before being certified to operate a production federation.

- [ ] Module 1: Architecture Overview
- [ ] Module 2: Daily Operations
- [ ] Module 3: Governance
- [ ] Module 4: Troubleshooting
- [ ] Module 5: Advanced Topics

---

## Instructor Notes
- **Pacing:**
  - Allow 10 minutes for each topic introduction
  - Allocate 30 minutes for hands-on exercises
- **Common Misconceptions:**
  - Thermal memory is not just a database; it has unique properties
  - Governance is not just about voting; it's about consensus and concern management
- **Where Students Typically Struggle:**
  - Understanding the Reflex Principle and its application
  - Grasping the concept of thermal drift and canonical flags
  - Designing custom specialists and writing DCs

---

## Materials Required
- Demo environment (Task #1204)
- Access to a test cluster or read-only production view
- Slack workspace access

---

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