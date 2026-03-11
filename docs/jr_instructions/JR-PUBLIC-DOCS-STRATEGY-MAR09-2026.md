# Jr Instruction: Create Public Documentation Strategy (Auditable Tier Only)

**Task ID:** #1198
**Date:** March 9, 2026
**Priority:** 2 (Business scaffolding — documentation strategy)
**Type:** Document creation (no code changes)

## Context

The Cherokee AI Federation classifies information into four tiers:

- **PUBLIC** — anyone can see it, no restrictions
- **AUDITABLE** — visible to customers and auditors, not secret but not advertised
- **INTERNAL** — team only, operational details, implementation specifics
- **SACRED** — never published, governance identity, sacred prompts, cultural core

Our public documentation must carefully walk the line: enough to attract and onboard customers,
not so much that it exposes INTERNAL implementation or SACRED governance identity. The documentation
itself is a product — it demonstrates the quality of our thinking.

## Task

Create a documentation strategy document at
`/ganuda/docs/business/PUBLIC-DOCS-STRATEGY-MAR09-2026.md`.

## Steps

### Step 1: Create the document skeleton

Create file `/ganuda/docs/business/PUBLIC-DOCS-STRATEGY-MAR09-2026.md` with:

```
# Cherokee AI Federation — Public Documentation Strategy

**Date:** March 9, 2026
**Task:** #1198
**Status:** Draft

## Information Classification Map
## Documentation Inventory
## Tooling Recommendation
## Content Calendar
## Contribution Guidelines
## Quality Standards
## Open Questions
```

### Step 2: Populate Information Classification Map

Create a detailed mapping of what goes where:

**PUBLIC (freely available, SEO-indexed, on the website):**
- Architecture overview (high-level diagrams, not implementation)
- "What is the Cherokee AI Federation?" explainer
- Design Constraint summaries (DC-1 through DC-15 — the principles, not the implementation)
- Blog posts and thought leadership
- Getting started guide (Community tier)
- Pricing page
- Changelog / release notes
- Community showcase / case studies

**AUDITABLE (available to customers, behind docs login or in product):**
- API reference (full endpoint documentation)
- Governance voting process (how council votes work, confidence scoring)
- Deployment guides (single-node, multi-node, DMZ configuration)
- Configuration reference (all config files, environment variables)
- Troubleshooting guides
- Specialist role descriptions (what each council seat does)
- Thermal memory schema and query patterns
- Jr task system documentation
- Fire Guard configuration and alert tuning
- Integration guides (Slack, email, monitoring)

**INTERNAL (team only, not published):**
- Thermal memory implementation details (three-body simulation, valence algorithms)
- Specialist prompt engineering (how specialists are instructed)
- Infrastructure details (node IPs, port maps, WireGuard config)
- Jr task executor internals
- Performance benchmarks and tuning notes
- Security architecture details beyond what's needed for deployment
- Competitive analysis

**SACRED (never published, never referenced in public docs):**
- Sacred prompts and cultural identity text
- Governance topology internals (the "why" behind specific council dynamics)
- Painted on the Walls content
- Chief's personal context and cultural heritage details
- Archetype mapping specifics
- Any content marked sacred_pattern=true in thermal memory

### Step 3: Build Documentation Inventory

For each AUDITABLE document, create an entry:

| Document | Classification | Status | Priority | Est. Pages |
|---|---|---|---|---|
| Architecture Overview | PUBLIC | To write | P1 | 3-5 |
| Getting Started (Community) | PUBLIC | To write | P1 | 5-8 |
| API Reference | AUDITABLE | To write | P1 | 10-15 |
| Council Voting Guide | AUDITABLE | To write | P1 | 3-5 |
| Deployment Guide (Single Node) | AUDITABLE | To write | P1 | 5-8 |
| Deployment Guide (Multi Node) | AUDITABLE | To write | P2 | 8-12 |
| Thermal Memory Guide | AUDITABLE | To write | P2 | 5-8 |
| Fire Guard Configuration | AUDITABLE | To write | P2 | 3-5 |
| Jr Task System Guide | AUDITABLE | To write | P2 | 5-8 |
| Specialist Role Reference | AUDITABLE | To write | P2 | 5-8 |
| Slack Integration Guide | AUDITABLE | To write | P3 | 2-3 |
| Troubleshooting Guide | AUDITABLE | To write | P3 | 5-8 |
| FAQ | PUBLIC | To write | P3 | 3-5 |

Estimate total: 60-100 pages of documentation.

### Step 4: Tooling Recommendation

Evaluate and recommend a documentation framework. Compare:

