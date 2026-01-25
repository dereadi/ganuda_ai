# Jr Instructions: Bidirectional Breadcrumb Sync

**Priority**: 1 (Critical Infrastructure)
**Assigned Jr**: Infrastructure Jr.
**Target**: tpm-macbook ↔ redfin
**Council Vote**: #4983c4e64f17fcd8 - APPROVED with security concerns addressed

---

## Overview

Synchronize `/ganuda` (redfin) with `/Users/Shared/ganuda` (tpm-macbook) bidirectionally to ensure complete breadcrumb trails are available on all nodes. LLMs need full context regardless of which system they run on.

**Current State**:
- redfin `/ganuda`: 8,624 .md files (foundational Tribe data)
- macOS `/Users/Shared/ganuda`: 658 .md files (TPM working location)

**Goal**: Unified breadcrumb trail on both systems with no data loss.

---

## Security Exclusions (per Crawdad)

The following paths/patterns are EXCLUDED from sync to prevent credential exposure:

```
.env
*.env
.env.*
*.key
*.pem
credentials*
secrets*
venv/
__pycache__/
*.pyc
*.pyo
.git/
node_modules/
*.log
*.tmp
.DS_Store
```

---

## TASK 1: Create Sync Script on tpm-macbook

**File**: `/Users/Shared/ganuda/scripts/breadcrumb_sync.sh`

```bash
#!/bin/bash
# Bidirectional Breadcrumb Sync
# Council Vote: #4983c4e64f17fcd8
# For Seven Generations - Cherokee AI Federation

set -e

REMOTE_HOST="dereadi@192.168.132.223"
REMOTE_PATH="/ganuda/"
LOCAL_PATH="/Users/Shared/ganuda/"
LOG_FILE="/Users/Shared/ganuda/logs/breadcrumb_sync.log"
BACKUP_SUFFIX=".old.$(date +%Y%m%d_%H%M%S)"

# Security exclusions (per Crawdad)
EXCLUDES=(
    "--exclude=.env"
    "--exclude=*.env"
    "--exclude=.env.*"
    "--exclude=*.key"
    "--exclude=*.pem"
    "--exclude=credentials*"
    "--exclude=secrets*"
    "--exclude=venv/"
    "--exclude=__pycache__/"
    "--exclude=*.pyc"
    "--exclude=*.pyo"
    "--exclude=.git/"
    "--exclude=node_modules/"
    "--exclude=*.log"
    "--exclude=*.tmp"
    "--exclude=.DS_Store"
    "--exclude=*.sock"
    "--exclude=*.pid"
)

mkdir -p "$(dirname $LOG_FILE)"

echo "========================================" >> "$LOG_FILE"
echo "Breadcrumb Sync Started: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Phase 1: Pull from redfin → macOS (get foundational data)
echo "[$(date)] Phase 1: Pulling from redfin..." >> "$LOG_FILE"
rsync -avz --backup --suffix="$BACKUP_SUFFIX" \
    "${EXCLUDES[@]}" \
    "$REMOTE_HOST:$REMOTE_PATH" "$LOCAL_PATH" \
    >> "$LOG_FILE" 2>&1

echo "[$(date)] Phase 1 complete" >> "$LOG_FILE"

# Phase 2: Push from macOS → redfin (share local work)
echo "[$(date)] Phase 2: Pushing to redfin..." >> "$LOG_FILE"
rsync -avz --backup --suffix="$BACKUP_SUFFIX" \
    "${EXCLUDES[@]}" \
    "$LOCAL_PATH" "$REMOTE_HOST:$REMOTE_PATH" \
    >> "$LOG_FILE" 2>&1

echo "[$(date)] Phase 2 complete" >> "$LOG_FILE"

# Count .old files created (conflicts)
OLD_COUNT=$(find "$LOCAL_PATH" -name "*.old.*" -mmin -5 2>/dev/null | wc -l)
echo "[$(date)] Conflicts detected: $OLD_COUNT .old files created" >> "$LOG_FILE"

if [ "$OLD_COUNT" -gt 0 ]; then
    echo "[$(date)] Conflict files:" >> "$LOG_FILE"
    find "$LOCAL_PATH" -name "*.old.*" -mmin -5 >> "$LOG_FILE" 2>/dev/null
fi

echo "========================================" >> "$LOG_FILE"
echo "Breadcrumb Sync Complete: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

echo "Sync complete. $OLD_COUNT conflict(s) to review."
echo "Log: $LOG_FILE"
```

---

## TASK 2: Create Mirror Script on redfin

