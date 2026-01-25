# JR Instruction: goldfin PII Token Vault Setup (Phase 3)

## Metadata
```yaml
task_id: goldfin_pii_vault_setup
priority: 2
council_vote: 6700b2d88464ab8b
assigned_to: it_triad_jr
estimated_duration: 60_minutes
requires_sudo: true
requires_restart: false
target_node: goldfin
depends_on:
  - presidio_pii_integration_v2
  - vetassist_pii_chat_integration
```

## Overview

Set up a secure PostgreSQL database on goldfin to store PII token mappings. This vault allows:
- Reversible tokenization (token → original value)
- Audit logging for all access
- Encryption at rest
- Separate from main database (bluefin) for security isolation

**Security Boundary:** goldfin holds the "keys to the kingdom" - original PII values. Access must be tightly controlled.

---

## Prerequisites

1. goldfin node accessible on VLAN 20 (Tailscale IP: 100.x.x.x)
2. PostgreSQL installed on goldfin
3. Phase 1 (Presidio) and Phase 2 (Chat Integration) complete
4. Network route from redfin to goldfin

---

## Tasks

### Task 1: Create PII Vault Database on goldfin

SSH to goldfin and create the database:

```bash
ssh goldfin

# Switch to postgres user
sudo -u postgres psql << 'SQL'
-- Create dedicated database for PII vault
CREATE DATABASE vetassist_pii_vault
    WITH ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8';

-- Create restricted user for VetAssist backend
CREATE USER vetassist_pii WITH PASSWORD 'GENERATE_SECURE_PASSWORD';

-- Grant minimal privileges
GRANT CONNECT ON DATABASE vetassist_pii_vault TO vetassist_pii;

\c vetassist_pii_vault

-- Enable pgcrypto for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Enable uuid-ossp for token generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
SQL
```

### Task 2: Create Token Storage Schema

```sql
-- Connect to vault database
\c vetassist_pii_vault

-- PII Token table
CREATE TABLE pii_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(64) NOT NULL UNIQUE,
    user_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    -- Original value encrypted with pgcrypto
    encrypted_value BYTEA NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    -- Metadata for context
    source_session UUID,
    expiry_date TIMESTAMP
);

-- Index for fast lookups
CREATE INDEX idx_pii_tokens_token ON pii_tokens(token);
CREATE INDEX idx_pii_tokens_user ON pii_tokens(user_id);

-- Audit log table
CREATE TABLE pii_access_log (
    id SERIAL PRIMARY KEY,
    token VARCHAR(64) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- 'store', 'retrieve', 'delete'
    requested_by VARCHAR(100) NOT NULL,  -- service or user
    request_ip INET,
    request_reason TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Index for audit queries
CREATE INDEX idx_pii_access_time ON pii_access_log(timestamp);
CREATE INDEX idx_pii_access_token ON pii_access_log(token);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON pii_tokens TO vetassist_pii;
GRANT SELECT, INSERT ON pii_access_log TO vetassist_pii;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vetassist_pii;
```

### Task 3: Create Encryption Key

Generate and securely store encryption key:

```bash
# Generate 256-bit AES key
PII_ENCRYPTION_KEY=$(openssl rand -hex 32)
echo "PII_ENCRYPTION_KEY=$PII_ENCRYPTION_KEY"

# Store in goldfin secure location (NOT in code repo)
echo "PII_ENCRYPTION_KEY=$PII_ENCRYPTION_KEY" | sudo tee /etc/vetassist/pii_vault.env
sudo chmod 600 /etc/vetassist/pii_vault.env
sudo chown root:root /etc/vetassist/pii_vault.env
```

### Task 4: Create Vault Service Module

Create `/ganuda/vetassist/backend/app/services/pii_vault.py`:

