# Ultrathink: VetAssist Resources Page — Content Strategy, KB Publishing Pipeline & External Links

**Date:** January 31, 2026
**Author:** TPM (Claude Opus 4.5)
**Council Vote:** 7c7a479ecd840c46 (84.3% confidence, 5 concerns, consensus: EXPAND + REORGANIZE)
**Status:** PENDING COUNCIL RATIFICATION

---

## Executive Summary

Transform the VetAssist resources page from a flat grid of 18 articles into a topic-organized knowledge base with editorial governance, curated external links to authoritative sources, and automated content freshness monitoring. This addresses the Council's unanimous recommendation to expand content and reorganize by topic while adding Darrell's requirements for KB-grade authorship, review workflows, and link reliability.

---

## Current State

### What We Have
- 18 rows in `educational_content` (17 real articles + 1 test stub "Gap 2 Verification Test")
- 6 beginner, 6 intermediate, 5 advanced articles covering: claims basics, ratings, PTSD, secondary conditions, C&P prep, buddy statements, decision letters, common conditions, appeals, TDIU, bilateral factor, PACT Act
- Flat grid display with difficulty filter and tag filter
- Article detail page (`/resources/[slug]`) with markdown rendering and related articles
- Backend API: list, search, get-by-slug, tag-list endpoints
- Tags stored as JSON strings in `text` column (fixed Jan 31 to parse in `to_dict()`)

### What's Missing
- **No content governance**: No author, reviewer, version tracking, or publishing workflow
- **No external links**: No references to VA.gov, eBenefits, VSO sites
- **No topic sections**: Flat grid doesn't guide the veteran's journey
- **No freshness monitoring**: No mechanism to flag stale content
- **Articles are thin**: Most are 200-400 words — should be 800-1500 for credibility and RAG quality
- **Test stub**: "Gap 2 Verification Test" still in the table

### Council Direction
All 7 specialists agreed on:
1. Expand content — focus on quality, not quantity
2. Reorganize into topic-based sections
3. Missing topics: VA.gov navigation, VA forms, medical records, women veterans, mental health resources, legal assistance
4. Crawdad: fact-check everything; Turtle: respect cultural sovereignty; Gecko: load test RAG after expansion; Peace Chief: get veteran feedback

### Darrell's Direction
- Treat articles as KB articles with author, publishing process, reviewers
- Add curated external links to VA.gov and reputable sites
- Split links by stability (VA.gov = stable, VSO sites = dynamic)
- Monitor links weekly/daily based on stability category
- Automate the review process using the Council

---

## Architecture

### Phase 1: Schema Migration — KB Publishing Fields + External Links Table

#### 1A. Migrate `educational_content` table

Add columns to support KB-grade publishing workflow:

```sql
-- KB Publishing Pipeline fields
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS author VARCHAR(100) DEFAULT 'Ganuda AI';
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS reviewer VARCHAR(100);
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS review_notes TEXT;
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS review_audit_hash VARCHAR(32);
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS content_version INTEGER DEFAULT 1;
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'published';
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS section VARCHAR(50);
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS section_order INTEGER DEFAULT 0;
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS source_references TEXT;
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS last_accuracy_check TIMESTAMPTZ;
ALTER TABLE educational_content ADD COLUMN IF NOT EXISTS needs_update BOOLEAN DEFAULT FALSE;

-- Index for section-based queries
CREATE INDEX IF NOT EXISTS idx_content_section ON educational_content(section, section_order);
CREATE INDEX IF NOT EXISTS idx_content_status ON educational_content(status);
```

**Status values:** `draft` → `in_review` → `approved` → `published` → `needs_update` → `archived`

The existing `is_published` boolean remains for backward compatibility. The `status` field is the canonical source of truth going forward. `is_published = (status == 'published')`.

**Review pipeline:**
1. Jr writes article → status = `draft`
2. Council reviews (via `/v1/council/vote` with content-review prompt) → status = `in_review`
3. Council approves (confidence > 0.7, no Crawdad SECURITY CONCERN) → status = `approved`, `review_audit_hash` = council vote hash
4. TPM signs off → status = `published`, `is_published = true`
5. Freshness daemon flags → status = `needs_update`, `needs_update = true`

#### 1B. Create `vetassist_resource_links` table

