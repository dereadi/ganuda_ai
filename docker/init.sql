-- Ganuda Database Initialization
-- Creates core tables for Gateway v1.0

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit_rpm INTEGER DEFAULT 60,
    permissions JSONB DEFAULT '{"chat": true, "models": true}'
);

-- API Audit Log
CREATE TABLE IF NOT EXISTS api_audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    request_id VARCHAR(36) NOT NULL,
    api_key_id INTEGER REFERENCES api_keys(id),
    endpoint VARCHAR(100) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    tokens_in INTEGER,
    tokens_out INTEGER,
    model VARCHAR(100),
    ip_address INET
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON api_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_request ON api_audit_log(request_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

-- Insert default admin key (CHANGE IN PRODUCTION!)
-- Default key: gnd-admin-default-key
INSERT INTO api_keys (key_hash, name, permissions)
VALUES (
    encode(sha256('gnd-admin-default-key'::bytea), 'hex'),
    'Default Admin Key - CHANGE ME',
    '{"chat": true, "models": true, "admin": true}'
) ON CONFLICT (key_hash) DO NOTHING;

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO ganuda;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO ganuda;
