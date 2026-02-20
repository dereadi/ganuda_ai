CREATE TABLE IF NOT EXISTS security_health_checks (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(64) NOT NULL,
    check_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    trivy_critical INTEGER DEFAULT 0,
    trivy_high INTEGER DEFAULT 0,
    trivy_report_path TEXT,
    lynis_score INTEGER DEFAULT 0,
    lynis_warnings INTEGER DEFAULT 0,
    lynis_report_path TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_shc_hostname ON security_health_checks(hostname);
CREATE INDEX idx_shc_timestamp ON security_health_checks(check_timestamp);