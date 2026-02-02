# Jr Instruction: Expand Educational Articles to Full-Length KB Content

**Task ID:** VETASSIST-ARTICLES-EXPAND-001
**Assigned To:** Software Engineer Jr.
**Priority:** P1 — Articles are live but thin; veterans need substantive guidance
**Created:** January 31, 2026
**Depends On:** VETASSIST-RESOURCES-SCHEMA-001 (section, section_order, content_version, author, source_references, status columns must exist on educational_content table)
**Estimated Steps:** 5

---

## Objective

Expand all 17 existing educational articles from their current stub length (~200-400 words each) to full-length knowledge base articles (~800-1500 words each). Assign each article to a topical section, set display ordering, and populate metadata fields including source references to 38 CFR regulatory citations. This is Phase 2 of the resources content buildout.

---

## Background

Phase 1 (VETASSIST-SEED-EDUCATIONAL-CONTENT) seeded 17 articles with short placeholder content so the resources page would not be empty. Those stubs are now live at `https://vetassist.ganuda.us/resources`. Phase 2 replaces each stub with substantive, veteran-friendly educational content that follows a consistent KB template, organized into browsable sections.

The `educational_content` table on bluefin (192.168.132.222) was extended by VETASSIST-RESOURCES-SCHEMA-001 with the following columns that Phase 1 did not populate:

| Column | Type | Purpose |
|--------|------|---------|
| section | varchar | Topic grouping (e.g., 'getting-started') |
| section_order | integer | Display order within section |
| content_version | integer | Tracks content revisions (Phase 1 = 1) |
| author | varchar | Content author attribution |
| source_references | text | Regulatory citations (38 CFR sections) |
| status | varchar | 'draft' or 'published' |

---

## Section Assignments

All 17 articles must be assigned to one of five sections. The `section` and `section_order` values are as follows:

### Section: `getting-started`

| Order | Slug | Title |
|-------|------|-------|
| 1 | understanding-va-disability-claims | Understanding VA Disability Claims |
| 2 | getting-started-with-vetassist | Getting Started with VetAssist |
| 3 | va-claims-timeline | The VA Claims Timeline: What to Expect |
| 4 | types-of-va-disability-claims | Types of VA Disability Claims |

### Section: `building-your-claim`

| Order | Slug | Title |
|-------|------|-------|
| 1 | evidence-you-need-for-va-claim | Evidence You Need for Your VA Claim |
| 2 | understanding-ptsd-claims | Understanding PTSD Claims |
| 3 | secondary-service-connection-explained | Secondary Service Connection Explained |
| 4 | common-conditions-veterans-claim | Common Conditions Veterans Claim |
| 5 | buddy-statements-that-win-claims | Buddy Statements That Win Claims |
| 6 | cp-exam-preparation-guide | The C&P Exam: Preparation Guide |

### Section: `understanding-your-rating`

| Order | Slug | Title |
|-------|------|-------|
| 1 | how-va-disability-ratings-work | How VA Disability Ratings Work |
| 2 | understanding-va-decision-letter | Understanding Your VA Decision Letter |
| 3 | bilateral-factor-va-ratings | The Bilateral Factor in VA Ratings |

### Section: `appeals-and-next-steps`

| Order | Slug | Title |
|-------|------|-------|
| 1 | filing-supplemental-claim | Filing a Supplemental Claim |
| 2 | higher-level-review-vs-board-appeal | Higher-Level Review vs Board Appeal |
| 3 | tdiu-total-disability-unemployability | Total Disability Based on Individual Unemployability (TDIU) |

### Section: `special-topics`

| Order | Slug | Title |
|-------|------|-------|
| 1 | presumptive-service-connection-pact-act | Presumptive Service Connection |

---

## Source References by Article

Each article must have the `source_references` field populated with the relevant 38 CFR citations. Use these mappings:

