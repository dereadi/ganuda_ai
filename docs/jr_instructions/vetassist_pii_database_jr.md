# Jr Task: VetAssist PII Database Setup

**Date**: January 5, 2026
**Priority**: HIGH
**Target Node**: bluefin (192.168.132.222)
**Council Vote**: APPROVED (88% confidence)
**Migration Target**: goldfin (when hardware ready)

## Background

The Cherokee AI Federation VetAssist project requires secure storage for veteran PII. The Council approved creating the database on bluefin NOW with a planned migration to the isolated goldfin node (VLAN 20, Tailscale-only) when hardware arrives.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CURRENT (Bluefin)                        │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ zammad_production│    │ vetassist_pii   │  ← NEW        │
│  │ (Federation ops) │    │ (Veteran data)  │               │
│  └─────────────────┘    └────────┬────────┘               │
│                                  │                         │
│                         ┌────────▼────────┐                │
│                         │ Read-Only API   │                │
│                         │ (vetassist_api) │                │
│                         └────────┬────────┘                │
└──────────────────────────────────┼─────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │     AI Agents (Triads)      │
                    │   Query veteran context     │
                    └─────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    FUTURE (Goldfin)                         │
│  ┌─────────────────┐                                       │
│  │ vetassist_pii   │  ← Migrated via pg_dump               │
│  │ VLAN 20 isolated│                                       │
│  │ Tailscale-only  │                                       │
│  │ YubiKey auth    │                                       │
│  └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

## Task 1: Create Database and Roles

Connect to bluefin as postgres superuser:

```bash
sudo -u postgres psql
```

```sql
-- Create database
CREATE DATABASE vetassist_pii
    ENCODING 'UTF8'
    LC_COLLATE 'en_US.UTF-8'
    LC_CTYPE 'en_US.UTF-8';

-- Create read-only API role (minimal privileges per Ops Chief)
CREATE ROLE vetassist_api WITH LOGIN PASSWORD 'GENERATE_SECURE_PASSWORD';

-- Create admin role for migrations/maintenance
CREATE ROLE vetassist_admin WITH LOGIN PASSWORD 'GENERATE_SECURE_PASSWORD';

-- Grant connect
GRANT CONNECT ON DATABASE vetassist_pii TO vetassist_api;
GRANT CONNECT ON DATABASE vetassist_pii TO vetassist_admin;

\c vetassist_pii

-- Enable pgcrypto for column encryption (per Ops Chief)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Grant schema access
GRANT USAGE ON SCHEMA public TO vetassist_api;
GRANT ALL ON SCHEMA public TO vetassist_admin;
```

## Task 2: Create Schema with Audit Logging