```python
"""
PII Token Vault Service
Manages reversible tokenization with goldfin PostgreSQL

Cherokee AI Federation - For the Seven Generations
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class PIIVaultService:
    """Service for storing and retrieving PII tokens from goldfin vault."""

    def __init__(self):
        self.conn_params = {
            'host': os.environ.get('PII_VAULT_HOST', '100.x.x.x'),  # goldfin Tailscale
            'port': os.environ.get('PII_VAULT_PORT', 5432),
            'database': 'vetassist_pii_vault',
            'user': 'vetassist_pii',
            'password': os.environ.get('PII_VAULT_PASSWORD')
        }
        self.encryption_key = os.environ.get('PII_ENCRYPTION_KEY')

    def _get_connection(self):
        return psycopg2.connect(**self.conn_params)

    def store_token(
        self,
        token: str,
        user_id: str,
        entity_type: str,
        original_value: str,
        session_id: Optional[str] = None,
        requested_by: str = 'vetassist_backend'
    ) -> bool:
        """
        Store encrypted PII value with its token.

        Returns True on success, False if token already exists.
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Encrypt the original value
                    cur.execute("""
                        INSERT INTO pii_tokens
                        (token, user_id, entity_type, encrypted_value, source_session)
                        VALUES (
                            %s, %s, %s,
                            pgp_sym_encrypt(%s, %s),
                            %s
                        )
                        ON CONFLICT (token) DO NOTHING
                    """, (token, user_id, entity_type, original_value,
                          self.encryption_key, session_id))

                    # Log access
                    cur.execute("""
                        INSERT INTO pii_access_log
                        (token, action, requested_by)
                        VALUES (%s, 'store', %s)
                    """, (token, requested_by))

                    conn.commit()
                    return cur.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to store PII token: {e}")
            return False

    def retrieve_token(
        self,
        token: str,
        requested_by: str,
        request_reason: str
    ) -> Optional[Dict]:
        """
        Retrieve and decrypt PII value by token.

        Requires reason for audit trail.
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    # Decrypt and retrieve
                    cur.execute("""
                        SELECT
                            token,
                            user_id,
                            entity_type,
                            pgp_sym_decrypt(encrypted_value, %s) as original_value
                        FROM pii_tokens
                        WHERE token = %s
                    """, (self.encryption_key, token))

                    result = cur.fetchone()

                    if result:
                        # Update access tracking
                        cur.execute("""
                            UPDATE pii_tokens
                            SET last_accessed = NOW(), access_count = access_count + 1
                            WHERE token = %s
                        """, (token,))

                        # Log access with reason
                        cur.execute("""
                            INSERT INTO pii_access_log
                            (token, action, requested_by, request_reason)
                            VALUES (%s, 'retrieve', %s, %s)
                        """, (token, requested_by, request_reason))

                        conn.commit()

                        return {
                            'token': result['token'],
                            'user_id': str(result['user_id']),
                            'entity_type': result['entity_type'],
                            'original_value': result['original_value']
                        }

                    return None

        except Exception as e:
            logger.error(f"Failed to retrieve PII token: {e}")
            return None


# Singleton instance
pii_vault = PIIVaultService()
```

### Task 5: Update VetAssist Backend Environment

Add to `/ganuda/vetassist/backend/.env`:

```bash
# PII Vault (goldfin) - Phase 3
PII_VAULT_HOST=100.x.x.x  # Update with actual goldfin Tailscale IP
PII_VAULT_PORT=5432
PII_VAULT_PASSWORD=SECURE_PASSWORD_HERE
PII_ENCRYPTION_KEY=KEY_FROM_STEP_3
```

### Task 6: Configure goldfin pg_hba.conf

Allow connections from redfin:

```bash
# On goldfin
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Add line:
host    vetassist_pii_vault    vetassist_pii    100.x.x.x/32    scram-sha-256

# Reload PostgreSQL
sudo systemctl reload postgresql
```

---

## Verification

```bash
# From redfin, test connection to goldfin vault
cd /ganuda/vetassist/backend
source venv/bin/activate

python << 'TEST'
import os
os.environ['PII_VAULT_HOST'] = '100.x.x.x'  # goldfin IP
os.environ['PII_VAULT_PASSWORD'] = 'YOUR_PASSWORD'
os.environ['PII_ENCRYPTION_KEY'] = 'YOUR_KEY'

from app.services.pii_vault import PIIVaultService

vault = PIIVaultService()

# Test store
success = vault.store_token(
    token='test-token-123',
    user_id='00000000-0000-0000-0000-000000000001',
    entity_type='US_SSN',
    original_value='123-45-6789',
    requested_by='test_script'
)
print(f"Store: {'OK' if success else 'FAILED'}")

# Test retrieve
result = vault.retrieve_token(
    token='test-token-123',
    requested_by='test_script',
    request_reason='Integration test'
)
print(f"Retrieve: {result}")

# Verify encryption
print(f"Original value retrieved: {result['original_value'] if result else 'NONE'}")
TEST
```

---

## Security Checklist

- [ ] goldfin firewall allows only redfin access to port 5432
- [ ] PostgreSQL user has minimal privileges (SELECT, INSERT, UPDATE only)
- [ ] Encryption key stored outside code repository
- [ ] All access logged with reason
- [ ] No plaintext PII in logs

---

## Rollback

```sql
-- On goldfin as postgres
DROP DATABASE IF EXISTS vetassist_pii_vault;
DROP USER IF EXISTS vetassist_pii;
```

---

*Cherokee AI Federation - For the Seven Generations*
*"Some knowledge must be kept safe. The vault protects what matters most."*
