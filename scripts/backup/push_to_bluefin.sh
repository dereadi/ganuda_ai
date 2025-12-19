#\!/bin/bash
# Cherokee AI Federation - Push Ganuda to Bluefin Backup
# Run from redfin to push /ganuda to bluefin 16TB drive
# For Seven Generations

set -e

BACKUP_ROOT="/ewe/cherokee_backups"
BLUEFIN_HOST="192.168.132.222"
BLUEFIN_USER="dereadi"
DATE=$(date +%Y%m%d)
DAY_OF_WEEK=$(date +%u)
LOG_FILE="/ganuda/logs/backup_push.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

mkdir -p /ganuda/logs

log "=== Pushing Ganuda to Bluefin Backup ==="

DAILY_DIR="$BACKUP_ROOT/ganuda/daily/current"

# Rsync push to bluefin
if rsync -avz --delete \
    --exclude "__pycache__" \
    --exclude "*.pyc" \
    --exclude ".git" \
    --exclude "venv" \
    --exclude "*.log" \
    --exclude "node_modules" \
    --exclude ".venv" \
    --exclude "cherokee_training_env" \
    --exclude "old_dereadi_data" \
    --exclude "*.log.old*" \
    /ganuda/ "$BLUEFIN_USER@$BLUEFIN_HOST:$DAILY_DIR/" 2>&1; then

    log "Push complete\!"
    
    # Create dated snapshot on bluefin
    ssh "$BLUEFIN_USER@$BLUEFIN_HOST" "
        SNAPSHOT_DIR=$BACKUP_ROOT/ganuda/daily/snapshot_${DATE}
        if [ \! -d \"\$SNAPSHOT_DIR\" ]; then
            cp -al $DAILY_DIR \$SNAPSHOT_DIR
            echo Snapshot created: $SNAPSHOT_DIR
        fi
    "
    
    # Weekly archive on Sunday
    if [ "$DAY_OF_WEEK" -eq 7 ]; then
        log "Creating weekly archive on bluefin..."
        ssh "$BLUEFIN_USER@$BLUEFIN_HOST" "
            tar -czf $BACKUP_ROOT/ganuda/weekly/ganuda_week_\$(date +%Y%W).tar.gz -C $DAILY_DIR .
        "
    fi
else
    log "ERROR: rsync push failed\!"
    exit 1
fi

log "=== Push Complete ==="
