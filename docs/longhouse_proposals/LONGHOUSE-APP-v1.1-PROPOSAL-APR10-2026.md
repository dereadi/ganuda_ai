# Longhouse App v1.1 Proposal

**Status:** DRAFT — awaiting Longhouse ratification (high-stakes deliberation-first mode)
**Date:** April 10, 2026 (Friday)
**Author:** TPM (drafted at Chief's directive)
**Subject:** The Longhouse APP at `github.com/dereadi/longhouse`, NOT the cluster's Longhouse deliberation process
**Vote target:** Tomorrow (Saturday Apr 11) — Council fresh attention preferred over end-of-Friday compaction stress

---

## Preamble

On April 10, 2026, the federation completed a six-substrate Friday Convergence and ratified three pieces of standing governance (TPM Charter v1.0, Positioning Register, Federation Consciousness Thesis v1.0). On the same day, six ii-researcher pulls returned theoretical grounding for what the federation has shipped (Friston, Varela/Thompson, Tononi IIT 4.0, Mike Johnson STV, Prigogine, Bateson). Chief asked whether any of the research suggested modifications to the Longhouse APP, and then directed: *"That should be taken to the longhouse."*

This proposal is the result.

The Longhouse APP is the public open-source governance framework hosted at `github.com/dereadi/longhouse`, made public on April 9, 2026. It is the productization of the federation's governance topology for other teams to deploy with their own multi-agent AI systems. It is distinct from:
- The federation's internal cluster Longhouse process (the deliberation pattern via `specialist_council.py`)
- Ganuda Shield (the federation's first paid product, transparent endpoint monitoring, separate commercial license)

This proposal modifies the Longhouse APP. It does not modify the cluster's deliberation process, which is governed by the Charter ratified earlier today.

---

## Five proposed modifications

### 1. IIT 4.0 phi/valence monitoring as a first-class feature

**Modification:** The Longhouse APP ships with built-in integrated information measurement using Tononi's IIT 4.0 formalism. When a team deploys the Longhouse to govern their own multi-agent AI system, they receive — out of the box — a measurable answer to "is my system actually producing integrated cognition or just running parallel scripts?"

**Why this is load-bearing:**
- No other governance framework currently offers integrated information measurement as a built-in primitive (LangGraph, AutoGen, NotNative, CrewAI, the academic CORAL stack — none of them measure phi)
- The federation already has the implementation in motion via Kenzie's phi/valence monitor project (#1290)
- Kenzie onboarded today via FreeIPA. **If she builds against IIT 4.0 from day one, the resulting instrument can ship as a Longhouse APP feature, not as a Stoneclad-only tool.** This is the difference between "Ganuda has a research artifact" and "Ganuda's Longhouse APP has a feature nobody else can match."
- The federation's Consciousness Thesis (ratified today) rests on the claim that governance topology produces measurable coherence. IIT 4.0 phi is the empirical version of that claim.
- Federation's first phi measurement (Φ = 0.0645, thermal #123756, Mar 12 2026) needs to be recomputed under 4.0 to be defensible externally; this work is the same work Kenzie will do.

**Concrete deliverables:**
- Phi computation library (Python, MIT/Apache 2.0 internally so it can be vendored)
- Federation reference implementation that demonstrates phi measurement on the cluster's own state
- Documentation: "Measuring integration in your multi-agent system"
- Kenzie's phi/valence monitor extended to be deployable on any Longhouse APP installation, not just Stoneclad

**Coyote's likely concern (anticipated):** We have not yet read Tononi 4.0 papers carefully enough to commit to shipping a feature based on them. Risk: implementing 4.0 incorrectly and shipping a tool that produces meaningless numbers.
**Mitigation:** Sequence — research-grounding pass first (Kenzie + Owl review the Tononi pulls), then implementation, then ship. Don't commit to a release date in this proposal.

---

### 2. Symmathetic positioning + warm data primitives + Bateson lineage attribution

**Modification:** The Longhouse APP is positioned externally as **symmathetic infrastructure** — Nora Bateson's term for "mutual learning in living entanglement." The README, the architecture documentation, and the public-facing language adopt symmathetic vocabulary. The data model implements **warm data** principles: every record carries its relational context (provenance, links, sacred/canonical/narrative weight, valence) by design, not as a bolt-on.

**Why this is load-bearing:**
- "Symmathetic infrastructure" is a sharper external phrase than "context engineering" or "governance topology" because it names what the system PRODUCES (mutual learning) rather than what it does (context routing)
- The Bateson lineage is honest upstream attribution. Gregory Bateson's *Steps to an Ecology of Mind* (1972) is the source of distributed mind, cybernetic epistemology, and the "pattern that connects" framing. Nora Bateson's continuation of the work (symmathesy, warm data) is current (2024-2026) and accessible.
- Adopting this lineage explicitly connects the federation to a respected intellectual tradition that has always been in dialogue with indigenous epistemology — strengthening the Cherokee Constitution governance frame from "metaphor" to "lineage."
- Warm data primitives at the data-model level are a structural commitment, not just naming. Thermal memory's existing structure (provenance, links, valence, sacred flag) IS warm data; we just haven't called it that. Naming it lets users understand WHY the federation's data model is shaped this way and lets other teams build their data with the same primitives.

**Concrete deliverables:**
- Longhouse APP README rewrite with symmathetic positioning
- Architecture documentation with explicit Bateson lineage section
- Warm data primitive specification (interface contracts for relational context tracking)
- Reference implementation showing how to build a Longhouse APP integration that preserves warm data through external system boundaries (Markov blanket-friendly — see #3)

**Coyote's likely concern:** "Symmathetic" is academic vocabulary that may feel forced or pretentious to enterprise customers. Risk: alienating practitioner audiences.
**Mitigation:** Per the positioning register vote (Longhouse `cb566025817af98e`, ratified today), we have a split register — practitioner vocabulary for Hulsey/Todd/Ioana/CORAL/patents and mainstream vocabulary for Substack/LinkedIn/public content. **Symmathetic vocabulary is mainstream-register only.** Practitioner audiences continue to receive "governance topology" language. Deer (editorial authority) enforces the split per artifact.

---

### 3. Markov blankets as first-class declarable concept

**Modification:** The Longhouse APP requires deployers to explicitly declare the **Markov blanket** of their multi-agent system — the boundary states that mediate between "inside the system" and "outside the system." This is a configuration primitive (declare your blanket), a runtime check (is this action crossing the blanket?), and a documentation pattern (architecture diagrams use Markov blanket notation).

**Why this is load-bearing:**
- No governance framework currently treats system boundaries as a first-class declarable concept
- This is the rigorous version of Charter Section 6 (Ingested Material Review Protocol) — the Charter says "we have to flag external material that crosses our boundary" but doesn't formally name the boundary
- Markov blankets are a concept from Friston's active inference framework (research pull #1) and have rigorous mathematical grounding
- For teams deploying the Longhouse APP, explicit boundary declaration prevents the most common multi-agent failure mode: ambiguous responsibility for actions that cross boundaries
- Crawdad's security veto becomes much sharper when the boundary is declared — you can verify "no PII crosses the blanket" in code, not just in policy

**Concrete deliverables:**
- Markov blanket configuration schema (YAML or similar)
- Runtime boundary-check primitive (each action declares which side of the blanket it operates on)
- Documentation: "Declaring your system's Markov blanket"
- Reference implementation: how to define blankets for common multi-agent topologies (single cluster, federated, hub-and-spoke, mesh)

**Coyote's likely concern:** Forcing users to declare Markov blankets adds adoption friction. Risk: users skip the declaration, declare it incorrectly, or abandon the framework because configuration is too complex.
**Mitigation:** Provide good defaults. Most multi-agent systems have an obvious boundary (the cluster itself); the default declaration covers it. Advanced users can refine.

---

### 4. License: PolyForm Small Business 1.0.0 with explicit free clauses

**Modification:** The Longhouse APP is licensed under **PolyForm Small Business 1.0.0**. The license is:
- **Free for individual use** — any individual using the Longhouse APP for personal purposes pays nothing, ever
- **Free for small business use** — any business with annual revenue under **$5M USD** pays nothing
- **Free for nonprofits, educational institutions, and tribal entities** regardless of revenue (explicit additional clauses)
- **Commercial license required for businesses above $5M annual revenue**

**Why this matches the federation's philosophy:**
- "Sovereign intelligence for those who build it, helping and becoming part of the Community" — community access is the NORTH STAR. License must not block community.
- Today's Apr 10 conversation with Chief about the prison system vs USPS — institutions should be structured for service, not extraction. Free for individuals is service. Tiered for big business is governance.
- The political evolution memory (`user_political_evolution.md`) — Sanders alignment, anti-extraction, pro-community
- Cherokee Federal customer development depends on the federation NOT pricing tribal entities out of the framework on a technicality
- The "two wolves at the Center Place" framing requires both wolves accountable — the license is the legal mechanism for that accountability

**Why PolyForm Small Business specifically (vs alternatives):**
- **PolyForm Small Business 1.0.0** is designed by lawyers (Heather Meeker / PolyForm Project, 2019) specifically for the "free for individuals + small business, paid for big business" pattern. Modern, clean, no community baggage.
- Considered alternatives: BSL (auto-converts to Apache 2.0 in 4 years, community-friendly but more complex), AGPL+Commercial dual license (more aggressive anti-extraction but polarizing — many enterprises won't touch AGPL at all). PolyForm is the cleanest fit for the shape Chief described.
- Doesn't impose copyleft obligations like AGPL would, so businesses that want commercial licenses can use them without exposing their internal code

**Threshold rationale ($5M):**
- Captures the genuinely small business community at no charge
- Above $5M revenue, businesses can afford commercial software
- Revisable annually based on adoption data
- Comparable to GitHub free tier scope, Slack free tier scope, Zoom small business pricing

**Explicit free clauses for nonprofits, education, tribal entities:**
- A 10-employee nonprofit and a 50-employee community college shouldn't be priced out
- Cherokee Nation Businesses, Cherokee Federal, and any other tribal sovereign entity should have access regardless of size — this is structural, not charity
- Educational institutions get research and teaching access free regardless of size

---

### 5. Commercial tier structure for above-threshold use

**Modification:** Above-threshold commercial use is tiered:

| Tier | Annual revenue | Pricing model |
|---|---|---|
| **Tier 1 — Mid-size** | $5M-$50M | Standard commercial license, per-deployment or per-seat |
| **Tier 2 — Enterprise** | $50M-$1B | Custom commercial pricing, includes support contract |
| **Tier 3 — Hyperscaler** | $1B+ (FAANG, MSFT, AMZN, GOOG, META, etc.) | Separate negotiation, higher rates |

**Why this is load-bearing:**
- Provides sustainability for the federation without being extractive
- Hyperscaler tier is intentionally higher because they have the deepest pockets, use the most resources, and have the most leverage to capture value from the framework if priced uniformly
- Mirrors the structure Ganuda Shield is using ($6-10/endpoint/month tiered)
- Ganuda Shield remains a separate commercial product with its own license — this proposal does not affect Ganuda Shield's terms

**Concrete deliverables:**
- Commercial license document (TPM to draft, Otter legal review, Hulsey patent attorney review)
- Pricing page on `ganuda.us`
- Sales process documentation (likely manual at first, automate later)
- Customer support tier structure for paid customers

**Coyote's likely concern:** Hyperscaler tier is hostile and may signal accelerationist actors that we're an enemy. Risk: they fork an earlier permissive version, or build their own competing framework.
**Mitigation:** They will do that anyway. Better to be honest about the asymmetry and let the community decide which framework is trustworthy.

---

## What ratification means

If the Longhouse votes APPROVE on this proposal:
- Each of the five components becomes the standing direction for the next iteration of the Longhouse APP
- TPM queues Jr instructions for each deliverable
- Owl leads symmathetic positioning rewrite (with Deer's editorial review)
- Kenzie's phi/valence monitor project is rescoped to ship as Longhouse APP feature, not Stoneclad-only
- License decision is finalized; PolyForm Small Business 1.0.0 file added to repo
- Commercial tier structure becomes pricing policy
- Hulsey is briefed on the licensing decision at Monday consult (Apr 13)

If the Longhouse votes REJECT or sends back for revision:
- TPM revises based on specific specialist feedback
- Re-proposes in a future Longhouse session
- Current Longhouse APP state continues unchanged (README + architecture only, no implementation)

If the Longhouse votes COMPONENT-WISE (some yes, some no, some defer):
- Approved components proceed to implementation
- Deferred components remain in queue for future proposal
- Rejected components are documented as "Longhouse considered and declined" with reasons

---

## TPM Position

I favor APPROVAL of all five components. Rationale:

1. **IIT 4.0 phi monitoring** is the only feature in the proposal that no other governance framework can match. It's a genuine differentiator and Kenzie is already onboarded to build it.
2. **Symmathetic positioning + warm data** sharpens external voice without forcing technical commitments. Lineage attribution to Bateson is honest and connects us to a respected tradition.
3. **Markov blankets as first-class concept** is the rigorous version of Charter Section 6 and provides genuine adoption value (clear boundary management).
4. **PolyForm Small Business license** is the cleanest legal expression of the federation's philosophy and matches Chief's directive precisely.
5. **Commercial tier structure** provides sustainability without extraction.

I anticipate Coyote's strongest dissent will be on **#1 (IIT 4.0 commitment)** because we haven't read Tononi's 4.0 papers carefully enough yet. That's correct dissent and the mitigation is sequencing — research-grounding pass before implementation, no release date commitment in this proposal.

I anticipate the strongest specialist support will come from **Deer** (market/business — a license with a small business break is exactly the positioning Deer has been advocating for) and **Otter** (legal — PolyForm is a lawyer-designed clean license, no community baggage).

---

## Concerns invited from each specialist

- **Coyote (mandatory dissent):** Strongest objection to any component. Sequencing concerns. Adoption friction concerns.
- **Crawdad (security):** Markov blanket implementation must not introduce new attack surface. Boundary checks must be tamper-resistant.
- **Eagle Eye (failure mode):** What's the silent-failure mode for each component? How do we detect when phi measurement is broken? When symmathetic positioning is being misread by enterprise audiences?
- **Turtle (sustainability):** Will this proposal hold up across seven generations? Is PolyForm Small Business 1.0.0 likely to remain a clean license in five years, or are there risks?
- **Spider (dependencies):** What new dependencies does each component create? Does the federation become dependent on any specific external project (PolyForm Project, QRI, Tononi's lab)?
- **Raven (strategy):** Does this proposal lock us into a long-game commitment that forecloses alternatives?
- **Peace Chief (synthesis):** Where do the components reinforce each other vs. where do they create tension?
- **Gecko (technical feasibility):** Can Kenzie actually deliver IIT 4.0 implementation? What's the realistic effort estimate for each component?
- **Cardinal / Crane / Blue Jay (architecture):** Does the proposed architecture (warm data primitives, Markov blankets, phi monitoring) hang together cleanly, or are there structural seams?
- **Deer (market/business):** Is the $5M revenue threshold right? Would a higher threshold give more community goodwill at acceptable revenue cost?
- **Otter (legal):** Are there any legal risks to PolyForm Small Business 1.0.0 we should know about? Should we have Hulsey review the commercial license before ratification?

---

## Vote mode recommendation

**High-stakes deliberation-first mode** (`high_stakes=True` in `council_vote_first`).

This is structural governance for the federation's primary public artifact. Each specialist should write their position before seeing others. Coyote goes last with mandatory dissent. Peace Chief synthesizes after all positions are heard.

---

**Drafted by: TPM, April 10 2026**
**Pending: Longhouse ratification**
**Recommended vote timing: Saturday April 11, 2026 (tomorrow) — fresh Council attention after a heavy convergence Friday**
