# Jr Instruction: AIDE File Integrity Monitoring

**Date**: January 11, 2026
**Priority**: HIGH
**Target Nodes**: redfin, bluefin, greenfin, goldfin
**TPM**: Flying Squirrel (dereadi)
**Council Approval**: ULTRATHINK 7f3a91c2d8e4b5f0

## Problem

No file integrity monitoring exists on Linux nodes. Cannot detect unauthorized changes to system files, configs, or binaries. This is a compliance requirement for VetAssist PII handling.

## Solution

Deploy AIDE (Advanced Intrusion Detection Environment) on all Linux nodes. Establish baselines TONIGHT before silverfin replacement changes the environment.

---

## Installation

### Debian/Ubuntu (bluefin, redfin, greenfin)
```bash
sudo apt install -y aide aide-common

# Initialize the database (takes a few minutes)
sudo aideinit

# The database is created at /var/lib/aide/aide.db.new
# Move to active location
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

### Rocky Linux (goldfin)
```bash
sudo dnf install -y aide

# Initialize
sudo aide --init

# Move database
sudo mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz
```

---

## Configuration

### Custom AIDE config for Cherokee Federation

```bash
# Backup original config
sudo cp /etc/aide/aide.conf /etc/aide/aide.conf.orig

# Add Cherokee-specific rules
sudo tee -a /etc/aide/aide.conf << 'EOF'

# Cherokee AI Federation Custom Rules
# Added: January 11, 2026

# Monitor /ganuda directory
/ganuda CONTENT_EX

# Monitor thermal memory config
/ganuda/config CONTENT_EX

# Monitor scripts
/ganuda/scripts CONTENT_EX

# Exclude frequently changing files
!/ganuda/logs
!/ganuda/backups
!/var/log
!/var/cache
!/tmp
!/run

# High-security monitoring for secrets
/ganuda/config/secrets CONTENT_EX+sha512

# Monitor SSH configs
/etc/ssh CONTENT_EX

# Monitor sudo configs
/etc/sudoers CONTENT_EX
/etc/sudoers.d CONTENT_EX

# Monitor cron
/etc/cron.d CONTENT_EX
/etc/crontab CONTENT_EX
/var/spool/cron CONTENT_EX
EOF
```

---

## Scheduled Checks

### Create daily check script
```bash
sudo tee /ganuda/scripts/aide-daily-check.sh << 'EOF'
#!/bin/bash
# AIDE Daily Integrity Check
# Cherokee AI Federation

HOSTNAME=$(hostname)
DATE=$(date +%Y-%m-%d)
REPORT_DIR="/ganuda/logs/aide"
REPORT_FILE="${REPORT_DIR}/aide-${HOSTNAME}-${DATE}.log"

mkdir -p $REPORT_DIR

echo "=== AIDE Check: $HOSTNAME - $DATE ===" > $REPORT_FILE
echo "" >> $REPORT_FILE

# Run AIDE check
aide --check >> $REPORT_FILE 2>&1
AIDE_EXIT=$?

if [ $AIDE_EXIT -eq 0 ]; then
    echo "STATUS: NO CHANGES DETECTED" >> $REPORT_FILE
elif [ $AIDE_EXIT -eq 1 ]; then
    echo "STATUS: CHANGES DETECTED - REVIEW REQUIRED" >> $REPORT_FILE
    # Could add thermal memory alert here
else
    echo "STATUS: AIDE ERROR (exit code $AIDE_EXIT)" >> $REPORT_FILE
fi

echo "" >> $REPORT_FILE
echo "Report saved to: $REPORT_FILE"
EOF

sudo chmod +x /ganuda/scripts/aide-daily-check.sh
```

### Add to cron
```bash
# Run daily at 3 AM
echo "0 3 * * * root /ganuda/scripts/aide-daily-check.sh" | sudo tee /etc/cron.d/aide-check
```

---

## Node-Specific Considerations

### bluefin (Database)
```bash
# Additional monitoring for PostgreSQL
sudo tee -a /etc/aide/aide.conf << 'EOF'
# PostgreSQL configs
/etc/postgresql CONTENT_EX
/var/lib/postgresql/*/main/pg_hba.conf CONTENT_EX
/var/lib/postgresql/*/main/postgresql.conf CONTENT_EX
EOF
```

### redfin (GPU/Inference)
```bash
# Additional monitoring for vLLM/Gateway
sudo tee -a /etc/aide/aide.conf << 'EOF'
# LLM Gateway configs
/home/dereadi/llm-gateway CONTENT_EX
!/ganuda/models  # Exclude large model files
EOF
```

### goldfin (PII Sanctum)
```bash
# STRICT monitoring - this is the PII node
sudo tee -a /etc/aide/aide.conf << 'EOF'
# STRICT PII NODE MONITORING
/u/postgres CONTENT_EX+sha512
/etc/firewalld CONTENT_EX
# Everything in /ganuda gets hash verification
/ganuda CONTENT_EX+sha512
EOF
```

---

## Baseline Procedure (DO TONIGHT)

1. Install AIDE on all nodes
2. Configure custom rules per node
3. Initialize database (creates baseline)
4. Verify check works: `sudo aide --check`
5. Save baseline hash to thermal memory

```bash
# Get baseline database hash for verification
sha256sum /var/lib/aide/aide.db
# Record this in thermal memory!
```

---

## Updating Baseline After Legitimate Changes

When you make intentional changes:
```bash
# Update the database
sudo aide --update

# Review changes shown
# If acceptable, replace old database
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

---

## Thermal Memory Archive

After baseline established:
```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'AIDE FILE INTEGRITY BASELINES ESTABLISHED - January 11, 2026

  Baselines created on:
  - bluefin: /var/lib/aide/aide.db (sha256: <INSERT HASH>)
  - redfin: /var/lib/aide/aide.db (sha256: <INSERT HASH>)
  - greenfin: /var/lib/aide/aide.db (sha256: <INSERT HASH>)
  - goldfin: /var/lib/aide/aide.db.gz (sha256: <INSERT HASH>)

  Daily checks scheduled at 3 AM.
  Reports written to /ganuda/logs/aide/

  IMPORTANT: Update baselines after intentional changes!

  For Seven Generations.',
  93, 'it_triad_jr',
  ARRAY['aide', 'file-integrity', 'security', 'baseline', 'audit', 'january-2026'],
  'federation'
);
```

---

## Integration with VetAssist Audit

AIDE reports can be cross-referenced with VetAssist audit_log to detect:
- Config changes before/after PII access
- Unauthorized modifications to API code
- Changes to database configs

This supports the auditability requirement for PII handling.

---

For Seven Generations.
