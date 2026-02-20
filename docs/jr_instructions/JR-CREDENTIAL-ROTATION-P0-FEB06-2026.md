# JR-CREDENTIAL-ROTATION-P0-FEB06-2026

## Priority: P0 (Security Emergency)
## Assigned Specialist: Crawdad (Security)
## Date: February 6, 2026

---

## 1. Context

The Trust Paradox Security Audit (Task 594) discovered the database password `jawaseatlasers2` hardcoded in 50+ files. This credential is now considered compromised and must be rotated immediately.

## 2. Objective

Rotate the PostgreSQL database password for user `claude` on bluefin (192.168.132.222) and update all configuration files.

## 3. Steps

### Step 1: Generate New Password

```bash
# Generate a secure 32-character password
NEW_PASS=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)
echo "New password: $NEW_PASS"
# Store temporarily for this session
echo "CHEROKEE_DB_PASS=$NEW_PASS" > /tmp/new_db_cred.env
```

### Step 2: Update PostgreSQL Password

Run on bluefin as postgres user:

```sql
ALTER USER claude WITH PASSWORD '<new_password>';
```

### Step 3: Update secrets.env on All Nodes

Create/update `/ganuda/config/secrets.env` on each node:

```bash
# On each node (redfin, bluefin, greenfin)
cat > /ganuda/config/secrets.env << 'EOF'
CHEROKEE_DB_HOST=192.168.132.222
CHEROKEE_DB_NAME=zammad_production
CHEROKEE_DB_USER=claude
CHEROKEE_DB_PASS=<new_password>
CHEROKEE_DB_PORT=5432
EOF
chmod 600 /ganuda/config/secrets.env
```

### Step 4: Update Systemd Service Files

Add to each Jr service file in `/etc/systemd/system/`:

```ini
[Service]
EnvironmentFile=/ganuda/config/secrets.env
```

### Step 5: Restart All Jr Services

```bash
sudo systemctl daemon-reload
sudo systemctl restart jr-queue-worker jr-research jr-executor
```

### Step 6: Verify Connectivity

```bash
PGPASSWORD=$CHEROKEE_DB_PASS psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 1"
```

## 4. Verification

- [ ] New password set in PostgreSQL
- [ ] `/ganuda/config/secrets.env` created on all nodes with correct permissions (600)
- [ ] All Jr services restarted and healthy
- [ ] Database connectivity verified from all nodes

## 5. Rollback

If issues occur, the old password can be restored:

```sql
ALTER USER claude WITH PASSWORD 'jawaseatlasers2';
```

## For Seven Generations

Credential rotation is a sacred responsibility - protecting access to our collective memory.
