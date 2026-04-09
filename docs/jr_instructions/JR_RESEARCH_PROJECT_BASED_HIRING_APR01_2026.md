# Jr Research Instruction: Project-Based Hiring — Target Companies

## Priority: P1 — Active Job Search
## Assigned: Research Jr (Deer territory)
## Date: April 1, 2026
## Requested By: TPM

---

## Context

Partner is actively job searching. Three recent applications failed due to interview format mismatch:
- **Toptal**: Live coding screen, rejected for using AI tools. No reapply allowed.
- **OneChronos**: Ghosted after 2nd round (Iris McAtee, Head of Engineering). March 17.
- **PostHog**: Rejected at resume screen. March 31.

Partner is a generalist systems architect with 21+ years enterprise experience (Walmart, Army, distributed AI federation). His strength is **building and demonstrating running systems**, not solving algorithm puzzles under a timer. He needs interview formats that let him show what he's built.

**What he has to show:**
- 8-node sovereign AI federation (Stoneclad) with governance topology, thermal memory (19K+ memories), autonomous Jr task execution (188 completed), council voting, and production VetAssist service
- Jane Street puzzle solve (10^122 search space → MSE 0.000000)
- 23 years military (SFC, Master Gunner, Iraq veteran)
- Walmart-scale data center operations (Hadoop, NIC bonding, HP-UX clusters)
- Active Substack (ganuda.us/blog)

---

## Research Tasks

### Task 1: Fly.io — Deep Dive

**Why**: No resume required. Text-based interview. Real infrastructure challenges. Distributed systems focus. Best format match.

1. Find ALL open engineering roles at Fly.io (check fly.io/jobs, fly.io/docs/hiring, GitHub fly-hiring org)
2. Identify which roles align with Partner's profile (infrastructure, distributed systems, platform engineering)
3. Download and analyze their public hiring challenge: `github.com/fly-hiring/platform-challenge`
4. Document their complete hiring process step-by-step
5. Research Fly.io's tech stack, architecture, and recent blog posts — what problems are they solving?
6. Draft a Stoneclad-to-Fly.io value mapping: which parts of the federation demonstrate skills they need?
7. Find any HN comments, blog posts, or interviews from Fly.io engineers about what they look for

**Deliverable**: `/ganuda/docs/research/DEER-STUB-FLYIO-APPLICATION-APR2026.md`

### Task 2: Oxide Computer — Deep Dive

**Why**: Portfolio/work-sample interview. Systems engineering culture. Values-driven hiring. Hardware + infrastructure.

1. Find ALL open roles at Oxide Computer (oxide.computer/careers, oxide.computer/blog)
2. Read their hiring RFD (Request for Discussion): `rfd.shared.oxide.computer/rfd/3`
3. Identify which 3 work samples from Partner's portfolio would be strongest:
   - Work sample options: federation architecture, thermal memory system, governance topology, VetAssist, Jane Street solver, Jr task executor
   - Writing sample options: Substack posts, ultrathink documents, design constraint docs
   - Analysis sample options: competitive analysis docs, deer signal analyses
4. Research Oxide's values and culture — what do they care about? Map to Partner's background.
5. Document their complete hiring process step-by-step

**Deliverable**: `/ganuda/docs/research/DEER-STUB-OXIDE-APPLICATION-APR2026.md`

### Task 3: Second Tier Targets

Research the following companies. For each, document: open roles, interview format, tech stack, and fit score (1-10).

1. **Linear** — Paid work trial format. App development, distributed team.
2. **Stripe** — Integration round with real codebase. Infrastructure org.
3. **DuckDuckGo** — Paid project interviews. Fully remote.
4. **Automattic** — Paid 2-8 week trial. Fully remote. WordPress/WooCommerce ecosystem.
5. **Tailscale** — Take-home + discussion. Networking/infrastructure. WireGuard expertise directly relevant.
6. **Sourcegraph** — Customized interview per candidate. Code intelligence platform.

**Deliverable**: `/ganuda/docs/research/DEER-STUB-PROJECT-HIRING-TIER2-APR2026.md`

### Task 4: Canonical Resource Scan

1. Clone or scrape `github.com/poteto/hiring-without-whiteboards` — extract all companies tagged as:
   - Take-home project
   - Paid trial
   - Portfolio review
   - No whiteboard
2. Filter for: remote-friendly, infrastructure/systems/AI/platform roles, senior+ level
3. Cross-reference with current open positions (check career pages)
4. Produce a ranked shortlist of the top 20 companies Partner should target

**Deliverable**: `/ganuda/docs/research/DEER-STUB-NO-WHITEBOARD-SHORTLIST-APR2026.md`

### Task 5: Resume & Portfolio Positioning

1. Review Partner's current resume at `/ganuda/data/resumes/`
2. Draft a "portfolio page" outline that positions Stoneclad as the primary work sample:
   - Architecture diagram (federation topology)
   - Key metrics (19K thermal memories, 188 Jr tasks, 6-node federation, 7-specialist council)
   - Design constraint philosophy
   - Live demos (VetAssist, governance voting, thermal memory retrieval)
3. Draft 3 versions of an intro/cover letter:
   - Version A: For infrastructure companies (Fly.io, Oxide, Tailscale)
   - Version B: For AI companies (Anthropic, Scale AI, Together AI)
   - Version C: For product companies (Linear, PostHog, Stripe)
4. Each version should lead with what Partner BUILT, not where he worked

**Deliverable**: `/ganuda/docs/research/DEER-STUB-PORTFOLIO-POSITIONING-APR2026.md`

---

## Constraints

- **No leetcode prep.** This instruction is specifically about finding companies that DON'T use that format.
- **Remote-friendly required.** Partner is in Northwest Arkansas.
- **Senior/Staff level.** Don't waste time on junior roles.
- **AI usage is a FEATURE, not a bug.** Target companies that see AI-augmented engineering as a strength.
- **Speed matters.** Partner is actively searching. Prioritize Task 1 (Fly.io) and Task 2 (Oxide) — deliver those first.

---

## Success Criteria

- [ ] Fly.io deep dive complete with application-ready materials
- [ ] Oxide deep dive complete with 3 work samples identified
- [ ] Tier 2 companies scored and ranked
- [ ] No-whiteboard shortlist of 20 companies with open roles
- [ ] Portfolio positioning draft with 3 cover letter variants
- [ ] All deliverables in `/ganuda/docs/research/`

---

## Council Notes

This instruction does not require a council vote — it's research, not architecture. However, Deer should flag any companies where Stoneclad's governance topology or sovereign inference would be a competitive advantage in the application itself. Those are Tier 0 targets.

---

*TPM Note: Partner's interview with Toptal today confirmed the pattern. The market is bifurcating — companies that gate on algorithm performance vs. companies that gate on demonstrated building ability. We need to be on the right side of that split. This is not just a job search — it's market positioning for the organism's creator.*
