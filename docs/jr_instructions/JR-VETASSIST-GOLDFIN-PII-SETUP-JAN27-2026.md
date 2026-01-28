# JR Instruction: Complete VetAssist PII Database Setup on Goldfin

**JR ID:** JR-VETASSIST-GOLDFIN-PII-SETUP
**Priority:** P1 (Security/Compliance)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Assigned To:** Database Jr. or Infrastructure Jr.
**Effort:** Medium (2-4 hours)

---

## Current State (Assessed 2026-01-27)

| Component | Status |
|-----------|--------|
| **OS** | Rocky Linux 10.1 ✅ |
| **PostgreSQL** | 16.11 running ✅ |
| **vetassist_pii database** | Exists (empty) ✅ |
| **pgcrypto extension** | NOT installed ❌ |
| **PII tables** | NOT created ❌ |
| **Network access** | Only greenfin allowed ❌ |

### Network Architecture

```
redfin (VetAssist backend)     goldfin (PII vault)
   192.168.132.223          →      192.168.20.10
         VLAN 132                    VLAN 20 (Sanctum)
              ↓                           ↑
         greenfin (gateway/proxy)
           192.168.132.224 + 192.168.20.1
```

**Key Finding:** Redfin cannot reach goldfin directly. All traffic must route through greenfin.

---

## Phase 1: Install pgcrypto Extension

```bash
# On goldfin as postgres user
sudo -u postgres psql -d vetassist_pii -c "CREATE EXTENSION pgcrypto;"

# Verify
sudo -u postgres psql -d vetassist_pii -c "\dx"
```

---

## Phase 2: Create PII Tables

```sql
-- Connect to vetassist_pii database
\c vetassist_pii

-- Encrypted wizard sessions (PII data)
CREATE TABLE vetassist_wizard_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT gen_random_uuid(),
    wizard_type VARCHAR(50),
    veteran_id VARCHAR(50),
    current_step INTEGER DEFAULT 1,
    -- PII fields encrypted with pgp_sym_encrypt
    answers_encrypted BYTEA,  -- Contains SSN, DOB, name, medical
    status VARCHAR(20) DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Encrypted files metadata
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

-- Users with PII (migrated from triad_federation)
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    email_encrypted BYTEA,
    full_name_encrypted BYTEA,
    phone_encrypted BYTEA,
    hashed_password VARCHAR(255),
    role VARCHAR(20) DEFAULT 'veteran',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO vetassist;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vetassist;
```

---

## Phase 3: Configure Network Access

### Option A: Add PgBouncer on Greenfin (Recommended)

Since redfin cannot reach goldfin directly, use greenfin as a PostgreSQL proxy.

```bash
# On greenfin
sudo apt install pgbouncer

# /etc/pgbouncer/pgbouncer.ini
[databases]
vetassist_pii = host=192.168.20.10 port=5432 dbname=vetassist_pii

[pgbouncer]
listen_addr = 192.168.132.224
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# /etc/pgbouncer/userlist.txt
"vetassist" "SCRAM-SHA-256$..."
```

### Option B: Direct Route (if VLAN routing configured)

If greenfin routes VLAN 132 to VLAN 20:

```bash
# On goldfin - add redfin to pg_hba.conf
echo 'host    vetassist_pii   vetassist    192.168.132.223/32    scram-sha-256' | sudo tee -a /var/lib/pgsql/data/pg_hba.conf
sudo systemctl reload postgresql
```

### Option C: SSH Tunnel from Redfin

```bash
# On redfin, create persistent SSH tunnel
ssh -f -N -L 5433:192.168.20.10:5432 greenfin

# Backend connects to localhost:5433
```

---

## Phase 4: Update VetAssist Backend

### 4.1 Add PII Database Configuration

```bash
# /ganuda/vetassist/backend/.env
# Add goldfin PII connection (via greenfin proxy)
PII_DB_HOST=192.168.132.224  # greenfin pgbouncer
PII_DB_PORT=6432
PII_DB_NAME=vetassist_pii
PII_DB_USER=vetassist
PII_DB_PASSWORD=<from-silverfin-vault>
```

### 4.2 Update database_config.py

```python
def get_pii_db_connection():
    """Connect to goldfin for PII data via greenfin proxy."""
    return psycopg2.connect(
        host=os.environ.get("PII_DB_HOST", "192.168.132.224"),
        port=os.environ.get("PII_DB_PORT", "6432"),
        database=os.environ.get("PII_DB_NAME", "vetassist_pii"),
        user=os.environ.get("PII_DB_USER", "vetassist"),
        password=os.environ.get("PII_DB_PASSWORD")
    )
```

---

## Phase 5: Data Migration

Once network access is configured:

```bash
# Export from bluefin
pg_dump -h 192.168.132.222 -U claude -d zammad_production \
    -t vetassist_wizard_sessions \
    > /tmp/wizard_export.sql

# Transform and import to goldfin (encrypt PII fields)
# See JR-VETASSIST-GOLDFIN-PII-MIGRATION-JAN27-2026.md for details
```

---

## Success Criteria

- [ ] pgcrypto extension installed on vetassist_pii
- [ ] PII tables created (vetassist_wizard_sessions, vetassist_files, users)
- [ ] Network path working (redfin → greenfin → goldfin)
- [ ] VetAssist backend can connect to goldfin for PII operations
- [ ] Test encryption/decryption working

---

## Testing Commands

```bash
# Test connection from redfin (via tunnel/proxy)
psql -h localhost -p 5433 -U vetassist -d vetassist_pii -c "SELECT 1;"

# Test encryption
psql -d vetassist_pii -c "SELECT pgp_sym_encrypt('test', 'key')::text;"

# Test decryption
psql -d vetassist_pii -c "SELECT pgp_sym_decrypt(pgp_sym_encrypt('test', 'key'), 'key');"
```

---

## References

- KB-VETASSIST-SPLIT-DATABASE-ARCHITECTURE-JAN27-2026.md
- JR-VETASSIST-GOLDFIN-PII-MIGRATION-JAN27-2026.md (superseded by this)
- JR-Goldfin-Security-Architecture.md

---

FOR SEVEN GENERATIONS
