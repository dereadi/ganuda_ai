# JR Instruction: VetAssist PII Migration to Goldfin

**JR ID:** JR-VETASSIST-GOLDFIN-PII-MIGRATION
**Priority:** P1 (Security/Compliance)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Assigned To:** Database Jr. or Infrastructure Jr.
**Effort:** Large (3-5 days)

---

## Objective

Migrate VetAssist veteran PII data from bluefin to goldfin to achieve proper security isolation.

## Current State

| Data Type | Current Location | Contains PII |
|-----------|------------------|--------------|
| vetassist_wizard_sessions | bluefin (zammad_production) | YES - SSN, DOB, name, medical |
| vetassist_files | bluefin (zammad_production) | YES - medical records |
| users | bluefin (triad_federation) | YES - email, phone |
| thermal_memory_archive | bluefin (zammad_production) | NO |
| chat_sessions | bluefin (triad_federation) | MAYBE - could contain PII |

## Target State

| Data Type | Target Location | Notes |
|-----------|-----------------|-------|
| vetassist_wizard_sessions | goldfin (vetassist_pii) | Encrypted at rest |
| vetassist_files | goldfin (vetassist_pii) | File metadata + storage |
| users | goldfin (vetassist_pii) | Encrypted PII fields |
| chat_sessions | bluefin | With PII redacted |

---

## Phase 1: Goldfin PostgreSQL Setup

### 1.1 Install PostgreSQL 17 on Goldfin

```bash
# On goldfin (192.168.132.226)
sudo apt install postgresql-17 postgresql-17-pgcrypto
sudo systemctl enable postgresql
```

### 1.2 Create Encrypted PII Database

```sql
CREATE DATABASE vetassist_pii;
\c vetassist_pii
CREATE EXTENSION pgcrypto;

-- Encryption key management (use Silverfin vault in production)
CREATE TABLE encryption_keys (
    key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_name VARCHAR(100) UNIQUE NOT NULL,
    key_value BYTEA NOT NULL,  -- Encrypted master key
    created_at TIMESTAMP DEFAULT NOW(),
    rotated_at TIMESTAMP
);
```

### 1.3 Configure Network Access

```bash
# pg_hba.conf - Only allow from redfin (backend server)
host vetassist_pii vetassist_app 192.168.132.223/32 scram-sha-256
```

---

## Phase 2: Schema Migration

### 2.1 Create PII Tables on Goldfin

```sql
-- Encrypted wizard sessions
CREATE TABLE vetassist_wizard_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT gen_random_uuid(),
    wizard_type VARCHAR(50),
    veteran_id VARCHAR(50),  -- References users.id
    current_step INTEGER DEFAULT 1,
    -- PII fields encrypted with pgp_sym_encrypt
    answers_encrypted BYTEA,  -- Contains SSN, DOB, name, medical
    status VARCHAR(20) DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Encrypted files
CREATE TABLE vetassist_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    veteran_id VARCHAR(50),
    filename_encrypted BYTEA,
    file_path_encrypted BYTEA,
    file_type VARCHAR(50),
    category VARCHAR(50),
    file_size BIGINT,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    deleted BOOLEAN DEFAULT FALSE
);
```

---

## Phase 3: Backend Code Updates

### 3.1 Update database_config.py

```python
# Add goldfin connection for PII data
def get_pii_db_connection():
    """Connect to goldfin for PII data."""
    return psycopg2.connect(
        host="192.168.132.226",  # goldfin
        database="vetassist_pii",
        user=os.environ.get("PII_DB_USER", "vetassist_app"),
        password=os.environ.get("PII_DB_PASSWORD"),
        port=5432
    )
```

### 3.2 Update .env

```bash
# Operational database (bluefin)
DB_HOST=192.168.132.222
DB_NAME=zammad_production

# PII database (goldfin)
PII_DB_HOST=192.168.132.226
PII_DB_NAME=vetassist_pii
PII_DB_USER=vetassist_app
PII_DB_PASSWORD=<from-silverfin-vault>
```

### 3.3 Update Dashboard Endpoint

```python
# app/api/v1/endpoints/dashboard.py
from app.core.database_config import get_pii_db_connection

def get_dashboard_data(veteran_id: str, ...):
    # Use PII connection for wizard data
    with get_pii_db_connection() as conn:
        cur.execute("SELECT * FROM vetassist_wizard_sessions WHERE ...")
```

---

## Phase 4: Data Migration

### 4.1 Export from Bluefin

```bash
pg_dump -h 192.168.132.222 -U claude -d zammad_production \
    -t vetassist_wizard_sessions \
    -t vetassist_files \
    > /tmp/vetassist_pii_export.sql
```

### 4.2 Import to Goldfin (with encryption)

```sql
-- Transform and encrypt during import
INSERT INTO vetassist_wizard_sessions (
    session_id, wizard_type, veteran_id, current_step,
    answers_encrypted, status, created_at
)
SELECT
    session_id, wizard_type, veteran_id, current_step,
    pgp_sym_encrypt(answers::text, 'encryption_key'),
    status, created_at
FROM old_vetassist_wizard_sessions;
```

### 4.3 Verify and Cutover

```bash
# Verify counts match
psql -h goldfin -d vetassist_pii -c "SELECT COUNT(*) FROM vetassist_wizard_sessions"
psql -h bluefin -d zammad_production -c "SELECT COUNT(*) FROM vetassist_wizard_sessions"

# Update backend to use goldfin
systemctl restart vetassist-backend
```

---

## Success Criteria

- [ ] PostgreSQL 17 with pgcrypto running on goldfin
- [ ] vetassist_pii database created with encrypted tables
- [ ] Backend connects to goldfin for PII operations
- [ ] All existing wizard sessions migrated
- [ ] Dashboard shows claims from goldfin
- [ ] No PII remains on bluefin

---

## References

- KB-VETASSIST-SPLIT-DATABASE-ARCHITECTURE-JAN27-2026
- ULTRATHINK-VETASSIST-PLATFORM-JAN16-2026
- JR-GOLDFIN-PII-VAULT-SETUP-JAN16-2026

---

FOR SEVEN GENERATIONS
