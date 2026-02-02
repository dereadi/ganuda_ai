# JR Instruction: VetAssist Resources Schema Migration & External Links Table

**Task ID:** VETASSIST-RESOURCES-SCHEMA-001
**Date:** January 31, 2026
**Priority:** P1
**Type:** infrastructure
**Assigned To:** Infrastructure Jr.
**Depends On:** None

---

## Objective

Evolve the `educational_content` table to support KB-quality publishing fields, create a new `vetassist_resource_links` table for curated external links with health-check metadata, remove a leftover test stub, and seed 19 curated external resource links that veterans need.

This is Phase 1 of the Resources page data layer. Phase 2 (API endpoints) and Phase 3 (frontend) depend on these tables being correct.

---

## Prerequisites

- Access to bluefin database: `host=192.168.132.222`, `db=zammad_production`, `user=claude`, `password=jawaseatlasers2`
- Python 3 with `psycopg2` installed (use the vetassist backend venv: `/ganuda/vetassist/backend/venv/bin/python`)
- `psql` CLI does **not** have the password configured on this host; use `psycopg2` for all database operations

---

## Steps

### Step 1: Add KB publishing fields to educational_content table

Connect via psycopg2 and execute the following ALTER statements. These add author/reviewer tracking, content versioning, section ordering, and accuracy-check metadata.

```python
import psycopg2

conn = psycopg2.connect(
    host="192.168.132.222",
    dbname="zammad_production",
    user="claude",
    password="jawaseatlasers2"
)
conn.autocommit = True
cur = conn.cursor()

migration_sql = """
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
CREATE INDEX IF NOT EXISTS idx_content_section ON educational_content(section, section_order);
CREATE INDEX IF NOT EXISTS idx_content_status ON educational_content(status);
"""

for statement in migration_sql.strip().split(";"):
    statement = statement.strip()
    if statement:
        cur.execute(statement + ";")
        print(f"OK: {statement[:60]}...")

cur.close()
conn.close()
print("Step 1 complete: educational_content columns added.")
```

**What this adds:**

| Column | Type | Purpose |
|--------|------|---------|
| author | VARCHAR(100) | Who wrote the article (default: 'Ganuda AI') |
| reviewer | VARCHAR(100) | Who reviewed for accuracy |
| reviewed_at | TIMESTAMPTZ | When it was reviewed |
| review_notes | TEXT | Reviewer comments |
| review_audit_hash | VARCHAR(32) | Audit trail hash for review event |
| content_version | INTEGER | Version counter (default: 1) |
| status | VARCHAR(20) | 'published', 'draft', 'archived' (default: 'published') |
| section | VARCHAR(50) | Section grouping for Resources page |
| section_order | INTEGER | Display order within section (default: 0) |
| source_references | TEXT | CFR/source citations backing the content |
| last_accuracy_check | TIMESTAMPTZ | When content was last verified for accuracy |
| needs_update | BOOLEAN | Flag for stale content needing refresh |

---

### Step 2: Create vetassist_resource_links table

This table stores curated external links to VA.gov, VSO organizations, and reference resources. It includes health-check fields so a future daemon can verify links haven't gone stale or started redirecting.

```python
import psycopg2

conn = psycopg2.connect(
    host="192.168.132.222",
    dbname="zammad_production",
    user="claude",
    password="jawaseatlasers2"
)
conn.autocommit = True
cur = conn.cursor()

create_sql = """
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
"""

for statement in create_sql.strip().split(";"):
    statement = statement.strip()
    if statement:
        cur.execute(statement + ";")
        print(f"OK: {statement[:60]}...")

cur.close()
conn.close()
print("Step 2 complete: vetassist_resource_links table created.")
```

**Table schema:**

| Column | Type | Purpose |
|--------|------|---------|
| id | SERIAL PK | Auto-increment primary key |
| title | VARCHAR(300) | Display title of the link |
| url | TEXT UNIQUE | Full URL (unique constraint prevents duplicates) |
| description | TEXT | Short description for display |
| section | VARCHAR(50) | Which Resources page section it belongs to |
| link_category | VARCHAR(20) | 'stable', 'dynamic', 'seasonal' — drives check frequency |
| source_org | VARCHAR(100) | Organization that owns the resource (VA, DAV, etc.) |
| last_checked | TIMESTAMPTZ | When the link was last health-checked |
| last_status | INTEGER | HTTP status code from last check |
| last_redirect_url | TEXT | If the link redirected, where to |
| check_frequency | VARCHAR(20) | 'daily', 'weekly', 'monthly', 'seasonal' |
| is_active | BOOLEAN | Soft-delete flag |
| display_order | INTEGER | Controls ordering within section |
| created_at | TIMESTAMPTZ | Row creation timestamp |
| updated_at | TIMESTAMPTZ | Last modification timestamp |

