#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Phoenix Backup — Cherokee AI Federation
# Runs on bluefin (DB host). Dumps critical tables, compresses,
# retains 7 days locally + pushes to redfin for geographic redundancy.
#
# The bigger the river, the bigger the drought.
# This script is the dam.
#
# Cron: 0 3 * * * /ganuda/scripts/phoenix_backup.sh
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

# Config
DB_NAME="zammad_production"
DB_USER="claude"
DB_HOST="localhost"
SECRETS_FILE="/ganuda/config/secrets.env"
LOCAL_BACKUP_DIR="/ganuda/backups/postgres"
REMOTE_BACKUP_DIR="/ganuda/backups/postgres"
REMOTE_HOST="redfin"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="phoenix_${TIMESTAMP}.sql.gz"
LOG_FILE="/ganuda/backups/postgres/phoenix_backup.log"

# Get password
DB_PASS=$(grep CHEROKEE_DB_PASS "$SECRETS_FILE" | cut -d= -f2)
export PGPASSWORD="$DB_PASS"

mkdir -p "$LOCAL_BACKUP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Phoenix backup starting..."

# Full database dump — compressed
log "Dumping ${DB_NAME}..."
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    --no-owner --no-privileges \
    --format=plain \
    | gzip -9 > "${LOCAL_BACKUP_DIR}/${BACKUP_FILE}"

BACKUP_SIZE=$(du -h "${LOCAL_BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
log "Local backup complete: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Row counts for verification
COUNTS=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
SELECT json_build_object(
    'thermal_memories', (SELECT COUNT(*) FROM thermal_memory_archive),
    'council_votes', (SELECT COUNT(*) FROM council_votes),
    'jr_tasks', (SELECT COUNT(*) FROM jr_work_queue),
    'kanban', (SELECT COUNT(*) FROM duyuktv_tickets),
    'sacred', (SELECT COUNT(*) FROM thermal_memory_archive WHERE sacred_pattern = true),
    'timestamp', NOW()::text
);")
echo "$COUNTS" > "${LOCAL_BACKUP_DIR}/phoenix_${TIMESTAMP}_manifest.json"
log "Manifest: ${COUNTS}"

# Push to redfin for geographic redundancy
# Note: bluefin→redfin direct SSH may fail. Try direct first, then via IP.
log "Pushing to ${REMOTE_HOST}:${REMOTE_BACKUP_DIR}..."
scp -o ConnectTimeout=15 -q "${LOCAL_BACKUP_DIR}/${BACKUP_FILE}" "${REMOTE_HOST}:${REMOTE_BACKUP_DIR}/${BACKUP_FILE}" 2>/dev/null && \
    scp -o ConnectTimeout=15 -q "${LOCAL_BACKUP_DIR}/phoenix_${TIMESTAMP}_manifest.json" "${REMOTE_HOST}:${REMOTE_BACKUP_DIR}/phoenix_${TIMESTAMP}_manifest.json" 2>/dev/null && \
    log "Remote push complete." || {
    # Fallback: try by IP
    log "Direct push failed, trying 192.168.132.223..."
    scp -o ConnectTimeout=15 -q "${LOCAL_BACKUP_DIR}/${BACKUP_FILE}" "192.168.132.223:${REMOTE_BACKUP_DIR}/${BACKUP_FILE}" 2>/dev/null && \
        scp -o ConnectTimeout=15 -q "${LOCAL_BACKUP_DIR}/phoenix_${TIMESTAMP}_manifest.json" "192.168.132.223:${REMOTE_BACKUP_DIR}/phoenix_${TIMESTAMP}_manifest.json" 2>/dev/null && \
        log "Remote push complete (via IP)." || \
        log "WARNING: Remote push to ${REMOTE_HOST} FAILED. Local backup still valid. Run manually: scp bluefin:/ganuda/backups/postgres/${BACKUP_FILE} redfin:/ganuda/backups/postgres/"
}

# Rotate old backups — keep RETENTION_DAYS days
log "Rotating backups older than ${RETENTION_DAYS} days..."
find "$LOCAL_BACKUP_DIR" -name "phoenix_*.sql.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null
find "$LOCAL_BACKUP_DIR" -name "phoenix_*_manifest.json" -mtime +${RETENTION_DAYS} -delete 2>/dev/null
# Rotate on remote too
ssh "$REMOTE_HOST" "find ${REMOTE_BACKUP_DIR} -name 'phoenix_*.sql.gz' -mtime +${RETENTION_DAYS} -delete 2>/dev/null; find ${REMOTE_BACKUP_DIR} -name 'phoenix_*_manifest.json' -mtime +${RETENTION_DAYS} -delete 2>/dev/null" 2>/dev/null || true

# Count remaining backups
LOCAL_COUNT=$(ls -1 "${LOCAL_BACKUP_DIR}"/phoenix_*.sql.gz 2>/dev/null | wc -l)
log "Backup complete. ${LOCAL_COUNT} local backups retained."

unset PGPASSWORD
log "Phoenix backup finished."
