#!/usr/bin/env bash
#
# Incident Evidence Collection Script
# Collects system state, logs, database info, and network state.
# All evidence is hashed for integrity verification.
#
# Usage: ./collect_incident_evidence.sh <incident_id>
#
# Created: 2026-02-02

set -euo pipefail

# --- Configuration ---
EVIDENCE_BASE="/ganuda/security/evidence"
LOG_SOURCES=(
    "/var/log/syslog"
    "/var/log/auth.log"
    "/var/log/postgresql"
    "/ganuda/logs/security"
    "/ganuda/logs"
)
DB_NAME="cherokee"
DB_USER="claude"
DB_HOST="localhost"
DB_PORT="5432"

# --- Argument validation ---
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <incident_id>"
    echo ""
    echo "Collects forensic evidence for a security incident."
    echo ""
    echo "Arguments:"
    echo "  incident_id   Unique identifier for the incident (e.g., INC-2026-001)"
    echo ""
    echo "Evidence is stored in: ${EVIDENCE_BASE}/incident_<incident_id>/"
    exit 1
fi

INCIDENT_ID="$1"
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
EVIDENCE_DIR="${EVIDENCE_BASE}/incident_${INCIDENT_ID}"
MANIFEST="${EVIDENCE_DIR}/manifest.sha256"

# --- Prevent overwriting existing evidence ---
if [[ -d "${EVIDENCE_DIR}" ]]; then
    echo "[WARNING] Evidence directory already exists: ${EVIDENCE_DIR}"
    echo "          Appending to existing evidence with timestamp: ${TIMESTAMP}"
fi

mkdir -p "${EVIDENCE_DIR}"

echo "=============================================="
echo " Incident Evidence Collection"
echo " Incident ID: ${INCIDENT_ID}"
echo " Timestamp:   ${TIMESTAMP}"
echo " Output:      ${EVIDENCE_DIR}"
echo "=============================================="
echo ""

# --- Helper function: hash a file and append to manifest ---
hash_file() {
    local filepath="$1"
    if [[ -f "${filepath}" ]]; then
        sha256sum "${filepath}" >> "${MANIFEST}"
    fi
}

# --- 1. System State ---
echo "[1/6] Collecting system state..."
ps auxf > "${EVIDENCE_DIR}/processes_${TIMESTAMP}.txt" 2>/dev/null || true
hash_file "${EVIDENCE_DIR}/processes_${TIMESTAMP}.txt"

uptime > "${EVIDENCE_DIR}/uptime_${TIMESTAMP}.txt" 2>/dev/null || true
hash_file "${EVIDENCE_DIR}/uptime_${TIMESTAMP}.txt"

uname -a > "${EVIDENCE_DIR}/uname_${TIMESTAMP}.txt" 2>/dev/null || true
hash_file "${EVIDENCE_DIR}/uname_${TIMESTAMP}.txt"

who > "${EVIDENCE_DIR}/logged_in_users_${TIMESTAMP}.txt" 2>/dev/null || true
hash_file "${EVIDENCE_DIR}/logged_in_users_${TIMESTAMP}.txt"

last -50 > "${EVIDENCE_DIR}/recent_logins_${TIMESTAMP}.txt" 2>/dev/null || true
hash_file "${EVIDENCE_DIR}/recent_logins_${TIMESTAMP}.txt"

systemctl list-units --type=service --state=running > "${EVIDENCE_DIR}/running_services_${TIMESTAMP}.txt" 2>/dev/null || true
hash_file "${EVIDENCE_DIR}/running_services_${TIMESTAMP}.txt"

echo "  System state collected."

# --- 2. Network State ---
echo "[2/6] Collecting network state..."
ss -tulnp > "${EVIDENCE_DIR}/listening_sockets_${TIMESTAMP}.txt" 2>/dev/null || true
hash_file "${EVIDENCE_DIR}/listening_sockets_${TIMESTAMP}.txt"

ss -anp > "${EVIDENCE_DIR}/all_connections_${TIMESTAMP}.txt" 2>/dev/null || true
hash_file "${EVIDENCE_DIR}/all_connections_${TIMESTAMP}.txt"

ip addr > "${EVIDENCE_DIR}/ip_addresses_${TIMESTAMP}.txt" 2>/dev/null || true
hash_file "${EVIDENCE_DIR}/ip_addresses_${TIMESTAMP}.txt"

ip route > "${EVIDENCE_DIR}/routes_${TIMESTAMP}.txt" 2>/dev/null || true
hash_file "${EVIDENCE_DIR}/routes_${TIMESTAMP}.txt"

nft list ruleset > "${EVIDENCE_DIR}/firewall_rules_${TIMESTAMP}.txt" 2>/dev/null || true
hash_file "${EVIDENCE_DIR}/firewall_rules_${TIMESTAMP}.txt"

echo "  Network state collected."

# --- 3. System Logs ---
echo "[3/6] Collecting system logs..."
LOGS_DIR="${EVIDENCE_DIR}/logs_${TIMESTAMP}"
mkdir -p "${LOGS_DIR}"