---

### Step 3: Remove test stub from educational_content

Delete the leftover test row that was inserted during integration testing.

```python
import psycopg2

conn = psycopg2.connect(
    host="192.168.132.222",
    dbname="zammad_production",
    user="claude",
    password="jawaseatlasers2"
)
conn.autocommit = True
cur = conn.cursor()

cur.execute("DELETE FROM educational_content WHERE slug = 'gap2-verify-test-v2';")
print(f"Deleted {cur.rowcount} test stub row(s).")

cur.close()
conn.close()
print("Step 3 complete: test stub removed.")
```

If the row does not exist (rowcount = 0), that is fine. This step is idempotent.

---

### Step 4: Seed curated external links

Insert 19 curated external resource links across four sections. Uses `ON CONFLICT (url) DO NOTHING` for idempotency.

```python
import psycopg2

conn = psycopg2.connect(
    host="192.168.132.222",
    dbname="zammad_production",
    user="claude",
    password="jawaseatlasers2"
)
conn.autocommit = True
cur = conn.cursor()

# -- Stable links (check weekly) --
stable_links = [
    ("VA Disability Compensation", "https://www.va.gov/disability/", "Official VA disability compensation overview and eligibility information.", "getting-started", "VA", 1),
    ("How to File a VA Disability Claim", "https://www.va.gov/disability/how-to-file-claim/", "Step-by-step instructions for filing your initial disability claim.", "getting-started", "VA", 2),
    ("Check Your Claim Status", "https://www.va.gov/claim-or-appeal-status/", "Track the current status of your pending VA claim or appeal.", "getting-started", "VA", 3),
    ("VA Disability Ratings", "https://www.va.gov/disability/about-disability-ratings/", "How VA assigns disability ratings and what they mean for your benefits.", "understanding-your-rating", "VA", 1),
    ("VA Combined Ratings Calculator", "https://www.va.gov/disability/about-disability-ratings/rating-calculator/", "Official VA tool to estimate your combined disability rating.", "understanding-your-rating", "VA", 2),
    ("eCFR Title 38 Part 4", "https://www.ecfr.gov/current/title-38/chapter-I/part-4", "Schedule for Rating Disabilities — the regulatory basis for all VA ratings.", "building-your-claim", "GPO", 1),
    ("VA Forms Library", "https://www.va.gov/find-forms/", "Search and download all VA forms including claim and appeal forms.", "building-your-claim", "VA", 2),
    ("Decision Reviews and Appeals", "https://www.va.gov/decision-reviews/", "Overview of your options after receiving a VA decision.", "appeals-and-next-steps", "VA", 1),
    ("Supplemental Claims", "https://www.va.gov/decision-reviews/supplemental-claim/", "How to file a Supplemental Claim with new and relevant evidence.", "appeals-and-next-steps", "VA", 2),
    ("Higher-Level Review", "https://www.va.gov/decision-reviews/higher-level-review/", "Request a senior reviewer to re-examine your claim decision.", "appeals-and-next-steps", "VA", 3),
    ("Board of Veterans' Appeals", "https://www.va.gov/decision-reviews/board-appeal/", "Appeal your decision to the Board of Veterans' Appeals.", "appeals-and-next-steps", "VA", 4),
    ("PACT Act Information", "https://www.va.gov/resources/the-pact-act-and-your-va-benefits/", "How the PACT Act expands benefits for toxic exposure veterans.", "special-topics", "VA", 1),
    ("VA Health Care", "https://www.va.gov/health-care/", "Enroll in and manage your VA health care benefits.", "special-topics", "VA", 2),
]

for title, url, description, section, source_org, display_order in stable_links:
    cur.execute("""
        INSERT INTO vetassist_resource_links (title, url, description, section, link_category, source_org, check_frequency, display_order)
        VALUES (%s, %s, %s, %s, 'stable', %s, 'weekly', %s)
        ON CONFLICT (url) DO NOTHING;
    """, (title, url, description, section, source_org, display_order))

print(f"Inserted stable links.")

# -- Dynamic links (check daily) --
dynamic_links = [
    ("DAV Veterans Help", "https://www.dav.org/veterans/i-need-help/", "Disabled American Veterans — free claims assistance and advocacy.", "getting-started", "DAV", 4),
    ("VFW Veterans Assistance", "https://www.vfw.org/assistance", "Veterans of Foreign Wars — benefits assistance and service officer support.", "getting-started", "VFW", 5),
    ("American Legion Claims Help", "https://www.legion.org/veteransbenefits", "American Legion — free accredited claims representatives.", "getting-started", "American Legion", 6),
    ("National Veterans Legal Services Program", "https://www.nvlsp.org/", "Free legal services for veterans navigating appeals and complex claims.", "appeals-and-next-steps", "NVLSP", 5),
    ("Veterans Crisis Line", "https://www.veteranscrisisline.net/", "24/7 crisis support for veterans — call 988 then press 1.", "special-topics", "VA", 3),
]

for title, url, description, section, source_org, display_order in dynamic_links:
    cur.execute("""
        INSERT INTO vetassist_resource_links (title, url, description, section, link_category, source_org, check_frequency, display_order)
        VALUES (%s, %s, %s, %s, 'dynamic', %s, 'daily', %s)
        ON CONFLICT (url) DO NOTHING;
    """, (title, url, description, section, source_org, display_order))

print(f"Inserted dynamic links.")

# -- Seasonal link (check monthly, but really matters in December for rate changes) --
cur.execute("""
    INSERT INTO vetassist_resource_links (title, url, description, section, link_category, source_org, check_frequency, display_order)
    VALUES (%s, %s, %s, %s, 'seasonal', %s, 'monthly', %s)
    ON CONFLICT (url) DO NOTHING;
""", (
    "VA Disability Compensation Rates",
    "https://www.va.gov/disability/compensation-rates/",
    "Current VA disability compensation rate tables — updated annually in December.",
    "understanding-your-rating",
    "VA",
    3
))

print(f"Inserted seasonal link.")

cur.close()
conn.close()
print("Step 4 complete: 19 curated resource links seeded.")
```

