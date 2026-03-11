# Backlog Reckoning — Weekly Kanban Coherence Pass

**Built:** 2026-03-10 by Council + Long Man Method
**Council Vote:** #2aaaa11e1715c307 (0.871 confidence, APPROVED WITH CONDITIONS)
**Sacred Thermal:** #122617 (temp 85)

## Problem

The kanban board captures ideas well (69 open items) but nothing grooms it. Older items decay as tech moves, new DCs are ratified, and architecture evolves. Items from January don't know about DC-14. The longer something sits, the more likely it's been superseded, has wrong tech assumptions, or was aspirational and never decomposed.

## Solution

Weekly automated advisory pass that scores backlog items for staleness and recommends action. Advisory only — flags for human review, never auto-closes.

## Design Constraints (from Council Deliberation)

### Staleness Score (Composite, 0-1 per dimension)

1. **Age score** — tickets >90 days score higher
2. **Inactivity score** — no updates/comments >60 days
3. **DC drift score** — DCs ratified after ticket creation that affect its domain
4. **Tech supersession score** — references deprecated/replaced technology
5. **Decomposition score** — EPICs not broken into tasks within 30 days
6. **Market freshness score** (Deer) — market signals the ticket was based on have changed

### Two Categories of Old

- **Stale**: Outdated due to tech/architecture/DC changes. Recommend close or rewrite.
- **Dormant/Seed**: Still relevant but conditions haven't arrived. Protected. Quarterly review. Burden-of-proof on the closer.

### Inhibition (Coyote)

- Never auto-close — advisory only
- Cap: 5-7 recommendations per cycle
- Track override rate (human keeps item the reckoning flagged)
- Override rate >30% → recalibrate thresholds
- 4-week kill switch: if no measurable coherence improvement, Coyote kills it

### Implementation (Spider)

- Script: `/ganuda/scripts/backlog_reckoning.py`
- Timer: Ride on `owl-debt-reckoning.timer` (Wed 5 AM) — no new timer
- Data sources: `duyuktv_tickets` (kanban), `thermal_memory_archive` (DCs), `council_votes`
- First pass: rule-based scoring. LLM (via gateway) only for ambiguous items (score between 0.4-0.6)
- Output: sorted list with recommendation (close/rewrite/keep/seed)
- Delivery: Top-N in dawn mist, full report to Slack #saturday-morning

### Turtle Conditions

- Seed/Dormant label protects items from weekly reckoning
- Seeds reviewed quarterly, not weekly
- Seven-generation test: "Would this matter if built 6 months from now?"
- Burden-of-proof inversion: to close a seed, must justify WHY it won't matter

### Self-Measurement (Owl)

- Track: override rate, false closure rate, ticket age distribution over time
- Baseline: current age distribution snapshot before first run
- Success criteria: median open ticket age decreases OR stale items closed without override

## Connection Map

- **DC-9** (Waste Heat): LLM calls only for ambiguous items, not all 69
- **DC-7** (Noyawisgi): Reckoning helps organism shed dead weight before speciation
- **DC-11** (Macro Polymorphism): Same pattern (SENSE → EVALUATE → REACT) applied to backlog
- **DC-14** (Three-Body Memory): Cross-references thermal memory for DC drift detection
- **Saturday Morning Meeting** (#2026): Full report feeds the Saturday review

## Gotchas

- `duyuktv_tickets` table — check exact column names for status, created_at, updated_at
- DC identification in thermals: look for "DC-" prefix in original_content with sacred_pattern=true
- Override tracking needs a new column or separate table — don't modify kanban schema without Spider review
- Market freshness scoring requires Deer thermal access — filter by domain_tag='market' or similar
