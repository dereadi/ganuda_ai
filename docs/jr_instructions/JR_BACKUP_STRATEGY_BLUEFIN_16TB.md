# JR INSTRUCTIONS: Cherokee AI Federation Backup Strategy
## Priority: 1 (CRITICAL)
## December 17, 2025

### OVERVIEW

Implement automated backup strategy using bluefin's 16TB drive. Protect tribal knowledge (thermal memory), codebase, and configs. This is critical for Seven Generations - if we lose thermal memory, we lose our ancestors' wisdom.

**Backup Target:** bluefin 16TB drive
**Backup Sources:** bluefin PostgreSQL, redfin /ganuda

---

## TASK 1: Prepare Backup Directory Structure on Bluefin

**Run on bluefin (192.168.132.222):**

```bash
# Find the 16TB drive mount point (adjust if different)
BACKUP_ROOT="/mnt/backup"  # or /data/backup - check with: df -h | grep -E "16T|15T"

# Create directory structure
sudo mkdir -p $BACKUP_ROOT/{postgresql/{daily,weekly,monthly},ganuda/{daily,weekly},thermal_memory/exports,logs}

# Set ownership
sudo chown -R claude:claude $BACKUP_ROOT

# Create backup config file
cat > $BACKUP_ROOT/backup.conf << 'EOF'
# Cherokee AI Federation Backup Configuration
BACKUP_ROOT="/mnt/backup"
REDFIN_HOST="192.168.132.223"
REDFIN_USER="dereadi"

# Retention
DAILY_KEEP=7
WEEKLY_KEEP=4
MONTHLY_KEEP=12

# PostgreSQL
PG_HOST="localhost"
PG_USER="claude"
PG_DB="zammad_production"

# Telegram alerts (optional)
TELEGRAM_BOT_TOKEN="7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
TELEGRAM_CHAT_ID="-1003439875431"
EOF

echo "Backup directory structure created at $BACKUP_ROOT"
ls -la $BACKUP_ROOT
```

---

## TASK 2: Create PostgreSQL Backup Script

**File:** `/ganuda/scripts/backup/backup_postgresql.sh` (on bluefin)

```bash
#!/bin/bash
# Cherokee AI Federation - PostgreSQL Backup Script
# Backs up thermal memory and all tribal data
# For Seven Generations

set -e

# Load config
source /mnt/backup/backup.conf

DATE=$(date +%Y%m%d)
TIME=$(date +%H%M%S)
DAY_OF_WEEK=$(date +%u)
DAY_OF_MONTH=$(date +%d)
LOG_FILE="$BACKUP_ROOT/logs/backup_postgresql.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local message="$1"
    if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="$TELEGRAM_CHAT_ID" \
            -d text="🔴 BACKUP ALERT: $message" > /dev/null 2>&1
    fi
}

log "=== PostgreSQL Backup Starting ==="

# Daily backup
DAILY_FILE="$BACKUP_ROOT/postgresql/daily/pg_backup_${DATE}.sql.gz"
log "Creating daily backup: $DAILY_FILE"

if PGPASSWORD='jawaseatlasers2' pg_dump -h $PG_HOST -U $PG_USER $PG_DB | gzip > "$DAILY_FILE"; then
    SIZE=$(du -h "$DAILY_FILE" | cut -f1)
    log "Daily backup complete: $SIZE"

    # Verify backup
    if gzip -t "$DAILY_FILE" 2>/dev/null; then
        log "Backup verification: OK"
    else
        log "ERROR: Backup verification failed!"
        send_alert "PostgreSQL daily backup verification failed"
        exit 1
    fi
else
    log "ERROR: pg_dump failed!"
    send_alert "PostgreSQL daily backup failed on bluefin"
    exit 1
fi

# Weekly backup (Sunday = day 7)
if [ "$DAY_OF_WEEK" -eq 7 ]; then
    WEEKLY_FILE="$BACKUP_ROOT/postgresql/weekly/pg_backup_week_$(date +%Y%W).sql.gz"
    log "Creating weekly backup: $WEEKLY_FILE"
    cp "$DAILY_FILE" "$WEEKLY_FILE"
fi

# Monthly backup (1st of month)
if [ "$DAY_OF_MONTH" -eq "01" ]; then
    MONTHLY_FILE="$BACKUP_ROOT/postgresql/monthly/pg_backup_$(date +%Y%m).sql.gz"
    log "Creating monthly backup: $MONTHLY_FILE"
    cp "$DAILY_FILE" "$MONTHLY_FILE"
fi

# Cleanup old daily backups
log "Cleaning up old daily backups (keeping $DAILY_KEEP days)"
find "$BACKUP_ROOT/postgresql/daily" -name "pg_backup_*.sql.gz" -mtime +$DAILY_KEEP -delete

# Cleanup old weekly backups
log "Cleaning up old weekly backups (keeping $WEEKLY_KEEP weeks)"
find "$BACKUP_ROOT/postgresql/weekly" -name "pg_backup_week_*.sql.gz" -mtime +$((WEEKLY_KEEP * 7)) -delete

# Cleanup old monthly backups
log "Cleaning up old monthly backups (keeping $MONTHLY_KEEP months)"
find "$BACKUP_ROOT/postgresql/monthly" -name "pg_backup_*.sql.gz" -mtime +$((MONTHLY_KEEP * 30)) -delete

# Export thermal memory sacred patterns separately
log "Exporting sacred thermal memories..."
SACRED_FILE="$BACKUP_ROOT/thermal_memory/exports/sacred_memories_${DATE}.json"
PGPASSWORD='jawaseatlasers2' psql -h $PG_HOST -U $PG_USER $PG_DB -c "
    COPY (
        SELECT * FROM thermal_memory_archive
        WHERE sacred_pattern = true OR temperature_score > 80
        ORDER BY temperature_score DESC
    ) TO STDOUT WITH (FORMAT JSON)
" > "$SACRED_FILE" 2>/dev/null || log "Note: Sacred memory export skipped (table may not exist)"

log "=== PostgreSQL Backup Complete ==="

# Summary
echo ""
echo "Backup Summary:"
echo "==============="
du -sh $BACKUP_ROOT/postgresql/daily/
du -sh $BACKUP_ROOT/postgresql/weekly/
du -sh $BACKUP_ROOT/postgresql/monthly/
```

