-- Ganuda Shield — Collection Server Schema
-- Council vote #7cfe224b87cb349f
-- PRIVATE — Commercial License

-- Agent registry
CREATE TABLE IF NOT EXISTS agents (
    machine_id VARCHAR(100) PRIMARY KEY,
    employee_id VARCHAR(100) NOT NULL,
    api_key VARCHAR(64) NOT NULL,
    encryption_key VARCHAR(64),
    last_heartbeat TIMESTAMPTZ,
    agent_version VARCHAR(20),
    os_type VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active',
    escalated BOOLEAN DEFAULT FALSE,
    escalation_reason TEXT,
    escalated_by VARCHAR(100),
    escalated_at TIMESTAMPTZ,
    registered_at TIMESTAMPTZ DEFAULT NOW()
);

-- Consent records (IMMUTABLE audit trail — never delete)
CREATE TABLE IF NOT EXISTS consent_log (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(100) NOT NULL,
    machine_id VARCHAR(100) NOT NULL,
    consent_timestamp TIMESTAMPTZ NOT NULL,
    consent_text_hash VARCHAR(64) NOT NULL,
    jurisdiction VARCHAR(20) NOT NULL,
    agent_version VARCHAR(20) NOT NULL,
    withdrawn_at TIMESTAMPTZ
);

-- Activity reports (rolling retention — 90 days default)
CREATE TABLE IF NOT EXISTS activity_reports (
    id BIGSERIAL PRIMARY KEY,
    machine_id VARCHAR(100) NOT NULL,
    employee_id VARCHAR(100) NOT NULL,
    report_timestamp TIMESTAMPTZ NOT NULL,
    report_data JSONB NOT NULL,
    batch_size INTEGER DEFAULT 1,
    encrypted BOOLEAN DEFAULT FALSE,
    anomaly_score REAL DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_reports_machine ON activity_reports(machine_id, report_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_reports_anomaly ON activity_reports(anomaly_score DESC) WHERE anomaly_score > 0;

-- Anomalies
CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(100) NOT NULL,
    employee_id VARCHAR(100) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    trigger_data JSONB,
    admin_action VARCHAR(20),
    admin_user VARCHAR(100),
    admin_timestamp TIMESTAMPTZ,
    employee_flagged_false BOOLEAN DEFAULT FALSE,
    employee_false_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Evidence vault (SEPARATE — append only)
CREATE SCHEMA IF NOT EXISTS evidence;

CREATE TABLE IF NOT EXISTS evidence.records (
    id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL,
    anomaly_id INTEGER REFERENCES anomalies(id),
    machine_id VARCHAR(100) NOT NULL,
    employee_id VARCHAR(100) NOT NULL,
    evidence_type VARCHAR(50) NOT NULL,
    evidence_data BYTEA NOT NULL,
    pii_classification VARCHAR(20) DEFAULT 'none',
    capture_timestamp TIMESTAMPTZ NOT NULL,
    capture_hash VARCHAR(64) NOT NULL,
    legal_hold BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Immutable: revoke modification
-- REVOKE UPDATE, DELETE ON evidence.records FROM PUBLIC;

CREATE TABLE IF NOT EXISTS evidence.custody_log (
    id BIGSERIAL PRIMARY KEY,
    evidence_id BIGINT REFERENCES evidence.records(id),
    accessed_by VARCHAR(100) NOT NULL,
    access_type VARCHAR(20) NOT NULL,
    access_reason TEXT NOT NULL,
    source_ip INET,
    access_timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- REVOKE UPDATE, DELETE ON evidence.custody_log FROM PUBLIC;

-- Retention policy helper
CREATE OR REPLACE FUNCTION purge_old_reports(retention_days INTEGER DEFAULT 90) RETURNS INTEGER AS $$
DECLARE
    deleted INTEGER;
BEGIN
    DELETE FROM activity_reports
    WHERE created_at < NOW() - (retention_days || ' days')::INTERVAL
    AND machine_id NOT IN (
        SELECT DISTINCT machine_id FROM anomalies
        WHERE created_at > NOW() - INTERVAL '1 year'
    );
    GET DIAGNOSTICS deleted = ROW_COUNT;
    RETURN deleted;
END;
$$ LANGUAGE plpgsql;
