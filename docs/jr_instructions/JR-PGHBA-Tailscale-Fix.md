# Jr Instructions: Fix pg_hba.conf for Tailscale Access on Bluefin

**Task ID**: PGHBA-TAILSCALE-001
**Priority**: MEDIUM
**Target Node**: bluefin (192.168.132.222 / 100.112.254.96)
**Requires**: sudo access

---

## Problem Statement

The PostgreSQL pg_hba.conf on bluefin does not allow connections from Tailscale IP range (100.0.0.0/8). This blocks:
- TPM macbook (100.103.27.106) from accessing thermal memory
- Redfin (100.116.27.89) from accessing bluefin DBs via Tailscale
- Any other Tailscale node from connecting to PostgreSQL

## Current Error

```
FATAL: no pg_hba.conf entry for host "100.103.27.106", user "claude", database "zammad_production", no encryption
```

---

## Solution

### Step 1: Find pg_hba.conf Location

```bash
ssh dereadi@100.112.254.96 "sudo -u postgres psql -c 'SHOW hba_file;'"
```

Expected output: `/etc/postgresql/17/main/pg_hba.conf` or similar

### Step 2: Backup Current Config

```bash
ssh dereadi@100.112.254.96 "sudo cp /etc/postgresql/17/main/pg_hba.conf /etc/postgresql/17/main/pg_hba.conf.backup-$(date +%Y%m%d)"
```

### Step 3: Add Tailscale Network Entry

Add BEFORE any "host all all ... reject" lines:

```bash
ssh dereadi@100.112.254.96 "echo '# Tailscale network access for Cherokee AI Federation
host    all             claude          100.0.0.0/8             scram-sha-256
host    zammad_production   claude      100.0.0.0/8             scram-sha-256' | sudo tee -a /etc/postgresql/17/main/pg_hba.conf"
```

**Note**: Order matters in pg_hba.conf - entries are processed top-to-bottom.

### Step 4: Verify Entry Position

```bash
ssh dereadi@100.112.254.96 "sudo tail -20 /etc/postgresql/17/main/pg_hba.conf"
```

Make sure the Tailscale entries appear before any reject rules.

### Step 5: Reload PostgreSQL

```bash
ssh dereadi@100.112.254.96 "sudo systemctl reload postgresql"
```

Or:
```bash
ssh dereadi@100.112.254.96 "sudo -u postgres psql -c 'SELECT pg_reload_conf();'"
```

### Step 6: Verify Connection Works

From TPM macbook:
```bash
PGPASSWORD=jawaseatlasers2 /opt/homebrew/opt/postgresql@17/bin/psql -h 100.112.254.96 -U claude -d zammad_production -c "SELECT COUNT(*) FROM thermal_memory_archive;"
```

Expected: Returns count (currently 5,200+)

---

## Security Notes

- Only allowing the `claude` user from Tailscale network
- Tailscale provides authentication (only authorized devices on tailnet)
- Using scram-sha-256 for password hashing
- Consider adding specific host entries for known nodes if tighter control needed:
  ```
  host    all    claude    100.116.27.89/32    scram-sha-256   # redfin
  host    all    claude    100.112.254.96/32   scram-sha-256   # bluefin localhost
  host    all    claude    100.100.243.116/32  scram-sha-256   # greenfin
  host    all    claude    100.103.27.106/32   scram-sha-256   # tpm-macbook
  ```

---

## Rollback

If issues occur:
```bash
ssh dereadi@100.112.254.96 "sudo cp /etc/postgresql/17/main/pg_hba.conf.backup-$(date +%Y%m%d) /etc/postgresql/17/main/pg_hba.conf && sudo systemctl reload postgresql"
```

---

## Validation Checklist

- [ ] pg_hba.conf backup created
- [ ] Tailscale entries added
- [ ] PostgreSQL reloaded successfully
- [ ] TPM macbook can connect via Tailscale IP
- [ ] Redfin can connect to bluefin via Tailscale IP
- [ ] Existing local connections still work (192.168.x)

---

## Related

- KB-0017: Infrastructure Audit (identified this issue)
- KB-0021: RASC/CISC (blocked by this)

---

*For Seven Generations*