for log_source in "${LOG_SOURCES[@]}"; do
    if [[ -e "${log_source}" ]]; then
        src_name=$(echo "${log_source}" | tr '/' '_' | sed 's/^_//')
        if [[ -d "${log_source}" ]]; then
            # Copy directory contents (only files modified in last 24h)
            find "${log_source}" -maxdepth 2 -type f -mtime -1 -exec cp --parents {} "${LOGS_DIR}/" \; 2>/dev/null || true
        else
            cp "${log_source}" "${LOGS_DIR}/${src_name}" 2>/dev/null || true
        fi
    fi
done

# Hash all collected logs
find "${LOGS_DIR}" -type f -exec sha256sum {} \; >> "${MANIFEST}" 2>/dev/null || true
echo "  System logs collected."

# --- 4. Database State ---
echo "[4/6] Collecting database state..."
DB_DIR="${EVIDENCE_DIR}/database_${TIMESTAMP}"
mkdir -p "${DB_DIR}"

# Active connections
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c \
    "SELECT pid, usename, application_name, client_addr, state, query_start, query FROM pg_stat_activity;" \
    > "${DB_DIR}/pg_stat_activity.txt" 2>/dev/null || echo "  [WARN] Could not query pg_stat_activity"
hash_file "${DB_DIR}/pg_stat_activity.txt"

# Recent execution audit entries
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c \
    "SELECT * FROM execution_audit_log ORDER BY created_at DESC LIMIT 100;" \
    > "${DB_DIR}/recent_audit_log.txt" 2>/dev/null || echo "  [WARN] Could not query execution_audit_log"
hash_file "${DB_DIR}/recent_audit_log.txt"

# Recent queue entries
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c \
    "SELECT * FROM jr_task_queue ORDER BY created_at DESC LIMIT 100;" \
    > "${DB_DIR}/recent_queue_entries.txt" 2>/dev/null || echo "  [WARN] Could not query jr_task_queue"
hash_file "${DB_DIR}/recent_queue_entries.txt"

# Recent thermal memories
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c \
    "SELECT id, source, created_at, LEFT(content, 200) as content_preview FROM thermal_memories ORDER BY created_at DESC LIMIT 100;" \
    > "${DB_DIR}/recent_thermal_memories.txt" 2>/dev/null || echo "  [WARN] Could not query thermal_memories"
hash_file "${DB_DIR}/recent_thermal_memories.txt"

# Database size and table stats
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c \
    "SELECT schemaname, relname, n_live_tup, last_autovacuum, last_autoanalyze FROM pg_stat_user_tables ORDER BY n_live_tup DESC;" \
    > "${DB_DIR}/table_stats.txt" 2>/dev/null || echo "  [WARN] Could not query table stats"
hash_file "${DB_DIR}/table_stats.txt"

echo "  Database state collected."

# --- 5. Application State ---
echo "[5/6] Collecting application state..."
APP_DIR="${EVIDENCE_DIR}/application_${TIMESTAMP}"
mkdir -p "${APP_DIR}"

# Git state
cd /ganuda && git log --oneline -20 > "${APP_DIR}/recent_commits.txt" 2>/dev/null || true
hash_file "${APP_DIR}/recent_commits.txt"

cd /ganuda && git status > "${APP_DIR}/git_status.txt" 2>/dev/null || true
hash_file "${APP_DIR}/git_status.txt"

cd /ganuda && git diff > "${APP_DIR}/uncommitted_changes.diff" 2>/dev/null || true
hash_file "${APP_DIR}/uncommitted_changes.diff"

# Sanctuary state check
if [[ -f /tmp/jr_executor_paused ]]; then
    echo "SANCTUARY STATE ACTIVE" > "${APP_DIR}/sanctuary_state.txt"
else
    echo "SANCTUARY STATE INACTIVE" > "${APP_DIR}/sanctuary_state.txt"
fi
hash_file "${APP_DIR}/sanctuary_state.txt"

# Cron jobs
crontab -l > "${APP_DIR}/crontab.txt" 2>/dev/null || echo "No crontab" > "${APP_DIR}/crontab.txt"
hash_file "${APP_DIR}/crontab.txt"

echo "  Application state collected."

# --- 6. Generate Final Manifest ---
echo "[6/6] Generating final manifest..."

# Create timeline template
cat > "${EVIDENCE_DIR}/timeline.md" << TLEOF
# Incident Timeline: ${INCIDENT_ID}

| Time (UTC) | Event | Source | Notes |
|------------|-------|--------|-------|
| ${TIMESTAMP} | Evidence collection started | collect_incident_evidence.sh | Automated collection |

TLEOF
hash_file "${EVIDENCE_DIR}/timeline.md"

# Count collected files
FILE_COUNT=$(find "${EVIDENCE_DIR}" -type f | wc -l)
TOTAL_SIZE=$(du -sh "${EVIDENCE_DIR}" | cut -f1)

echo ""
echo "=============================================="
echo " Evidence Collection Complete"
echo " Incident ID: ${INCIDENT_ID}"
echo " Files:       ${FILE_COUNT}"
echo " Total Size:  ${TOTAL_SIZE}"
echo " Manifest:    ${MANIFEST}"
echo " Directory:   ${EVIDENCE_DIR}"
echo "=============================================="
echo ""
echo "IMPORTANT: Review the manifest and verify hashes before proceeding."
echo "           Do NOT modify any files in the evidence directory."