```sql
-- Audit log table (per Ops Chief recommendation)
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(10) NOT NULL,  -- SELECT, INSERT, UPDATE, DELETE
    actor VARCHAR(100),
    actor_ip INET,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB
);

CREATE INDEX idx_audit_log_table ON audit_log(table_name);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_record ON audit_log(table_name, record_id);

-- Veteran profiles (core PII - encrypted sensitive fields)
CREATE TABLE veteran_profiles (
    id SERIAL PRIMARY KEY,
    -- Identifiers
    veteran_id VARCHAR(20) UNIQUE NOT NULL,  -- Internal ID

    -- Encrypted PII (using pgcrypto)
    ssn_encrypted BYTEA,  -- pgp_sym_encrypt(ssn, key)
    full_name_encrypted BYTEA,
    date_of_birth_encrypted BYTEA,

    -- Non-sensitive metadata (searchable)
    branch_of_service VARCHAR(50),
    discharge_status VARCHAR(50),
    service_start_date DATE,
    service_end_date DATE,

    -- Contact (encrypted)
    email_encrypted BYTEA,
    phone_encrypted BYTEA,
    address_encrypted BYTEA,

    -- System fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_veteran_profiles_veteran_id ON veteran_profiles(veteran_id);
CREATE INDEX idx_veteran_profiles_branch ON veteran_profiles(branch_of_service);

-- Case notes (interaction history)
CREATE TABLE case_notes (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(20) REFERENCES veteran_profiles(veteran_id),

    -- Note content
    note_type VARCHAR(50),  -- intake, followup, referral, resolution
    summary TEXT,  -- AI-accessible summary (non-PII)
    detailed_notes_encrypted BYTEA,  -- Full notes with PII

    -- Metadata
    case_worker VARCHAR(100),
    interaction_channel VARCHAR(50),  -- phone, email, chat, in_person

    -- System fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_case_notes_veteran ON case_notes(veteran_id);
CREATE INDEX idx_case_notes_type ON case_notes(note_type);
CREATE INDEX idx_case_notes_date ON case_notes(created_at);

-- Service history (military service details)
CREATE TABLE service_history (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(20) REFERENCES veteran_profiles(veteran_id),

    -- Service details
    branch VARCHAR(50),
    rank_at_discharge VARCHAR(50),
    mos_code VARCHAR(20),  -- Military Occupational Specialty
    mos_description TEXT,
    duty_stations TEXT[],  -- Array of locations
    deployments JSONB,  -- {location, start, end, campaign}

    -- Awards and qualifications
    awards TEXT[],
    security_clearance VARCHAR(50),

    -- System fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    verified_at TIMESTAMPTZ,
    verified_by VARCHAR(100)
);

CREATE INDEX idx_service_history_veteran ON service_history(veteran_id);
CREATE INDEX idx_service_history_branch ON service_history(branch);

-- Benefits tracking
CREATE TABLE benefits_tracking (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(20) REFERENCES veteran_profiles(veteran_id),

    -- Benefit details
    benefit_type VARCHAR(100),  -- disability, education, healthcare, housing
    benefit_name VARCHAR(200),
    status VARCHAR(50),  -- pending, approved, denied, active, expired

    -- Application tracking
    application_date DATE,
    decision_date DATE,
    effective_date DATE,
    expiration_date DATE,

    -- Amounts (encrypted for financial PII)
    monthly_amount_encrypted BYTEA,

    -- Notes
    status_notes TEXT,

    -- System fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_benefits_veteran ON benefits_tracking(veteran_id);
CREATE INDEX idx_benefits_type ON benefits_tracking(benefit_type);
CREATE INDEX idx_benefits_status ON benefits_tracking(status);

-- AI context view (non-PII summary for agent queries)
CREATE VIEW veteran_context AS
SELECT
    vp.veteran_id,
    vp.branch_of_service,
    vp.discharge_status,
    vp.service_start_date,
    vp.service_end_date,
    vp.is_active,
    sh.rank_at_discharge,
    sh.mos_description,
    sh.deployments,
    (SELECT COUNT(*) FROM case_notes cn WHERE cn.veteran_id = vp.veteran_id) as total_interactions,
    (SELECT MAX(created_at) FROM case_notes cn WHERE cn.veteran_id = vp.veteran_id) as last_interaction,
    (SELECT array_agg(DISTINCT benefit_type) FROM benefits_tracking bt WHERE bt.veteran_id = vp.veteran_id AND bt.status = 'active') as active_benefits
FROM veteran_profiles vp
LEFT JOIN service_history sh ON vp.veteran_id = sh.veteran_id;
```

## Task 3: Grant Permissions (Minimal Privilege)

```sql
-- API role: READ ONLY on views and non-PII columns
GRANT SELECT ON veteran_context TO vetassist_api;
GRANT SELECT (id, veteran_id, branch_of_service, discharge_status, service_start_date, service_end_date, is_active, created_at) ON veteran_profiles TO vetassist_api;
GRANT SELECT (id, veteran_id, note_type, summary, case_worker, interaction_channel, created_at) ON case_notes TO vetassist_api;
GRANT SELECT ON service_history TO vetassist_api;
GRANT SELECT (id, veteran_id, benefit_type, benefit_name, status, application_date, decision_date, status_notes) ON benefits_tracking TO vetassist_api;

-- API role: INSERT to audit log only
GRANT INSERT ON audit_log TO vetassist_api;
GRANT USAGE ON SEQUENCE audit_log_id_seq TO vetassist_api;

-- Admin role: Full access for migrations
GRANT ALL ON ALL TABLES IN SCHEMA public TO vetassist_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO vetassist_admin;
```

## Task 4: Create Audit Trigger Function