```sql
CREATE TABLE IF NOT EXISTS vetassist_resource_links (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    description TEXT,
    section VARCHAR(50) NOT NULL,
    link_category VARCHAR(20) NOT NULL DEFAULT 'stable',
    source_org VARCHAR(100),
    last_checked TIMESTAMPTZ,
    last_status INTEGER,
    last_redirect_url TEXT,
    check_frequency VARCHAR(20) DEFAULT 'weekly',
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resource_links_section ON vetassist_resource_links(section, display_order);
CREATE INDEX IF NOT EXISTS idx_resource_links_category ON vetassist_resource_links(link_category);
CREATE INDEX IF NOT EXISTS idx_resource_links_check ON vetassist_resource_links(check_frequency, last_checked);
```

**link_category values:**
- `stable` — VA.gov official pages, eCFR. Check weekly. These URLs rarely change.
- `dynamic` — VSO sites (DAV, VFW, American Legion), eBenefits, benefits calculators. Check daily.
- `seasonal` — VA compensation rate tables. Check in December (annual update).

#### 1C. Remove test stub

```sql
DELETE FROM educational_content WHERE slug = 'gap2-verify-test-v2';
```

### Phase 2: Beef Up Existing 17 Articles

Each article needs to be expanded from ~200-400 words to ~800-1500 words. The content should:
- Add practical examples and specific scenarios
- Reference relevant 38 CFR sections (stored in `source_references`)
- Include "Official Resources" links at the bottom of each article
- Follow the standard KB article template (see below)
- Add proper metadata: author, section assignment, section_order

**KB Article Template:**
```markdown
## [Title]

[Opening — why this matters to the veteran, 2-3 sentences]

### What You Need to Know

[Core information, organized with subheadings]

### Step-by-Step Guide (if applicable)

[Numbered actionable steps]

### Common Questions

[2-3 FAQ items relevant to this topic]

### Official VA Resources

- [VA.gov: Relevant Page](https://va.gov/...)
- [eCFR: Relevant Section](https://ecfr.gov/...)

### What to Do Next

[Actionable next steps, link to VetAssist tools]

---

*Last updated: [date]. This is educational information only, not legal advice.
Consult a VA-accredited representative for guidance specific to your situation.*
```

**Section assignments for existing articles:**

| Section | Articles | section_order |
|---------|----------|---------------|
| getting-started | Understanding VA Disability Claims, Getting Started with VetAssist, The VA Claims Timeline, Types of VA Disability Claims | 1-4 |
| building-your-claim | Evidence You Need, How VA Disability Ratings Work, Understanding PTSD Claims, Secondary Service Connection, Common Conditions Veterans Claim, Buddy Statements That Win Claims, The C&P Exam: Preparation Guide | 1-7 |
| understanding-your-rating | How VA Disability Ratings Work (also here), Understanding Your VA Decision Letter, The Bilateral Factor | 1-3 |
| appeals-and-next-steps | Filing a Supplemental Claim, Higher-Level Review vs Board Appeal, TDIU | 1-3 |
| special-topics | Presumptive Service Connection and the PACT Act | 1 |

Note: Some articles may appear in multiple sections conceptually, but each gets ONE primary section assignment.

### Phase 3: Seed Curated External Links

**Stable Links (VA.gov — check weekly):**

| Title | URL | Section |
|-------|-----|---------|
| VA Disability Compensation | https://www.va.gov/disability/ | getting-started |
| How to File a VA Disability Claim | https://www.va.gov/disability/how-to-file-claim/ | getting-started |
| VA Disability Ratings | https://www.va.gov/disability/about-disability-ratings/ | understanding-your-rating |
| Decision Reviews and Appeals | https://www.va.gov/decision-reviews/ | appeals-and-next-steps |
| Supplemental Claims | https://www.va.gov/decision-reviews/supplemental-claim/ | appeals-and-next-steps |
| Higher-Level Review | https://www.va.gov/decision-reviews/higher-level-review/ | appeals-and-next-steps |
| Board of Veterans' Appeals | https://www.va.gov/decision-reviews/board-appeal/ | appeals-and-next-steps |
| PACT Act Information | https://www.va.gov/resources/the-pact-act-and-your-va-benefits/ | special-topics |
| VA Combined Ratings Calculator | https://www.va.gov/disability/about-disability-ratings/rating-calculator/ | understanding-your-rating |
| Check Your Claim Status | https://www.va.gov/claim-or-appeal-status/ | getting-started |
| VA Health Care | https://www.va.gov/health-care/ | special-topics |
| eCFR Title 38 Part 4 | https://www.ecfr.gov/current/title-38/chapter-I/part-4 | building-your-claim |
| VA Forms Library | https://www.va.gov/find-forms/ | building-your-claim |