**Link summary by section:**

| Section | Count | Links |
|---------|-------|-------|
| getting-started | 6 | VA Disability Compensation, How to File, Check Status, DAV, VFW, American Legion |
| understanding-your-rating | 3 | VA Disability Ratings, Combined Ratings Calculator, Compensation Rates |
| building-your-claim | 2 | eCFR Title 38 Part 4, VA Forms Library |
| appeals-and-next-steps | 5 | Decision Reviews, Supplemental Claims, Higher-Level Review, Board of Appeals, NVLSP |
| special-topics | 3 | PACT Act, VA Health Care, Veterans Crisis Line |

**Link category check schedule:**

| Category | Frequency | Count | Rationale |
|----------|-----------|-------|-----------|
| stable | weekly | 13 | VA.gov pages rarely change URLs |
| dynamic | daily | 5 | VSO/nonprofit sites restructure more often |
| seasonal | monthly | 1 | Compensation rates update once per year in December |

---

### Step 5: Verify

Run these verification queries to confirm everything is correct.

```python
import psycopg2

conn = psycopg2.connect(
    host="192.168.132.222",
    dbname="zammad_production",
    user="claude",
    password="jawaseatlasers2"
)
cur = conn.cursor()

# 1. Verify educational_content new columns exist
cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'educational_content'
    AND column_name IN ('author', 'reviewer', 'reviewed_at', 'review_notes',
                        'review_audit_hash', 'content_version', 'status',
                        'section', 'section_order', 'source_references',
                        'last_accuracy_check', 'needs_update')
    ORDER BY column_name;
""")
new_cols = [row[0] for row in cur.fetchall()]
print(f"New columns in educational_content: {len(new_cols)}/12")
assert len(new_cols) == 12, f"FAIL: Expected 12 new columns, found {len(new_cols)}: {new_cols}"
print(f"  Columns: {new_cols}")

# 2. Verify educational_content row count (test stub removed)
cur.execute("SELECT COUNT(*) FROM educational_content;")
ec_count = cur.fetchone()[0]
print(f"educational_content rows: {ec_count}")
assert ec_count == 17, f"FAIL: Expected 17 rows, found {ec_count}"

# 3. Verify test stub is gone
cur.execute("SELECT COUNT(*) FROM educational_content WHERE slug = 'gap2-verify-test-v2';")
stub_count = cur.fetchone()[0]
assert stub_count == 0, f"FAIL: Test stub still exists"
print("Test stub removed: confirmed.")

# 4. Verify vetassist_resource_links table exists and has correct count
cur.execute("SELECT COUNT(*) FROM vetassist_resource_links;")
rl_count = cur.fetchone()[0]
print(f"vetassist_resource_links rows: {rl_count}")
assert rl_count == 19, f"FAIL: Expected 19 rows, found {rl_count}"

# 5. Verify section distribution
cur.execute("""
    SELECT section, COUNT(*) FROM vetassist_resource_links
    GROUP BY section ORDER BY section;
""")
for section, count in cur.fetchall():
    print(f"  {section}: {count} links")

# 6. Verify category distribution
cur.execute("""
    SELECT link_category, check_frequency, COUNT(*) FROM vetassist_resource_links
    GROUP BY link_category, check_frequency ORDER BY link_category;
""")
for cat, freq, count in cur.fetchall():
    print(f"  {cat} ({freq}): {count} links")

# 7. Verify indexes exist
cur.execute("""
    SELECT indexname FROM pg_indexes
    WHERE tablename IN ('educational_content', 'vetassist_resource_links')
    AND indexname IN ('idx_content_section', 'idx_content_status',
                      'idx_resource_links_section', 'idx_resource_links_category',
                      'idx_resource_links_check')
    ORDER BY indexname;
""")
indexes = [row[0] for row in cur.fetchall()]
print(f"Indexes found: {len(indexes)}/5")
assert len(indexes) == 5, f"FAIL: Expected 5 indexes, found {len(indexes)}: {indexes}"
for idx in indexes:
    print(f"  {idx}")

cur.close()
conn.close()
print("\n=== ALL VERIFICATIONS PASSED ===")
```