| Slug | source_references |
|------|-------------------|
| understanding-va-disability-claims | 38 CFR Part 3 Subpart A, 38 USC Chapter 11 |
| getting-started-with-vetassist | N/A (platform guide) |
| va-claims-timeline | 38 CFR 3.103, 38 CFR 3.156, 38 CFR 19.5 |
| types-of-va-disability-claims | 38 CFR 3.4, 38 CFR 3.310, 38 CFR 4.16 |
| evidence-you-need-for-va-claim | 38 CFR 3.159, 38 CFR 3.303 |
| understanding-ptsd-claims | 38 CFR 4.130, DC 9411, 38 CFR 3.304(f) |
| secondary-service-connection-explained | 38 CFR 3.310 |
| common-conditions-veterans-claim | 38 CFR Part 4 (Schedule for Rating Disabilities) |
| buddy-statements-that-win-claims | 38 CFR 3.159(a)(2), 38 CFR 3.303(a) |
| cp-exam-preparation-guide | 38 CFR 3.159(c)(4), 38 CFR 3.326 |
| how-va-disability-ratings-work | 38 CFR 4.25, 38 CFR 4.26 |
| understanding-va-decision-letter | 38 CFR 3.103(b), 38 CFR 19.29 |
| bilateral-factor-va-ratings | 38 CFR 4.26 |
| filing-supplemental-claim | 38 CFR 3.2501, 38 CFR 3.156(d) |
| higher-level-review-vs-board-appeal | 38 CFR 3.2601, 38 CFR 20.200 |
| tdiu-total-disability-unemployability | 38 CFR 4.16 |
| presumptive-service-connection-pact-act | 38 CFR 3.307, 38 CFR 3.309, PACT Act (PL 117-168) |

---

## KB Article Template

Every expanded article MUST follow this template structure in the `content` field. Content is markdown.

```markdown
## [Title]

[Opening -- why this matters to the veteran. 2-3 sentences that establish relevance and set expectations for what the article covers.]

### What You Need to Know

[Core information broken into logical subheadings. This is the meat of the article. Use plain language. Define acronyms on first use. Target 400-600 words in this section alone.]

#### [Subtopic A]
[Details]

#### [Subtopic B]
[Details]

### Step-by-Step Guide

[Numbered steps if the topic lends itself to a process. Not every article needs this section -- omit for purely informational topics like "How Ratings Work" and replace with a relevant alternative section heading.]

1. **Step name** -- Description
2. **Step name** -- Description
3. **Step name** -- Description

### Common Questions

**Q: [Frequent question]?**
A: [Clear, concise answer.]

**Q: [Frequent question]?**
A: [Clear, concise answer.]

**Q: [Frequent question]?**
A: [Clear, concise answer.]

### Official VA Resources

- [VA.gov: Disability Compensation](https://www.va.gov/disability/)
- [VA.gov: How to File a Claim](https://www.va.gov/disability/how-to-file-claim/)
- [Additional relevant links]

### What to Do Next

[2-3 actionable steps. Point the veteran toward VetAssist tools where relevant: the calculator, the claims wizard, the AI chat, the evidence checklist.]

---

*Last updated: January 31, 2026. This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*
```

### Content Guidelines

- Write in plain language. The audience is veterans, not attorneys.
- Define acronyms on first use: "Compensation & Pension (C&P) exam"
- Use markdown formatting: headers, bold, numbered lists, bullet points.
- Each article must be between **800 and 1500 words** in the `content` field.
- Include practical, actionable advice -- not just definitions.
- Do NOT fabricate statistics or cite specific case outcomes.
- Every article must end with the disclaimer shown in the template.

---

## Steps

### Step 1: Create the expansion script

**File to create:** `/ganuda/vetassist/backend/scripts/expand_articles.py`

The script must:

1. Connect to PostgreSQL at `postgresql://claude:jawaseatlasers2@192.168.132.222:5432/zammad_production`
2. Define all 17 articles as a list of dictionaries, each containing:
   - `slug` (used as the WHERE clause identifier)
   - `content` (the full expanded article, 800-1500 words, following the KB template above)
   - `section` (from the Section Assignments table above)
   - `section_order` (from the Section Assignments table above)
   - `source_references` (from the Source References table above)
   - `author` set to `'Ganuda AI'`
   - `status` set to `'published'`
3. For each article, execute an UPDATE statement:

```sql
UPDATE educational_content
SET content = %s,
    section = %s,
    section_order = %s,
    author = %s,
    content_version = 2,
    status = %s,
    source_references = %s,
    updated_at = NOW()
WHERE slug = %s
  AND (content_version IS NULL OR content_version <= 1);
```

