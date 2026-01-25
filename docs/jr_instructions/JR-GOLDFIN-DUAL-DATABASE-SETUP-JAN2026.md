# JR Instruction: goldfin Dual Database Setup

## Date: January 15, 2026
## Priority: MEDIUM (after Presidio integration)
## Assigned To: IT Triad
## Target: Q1 2026

---

## Overview

Set up goldfin to host two separate PostgreSQL databases:
1. **vetassist_pii** - PII data (SSN, addresses, medical info)
2. **vetassist_pci** - Financial data (credit cards, billing) - interim until platinumfin

This is an interim architecture. When platinumfin hardware is available, PCI data will migrate to its own node on VLAN 30.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOLDFIN (Interim)                             │
│                    192.168.20.10                                 │
│                    VLAN 20 (Sanctum)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────┐    ┌─────────────────────┐            │
│   │   vetassist_pii     │    │   vetassist_pci     │            │
│   │                     │    │                     │            │
│   │   PII Database      │    │   PCI Database      │            │
│   │   - pii_tokens      │    │   - payment_tokens  │            │
│   │   - user_pii        │    │   - billing_info    │            │
│   │   - medical_refs    │    │   - subscriptions   │            │
│   │                     │    │                     │            │
│   │   Owner: pii_user   │    │   Owner: pci_user   │            │
│   └─────────────────────┘    └─────────────────────┘            │
│                                                                  │
│   PostgreSQL 15                                                  │
│   LUKS encrypted disk                                            │
│   Tailscale access only                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

FUTURE (platinumfin):
┌─────────────────────┐         ┌─────────────────────┐
│     GOLDFIN         │         │    PLATINUMFIN      │
│     VLAN 20         │         │     VLAN 30         │
│   vetassist_pii     │         │   vetassist_pci     │
│      (PII)          │         │      (PCI)          │
└─────────────────────┘         └─────────────────────┘
```

---

## Prerequisites

- [ ] goldfin accessible via Tailscale (DONE - Jan 15, 2026)
- [ ] PostgreSQL installed on goldfin
- [ ] Presidio integration complete (in progress)

---

## Implementation Steps

### Step 1: Install PostgreSQL on goldfin

```bash
# On goldfin (Rocky Linux)
# Proxy should already be configured from Tailscale install

sudo dnf install -y postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

### Step 2: Configure PostgreSQL for Network Access

Edit `/var/lib/pgsql/data/postgresql.conf`:
```
listen_addresses = 'localhost,100.x.x.x'  # Tailscale IP
port = 5432
```

Edit `/var/lib/pgsql/data/pg_hba.conf`:
```
# Local connections
local   all             all                                     peer

# Tailscale connections (redfin)
host    vetassist_pii   pii_user        100.0.0.0/8             scram-sha-256
host    vetassist_pci   pci_user        100.0.0.0/8             scram-sha-256

# Deny all others
host    all             all             0.0.0.0/0               reject
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Step 3: Create Databases and Users

```sql
-- Connect as postgres
sudo -u postgres psql

-- Create PII database and user
CREATE USER pii_user WITH PASSWORD '<generate-secure-password>';
CREATE DATABASE vetassist_pii OWNER pii_user;

-- Create PCI database and user
CREATE USER pci_user WITH PASSWORD '<generate-secure-password>';
CREATE DATABASE vetassist_pci OWNER pci_user;

-- Ensure isolation - users can only access their own database
REVOKE ALL ON DATABASE vetassist_pii FROM PUBLIC;
REVOKE ALL ON DATABASE vetassist_pci FROM PUBLIC;

\q
```

### Step 4: Create PII Tables

```sql
-- Connect to vetassist_pii as pii_user
\c vetassist_pii pii_user

CREATE TABLE pii_tokens (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    token VARCHAR(16) NOT NULL,
    encrypted_value BYTEA NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    accessed_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    UNIQUE(session_id, token)
);

