# Jr Instruction: Create legal_register Table — Otter Foundation

**Task**: Create the legal_register table on bluefin for Otter (legal/regulatory outer council member)
**Priority**: 3
**Story Points**: 2
**Epic**: #1981

## Context

Otter needs a structured table to track legal/regulatory items: patents, compliance gaps, licenses, regulatory filings. This is the Otter equivalent of what duyuktv_tickets is for the inner council.

Database: bluefin (192.168.132.222), db=zammad_production, user=claude.

## Steps

### Step 1: Create migration script

Create `/ganuda/scripts/migrations/legal_register_schema.sql`

```text
-- Otter Legal Register — foundation table for legal/regulatory tracking
-- Ratified: Outer Council Regency Charter (Longhouse sessions 53457e87, 106cb142, 433b02d8)

CREATE TABLE IF NOT EXISTS legal_register (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,  -- patent, compliance, license, contract, regulatory, ip
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'open',  -- open, in_review, approved, filed, closed, blocked
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    assignee VARCHAR(100),  -- council member or human
    due_date DATE,
    jurisdiction VARCHAR(100),  -- US, state, tribal, international
    reference_url TEXT,
    kanban_id INTEGER REFERENCES duyuktv_tickets(id),  -- optional link to kanban
    thermal_id INTEGER,  -- optional link to thermal memory
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_legal_register_category ON legal_register(category);
CREATE INDEX IF NOT EXISTS idx_legal_register_status ON legal_register(status);

-- Seed with known items
INSERT INTO legal_register (category, title, description, status, priority, jurisdiction)
VALUES
    ('patent', 'SRE+C Governance Protocol — Novel Claims', 'Five novel patent claims identified vs IBM MAPE-K prior art. Governance (not control), retrospective valence, multi-scale protocol polymorphism, Cherokee scaffolding, Coyote circuit breaker.', 'open', 2, 'US'),
    ('ip', 'Open Source License Selection — Exportable Governance', 'Council Protocol as open framework. Need license that protects Cherokee cultural IP while enabling adoption.', 'open', 4, 'US'),
    ('compliance', 'VetAssist HIPAA Compliance Gaps', 'PII vault deployed but full HIPAA audit pending. Need BAA with hosting providers.', 'open', 3, 'US'),
    ('ip', 'Patent Inquiry — Meredith Lowry / WLJ', 'Initial patent inquiry sent. Tracking response.', 'in_review', 2, 'US')
ON CONFLICT DO NOTHING;
```

### Step 2: Create Python runner for the migration

Create `/ganuda/scripts/migrations/run_legal_register.py`

```python
#!/usr/bin/env python3
"""Run legal_register schema migration."""

import os
import re
import psycopg2

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

if not DB_PASS:
    try:
        with open("/ganuda/config/secrets.env") as f:
            for line in f:
                m = re.match(r"^(\w+)=(.+)$", line.strip())
                if m:
                    os.environ[m.group(1)] = m.group(2)
        DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
    except FileNotFoundError:
        pass

sql_path = os.path.join(os.path.dirname(__file__), "legal_register_schema.sql")
with open(sql_path) as f:
    sql = f.read()

conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
cur = conn.cursor()
cur.execute(sql)
conn.commit()

cur.execute("SELECT COUNT(*) FROM legal_register")
count = cur.fetchone()[0]
print(f"legal_register created with {count} seed items")

cur.close()
conn.close()
```

## Verification

1. Run: `cd /ganuda && python3 scripts/migrations/run_legal_register.py`
2. Output should show "legal_register created with 4 seed items"
3. Verify: `python3 -c "import psycopg2; c=psycopg2.connect(host='192.168.132.222',port=5432,dbname='zammad_production',user='claude',password=os.environ['CHEROKEE_DB_PASS']); cur=c.cursor(); cur.execute('SELECT category, title FROM legal_register'); [print(r) for r in cur.fetchall()]"`
