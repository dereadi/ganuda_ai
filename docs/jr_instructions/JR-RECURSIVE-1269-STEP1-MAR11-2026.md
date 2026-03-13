# [RECURSIVE] Chain Protocol: Associate/Temp Ring Registry + Dispatch Library - Step 1

**Parent Task**: #1269
**Auto-decomposed**: 2026-03-11T10:01:35.410204
**Original Step Title**: Extend duplo_tool_registry schema

---

### Step 1: Extend duplo_tool_registry schema

File: `/ganuda/scripts/migrations/chain_protocol_schema.sql`

```sql
-- Chain Protocol: Ring Registry Extension
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS ring_type VARCHAR(20) DEFAULT 'associate' CHECK (ring_type IN ('associate', 'temp'));
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS provider VARCHAR(100);
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS canonical_schema JSONB;
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS removal_procedure TEXT;
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS calibration_schedule VARCHAR(50);
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS cost_budget_daily NUMERIC(10,4);
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS ring_status VARCHAR(20) DEFAULT 'active' CHECK (ring_status IN ('active', 'quarantine', 'revoked'));
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS schema_version INTEGER DEFAULT 1;
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS last_calibration TIMESTAMP;
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS drift_score NUMERIC(5,4);

-- Ring health tracking
CREATE TABLE IF NOT EXISTS ring_health (
    id SERIAL PRIMARY KEY,
    ring_id INTEGER REFERENCES duplo_tool_registry(id),
    checked_at TIMESTAMP DEFAULT NOW(),
    calls_today INTEGER DEFAULT 0,
    errors_today INTEGER DEFAULT 0,
    avg_latency_ms NUMERIC(10,2),
    cost_today NUMERIC(10,4),
    status VARCHAR(20) DEFAULT 'healthy'
);

-- Scrub rules for outbound screening
CREATE TABLE IF NOT EXISTS scrub_rules (
    id SERIAL PRIMARY KEY,
    rule_type VARCHAR(20) NOT NULL CHECK (rule_type IN ('blocked_term', 'regex', 'field_scrub', 'image_check')),
    pattern TEXT NOT NULL,
    applies_to VARCHAR(50) DEFAULT 'all',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Seed scrub_rules from existing blocked terms
INSERT INTO scrub_rules (rule_type, pattern, applies_to) VALUES
('blocked_term', 'thermal_memory', 'all'),
('blocked_term', 'council_votes', 'all'),
('blocked_term', 'duyuktv', 'all'),
('blocked_term', 'jr_work_queue', 'all'),
('blocked_term', 'bluefin', 'all'),
('blocked_term', 'redfin', 'all'),
('blocked_term', 'greenfin', 'all'),
('blocked_term', 'owlfin', 'all'),
('blocked_term', 'eaglefin', 'all'),
('blocked_term', 'bmasass', 'all'),
('blocked_term', 'sacred_fire', 'all'),
('blocked_term', 'nftables', 'all'),
('blocked_term', '192.168', 'all'),
('blocked_term', '10.100.0', 'all'),
('blocked_term', 'zammad_production', 'all'),
('blocked_term', 'FreeIPA', 'all'),
('blocked_term', 'silverfin', 'all'),
('blocked_term', 'WireGuard', 'all'),
('blocked_term', 'cherokee_venv', 'all'),
('blocked_term', 'jr_executor', 'all'),
('blocked_term', 'SEARCH/REPLACE', 'all')
ON CONFLICT DO NOTHING;
```