**Dynamic Links (VSO/Tools — check daily):**

| Title | URL | Section | Source Org |
|-------|-----|---------|-----------|
| DAV (Disabled American Veterans) | https://www.dav.org/veterans/i-need-help/ | getting-started | DAV |
| VFW Veterans Assistance | https://www.vfw.org/assistance | getting-started | VFW |
| American Legion Claims Help | https://www.legion.org/veteransbenefits | getting-started | American Legion |
| National Veterans Legal Services Program | https://www.nvlsp.org/ | appeals-and-next-steps | NVLSP |
| Veterans Crisis Line | https://www.veteranscrisisline.net/ | special-topics | VA |

**Seasonal Links (check in December):**

| Title | URL | Section |
|-------|-----|---------|
| VA Disability Compensation Rates | https://www.va.gov/disability/compensation-rates/ | understanding-your-rating |

### Phase 4: Frontend Reorganization — Topic-Based Sections

Transform the flat grid into topic-based sections with external links integrated per section.

**New page structure:**

```
/resources
├── Hero header (unchanged)
├── Search bar (searches articles AND link titles)
├── Difficulty filter (unchanged, filters articles only)
├── Section: "Getting Started" ──────────────────────
│   ├── Article cards (grid)
│   └── "Official Resources" sidebar/footer (external links for this section)
├── Section: "Building Your Claim" ──────────────────
│   ├── Article cards (grid)
│   └── "Official Resources" sidebar/footer
├── Section: "Understanding Your Rating" ────────────
│   ├── Article cards (grid)
│   └── "Official Resources" sidebar/footer
├── Section: "Appeals & Next Steps" ─────────────────
│   ├── Article cards (grid)
│   └── "Official Resources" sidebar/footer
├── Section: "Special Topics" ───────────────────────
│   ├── Article cards (grid)
│   └── "Official Resources" sidebar/footer
└── Disclaimer footer (unchanged)
```

**Backend changes needed:**
- New endpoint: `GET /api/v1/content/sections` — returns articles grouped by section with section metadata
- New endpoint: `GET /api/v1/resource-links` — returns external links optionally filtered by section
- Modify `to_dict()` to include new KB fields (author, status, section, updated_at display)

**Frontend changes needed:**
- `page.tsx` — Render sections instead of flat grid; each section is a collapsible/expandable block
- Add external links component per section (styled differently from article cards — lighter, with external link icon)
- Article detail page — Add "Official VA Resources" section at bottom, sourced from links matching the article's section

### Phase 5: Link Monitoring Daemon

**Script:** `/ganuda/vetassist/backend/scripts/link_monitor.py`

Simple HTTP HEAD checker:
1. Query `vetassist_resource_links WHERE is_active = true`
2. Group by `check_frequency`
3. For each link due for check: HTTP HEAD request with 10s timeout
4. Update `last_checked`, `last_status`, `last_redirect_url`
5. If status >= 400 or timeout: set `is_active = false`, send Telegram alert
6. If redirect detected: log `last_redirect_url`, send Telegram notice

**Scheduling:**
- Run via cron: `*/15 * * * *` (every 15 minutes)
- Each run only checks links where `last_checked` is older than their `check_frequency`
- Daily links: checked if `last_checked > 24 hours ago`
- Weekly links: checked if `last_checked > 7 days ago`
- Seasonal links: checked if `last_checked > 30 days ago` OR if current month == December

**Alerting:**
- Telegram alert to Darrell if any link returns 404/500/timeout
- Weekly summary of all link statuses

### Phase 6: Council Content Review Automation (Future)

**Not implemented in this sprint, but architected for:**

When a Jr writes a new article (status = `draft`), the publishing pipeline:
1. Extract factual claims from the article (LLM extraction)
2. Cross-reference claims against 38 CFR RAG pipeline (once JR-VETASSIST-38CFR-RAG-BM25 is deployed)
3. Submit article text to Council for review via `/v1/council/vote` with prompt: "Review this educational article for accuracy, completeness, cultural sensitivity, and security concerns"
4. If Council confidence > 0.7 and no SECURITY CONCERN from Crawdad → auto-approve
5. If concerns raised → status stays `in_review`, TPM notified

