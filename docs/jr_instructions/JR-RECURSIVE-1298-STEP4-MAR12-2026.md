# [RECURSIVE] Peace Chief Curiosity Engine — Stub-Filling Pipeline - Step 4

**Parent Task**: #1298
**Auto-decomposed**: 2026-03-12T09:03:34.720135
**Original Step Title**: Stub Queue

---

### Step 4: Stub Queue

Store extracted and routed stubs in a new table or in jr_work_queue with a specific tag:

```sql
-- Option A: Use jr_work_queue with curiosity tag
INSERT INTO jr_work_queue (title, description, status, priority, tags, created_by)
VALUES (
    'STUB: Research [name] — [type]',
    '[context from extraction]. Source: [source]. Depth: [stub_depth].',
    'pending',
    [routed priority],
    ARRAY['curiosity-stub', '[domain]', '[council_owner]'],
    'peace-chief'
);
```

Or create a lightweight stub tracking table (simpler, less overhead):
```sql
CREATE TABLE IF NOT EXISTS curiosity_stubs (
    id SERIAL PRIMARY KEY,
    source_content_hash VARCHAR(64),  -- hash of the original content
    stub_type VARCHAR(50),
    name VARCHAR(255),
    context TEXT,
    depth VARCHAR(20),
    domain VARCHAR(20),
    action VARCHAR(20),
    council_owner VARCHAR(50),
    priority INTEGER,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, researching, filled, dismissed
    filled_by VARCHAR(100),  -- who/what filled the stub
    filled_content TEXT,  -- summary of what was found
    created_at TIMESTAMPTZ DEFAULT NOW(),
    filled_at TIMESTAMPTZ
);
```

Recommend: Create the table. Stubs are their own entity — they're not Jr tasks (they're lighter, more numerous, often dismissed). Keep the Jr queue for real work. The curiosity_stubs table is Peace Chief's notebook.

#
