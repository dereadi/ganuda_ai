# JR-VETASSIST-SEED-EDUCATIONAL-CONTENT-JAN30-2026
## Seed Educational Content for VetAssist Resources Page

**Priority:** P1 — Resources page is empty, no articles visible to users
**Target Node:** redfin (backend script) → bluefin (database)
**Estimated Scope:** 1 new script, 15-20 articles seeded

### Background

The VetAssist resources page at `https://vetassist.ganuda.us/resources` displays educational articles for veterans navigating VA disability claims. The full stack is wired up:

- **Frontend:** `app/resources/page.tsx` fetches from `/api/v1/content?limit=50`
- **Backend:** `app/api/v1/endpoints/content.py` queries `educational_content` table
- **Database:** `educational_content` table exists on bluefin with correct schema

But the table has **zero rows**. The resources page shows "No articles found."

### Database Schema

Table: `educational_content` on `zammad_production` (bluefin 192.168.132.222)

| Column | Type | Notes |
|--------|------|-------|
| id | serial | PK |
| title | varchar | Article title |
| slug | varchar | URL-friendly slug (unique) |
| content_type | varchar | 'article', 'guide', 'video', 'faq' |
| content | text | Full article body (markdown supported) |
| summary | text | Short summary for card display |
| video_url | varchar | Optional video link |
| difficulty_level | varchar | 'beginner', 'intermediate', 'advanced' |
| estimated_read_time | integer | Minutes |
| tags | text[] | PostgreSQL array of tag strings |
| view_count | integer | Default 0 |
| created_at | timestamp | Auto |
| updated_at | timestamp | Auto |
| is_published | boolean | Must be true to show on resources page |

### Task: Create Seed Script

Create `/ganuda/vetassist/backend/scripts/seed_educational_content.py`

The script should:
1. Connect to `postgresql://claude:jawaseatlasers2@192.168.132.222:5432/zammad_production`
2. Check if content already exists (idempotent — skip if slug exists)
3. Insert 15-20 educational articles covering the topics below
4. All articles must have `is_published = true`

### Required Articles (minimum 15)

#### Beginner Level (5-6 articles)
1. **"Understanding VA Disability Claims"** — Overview of the VA claims process, what disability compensation is, who qualifies. Tags: `claims`, `basics`, `getting-started`. Read time: 8 min.

2. **"How VA Disability Ratings Work"** — The combined rating formula (bilateral factor, rounding), why 50% + 30% doesn't equal 80%. Tags: `ratings`, `calculator`, `basics`. Read time: 6 min.

3. **"Types of VA Disability Claims"** — Original claims, increased rating, secondary conditions, TDIU. Tags: `claims`, `types`, `basics`. Read time: 7 min.

4. **"Evidence You Need for Your VA Claim"** — Service records, medical records, buddy statements, nexus letters. Tags: `evidence`, `documentation`, `basics`. Read time: 10 min.

5. **"The VA Claims Timeline: What to Expect"** — Filing to decision, typical wait times, stages of review. Tags: `timeline`, `process`, `basics`. Read time: 5 min.

6. **"Getting Started with VetAssist"** — How to use the platform: calculator, chat, dashboard, wizard. Tags: `vetassist`, `tutorial`, `getting-started`. Read time: 4 min.

#### Intermediate Level (5-6 articles)
7. **"Understanding PTSD Claims"** — Diagnostic criteria, stressor verification, C&P exam tips. Tags: `ptsd`, `mental-health`, `claims`. Read time: 12 min.

8. **"Secondary Service Connection Explained"** — How one condition can lead to claims for related conditions. Tags: `secondary`, `claims`, `strategy`. Read time: 8 min.

9. **"The C&P Exam: Preparation Guide"** — What happens during Compensation & Pension exams, how to prepare, what to bring. Tags: `c-and-p`, `exam`, `preparation`. Read time: 10 min.

10. **"Buddy Statements That Win Claims"** — How to write effective lay statements, what reviewers look for. Tags: `evidence`, `buddy-statements`, `writing`. Read time: 7 min.

11. **"Understanding Your VA Decision Letter"** — How to read the letter, what the codes mean, next steps. Tags: `decision`, `ratings`, `process`. Read time: 9 min.

12. **"Common Conditions Veterans Claim"** — Tinnitus, back conditions, knee conditions, sleep apnea, migraines. Tags: `conditions`, `common`, `claims`. Read time: 8 min.

#### Advanced Level (4-5 articles)
13. **"Filing a Supplemental Claim"** — When and how to file, new and relevant evidence requirement. Tags: `appeals`, `supplemental`, `advanced`. Read time: 10 min.

14. **"Higher-Level Review vs Board Appeal"** — Comparing appeal lanes, when to use each, timelines. Tags: `appeals`, `strategy`, `advanced`. Read time: 12 min.

15. **"Total Disability Based on Individual Unemployability (TDIU)"** — Eligibility criteria, schedular vs extraschedular, evidence needed. Tags: `tdiu`, `unemployability`, `advanced`. Read time: 11 min.

16. **"The Bilateral Factor in VA Ratings"** — How paired extremity conditions get a bilateral factor boost. Tags: `ratings`, `bilateral`, `calculator`, `advanced`. Read time: 6 min.

17. **"Presumptive Service Connection"** — Agent Orange, burn pits (PACT Act), Gulf War illness. Tags: `presumptive`, `pact-act`, `agent-orange`, `advanced`. Read time: 14 min.

### Content Guidelines

- Write in plain language. Target audience is veterans, not lawyers.
- Use markdown formatting in the `content` field (headers, lists, bold).
- Each article should have a clear summary (1-2 sentences) for the card display.
- Include practical advice, not just definitions.
- Add a disclaimer at the bottom of each article: *"This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation."*

### Article Content Template

Each article should follow this structure in the `content` field:
```markdown
## [Title]

[Opening paragraph — why this matters to the veteran]

### Key Points

- Point 1
- Point 2
- Point 3

### [Main sections with details]

[Body content with practical guidance]

### What to Do Next

[Actionable steps the veteran can take]

---

*This is educational information only, not legal advice. Consult a VA-accredited representative for guidance specific to your situation.*
```

### Running the Script

```bash
cd /ganuda/vetassist/backend
./venv/bin/python scripts/seed_educational_content.py
```

### Verification

After seeding:
```bash
# Check count
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT COUNT(*) FROM educational_content WHERE is_published = true;"
# Should return 15+

# Check the API
curl -s http://localhost:8001/api/v1/content?limit=5 | python3 -m json.tool | head -20

# Check the page
# Navigate to https://vetassist.ganuda.us/resources — should show article cards
```

### Files to Create

| File | Purpose |
|------|---------|
| `scripts/seed_educational_content.py` | Seed script with 15-20 articles |

### Why This Matters

The resources page is the first thing veterans see when exploring VetAssist. An empty page signals an incomplete product. These articles establish trust and demonstrate expertise. They also feed the RAG system for AI chat responses.