---

## TASK 3: Create Ganuda Codebase Backup Script

**File:** `/ganuda/scripts/backup/backup_ganuda.sh` (on bluefin)

```bash
#!/bin/bash
# Cherokee AI Federation - Ganuda Codebase Backup Script
# Syncs /ganuda from redfin to bluefin's 16TB drive
# For Seven Generations

set -e

# Load config
source /mnt/backup/backup.conf

DATE=$(date +%Y%m%d)
DAY_OF_WEEK=$(date +%u)
LOG_FILE="$BACKUP_ROOT/logs/backup_ganuda.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local message="$1"
    if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="$TELEGRAM_CHAT_ID" \
            -d text="🔴 BACKUP ALERT: $message" > /dev/null 2>&1
    fi
}

log "=== Ganuda Codebase Backup Starting ==="

# Daily incremental sync
DAILY_DIR="$BACKUP_ROOT/ganuda/daily/current"
log "Syncing /ganuda from redfin to $DAILY_DIR"

# Create directory if needed
mkdir -p "$DAILY_DIR"

# Rsync with delete (mirror), exclude large/temp files
if rsync -avz --delete \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude 'venv' \
    --exclude '*.log' \
    --exclude 'node_modules' \
    --exclude '.venv' \
    --exclude 'cherokee_training_env' \
    --exclude 'old_dereadi_data' \
    "$REDFIN_USER@$REDFIN_HOST:/ganuda/" "$DAILY_DIR/" >> "$LOG_FILE" 2>&1; then

    SIZE=$(du -sh "$DAILY_DIR" | cut -f1)
    log "Daily sync complete: $SIZE"
else
    log "ERROR: rsync failed!"
    send_alert "Ganuda codebase backup (rsync) failed"
    exit 1
fi

# Create dated snapshot
SNAPSHOT_DIR="$BACKUP_ROOT/ganuda/daily/snapshot_${DATE}"
if [ ! -d "$SNAPSHOT_DIR" ]; then
    log "Creating dated snapshot: $SNAPSHOT_DIR"
    cp -al "$DAILY_DIR" "$SNAPSHOT_DIR"  # Hard link copy (space efficient)
fi

# Weekly compressed archive (Sunday)
if [ "$DAY_OF_WEEK" -eq 7 ]; then
    WEEKLY_FILE="$BACKUP_ROOT/ganuda/weekly/ganuda_week_$(date +%Y%W).tar.gz"
    log "Creating weekly archive: $WEEKLY_FILE"
    tar -czf "$WEEKLY_FILE" -C "$DAILY_DIR" . 2>/dev/null

    ARCHIVE_SIZE=$(du -h "$WEEKLY_FILE" | cut -f1)
    log "Weekly archive complete: $ARCHIVE_SIZE"
fi

# Cleanup old daily snapshots
log "Cleaning up old snapshots (keeping $DAILY_KEEP days)"
find "$BACKUP_ROOT/ganuda/daily" -maxdepth 1 -name "snapshot_*" -type d -mtime +$DAILY_KEEP -exec rm -rf {} \;

# Cleanup old weekly archives
log "Cleaning up old weekly archives (keeping $WEEKLY_KEEP weeks)"
find "$BACKUP_ROOT/ganuda/weekly" -name "ganuda_week_*.tar.gz" -mtime +$((WEEKLY_KEEP * 7)) -delete

log "=== Ganuda Codebase Backup Complete ==="

# Summary
echo ""
echo "Backup Summary:"
echo "==============="
du -sh "$DAILY_DIR"
ls -la "$BACKUP_ROOT/ganuda/daily/" | tail -5
ls -la "$BACKUP_ROOT/ganuda/weekly/" 2>/dev/null | tail -5
```