CREATE INDEX idx_pii_session ON pii_tokens(session_id);
CREATE INDEX idx_pii_token ON pii_tokens(token);

-- Audit table
CREATE TABLE pii_access_log (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES pii_tokens(id),
    accessed_by VARCHAR(100),
    access_type VARCHAR(20),  -- 'read', 'write', 'delete'
    accessed_at TIMESTAMP DEFAULT NOW(),
    source_ip VARCHAR(45)
);
```

### Step 5: Create PCI Tables (Interim)

```sql
-- Connect to vetassist_pci as pci_user
\c vetassist_pci pci_user

CREATE TABLE payment_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    token VARCHAR(32) NOT NULL UNIQUE,
    card_last_four VARCHAR(4),
    card_brand VARCHAR(20),
    expiry_month INTEGER,
    expiry_year INTEGER,
    -- Actual card number NEVER stored, only tokenized reference
    processor_token VARCHAR(100),  -- Stripe/processor token
    created_at TIMESTAMP DEFAULT NOW(),
    is_default BOOLEAN DEFAULT FALSE
);

CREATE TABLE billing_info (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    billing_name VARCHAR(100),
    billing_address_token VARCHAR(16),  -- Reference to PII vault
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    plan_type VARCHAR(50),
    status VARCHAR(20),
    payment_token_id INTEGER REFERENCES payment_tokens(id),
    started_at TIMESTAMP,
    ends_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit table
CREATE TABLE pci_access_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50),
    record_id INTEGER,
    accessed_by VARCHAR(100),
    access_type VARCHAR(20),
    accessed_at TIMESTAMP DEFAULT NOW(),
    source_ip VARCHAR(45)
);
```

### Step 6: Configure Firewall for PostgreSQL

```bash
# On goldfin - allow PostgreSQL from Tailscale
sudo firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 -s 100.0.0.0/8 -p tcp --dport 5432 -j ACCEPT
sudo firewall-cmd --reload
```

### Step 7: Store Credentials in silverfin Vault

```bash
# On silverfin (FreeIPA) - store database credentials
# This step assumes FreeIPA Vault is configured

ipa vault-add vetassist-pii-credentials --type=standard
ipa vault-archive vetassist-pii-credentials --data='pii_user:<password>'

ipa vault-add vetassist-pci-credentials --type=standard
ipa vault-archive vetassist-pci-credentials --data='pci_user:<password>'
```

---

## Validation Checklist

- [ ] PostgreSQL running on goldfin
- [ ] vetassist_pii database created
- [ ] vetassist_pci database created
- [ ] Users isolated (can't access each other's DB)
- [ ] Tailscale-only access (pg_hba.conf)
- [ ] Firewall allows port 5432 from Tailscale
- [ ] Credentials stored in silverfin vault
- [ ] redfin can connect to both databases via Tailscale

---

## Connection Strings (for VetAssist backend)

```python
# .env on redfin
PII_DATABASE_URL=postgresql://pii_user:<password>@<goldfin-tailscale-ip>:5432/vetassist_pii
PCI_DATABASE_URL=postgresql://pci_user:<password>@<goldfin-tailscale-ip>:5432/vetassist_pci
```

---

## Migration Path (Future)

When platinumfin is ready:
1. Create vetassist_pci database on platinumfin
2. pg_dump from goldfin, pg_restore to platinumfin
3. Update connection strings
4. Drop vetassist_pci from goldfin
5. Update documentation

---

## Security Notes

1. **No raw card numbers** - Only processor tokens (Stripe, etc.)
2. **Separate users** - pii_user cannot access PCI, pci_user cannot access PII
3. **Tailscale only** - No direct network access
4. **Audit logging** - All access logged
5. **Encrypted disk** - LUKS encryption on goldfin

---

*Cherokee AI Federation - For the Seven Generations*
*"Guard the sacred data as you would guard the fire."*
