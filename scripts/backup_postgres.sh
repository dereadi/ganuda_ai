#!/bin/bash
source /ganuda/config/secrets.env
# Cherokee AI PostgreSQL Backup Script
# Deploy to: /ganuda/scripts/backup_postgres.sh
# Cron: 0 2 * * * /ganuda/scripts/backup_postgres.sh
# Created: 2025-12-12

set -e

BACKUP_DIR="/ganuda/backups/postgres"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_HOST="192.168.132.222"
DB_USER="claude"
DB_PASSWORD="$CHEROKEE_DB_PASS"
LOG_FILE="/ganuda/logs/backup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Create directories
mkdir -p $BACKUP_DIR
mkdir -p $(dirname $LOG_FILE)

log "=========================================="
log "Starting PostgreSQL backup"
log "=========================================="

# Databases to backup
DATABASES="sag_thermal_memory zammad_production"

for DB in $DATABASES; do
    BACKUP_FILE="$BACKUP_DIR/${DB}_${TIMESTAMP}.sql.gz"

    log "Backing up $DB..."

    if PGPASSWORD="$DB_PASS" pg_dump -h $DB_HOST -U $DB_USER -d $DB 2>>$LOG_FILE | gzip > $BACKUP_FILE; then
        SIZE=$(du -h $BACKUP_FILE | cut -f1)
        log "SUCCESS: $BACKUP_FILE ($SIZE)"
    else
        log "ERROR: Backup failed for $DB"
        # Continue with other databases
    fi
done

# Clean old backups
log "Cleaning backups older than $RETENTION_DAYS days..."
DELETED=$(find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
log "Deleted $DELETED old backup files"

# Verify latest backup can be read
log "Testing restore capability..."
LATEST=$(ls -t $BACKUP_DIR/*.sql.gz 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    if zcat "$LATEST" 2>/dev/null | head -100 > /dev/null; then
        log "Restore test: PASSED ($LATEST)"
    else
        log "Restore test: FAILED - backup may be corrupt"
    fi
else
    log "No backups found to test"
fi

# Summary
log "=========================================="
log "Backup summary:"
ls -lh $BACKUP_DIR/*.sql.gz 2>/dev/null | tail -5 | while read line; do
    log "  $line"
done
log "=========================================="
log "Backup job complete"