4. The `WHERE content_version <= 1` clause makes the script **idempotent**. If an article has already been expanded to version 2, the UPDATE will match zero rows and skip it.
5. After all updates, print a summary: how many articles were updated, how many were skipped (already at version 2), and the word count for each updated article.
6. Commit the transaction only after all 17 updates succeed. If any fail, rollback and report the error.

**Important:** Use `psycopg2` for the database connection. It is already installed in the backend venv.

### Step 2: Run the expansion script

```bash
cd /ganuda/vetassist/backend
./venv/bin/python scripts/expand_articles.py
```

The script should print output like:
```
Expanding 17 educational articles...
  [1/17] understanding-va-disability-claims: UPDATED (1,127 words)
  [2/17] getting-started-with-vetassist: UPDATED (943 words)
  ...
  [17/17] presumptive-service-connection-pact-act: UPDATED (1,401 words)

Summary: 17 updated, 0 skipped
All articles expanded to content_version 2.
```

### Step 3: Verify word counts

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT slug,
       section,
       section_order,
       content_version,
       author,
       LENGTH(content) as content_chars,
       array_length(string_to_array(content, ' '), 1) as approx_word_count,
       source_references IS NOT NULL as has_refs
FROM educational_content
ORDER BY section, section_order;
"
```

Every row must show:
- `content_version` = 2
- `approx_word_count` >= 800
- `has_refs` = true (except `getting-started-with-vetassist` which may have `N/A`)
- `section` is not null
- `section_order` is not null

### Step 4: Verify the API returns expanded content

```bash
# Check that section field comes through the API
curl -s http://192.168.132.223:8001/api/v1/content?limit=3 | python3 -m json.tool | head -40

# Check a specific article has full content
curl -s "http://192.168.132.223:8001/api/v1/content?limit=50" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('items', data.get('articles', []))
for a in items:
    words = len(a.get('content', '').split())
    section = a.get('section', 'MISSING')
    print(f\"{a['slug']:50s}  section={section:25s}  words={words}\")
"
```

### Step 5: Verify the resources page renders

```bash
# Smoke test the live page
curl -s https://vetassist.ganuda.us/resources | grep -c 'article\|Article'
```

Navigate to `https://vetassist.ganuda.us/resources` in a browser and confirm:
- Articles display with longer content previews
- Section groupings appear (if frontend supports section rendering)
- No rendering errors or blank cards

---

## Success Criteria

All of the following must be true:

- [ ] All 17 articles in `educational_content` have `content_version = 2`
- [ ] All 17 articles have word count >= 800 in the `content` field
- [ ] All 17 articles have a non-null `section` value matching the assignments above
- [ ] All 17 articles have a non-null `section_order` value matching the assignments above
- [ ] All 17 articles have `author = 'Ganuda AI'`
- [ ] All 17 articles have `status = 'published'`
- [ ] 16 of 17 articles have non-empty `source_references` (the VetAssist platform guide may have 'N/A')
- [ ] Every article content follows the KB template structure (opening, What You Need to Know, Common Questions, Official VA Resources, What to Do Next, disclaimer)
- [ ] The API at `/api/v1/content` returns the expanded content
- [ ] The expansion script is idempotent -- running it a second time updates 0 articles
- [ ] Script file exists at `/ganuda/vetassist/backend/scripts/expand_articles.py`

---

## Security Notes

- Database credentials are used only within the backend scripts directory on redfin. Do not log credentials in output.
- No new endpoints are created. This task only updates existing database rows.
- No PII is involved. All content is public educational material.
- The script uses parameterized queries (`%s` placeholders) to prevent SQL injection.
- The `content_version` guard prevents accidental double-expansion.

---

## Files

| File | Action | Purpose |
|------|--------|---------|
| `/ganuda/vetassist/backend/scripts/expand_articles.py` | CREATE | Python script that expands all 17 articles |

---

## Rollback

If the expanded content causes issues, revert to version 1:

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
UPDATE educational_content SET content_version = 1 WHERE content_version = 2;
"
```

Note: This only resets the version flag. The original short content is not preserved by this script. If a full rollback is needed, re-run the Phase 1 seed script (`scripts/seed_educational_content.py`) which is idempotent on slug.

---

*Cherokee AI Federation -- For Seven Generations*