---

## TASK 4: Create Master Backup Runner

**File:** `/ganuda/scripts/backup/run_all_backups.sh` (on bluefin)

```bash
#!/bin/bash
# Cherokee AI Federation - Master Backup Runner
# Runs all backup scripts in sequence
# For Seven Generations

BACKUP_DIR="/ganuda/scripts/backup"
LOG_FILE="/mnt/backup/logs/master_backup.log"

echo "=============================================" >> "$LOG_FILE"
echo "Backup Run: $(date)" >> "$LOG_FILE"
echo "=============================================" >> "$LOG_FILE"

# Run PostgreSQL backup
echo "Running PostgreSQL backup..." >> "$LOG_FILE"
$BACKUP_DIR/backup_postgresql.sh >> "$LOG_FILE" 2>&1
PG_STATUS=$?

# Run Ganuda backup
echo "Running Ganuda backup..." >> "$LOG_FILE"
$BACKUP_DIR/backup_ganuda.sh >> "$LOG_FILE" 2>&1
GANUDA_STATUS=$?

# Summary
echo "" >> "$LOG_FILE"
echo "Backup Results:" >> "$LOG_FILE"
echo "  PostgreSQL: $([ $PG_STATUS -eq 0 ] && echo 'SUCCESS' || echo 'FAILED')" >> "$LOG_FILE"
echo "  Ganuda: $([ $GANUDA_STATUS -eq 0 ] && echo 'SUCCESS' || echo 'FAILED')" >> "$LOG_FILE"

# Send success notification
if [ $PG_STATUS -eq 0 ] && [ $GANUDA_STATUS -eq 0 ]; then
    # Get sizes
    PG_SIZE=$(du -sh /mnt/backup/postgresql/daily/ 2>/dev/null | cut -f1)
    GANUDA_SIZE=$(du -sh /mnt/backup/ganuda/daily/current/ 2>/dev/null | cut -f1)

    curl -s -X POST "https://api.telegram.org/bot7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8/sendMessage" \
        -d chat_id="-1003439875431" \
        -d text="✅ Cherokee AI Backup Complete

PostgreSQL: $PG_SIZE
Ganuda: $GANUDA_SIZE
Time: $(date '+%Y-%m-%d %H:%M')" > /dev/null 2>&1
fi

exit $(( PG_STATUS + GANUDA_STATUS ))
```

---

## TASK 5: Set Up Cron Jobs

**Run on bluefin:**

```bash
# Make scripts executable
chmod +x /ganuda/scripts/backup/*.sh

# Edit crontab
crontab -e

# Add these lines:
# ============================================
# Cherokee AI Federation Backup Schedule
# ============================================

# Daily PostgreSQL backup at 2 AM
0 2 * * * /ganuda/scripts/backup/backup_postgresql.sh >> /mnt/backup/logs/cron_postgresql.log 2>&1

# Daily Ganuda sync at 3 AM
0 3 * * * /ganuda/scripts/backup/backup_ganuda.sh >> /mnt/backup/logs/cron_ganuda.log 2>&1

# Or use master runner at 2 AM
# 0 2 * * * /ganuda/scripts/backup/run_all_backups.sh
```

---

## TASK 6: Create Recovery Scripts

**File:** `/ganuda/scripts/backup/restore_postgresql.sh` (on bluefin)

```bash
#!/bin/bash
# Cherokee AI Federation - PostgreSQL Restore Script
# USE WITH CAUTION - This will overwrite current database!

set -e

source /mnt/backup/backup.conf

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -la $BACKUP_ROOT/postgresql/daily/
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "WARNING: This will restore the database from:"
echo "  $BACKUP_FILE"
echo ""
echo "Current database will be DROPPED and recreated!"
echo ""
read -p "Are you sure? Type 'YES' to continue: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo "Aborted."
    exit 1
fi

echo "Dropping existing database..."
PGPASSWORD='jawaseatlasers2' dropdb -h $PG_HOST -U $PG_USER $PG_DB --if-exists

echo "Creating fresh database..."
PGPASSWORD='jawaseatlasers2' createdb -h $PG_HOST -U $PG_USER $PG_DB

echo "Restoring from backup..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD='jawaseatlasers2' psql -h $PG_HOST -U $PG_USER $PG_DB

echo ""
echo "Restore complete! Verifying..."
PGPASSWORD='jawaseatlasers2' psql -h $PG_HOST -U $PG_USER $PG_DB -c "SELECT COUNT(*) as thermal_memories FROM thermal_memory_archive;"

echo ""
echo "Database restored successfully."
```