**Expected verification output:**

```
New columns in educational_content: 12/12
  Columns: [author, content_version, last_accuracy_check, needs_update, review_audit_hash, review_notes, reviewed_at, reviewer, section, section_order, source_references, status]
educational_content rows: 17
Test stub removed: confirmed.
vetassist_resource_links rows: 19
  appeals-and-next-steps: 5 links
  building-your-claim: 2 links
  getting-started: 6 links
  special-topics: 3 links
  understanding-your-rating: 3 links
  dynamic (daily): 5 links
  seasonal (monthly): 1 links
  stable (weekly): 13 links
Indexes found: 5/5
  idx_content_section
  idx_content_status
  idx_resource_links_category
  idx_resource_links_check
  idx_resource_links_section

=== ALL VERIFICATIONS PASSED ===
```

---

## Success Criteria

- [ ] 12 new columns added to `educational_content` table
- [ ] `vetassist_resource_links` table created with correct schema and UNIQUE constraint on url
- [ ] 5 indexes created (2 on educational_content, 3 on vetassist_resource_links)
- [ ] Test stub row `gap2-verify-test-v2` deleted from educational_content
- [ ] `educational_content` has exactly 17 rows
- [ ] `vetassist_resource_links` has exactly 19 rows
- [ ] All verification assertions pass

---

## Security Notes

- Database credentials are in this instruction for Infrastructure Jr execution only. Do NOT commit credentials to any source file, config, or log.
- The `psql` CLI does not have password configured on this host. Use `psycopg2` connections for all operations.
- All INSERT operations use `ON CONFLICT ... DO NOTHING` for idempotency. This task is safe to re-run.
- No application restart required. These are schema-only changes; the API endpoints (Phase 2) will be wired separately.

---

## Rollback

If this migration needs to be reversed:

```sql
-- Remove new columns from educational_content (only the ones added by this migration)
ALTER TABLE educational_content DROP COLUMN IF EXISTS author;
ALTER TABLE educational_content DROP COLUMN IF EXISTS reviewer;
ALTER TABLE educational_content DROP COLUMN IF EXISTS reviewed_at;
ALTER TABLE educational_content DROP COLUMN IF EXISTS review_notes;
ALTER TABLE educational_content DROP COLUMN IF EXISTS review_audit_hash;
ALTER TABLE educational_content DROP COLUMN IF EXISTS content_version;
ALTER TABLE educational_content DROP COLUMN IF EXISTS status;
ALTER TABLE educational_content DROP COLUMN IF EXISTS section;
ALTER TABLE educational_content DROP COLUMN IF EXISTS section_order;
ALTER TABLE educational_content DROP COLUMN IF EXISTS source_references;
ALTER TABLE educational_content DROP COLUMN IF EXISTS last_accuracy_check;
ALTER TABLE educational_content DROP COLUMN IF EXISTS needs_update;

-- Drop indexes
DROP INDEX IF EXISTS idx_content_section;
DROP INDEX IF EXISTS idx_content_status;

-- Drop the resource links table entirely
DROP TABLE IF EXISTS vetassist_resource_links;
```

Note: The test stub delete (Step 3) is not reversible via rollback. That row is gone and should not be re-inserted.

---

## Context

- **Database:** `zammad_production` on bluefin (192.168.132.222)
- **Backend:** runs on redfin (192.168.132.223:8001), entry at `app/main.py`
- **Existing schema reference:** `JR-VETASSIST-SEED-EDUCATIONAL-CONTENT-JAN30-2026.md` documents the original `educational_content` columns
- **Phase 2 (next):** API endpoints for resource links at `/api/v1/resources/links`
- **Phase 3 (after):** Frontend Resources page integration with external links section

---

*Cherokee AI Federation -- For Seven Generations*