This depends on the 38 CFR RAG pipeline being operational. For now, articles are manually reviewed by TPM.

---

## Section Definitions

| Section ID | Display Name | Description | Target Audience |
|------------|-------------|-------------|-----------------|
| getting-started | Getting Started | Basics for veterans new to the claims process | First-time filers |
| building-your-claim | Building Your Claim | Evidence, conditions, and preparation guidance | Active claimants |
| understanding-your-rating | Understanding Your Rating | Rating math, decision letters, bilateral factor | Veterans with existing ratings |
| appeals-and-next-steps | Appeals & Next Steps | Supplemental claims, HLR, Board, TDIU | Veterans with denials or low ratings |
| special-topics | Special Topics | PACT Act, presumptive conditions, specific populations | All veterans |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Article inaccuracy (wrong 38 CFR citation) | Medium | High — veteran acts on wrong info | Council review + 38 CFR RAG cross-reference |
| External link rot (404s) | Low for VA.gov, Medium for VSOs | Medium — broken trust signal | Link monitor daemon + Telegram alerts |
| RAG quality degradation from expanded content | Low | Medium — AI chat gives worse answers | Profile RAG queries before/after expansion |
| Schema migration breaks existing API consumers | Low | High — page goes down again | Additive-only migration, backward-compatible `is_published` |
| Jr fails on multi-step SEARCH/REPLACE (again) | High | Medium — delays deployment | Split into single-file focused instructions |

---

## Implementation Order

```
Phase 1A: Schema migration (SQL only, no code dependencies)        → Infra Jr
Phase 1B: External links table + seed links                        → Infra Jr
Phase 1C: Remove test stub                                         → Infra Jr (same task)
Phase 2:  Beef up 17 articles + assign sections                    → SWE Jr (content writing)
Phase 3:  Backend API changes (sections endpoint, links endpoint)  → SWE Jr
Phase 4:  Frontend reorganization                                  → SWE Jr
Phase 5:  Link monitor daemon + cron                               → Infra Jr
Phase 6:  Council review automation                                → FUTURE (depends on 38 CFR RAG)
```

Phases 1A/1B/1C can run in parallel.
Phase 2 depends on 1A (needs `section` column).
Phase 3 depends on 1A + 1B (needs both tables).
Phase 4 depends on 3 (needs new API endpoints).
Phase 5 depends on 1B (needs links table).

---

## Success Criteria

1. Test stub removed from `educational_content`
2. All 17 articles have: author, section, content_version, status='published', expanded content (800+ words each)
3. 19+ curated external links seeded with correct categories and check frequencies
4. Frontend renders topic-based sections with integrated external links
5. Link monitor runs on cron and sends Telegram alert on broken links
6. `updated_at` visible on article detail pages
7. Backend API backward-compatible (existing `GET /content` still works)

---

## Security Notes (Crawdad)

- External links are outbound only — no inbound data from external sites
- Link monitor uses HTTP HEAD only — minimal data exposure
- No PII in any article content
- `review_audit_hash` provides chain of custody from Council vote to published article
- `source_references` contains 38 CFR section numbers, not copyrighted text
- All VA.gov links use HTTPS

---

## Seven Generations Assessment (Turtle)

- Educational content empowers veterans for decades, not just one claim cycle
- KB publishing pipeline ensures content accuracy is maintained across team changes
- External links to VA.gov ground the platform in authoritative sources
- Section-based organization scales as new topics (women veterans, Native American veterans, burn pit registry) are added
- Content versioning enables historical audit — we can always see what was published when

---

## Council Vote Reference

**Audit Hash:** 7c7a479ecd840c46
**Confidence:** 84.3%
**Consensus:** "Expand beyond 18 articles focusing on high-quality, accurate content, prioritizing key missing topics like detailed explanations of complex processes and conditions. Reorganize into topic-based sections to cater to veterans' varying levels of knowledge."
**Concerns:** Gecko (PERF), Raven (STRATEGY), Crawdad (SECURITY), Peace Chief (CONSENSUS), Turtle (7GEN)
**All addressed in this document.**