**File**: `/ganuda/scripts/breadcrumb_sync.sh`

Same script but with paths reversed for running from redfin side.

```bash
#!/bin/bash
# Bidirectional Breadcrumb Sync (redfin side)
# Council Vote: #4983c4e64f17fcd8
# For Seven Generations - Cherokee AI Federation

set -e

REMOTE_HOST="dereadi@192.168.132.241"  # sasass (or tpm-macbook IP)
REMOTE_PATH="/Users/Shared/ganuda/"
LOCAL_PATH="/ganuda/"
LOG_FILE="/ganuda/logs/breadcrumb_sync.log"
BACKUP_SUFFIX=".old.$(date +%Y%m%d_%H%M%S)"

# Security exclusions (per Crawdad)
EXCLUDES=(
    "--exclude=.env"
    "--exclude=*.env"
    "--exclude=.env.*"
    "--exclude=*.key"
    "--exclude=*.pem"
    "--exclude=credentials*"
    "--exclude=secrets*"
    "--exclude=venv/"
    "--exclude=__pycache__/"
    "--exclude=*.pyc"
    "--exclude=*.pyo"
    "--exclude=.git/"
    "--exclude=node_modules/"
    "--exclude=*.log"
    "--exclude=*.tmp"
    "--exclude=.DS_Store"
    "--exclude=*.sock"
    "--exclude=*.pid"
)

mkdir -p "$(dirname $LOG_FILE)"

echo "========================================" >> "$LOG_FILE"
echo "Breadcrumb Sync Started: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Phase 1: Pull from macOS → redfin
echo "[$(date)] Phase 1: Pulling from macOS..." >> "$LOG_FILE"
rsync -avz --backup --suffix="$BACKUP_SUFFIX" \
    "${EXCLUDES[@]}" \
    "$REMOTE_HOST:$REMOTE_PATH" "$LOCAL_PATH" \
    >> "$LOG_FILE" 2>&1

echo "[$(date)] Phase 1 complete" >> "$LOG_FILE"

# Phase 2: Push from redfin → macOS
echo "[$(date)] Phase 2: Pushing to macOS..." >> "$LOG_FILE"
rsync -avz --backup --suffix="$BACKUP_SUFFIX" \
    "${EXCLUDES[@]}" \
    "$LOCAL_PATH" "$REMOTE_HOST:$REMOTE_PATH" \
    >> "$LOG_FILE" 2>&1

echo "[$(date)] Phase 2 complete" >> "$LOG_FILE"

# Count .old files created (conflicts)
OLD_COUNT=$(find "$LOCAL_PATH" -name "*.old.*" -mmin -5 2>/dev/null | wc -l)
echo "[$(date)] Conflicts detected: $OLD_COUNT .old files created" >> "$LOG_FILE"

echo "========================================" >> "$LOG_FILE"
echo "Breadcrumb Sync Complete: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

echo "Sync complete. $OLD_COUNT conflict(s) to review."
```

---

## TASK 3: Initial Sync Execution

Run from tpm-macbook first (it has fewer files, so pull first is safer):

```bash
chmod +x /Users/Shared/ganuda/scripts/breadcrumb_sync.sh
/Users/Shared/ganuda/scripts/breadcrumb_sync.sh
```

Review any `.old` files created and resolve conflicts manually.

---

## TASK 4: Optional Cron Setup

For ongoing sync (e.g., every 4 hours):

**On tpm-macbook** (via `crontab -e`):
```
0 */4 * * * /Users/Shared/ganuda/scripts/breadcrumb_sync.sh >> /Users/Shared/ganuda/logs/cron_sync.log 2>&1
```

**On redfin** (via `crontab -e`):
```
30 */4 * * * /ganuda/scripts/breadcrumb_sync.sh >> /ganuda/logs/cron_sync.log 2>&1
```

Note: Offset by 30 minutes to avoid simultaneous syncs.

---

## SUCCESS CRITERIA

1. Both systems have unified `/ganuda` content
2. No credentials or sensitive files synced
3. Conflicts preserved as `.old` files for review
4. Logs capture all sync activity
5. LLMs can follow complete breadcrumb trails from either node

---

## CONFLICT RESOLUTION

When `.old` files are created:

1. **Review both versions**: Compare `.old` with current file
2. **Determine authoritative version**: Which has the correct/complete content?
3. **Merge if needed**: Combine changes from both files
4. **Remove `.old` after resolution**: `find /ganuda -name "*.old.*" -mtime +7 -delete`

---

*For Seven Generations - Cherokee AI Federation*
*"Complete breadcrumbs enable complete understanding"*