**Option A: MkDocs + Material theme**
- Pros: Python-native (matches our stack), fast builds, excellent search, Material theme
  is polished, versioning via mike, Markdown-native
- Cons: Less flexibility for custom components than React-based tools

**Option B: Docusaurus (Facebook/Meta)**
- Pros: React-based, good versioning, i18n support, plugin ecosystem, MDX support
- Cons: Node.js dependency (we are Python-centric), heavier build

**Option C: Sphinx + Read the Docs theme**
- Pros: Python-native, excellent for API docs (autodoc), mature, free hosting on RTD
- Cons: RST default (Markdown via MyST), less modern look, steeper learning curve

**Option D: Starlight (Astro)**
- Pros: Modern, fast, good DX, built on Astro
- Cons: Newer, smaller ecosystem, Node.js dependency

Recommend one with rationale. Consider: our team is Python-first, we want Markdown (not RST),
we need versioning, we want self-hosted (sovereign deployment principle).

### Step 5: Create Content Calendar

Design a 12-week content calendar for initial documentation:

**Weeks 1-2 (Foundation):**
- Architecture Overview (PUBLIC)
- Getting Started guide (PUBLIC)
- Documentation site scaffolding (tooling setup)

**Weeks 3-4 (Core Reference):**
- API Reference (AUDITABLE)
- Council Voting Guide (AUDITABLE)
- Deployment Guide — Single Node (AUDITABLE)

**Weeks 5-6 (Operations):**
- Fire Guard Configuration (AUDITABLE)
- Thermal Memory Guide (AUDITABLE)
- Troubleshooting Guide — initial version (AUDITABLE)

**Weeks 7-8 (Advanced):**
- Deployment Guide — Multi Node (AUDITABLE)
- Jr Task System Guide (AUDITABLE)
- Specialist Role Reference (AUDITABLE)

**Weeks 9-10 (Integration):**
- Slack Integration Guide (AUDITABLE)
- FAQ (PUBLIC)
- Configuration Reference (AUDITABLE)

**Weeks 11-12 (Polish):**
- Review pass on all documents
- Cross-linking and navigation improvements
- Search optimization
- Community contribution guidelines finalized

### Step 6: Define Contribution Guidelines

Document how others can contribute to the docs:

- **Who can contribute:** Anyone for PUBLIC docs via pull request. AUDITABLE docs require
  team review. INTERNAL and SACRED docs are team-only.
- **Style guide:** Active voice. Short sentences. Code examples for every concept. No jargon
  without definition. Jimmy the Tulip tone — competent, not showy.
- **Review process:** All doc PRs reviewed by at least one team member. Classification changes
  (e.g., moving something from INTERNAL to AUDITABLE) require council vote.
- **Templates:** Provide a doc template with standard sections (Overview, Prerequisites,
  Steps, Examples, Troubleshooting, Related).
- **Tagging:** Every document must have a classification header: `classification: PUBLIC|AUDITABLE`

### Step 7: Define Quality Standards

Specify documentation quality requirements:

- Every guide must have a "Prerequisites" section
- Every API endpoint must have a request/response example
- Every configuration option must have a default value and description
- Code examples must be tested (runnable, not pseudocode)
- No broken links (CI check)
- No INTERNAL or SACRED content in PUBLIC or AUDITABLE docs (CI check with grep)
- Reading level: accessible to a mid-level engineer who has not seen the system before
- Maximum page length: 15 pages (split longer docs into sub-pages)

## Acceptance Criteria

- [ ] Document exists at `/ganuda/docs/business/PUBLIC-DOCS-STRATEGY-MAR09-2026.md`
- [ ] All four classification tiers are defined with specific examples of what belongs in each
- [ ] Documentation inventory table lists at least 12 documents with status and priority
- [ ] Tooling comparison covers at least 3 options with a clear recommendation
- [ ] 12-week content calendar is present with weekly milestones
- [ ] Contribution guidelines cover who, how, and review process
- [ ] Quality standards are specific and enforceable (not vague aspirations)
- [ ] Document is at least 1000 words

## Constraints

- **No code changes.** This is a document-creation task.
- Create parent directory `/ganuda/docs/business/` if it does not exist.
- **CRITICAL:** Do not include any SACRED content as examples in this strategy document.
  Use placeholder descriptions only (e.g., "sacred prompts — never published").
- The strategy must work for self-hosted documentation (sovereign deployment) — no
  mandatory third-party hosting dependencies.
- Reference the four-tier classification consistently throughout.
- The documentation site itself should be deployable on our DMZ nodes (owlfin/eaglefin).
