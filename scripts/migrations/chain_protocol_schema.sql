-- Chain Protocol: Ring Registry Extension
-- Jr Tasks #1269 + #1273
-- Extends duplo_tool_registry with ring governance columns
-- Creates ring_health and scrub_rules tables

-- Step 1: Extend duplo_tool_registry schema
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
    ring_id INTEGER REFERENCES duplo_tool_registry(tool_id),
    checked_at TIMESTAMP DEFAULT NOW(),
    calls_today INTEGER DEFAULT 0,
    errors_today INTEGER DEFAULT 0,
    avg_latency_ms NUMERIC(10,2),
    cost_today NUMERIC(10,4),
    status VARCHAR(20) DEFAULT 'healthy'
);

CREATE INDEX IF NOT EXISTS idx_ring_health_ring_date ON ring_health (ring_id, checked_at);

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

-- Seed Associate rings (permanent)
INSERT INTO duplo_tool_registry (tool_name, description, module_path, function_name, parameters, safety_class, ring_type, provider, ring_status, canonical_schema)
VALUES
('claude_opus', 'Claude Opus — strategic frontier model', 'lib/chain_protocol.py', 'dispatch', '{}', 'read', 'associate', 'anthropic', 'active', '{"input": "text", "output": "text", "tier": "strategic"}'),
('claude_sonnet', 'Claude Sonnet — content generation model', 'lib/chain_protocol.py', 'dispatch', '{}', 'read', 'associate', 'anthropic', 'active', '{"input": "text", "output": "text", "tier": "content"}'),
('claude_haiku', 'Claude Haiku — fast screening model', 'lib/chain_protocol.py', 'dispatch', '{}', 'read', 'associate', 'anthropic', 'active', '{"input": "text", "output": "text", "tier": "screening"}'),
('qwen_72b', 'Qwen 72B — local reasoning model on redfin', 'lib/chain_protocol.py', 'dispatch', '{}', 'read', 'associate', 'local_redfin', 'active', '{"input": "text", "output": "text", "tier": "reasoning"}'),
('qwen_vl_7b', 'Qwen VL 7B — local vision model on bluefin', 'lib/chain_protocol.py', 'dispatch', '{}', 'read', 'associate', 'local_bluefin', 'active', '{"input": "image+text", "output": "text", "tier": "vision"}'),
('qwen3_30b', 'Qwen3 30B — fast reasoning on bmasass', 'lib/chain_protocol.py', 'dispatch', '{}', 'read', 'associate', 'local_bmasass', 'active', '{"input": "text", "output": "text", "tier": "fast_reasoning"}'),
('llama_70b', 'Llama 70B — direct reasoning on bmasass', 'lib/chain_protocol.py', 'dispatch', '{}', 'read', 'associate', 'local_bmasass', 'active', '{"input": "text", "output": "text", "tier": "direct_reasoning"}'),
('bge_large', 'BGE Large — embedding model on greenfin', 'lib/chain_protocol.py', 'dispatch', '{}', 'read', 'associate', 'local_greenfin', 'active', '{"input": "text", "output": "vector_1024", "tier": "embedding"}')
ON CONFLICT (tool_name) DO NOTHING;

-- YouTube ring (Seasonal Temp — read-only, public data)
INSERT INTO duplo_tool_registry (tool_name, description, module_path, function_name, parameters, safety_class, ring_type, provider, ring_status, canonical_schema, removal_procedure, calibration_schedule, cost_budget_daily)
VALUES (
    'youtube', 'YouTube web service ring — transcript and metadata extraction', 'lib/rings/youtube_ring.py', 'dispatch', '{}', 'read', 'temp', 'google_youtube', 'active',
    '{"input": {"mode": "passive|active", "url": "string", "query": "string"}, "output": {"title": "string", "channel": "string", "content": "transcript_text", "provenance": "object"}}',
    'Remove row from duplo_tool_registry. No downstream dependencies beyond thermal_memory_archive (provenance-tagged, will cool naturally). Delete cached transcripts from /tmp/yt_transcript_*.',
    'weekly',
    5.00
)
ON CONFLICT (tool_name) DO NOTHING;
