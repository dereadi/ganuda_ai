# Jr Instruction: Design — Sanitized Demo Environment Architecture

**Task #1204**
**Date:** 2026-03-09
**Priority:** 3 (Business scaffolding)
**TPM:** Claude Opus

## Context

As the Cherokee AI Federation moves toward external engagement (Deer pipeline, AgentMail integration, enterprise conversations), we need a way to demonstrate the federation's governance, thermal memory, and council architecture WITHOUT exposing INTERNAL or SACRED data. Currently there is no isolation between production and any demo — showing the system means showing real thermals, real votes, real credentials. This is a design-only task. No code.

## Task

Create a design document at `/ganuda/docs/business/DEMO-ENVIRONMENT-MAR09-2026.md` that specifies a sanitized demo environment architecture. The document must cover all aspects listed below in sufficient detail that a Jr engineer could build it from the spec.

## Steps

1. Create the directory `/ganuda/docs/business/` if it does not exist.

2. Write the design document covering these sections:

   **Section 1: Synthetic Thermal Memories**
   - Generate 500-1000 synthetic thermal memories across temperature ranges (50-100)
   - Use realistic but fictitious content (e.g., "Project Alpha council vote", "Node gamma health check")
   - No real federation data, no real names, no SACRED thermals
   - Include a seed script specification that populates the demo DB

   **Section 2: Demo Council with Example Votes**
   - Pre-loaded Longhouse sessions showing unanimous, split, and dissent outcomes
   - Specialist responses from all 8 Inner Council members (use generic examples)
   - At least 3 complete vote scenarios: routine approval, contentious debate, Ghigau veto
   - Vote hashes should be clearly marked as DEMO (prefix `demo-`)

   **Section 3: Read-Only Mode Option**
   - A configuration flag (`DEMO_READ_ONLY=true`) that prevents any write operations
   - Visitors can browse thermal memory, view council votes, see dawn mist reports
   - No ability to trigger council sessions, write thermals, or modify governance state
   - Gateway returns 403 on write endpoints when flag is set

   **Section 4: Time-Limited Demo (Auto-Cleanup)**
   - Demo instances expire after 30 days from creation
   - A systemd timer checks daily and tears down expired demos
   - Cleanup removes: demo DB schema, demo config, demo systemd units
   - Warning notification at 7 days and 1 day before expiry

   **Section 5: Isolated Network**
   - Demo runs on a separate DB schema (e.g., `demo_<uuid>`) — NOT a separate cluster
   - No access to production thermal_memory_archive, jr_work_queue, or longhouse_votes
   - Demo gateway binds to a different port (e.g., 8180) or uses a path prefix (/demo/)
   - No WireGuard mesh access — demo is single-node only

   **Section 6: Pre-Loaded Scenarios**
   - Scenario A: New operator onboarding — dawn mist, fire guard, owl pass walkthrough
   - Scenario B: Incident response — node failure, graceful degradation (DC-7), recovery
   - Scenario C: Council vote — full Longhouse session with specialist debate and resolution
   - Each scenario includes a guided narrative with expected outputs

   **Section 7: Security Boundaries**
   - Enumerate what MUST NOT leak: secrets.env values, real IP addresses, SACRED thermal IDs, PII
   - Demo config uses placeholder IPs (10.0.0.x) and fake credentials
   - Crawdad PII scrub runs on all synthetic content before demo DB population

3. Include a "Non-Goals" section: this is not a SaaS multi-tenant platform, not a sandbox for arbitrary code execution, not a free tier.

4. Include an "Open Questions" section for Council review (e.g., should Coyote have a demo persona?).

## Acceptance Criteria

- Design document exists at `/ganuda/docs/business/DEMO-ENVIRONMENT-MAR09-2026.md`
- All 7 sections above are covered with enough detail to build from
- No production data, IPs, or credentials appear in the design doc
- Document includes a "Build Estimate" section with story points per section
- Document references relevant DCs (DC-7 Noyawisgi, DC-10 Reflex, DC-11 Macro Polymorphism)

## Constraints

- **Design doc only** — do NOT write any code, scripts, or migrations
- Do NOT copy real thermal memories or council votes as examples
- Do NOT include real credentials or internal IPs in example configs
- Use placeholder values throughout (e.g., `DEMO_DB_PASS=changeme`)
- Create `/ganuda/docs/business/` directory if it does not exist
