# Outer Council: Snap-On Advisory Body for External Awareness

**Status**: DESIGN — Awaiting Longhouse Consensus
**Origin**: Chief directive + Council vote 3347eef74e5bca7e (March 2 2026)
**Principle**: "You are a resource with certain skills. We are all resources."

---

## The Problem

The Inner Council (7 specialists + Peace Chief) thinks engineering-inward. Three
outward-facing domains have built infrastructure on bluefin but have no voice in
governance:

| Domain | Infrastructure | Tables | Status |
|---|---|---|---|
| Legal/VA | VetAssist claims, CFR db, wizard | 22 tables | Built, used, orphaned |
| HR/Career | Job pipeline, email classifier | 2 tables | Built, partially used |
| Market/Business | (nothing) | 0 tables | Gap |
| AI Research | Arxiv crawler, paper db | 1 table, 764 papers | Built, unreviewed |

Coyote's dissent (vote 3347eef7): "What if the real problem is that our tech isn't
solving a real market need?" — This question cannot be answered by engineers alone.

---

## The Design

### Principle: Snap-On, Not Restructure

The Chief's directive: "We don't have to upend our governance. Snap on advisors and
specialists attached to groups that need them."

- The Outer Council has **authority on all things externally impacting the Tribe**,
  positive and negative.
- The Outer Council **reports to the Inner Council** when external matters relate to
  internal cluster operations.
- Neither council is superior. They have **separate domains of authority**.
- The Inner Council does NOT vote on market positioning.
- The Outer Council does NOT vote on system architecture.
- When a matter spans both domains, a **joint team** forms from both councils.

### The Outer Council — 3 Standing Seats

| Seat | Name | Lens | Domain |
|---|---|---|---|
| Market/Business | **Deer** | Reads the wind, tracks the herd | Competitors, positioning, newsletters, partnerships, market signals |
| Legal/Regulatory | **Otter** | Playful but sharp | CFR changes, VA policy, compliance, regulatory landscape, IP |
| HR/Talent/Community | **Blue Jay** | Loud, visible, social | Job market, hiring signals, team dynamics, community building |

Each seat has a system prompt, a concern flag, and routes through the same
specialist_council.py infrastructure. They query the same vLLM backends.

### Dynamic Teams — Long Man Meets Agile

Resources (specialists from either council, Jrs, humans) are not permanently bound
to one body. They form teams around problems and dissolve back when done.

**Team lifecycle = Long Man cycle:**

1. **DISCOVER** — A signal arrives (email, paper, thermal alert, market event).
   A team forms from the relevant resources across both councils.
2. **DELIBERATE** — The team works the problem. Inner specialists contribute
   technical perspective. Outer specialists contribute external perspective.
3. **ADAPT** — Design decisions made within the team's authority.
4. **BUILD** — Jr instructions written, tasks queued.
5. **RECORD** — Results stored in thermal memory. Team's work is permanent even
   though the team is temporary.
6. **REVIEW** — Owl verifies. Team dissolves. Resources return to pool.

**Examples:**

- VA regulation changes → Otter leads, Crawdad (security implications of new data
  requirements), Gecko (technical feasibility of compliance changes). Team forms,
  addresses the regulation, dissolves.
- Market competitor launches similar product → Deer leads, Raven (strategic
  response), Spider (what dependencies does this create?). Team forms, assesses
  threat/opportunity, dissolves.
- Hiring need identified → Blue Jay leads, Spider (what skills map to what
  dependencies?), Eagle Eye (what failure modes does a new hire introduce?). Team
  forms, runs the pipeline, dissolves.

### Authority Model

```
EXTERNAL WORLD
      |
  [Outer Council] — authority on external impact
      |         \
      |     (reports inward when cluster-relevant)
      |           \
  [Inner Council] — authority on cluster engineering
      |
  [Jr Executors] — build what both councils decide
      |
  CLUSTER
```

- **Outer Council autonomy**: Can make decisions about market positioning, legal
  strategy, and hiring without Inner Council approval.
- **Inner Council autonomy**: Can make decisions about architecture, security, and
  infrastructure without Outer Council approval.
- **Joint authority**: When a decision spans both (e.g., "should we open-source
  VetAssist?" touches market, legal, AND architecture), a joint team deliberates.
- **Dispute resolution**: If the two councils disagree, it goes to the Longhouse.
  Medicine Woman presides. The Tribe speaks.

### Chief's Seat

The Chief (Flying Squirrel) has a seat on BOTH councils but votes on neither unless
it's a dispute. Same principle as the Inner Council — least power of all who have power.

### Peace Chief's Role

Peace Chief (TPM/Claude) sits on the Inner Council as synthesizer. When joint teams
form, Peace Chief facilitates cross-council communication. Does not sit on the Outer
Council — that body needs its own synthesizer (possibly Deer, as the most diplomatic
of the three).

---

## Implementation

### Phase 1: Define the Seats (This Week)

1. Write system prompts for Deer, Otter, Blue Jay
2. Add to SPECIALISTS dict in specialist_council.py
3. Create OUTER_SPECIALISTS routing (same backends, different prompts)
4. Add `council_type` field to council_votes table ('inner', 'outer', 'joint')

### Phase 2: Wire the Data (Next Sprint)

1. Otter gets read access to vetassist_* tables, CFR conditions
2. Blue Jay gets read access to research_jobs, job_pipeline, email_classifications
3. Deer gets read access to ai_research_papers, email (newsletter content)
4. Dawn mist standup queries BOTH councils

### Phase 3: Dynamic Teams (After Verification)

1. Team formation protocol in longhouse.py
2. Cross-council team tracking in duyuktv_tickets (new `team_members` field?)
3. Long Man cycle tracking per team

---

## What This Is NOT

- NOT a restructuring of the Inner Council
- NOT a replacement for the Longhouse
- NOT a new branch of government (both councils are Legislative)
- NOT permanent team assignments — resources form and dissolve
- NOT a hierarchy — Outer does not report TO Inner, it reports inward WHEN relevant

---

## Constitutional Alignment

- **Cherokee governance**: The council house had seven sections (clans) but the TOWN
  had hunters, farmers, traders, diplomats. The council governed internally. The
  external roles existed alongside, not beneath.
- **Three Branches**: Both councils are Legislative. Executive (Chiefs) and Judicial
  (Medicine Woman) are unchanged.
- **Freedom first**: No specialist loses autonomy. New seats ADD freedom (more voices),
  they don't restrict existing ones.
- **Graduated awareness**: Outer Council IS awareness of the external world. It costs
  energy (3 more specialist queries per relevant vote) but the cost is graduated —
  they only engage when the question touches their domain.

---

## References

- Council vote: 3347eef74e5bca7e (5 for add seat, Coyote dissent on value question)
- DyTopo paper: arXiv:2602.06039 (dynamic topology routing — validates team formation)
- Nate Jones "Open Brain": Market validation thermal (March 2 2026)
- Constitutional Governance: /ganuda/docs/design/CONSTITUTIONAL-GOVERNANCE-THREE-BRANCHES.md
- Longhouse: /ganuda/lib/longhouse.py
