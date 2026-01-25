# Jr Instruction: goldfin PostgreSQL VLAN 20 Configuration

**Date**: January 11, 2026
**Priority**: BLOCKER
**Target Node**: goldfin (192.168.20.10)
**TPM**: Flying Squirrel (dereadi)
**Requires**: Direct console access (VLAN 20 isolated)

## Problem

goldfin is now isolated on VLAN 20 (Sanctum). The VetAssist API on greenfin cannot connect to PostgreSQL:

```
greenfin$ ping 192.168.20.10     # SUCCESS - network path works
greenfin$ nc -zv 192.168.20.10 5432   # FAILED - Connection refused
```

## Root Cause

PostgreSQL is likely:
1. Only listening on localhost (127.0.0.1)
2. Missing pg_hba.conf entry for VLAN 20 subnet
3. Firewall blocking port 5432 from greenfin

## Solution

### Step 1: Access goldfin directly

goldfin is only accessible via VLAN 20. Options:
- Physical console
- SSH from greenfin (if keys configured)
- Temporary cable swap

### Step 2: Check PostgreSQL Status

```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql-15

# Check what PostgreSQL is listening on
sudo ss -tlnp | grep 5432
# Expected: Should show 0.0.0.0:5432 or 192.168.20.10:5432
# Problem: Likely shows 127.0.0.1:5432 only
```

### Step 3: Update postgresql.conf

```bash
# Find and edit postgresql.conf
sudo vi /u/postgres/data/postgresql.conf

# Change this line:
# listen_addresses = 'localhost'
# To:
listen_addresses = '*'
```

### Step 4: Update pg_hba.conf

```bash
# Edit pg_hba.conf to allow greenfin connection
sudo vi /u/postgres/data/pg_hba.conf

# Add this line (allow VLAN 20 subnet):
host    vetassist_pii   vetassist   192.168.20.0/24     scram-sha-256

# Or more specifically for greenfin only:
host    vetassist_pii   vetassist   192.168.20.1/32     scram-sha-256
```

### Step 5: Update Firewall

```bash
# Check current firewall rules
sudo firewall-cmd --list-all

# Add rule for PostgreSQL from VLAN 20
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.20.0/24" port protocol="tcp" port="5432" accept'

# Reload firewall
sudo firewall-cmd --reload
```

### Step 6: Restart PostgreSQL

```bash
sudo systemctl restart postgresql-15
```

### Step 7: Verify from greenfin

```bash
# From greenfin
nc -zv 192.168.20.10 5432
# Expected: Connection to 192.168.20.10 5432 port [tcp/postgresql] succeeded!

# Test VetAssist API
curl http://localhost:8091/health
# Expected: {"status":"healthy","presidio":"up","database":"up"}
```

## Security Notes

- VLAN 20 is the Sanctum (PII) network
- Only greenfin (192.168.20.1) should have access to goldfin
- Do NOT add rules for 192.168.132.0/24 (Compute VLAN)
- This maintains air-gap between Compute and Sanctum

## Thermal Memory Update

After completion, archive to thermal memory:

```sql
INSERT INTO thermal_memory_archive (
    memory_hash, original_content, temperature_score, tags,
    source_triad, source_node, source_session, valid_from, memory_type
) VALUES (
    md5('goldfin_postgresql_vlan20_fixed_jan11_2026'),
    'GOLDFIN POSTGRESQL VLAN 20 FIXED - January 11, 2026

    PostgreSQL now accepting connections on VLAN 20:
    - listen_addresses = *
    - pg_hba.conf: host vetassist_pii vetassist 192.168.20.0/24 scram-sha-256
    - Firewall: port 5432 allowed from 192.168.20.0/24

    VetAssist API health: HEALTHY

    For Seven Generations.',
    95.0,
    ARRAY['goldfin', 'postgresql', 'vlan20', 'fixed', 'cmdb', 'january-2026'],
    'tpm', 'goldfin', 'claude-session-jan11', NOW(), 'cmdb_entry'
);
```

---

For Seven Generations.
