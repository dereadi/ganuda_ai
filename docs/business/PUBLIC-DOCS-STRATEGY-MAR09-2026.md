# Cherokee AI Federation — Public Documentation Strategy

**Date:** March 9, 2026
**Task:** #1198
**Status:** Draft

## Information Classification Map

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

## Documentation Inventory

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

## Tooling Recommendation

**Option A: MkDocs + Material theme**
- Pros: Python-native (matches our stack), fast builds, excellent search, Material theme is polished, versioning via mike, Markdown-native
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

**Recommendation:**
We recommend **MkDocs + Material theme**. It aligns well with our Python-centric stack, provides a modern and polished look, and supports versioning and Markdown natively. The fast build times and excellent search capabilities make it a strong choice for our needs.

## Content Calendar

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

## Contribution Guidelines

**Who can contribute:**
- Anyone for PUBLIC docs via pull request. AUDITABLE docs require team review. INTERNAL and SACRED docs are team-only.

**Style guide:**
- Active voice
- Short sentences
- Code examples for every concept
- No jargon without definition
- Jimmy the Tulip tone — competent, not showy

**Review process:**
- All doc PRs reviewed by at least one team member
- Classification changes (e.g., moving something from INTERNAL to AUDITABLE) require council vote

**Templates:**
- Provide a doc template with standard sections (Overview, Prerequisites, Steps, Examples, Troubleshooting, Related)

**Tagging:**
- Every document must have a classification header: `classification: PUBLIC|AUDITABLE`

## Quality Standards

- Every guide must have a "Prerequisites" section
- Every API endpoint must have a request/response example
- Every configuration option must have a default value and description
- Code examples must be tested (runnable, not pseudocode)
- No broken links (CI check)
- No INTERNAL or SACRED content in PUBLIC or AUDITABLE docs (CI check with grep)
- Reading level: accessible to a mid-level engineer who has not seen the system before
- Maximum page length: 15 pages (split longer docs into sub-pages)