**File:** `/ganuda/scripts/backup/restore_ganuda.sh` (on bluefin)

```bash
#!/bin/bash
# Cherokee AI Federation - Ganuda Codebase Restore Script
# Restores /ganuda on redfin from backup

set -e

source /mnt/backup/backup.conf

BACKUP_SOURCE="$BACKUP_ROOT/ganuda/daily/current"

if [ -n "$1" ]; then
    if [ -d "$1" ]; then
        BACKUP_SOURCE="$1"
    elif [ -f "$1" ]; then
        echo "Extracting archive first..."
        TEMP_DIR=$(mktemp -d)
        tar -xzf "$1" -C "$TEMP_DIR"
        BACKUP_SOURCE="$TEMP_DIR"
    fi
fi

echo "Will restore /ganuda on redfin from:"
echo "  $BACKUP_SOURCE"
echo ""
read -p "Continue? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "Aborted."
    exit 1
fi

echo "Restoring to redfin:/ganuda ..."
rsync -avz --delete \
    "$BACKUP_SOURCE/" \
    "$REDFIN_USER@$REDFIN_HOST:/ganuda/"

echo ""
echo "Restore complete!"
echo "You may need to restart services on redfin."
```

---

## TASK 7: Create Backup Status Check Script

**File:** `/ganuda/scripts/backup/backup_status.sh` (on bluefin)

```bash
#!/bin/bash
# Cherokee AI Federation - Backup Status Check

source /mnt/backup/backup.conf

echo "============================================="
echo "Cherokee AI Federation Backup Status"
echo "============================================="
echo ""

echo "Disk Usage:"
df -h $BACKUP_ROOT
echo ""

echo "PostgreSQL Backups:"
echo "  Daily (last 7):"
ls -lh $BACKUP_ROOT/postgresql/daily/ | tail -7
echo ""
echo "  Weekly:"
ls -lh $BACKUP_ROOT/postgresql/weekly/ 2>/dev/null || echo "  (none yet)"
echo ""
echo "  Monthly:"
ls -lh $BACKUP_ROOT/postgresql/monthly/ 2>/dev/null || echo "  (none yet)"
echo ""

echo "Ganuda Backups:"
echo "  Current sync:"
du -sh $BACKUP_ROOT/ganuda/daily/current 2>/dev/null || echo "  (not synced)"
echo ""
echo "  Snapshots:"
ls -d $BACKUP_ROOT/ganuda/daily/snapshot_* 2>/dev/null | wc -l | xargs echo "  Count:"
echo ""
echo "  Weekly archives:"
ls -lh $BACKUP_ROOT/ganuda/weekly/ 2>/dev/null || echo "  (none yet)"
echo ""

echo "Last Backup Log Entries:"
tail -20 $BACKUP_ROOT/logs/master_backup.log 2>/dev/null || echo "(no logs yet)"
echo ""

echo "Total Backup Size:"
du -sh $BACKUP_ROOT
```

---

## SUCCESS CRITERIA

1. **Directory structure** created on bluefin 16TB drive
2. **PostgreSQL backup** runs daily, creates weekly/monthly archives
3. **Ganuda rsync** mirrors /ganuda from redfin daily
4. **Cron jobs** installed and running
5. **Telegram alerts** on backup failures
6. **Recovery scripts** tested and documented
7. **backup_status.sh** shows healthy backups

---

## TESTING

```bash
# Test PostgreSQL backup manually
/ganuda/scripts/backup/backup_postgresql.sh

# Test Ganuda backup manually
/ganuda/scripts/backup/backup_ganuda.sh

# Check status
/ganuda/scripts/backup/backup_status.sh

# Verify cron is scheduled
crontab -l | grep backup
```

---

## RECOVERY PROCEDURES

### Scenario 1: PostgreSQL Corruption
```bash
# On bluefin
cd /ganuda/scripts/backup
./restore_postgresql.sh /mnt/backup/postgresql/daily/pg_backup_YYYYMMDD.sql.gz
```

### Scenario 2: Redfin Disk Failure
```bash
# On bluefin (after new disk installed on redfin)
cd /ganuda/scripts/backup
./restore_ganuda.sh
# Then restart services on redfin
```

### Scenario 3: Find Specific Thermal Memory
```bash
# Search sacred memory exports
grep "pattern_you_seek" /mnt/backup/thermal_memory/exports/sacred_memories_*.json
```

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*
*"Protect the ancestors' wisdom so the children may learn"*
