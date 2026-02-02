# JR Instruction: Fix Research Database Mismatch

**JR ID:** JR-FIX-RESEARCH-DATABASE-MISMATCH-JAN28-2026
**Priority:** P0 (Blocking Production)
**Assigned To:** Database Jr.
**Related:** KB-VETASSIST-II-RESEARCHER-INTEGRATION-JAN28-2026

---

## Problem

Research results are being inserted into `zammad_production` database but VetAssist dashboard queries `triad_federation` database. This causes Marcus (and all real users) to see no research history.

**Evidence:**
```sql
-- Research results exist in zammad_production:
zammad_production=# SELECT * FROM vetassist_research_results;
-- Returns: test-veteran-001 | research-78d4d52cfc30 | ...

-- But table doesn't exist in triad_federation:
triad_federation=# SELECT * FROM vetassist_research_results;
-- ERROR: relation "vetassist_research_results" does not exist
```

**Root Cause:**
- `/ganuda/services/research_file_watcher.py` line 38: hardcoded `'database': 'zammad_production'`
- `/ganuda/vetassist/backend/.env`: `DATABASE_URL=...triad_federation`

---

## Solution

### Step 1: Create table in triad_federation

```sql
-- Connect to triad_federation
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d triad_federation

-- Create the research results table
CREATE TABLE IF NOT EXISTS vetassist_research_results (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100),
    job_id VARCHAR(64) UNIQUE,
    question TEXT,
    answer TEXT,
    sources JSONB DEFAULT '[]',
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_research_veteran ON vetassist_research_results(veteran_id);
CREATE INDEX IF NOT EXISTS idx_research_created ON vetassist_research_results(created_at DESC);
```

### Step 2: Update research_file_watcher.py

Edit `/ganuda/services/research_file_watcher.py` line 38:

**BEFORE:**
```python
DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}
```

**AFTER:**
```python
DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': 'triad_federation',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}
```

### Step 3: Restart service

```bash
sudo systemctl restart research-file-watcher
sudo systemctl status research-file-watcher
```

### Step 4: Migrate existing test data (optional)

```sql
-- If you want to migrate the test record:
INSERT INTO triad_federation.vetassist_research_results
SELECT * FROM zammad_production.vetassist_research_results;
```

---

## Validation

1. Check table exists in triad_federation:
```bash
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d triad_federation \
  -c "SELECT COUNT(*) FROM vetassist_research_results;"
```

2. Trigger a test research request as a real user (Marcus)
3. Wait for completion (check `/ganuda/research/completed/`)
4. Verify dashboard shows research history

---

## VetAssist User ID Note

The `vetassist_users` table uses `id` as the primary key, not a separate `veteran_id`. Research requests should use the user's `id` from `vetassist_users` as the `veteran_id` field.

---

FOR SEVEN GENERATIONS