```sql
-- Audit trigger for SELECT queries (logged via API)
CREATE OR REPLACE FUNCTION log_pii_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, actor, timestamp)
    VALUES (TG_TABLE_NAME, NEW.id, TG_OP, current_user, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Audit trigger for modifications
CREATE OR REPLACE FUNCTION audit_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, record_id, action, actor, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, current_user, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, record_id, action, actor, old_values, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, current_user, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, record_id, action, actor, old_values)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, current_user, to_jsonb(OLD));
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER audit_veteran_profiles
    AFTER INSERT OR UPDATE OR DELETE ON veteran_profiles
    FOR EACH ROW EXECUTE FUNCTION audit_changes();

CREATE TRIGGER audit_case_notes
    AFTER INSERT OR UPDATE OR DELETE ON case_notes
    FOR EACH ROW EXECUTE FUNCTION audit_changes();

CREATE TRIGGER audit_benefits
    AFTER INSERT OR UPDATE OR DELETE ON benefits_tracking
    FOR EACH ROW EXECUTE FUNCTION audit_changes();
```

## Task 5: Create Encryption Helper Functions

```sql
-- Encryption key should be stored securely (env var or vault)
-- For now, create helper functions that accept key parameter

CREATE OR REPLACE FUNCTION encrypt_pii(plaintext TEXT, encryption_key TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(plaintext, encryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrypt_pii(ciphertext BYTEA, encryption_key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(ciphertext, encryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Revoke direct execution from API role
REVOKE EXECUTE ON FUNCTION decrypt_pii FROM vetassist_api;
-- Only admin can decrypt
GRANT EXECUTE ON FUNCTION encrypt_pii TO vetassist_admin;
GRANT EXECUTE ON FUNCTION decrypt_pii TO vetassist_admin;
```

## Task 6: PostgreSQL Config for Security

Add to `pg_hba.conf` on bluefin:

```
# VetAssist PII - API access only from greenfin (API server)
hostssl vetassist_pii vetassist_api 192.168.132.224/32 scram-sha-256

# VetAssist PII - Admin access only from localhost
hostssl vetassist_pii vetassist_admin 127.0.0.1/32 scram-sha-256

# Deny direct access from compute nodes
host vetassist_pii all 192.168.132.223/32 reject
```

Reload config:
```bash
sudo -u postgres psql -c "SELECT pg_reload_conf();"
```

## Task 7: Verify Setup

```sql
-- Test as vetassist_api role
SET ROLE vetassist_api;

-- Should work (non-PII view)
SELECT * FROM veteran_context LIMIT 1;

-- Should fail (encrypted column)
SELECT ssn_encrypted FROM veteran_profiles;  -- ERROR: permission denied

-- Should fail (decrypt function)
SELECT decrypt_pii(ssn_encrypted, 'key') FROM veteran_profiles;  -- ERROR: permission denied

RESET ROLE;
```

## Migration Path to Goldfin

When goldfin hardware is ready:

```bash
# 1. Dump database on bluefin
pg_dump -U vetassist_admin -h localhost -Fc vetassist_pii > vetassist_pii_backup.dump

# 2. Copy to goldfin (via Tailscale)
scp vetassist_pii_backup.dump dereadi@goldfin:/tmp/

# 3. Restore on goldfin
pg_restore -U postgres -d vetassist_pii /tmp/vetassist_pii_backup.dump

# 4. Update pg_hba.conf on goldfin for new network (VLAN 20)

# 5. Update API connection strings to point to goldfin

# 6. Drop database on bluefin after verification
```

## Acceptance Criteria

- [ ] vetassist_pii database created on bluefin
- [ ] pgcrypto extension enabled
- [ ] All tables created with proper indexes
- [ ] vetassist_api role has read-only access to non-PII columns only
- [ ] vetassist_admin role has full access
- [ ] Audit logging triggers active
- [ ] pg_hba.conf restricts access to API server only
- [ ] Encryption functions created and secured
- [ ] veteran_context view accessible by API role

## Security Notes

- **Encryption Key Management**: Store encryption key in environment variable or HashiCorp Vault, NOT in database
- **API Role**: Cannot decrypt PII, can only read non-sensitive metadata
- **Audit Trail**: All access and modifications logged with timestamp and actor
- **Network Isolation**: Only greenfin (API server) can connect to vetassist_pii database
- **Future**: Full isolation on goldfin with VLAN 20, Tailscale-only, YubiKey

## For Seven Generations
