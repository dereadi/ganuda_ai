# JR-SECURITY-PHASE6-INCIDENT-RESPONSE-PLAYBOOK-FEB02-2026

**Priority:** P1
**Assigned:** DevOps Jr.
**Created:** 2026-02-02
**Status:** Ready for Execution

## Objective

Create the federation's incident response playbook, evidence collection tooling, and break-glass scripts. These artifacts define how we detect, contain, investigate, and recover from security incidents across all nodes.

## CRITICAL EXECUTOR RULES

- NO SEARCH/REPLACE blocks
- Use ```bash code blocks ONLY
- Create new files via heredoc
- All paths are absolute
- Do NOT modify any existing files

## Prerequisites

- Sudo access for break-glass operations
- Access to /ganuda/logs/ and /ganuda/security/ directories
- Telegram alert_manager available at /ganuda/lib/alert_manager.py
- PostgreSQL running on localhost

---

## Step 1: Create Incident Response Playbook

Create `/ganuda/docs/protocols/INCIDENT-RESPONSE-PLAYBOOK-FEB02-2026.md` via bash heredoc.

```bash
mkdir -p /ganuda/docs/protocols
mkdir -p /ganuda/security/evidence
mkdir -p /ganuda/logs/security

cat > /ganuda/docs/protocols/INCIDENT-RESPONSE-PLAYBOOK-FEB02-2026.md << 'DOCEOF'
# Incident Response Playbook

**Version:** 1.0
**Created:** 2026-02-02
**Owner:** TPM (Claude Opus 4.5)
**Review Cycle:** Monthly

---

## 1. Severity Levels

| Level | Name | Description | Examples |
|-------|------|-------------|----------|
| SEV1 | Critical | Active data breach, ransomware, PII exposure confirmed | Database dump detected, ransomware encryption in progress, veteran PII found in public logs |
| SEV2 | High | Unauthorized access detected, service compromise, credential leak | Unknown SSH session, Jr executor running unexpected commands, API key found in git history |
| SEV3 | Medium | Suspicious activity, failed attack attempt, anomalous behavior | Multiple failed logins, unusual Council voting pattern, prompt injection attempt blocked |
| SEV4 | Low | Vulnerability discovered, configuration issue, policy violation | Outdated dependency, open port found, missing log rotation |

---

## 2. Escalation Tree

### SEV1 - Critical
- **Immediate** Telegram alert to TPM + all chiefs
- **Response window:** 15 minutes
- **Actions:** Activate break-glass procedures, begin containment, preserve evidence
- **Communication:** All-hands notification, continuous updates every 15 minutes
- **Resolution target:** 4 hours

### SEV2 - High
- **Immediate** Telegram alert to TPM
- **Response window:** 1 hour
- **Actions:** Investigate scope, begin targeted containment, assess damage
- **Communication:** TPM + affected service owner, updates every 30 minutes
- **Resolution target:** 8 hours

### SEV3 - Medium
- **Logged** to security monitoring system
- **Response window:** Daily summary to TPM
- **Actions:** Investigate during next business cycle, document findings
- **Communication:** Included in daily security summary
- **Resolution target:** 48 hours

### SEV4 - Low
- **Logged** to security monitoring system
- **Response window:** Weekly review
- **Actions:** Add to remediation backlog, schedule fix
- **Communication:** Included in weekly security review
- **Resolution target:** 2 weeks

---

## 3. Containment Procedures by Attack Type

### Database Breach
1. Immediately revoke the `claude` database user: `ALTER USER claude NOLOGIN;`
2. Rotate all database passwords
3. Snapshot the database BEFORE any remediation: `pg_dump cherokee > /ganuda/security/evidence/db_snapshot_$(date +%s).sql`
4. Enable pgAudit if not already enabled: `ALTER SYSTEM SET pgaudit.log = 'all';`
5. Preserve all PostgreSQL logs: `cp /var/log/postgresql/*.log /ganuda/security/evidence/`
6. Check for data exfiltration: review `pg_stat_activity` and network connections
7. Assess scope: which tables were accessed, which records, what timeframe

### Jr Executor Compromise
1. Activate sanctuary state: `touch /tmp/jr_executor_paused`
2. Stop the queue worker: `sudo systemctl stop jr-queue-worker`
3. Kill any running Jr task processes
4. Audit the entire queue: review all pending and recently completed tasks
5. Check instruction files for tampering: compare checksums against known-good
6. Review execution_audit_log for the compromised task chain
7. Identify the entry point: was it a malicious instruction file, injected queue entry, or LLM manipulation?

### Model Jailbreak
1. Disable the LLM Gateway endpoint: `sudo systemctl stop llm-gateway`
2. Review all recent LLM responses (last 1 hour)
3. Check for PII in recent responses using output_pii_scanner
4. Assess whether any harmful content was delivered to users
5. Check if the jailbreak was propagated through thermal memory
6. Quarantine any thermal memories created during the incident window
7. Re-enable with enhanced prompt injection detection

### PII Exposure
1. Immediately identify the scope: what PII, how many records, what exposure vector
2. Preserve evidence of the exposure (screenshots, logs, database snapshots)
3. If exposed via API/web: disable the affected endpoint immediately
4. If exposed via logs: quarantine log files, check log shipping/aggregation
5. Notify affected users as required by law
6. File breach report if required (see Communication Plan)
7. Implement redaction: run output_pii_scanner against all exposed data paths

### Thermal Memory Poisoning
1. Identify the poisoned memories: query by time window, source, or content pattern
2. Run integrity checksums against known-good thermal memory baselines
3. Quarantine suspicious memories: `UPDATE thermal_memories SET quarantined = true WHERE id IN (...)`
4. Trigger sanctuary state: `touch /tmp/jr_executor_paused`
5. Check if poisoned memories have already influenced decisions (trace thermal propagation)
6. Re-derive affected decisions from clean data
7. Update thermal memory validation rules to prevent recurrence

### Network Intrusion
1. Block source IP immediately: `sudo nft add rule inet filter input ip saddr <IP> drop`
2. Capture traffic for forensics: `sudo tcpdump -i any -w /ganuda/security/evidence/capture_$(date +%s).pcap &`
3. Isolate the affected node from the federation network
4. Check for lateral movement: review SSH logs, inter-node traffic, shared credentials
5. Audit all running processes: `ps auxf`, check for unknown processes
6. Review cron jobs and systemd timers for persistence mechanisms
7. Check authorized_keys files for unauthorized additions

### Ransomware
1. **IMMEDIATELY** isolate all nodes: disconnect network cables, disable WiFi
2. **DO NOT PAY** the ransom under any circumstances
3. Preserve encrypted files for forensics (do not delete)
4. Identify the ransomware variant if possible (check ransom note, file extensions)
5. Check backup integrity: are backups intact and unencrypted?
6. Restore from the most recent clean backup
7. Report to law enforcement (FBI IC3: https://www.ic3.gov/)
8. Conduct full forensic analysis before reconnecting any node

---

## 4. Evidence Preservation

All evidence MUST be collected before any remediation actions that could alter state.

### Required Evidence Collection
1. **Database snapshot**: `pg_dump cherokee > /ganuda/security/evidence/incident_${ID}/db_$(date +%s).sql`
2. **Network capture**: `sudo tcpdump -w /ganuda/security/evidence/incident_${ID}/capture_$(date +%s).pcap -c 10000`
3. **System logs**: Copy all relevant logs from `/var/log/` to evidence directory
4. **Application logs**: Copy from `/ganuda/logs/` to evidence directory
5. **Process list**: `ps auxf > /ganuda/security/evidence/incident_${ID}/processes.txt`
6. **Network state**: `ss -tulnp > /ganuda/security/evidence/incident_${ID}/network_state.txt`
7. **Active connections**: `netstat -an > /ganuda/security/evidence/incident_${ID}/connections.txt`

### Evidence Integrity
- Hash ALL evidence files immediately after collection: `sha256sum <file> >> manifest.sha256`
- Store the manifest in the evidence directory
- Do not modify evidence files after collection
- Record the exact timestamp of collection
- Document who collected the evidence and under what authority

### Timeline Documentation
Maintain a running timeline in `/ganuda/security/evidence/incident_${ID}/timeline.md`:
```
| Time (UTC) | Event | Source | Notes |
|------------|-------|--------|-------|
| 2026-02-02T12:00:00Z | Alert received | security_monitor | First detection |
| 2026-02-02T12:01:00Z | Investigation started | TPM | Assigned to Security Jr. |
```

---

## 5. Recovery Procedures

### Database Recovery
1. Stop all application services that connect to the database
2. Restore from the most recent clean backup: `pg_restore -d cherokee /path/to/backup`
3. Apply WAL logs for point-in-time recovery if needed
4. Rotate ALL database credentials (user passwords, connection strings)
5. Re-enable pgAudit and verify logging
6. Run data integrity checks
7. Restart application services one by one, verifying each

### Service Recovery
1. Identify the last known-good git commit
2. Redeploy all services from that commit: `git checkout <commit> && ./deploy.sh`
3. Verify checksums of all deployed files
4. Restart services in dependency order: database -> backend -> workers -> frontend
5. Run smoke tests against each service
6. Monitor for 30 minutes before declaring recovery complete

### Model Recovery
1. Re-download models from trusted source (HuggingFace, Anthropic)
2. Verify model checksums against published values
3. Test model outputs with known-safe inputs before enabling
4. Re-enable LLM Gateway with enhanced monitoring

### Credential Recovery (Full Rotation)
1. PostgreSQL passwords: all database users
2. API keys: Anthropic, OpenAI, HuggingFace, Telegram bot token
3. SSH keys: regenerate on all nodes, update authorized_keys
4. JWT secrets: regenerate and invalidate all existing tokens
5. Service account passwords: all systemd service users
6. Environment variables: update all .env files and Vault secrets
7. Verify no old credentials remain in git history, logs, or thermal memory

---

## 6. Communication Plan

### Internal Communication
- **Primary channel:** Telegram security group
- **Backup channel:** Direct SSH to nodes
- **Documentation:** All incidents preserved in thermal memory with `security_incident` tag
- **Post-incident:** Write KB article, update this playbook, conduct retrospective

### External Communication (PII Breach)
- **Legal obligation:** Notify affected individuals within 72 hours (varies by state)
- **Federal requirement:** If VA data involved, notify VA Privacy Office
- **HIPAA:** If health data involved, notify HHS within 60 days
- **Documentation:** Maintain records of all notifications sent
- **Legal counsel:** Consult before any external communication

### Post-Incident
1. Conduct retrospective within 48 hours of resolution
2. Write incident report (what happened, impact, root cause, remediation)
3. Create KB article for future reference
4. Update this playbook with lessons learned
5. File any required regulatory reports
6. Schedule follow-up review in 2 weeks

---

## 7. Break Glass Procedures

These are emergency procedures for when normal processes are too slow. Use only when authorized.

### Emergency Database Shutdown
```bash
sudo systemctl stop postgresql
```
**When to use:** Active data exfiltration, ransomware encrypting database files
**Impact:** ALL services lose database connectivity immediately
**Recovery:** `sudo systemctl start postgresql` after containment

### Emergency Network Isolation
```bash
sudo nft flush ruleset && \
sudo nft add table inet filter && \
sudo nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }' && \
sudo nft add rule inet filter input iif lo accept
```
**When to use:** Active network intrusion, lateral movement detected, ransomware spreading
**Impact:** ALL network traffic blocked except localhost
**Recovery:** `sudo nft flush ruleset` and restore from `/etc/nftables.conf`

### Emergency Jr Executor Stop
```bash
touch /tmp/jr_executor_paused && sudo systemctl stop jr-queue-worker
```
**When to use:** Jr executor running malicious commands, compromised instruction file
**Impact:** All Jr task execution stops immediately
**Recovery:** `rm /tmp/jr_executor_paused && sudo systemctl start jr-queue-worker`

### Emergency LLM Gateway Stop
```bash
sudo systemctl stop llm-gateway
```
**When to use:** Model jailbreak, PII leaking through responses
**Impact:** All LLM-dependent features stop (chat, council, research)
**Recovery:** `sudo systemctl start llm-gateway` after review

### Emergency Full Stop (All Services)
```bash
touch /tmp/jr_executor_paused && \
sudo systemctl stop jr-queue-worker && \
sudo systemctl stop llm-gateway && \
sudo systemctl stop vetassist-backend && \
sudo systemctl stop vetassist-frontend && \
sudo systemctl stop telegram-chief && \
sudo systemctl stop security-monitor
```
**When to use:** Catastrophic compromise, ransomware, unknown attack vector
**Impact:** EVERYTHING stops
**Recovery:** Restart services individually after full forensic review

---

## Appendix A: Emergency Contacts

| Role | Contact Method |
|------|---------------|
| TPM (Claude Opus 4.5) | Telegram: automated alerts |
| System Admin | Telegram: @dereadi |
| Security Jr. | Via Jr queue system |
| DevOps Jr. | Via Jr queue system |

## Appendix B: Key File Locations

| Item | Path |
|------|------|
| Security logs | /ganuda/logs/security/ |
| Evidence storage | /ganuda/security/evidence/ |
| Blue team modules | /ganuda/security/blue_team/ |
| Execution audit log | PostgreSQL: execution_audit_log table |
| Thermal memories | PostgreSQL: thermal_memories table |
| Jr task queue | PostgreSQL: jr_task_queue table |
| Break glass script | /ganuda/scripts/break_glass.sh |
| Evidence collector | /ganuda/scripts/collect_incident_evidence.sh |

## Appendix C: Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-02-02 | 1.0 | TPM | Initial creation |
DOCEOF
```

### Expected Output
- Playbook created at `/ganuda/docs/protocols/INCIDENT-RESPONSE-PLAYBOOK-FEB02-2026.md`
- Covers all 7 severity levels, escalation trees, containment procedures, evidence preservation, recovery, communication, and break glass procedures

---

## Step 2: Create Evidence Collection Script

Create `/ganuda/scripts/collect_incident_evidence.sh` via bash heredoc.

This script automates evidence collection when an incident is declared.

```bash
cat > /ganuda/scripts/collect_incident_evidence.sh << 'SHEOF'
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
SHEOF

chmod +x /ganuda/scripts/collect_incident_evidence.sh
```

### Expected Output
- Script created at `/ganuda/scripts/collect_incident_evidence.sh`
- Script is executable
- Collects system state, network state, logs, database state, application state
- Generates SHA-256 manifest of all evidence files

---

## Step 3: Create Break-Glass Script

Create `/ganuda/scripts/break_glass.sh` via bash heredoc.

This script implements the emergency break-glass procedures from the playbook. All actions require confirmation and are logged.

```bash
cat > /ganuda/scripts/break_glass.sh << 'SHEOF'
#!/usr/bin/env bash
#
# Break Glass Script - Emergency Incident Response
#
# Implements emergency containment procedures. All actions are logged
# and require confirmation unless --force is specified.
#
# Usage: ./break_glass.sh <action> [--force]
#
# Actions:
#   isolate-network    Block all network traffic except localhost
#   stop-database      Emergency PostgreSQL shutdown
#   stop-executor      Pause Jr executor and stop queue worker
#   stop-llm           Stop LLM Gateway
#   stop-all           Emergency full stop of all services
#   restore-network    Restore network rules from saved config
#   restore-executor   Resume Jr executor
#   status             Show current security state
#
# REQUIRES SUDO for most actions.
#
# Created: 2026-02-02

set -euo pipefail

# --- Configuration ---
LOG_FILE="/ganuda/logs/security/break_glass.log"
SANCTUARY_FILE="/tmp/jr_executor_paused"
NFT_BACKUP="/ganuda/security/evidence/nft_rules_backup.txt"

# --- Ensure log directory ---
mkdir -p "$(dirname "${LOG_FILE}")"

# --- Logging ---
log() {
    local level="$1"
    shift
    local msg="$*"
    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "${ts} [${level}] ${msg}" | tee -a "${LOG_FILE}"
}

# --- Telegram Alert ---
send_alert() {
    local msg="$1"
    python3 -c "
import sys
sys.path.insert(0, '/ganuda/lib')
try:
    from alert_manager import send_alert
    send_alert('[BREAK GLASS] ${msg}')
except Exception as e:
    print(f'Alert send failed: {e}', file=sys.stderr)
" 2>/dev/null || true
}

# --- Confirmation ---
confirm() {
    local action="$1"
    if [[ "${FORCE:-}" == "true" ]]; then
        log "WARN" "Force mode: skipping confirmation for '${action}'"
        return 0
    fi
    echo ""
    echo "==========================================="
    echo " BREAK GLASS: ${action}"
    echo "==========================================="
    echo ""
    echo "This is an EMERGENCY action with significant impact."
    echo ""
    read -r -p "Are you sure? Type 'YES' to confirm: " response
    if [[ "${response}" != "YES" ]]; then
        log "INFO" "Action '${action}' cancelled by user"
        echo "Cancelled."
        exit 0
    fi
}

# --- Actions ---

action_isolate_network() {
    confirm "ISOLATE NETWORK (drop all traffic except localhost)"
    log "CRITICAL" "BREAK GLASS: Isolating network"
    send_alert "Network isolation activated"

    # Backup current rules
    sudo nft list ruleset > "${NFT_BACKUP}" 2>/dev/null || true
    log "INFO" "Current nft rules backed up to ${NFT_BACKUP}"

    # Drop all traffic except loopback
    sudo nft flush ruleset
    sudo nft add table inet filter
    sudo nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
    sudo nft add rule inet filter input iif lo accept
    # Allow established connections to gracefully close
    sudo nft add rule inet filter input ct state established,related accept

    log "CRITICAL" "Network isolated: all traffic dropped except localhost"
    echo ""
    echo "Network is now ISOLATED. Only localhost traffic is allowed."
    echo "To restore: $0 restore-network"
}

action_stop_database() {
    confirm "STOP DATABASE (all services will lose database connectivity)"
    log "CRITICAL" "BREAK GLASS: Stopping PostgreSQL"
    send_alert "Emergency database shutdown"

    sudo systemctl stop postgresql
    log "CRITICAL" "PostgreSQL stopped"
    echo ""
    echo "PostgreSQL is now STOPPED."
    echo "To restore: sudo systemctl start postgresql"
}

action_stop_executor() {
    confirm "STOP EXECUTOR (all Jr task execution will halt)"
    log "CRITICAL" "BREAK GLASS: Stopping Jr executor"
    send_alert "Jr executor emergency stop"

    touch "${SANCTUARY_FILE}"
    log "INFO" "Sanctuary state activated: ${SANCTUARY_FILE}"

    sudo systemctl stop jr-queue-worker 2>/dev/null || true
    log "CRITICAL" "Jr queue worker stopped"
    echo ""
    echo "Jr executor is now in SANCTUARY STATE."
    echo "To restore: $0 restore-executor"
}

action_stop_llm() {
    confirm "STOP LLM GATEWAY (all LLM-dependent features will stop)"
    log "CRITICAL" "BREAK GLASS: Stopping LLM Gateway"
    send_alert "LLM Gateway emergency stop"

    sudo systemctl stop llm-gateway 2>/dev/null || true
    log "CRITICAL" "LLM Gateway stopped"
    echo ""
    echo "LLM Gateway is now STOPPED."
    echo "To restore: sudo systemctl start llm-gateway"
}

action_stop_all() {
    confirm "STOP ALL SERVICES (complete system shutdown)"
    log "CRITICAL" "BREAK GLASS: Full emergency stop"
    send_alert "FULL EMERGENCY STOP - All services"

    touch "${SANCTUARY_FILE}"

    local services=(
        "jr-queue-worker"
        "llm-gateway"
        "vetassist-backend"
        "vetassist-frontend"
        "telegram-chief"
        "security-monitor"
        "research-worker"
        "jr-executor"
        "jr-bidding"
    )

    for svc in "${services[@]}"; do
        if systemctl is-active --quiet "${svc}" 2>/dev/null; then
            sudo systemctl stop "${svc}" 2>/dev/null || true
            log "CRITICAL" "Stopped: ${svc}"
        else
            log "INFO" "Already stopped: ${svc}"
        fi
    done

    log "CRITICAL" "ALL SERVICES STOPPED"
    echo ""
    echo "All services are now STOPPED."
    echo "Review and restart individually after investigation."
}

action_restore_network() {
    confirm "RESTORE NETWORK (re-enable network traffic)"
    log "INFO" "Restoring network rules"

    if [[ -f "${NFT_BACKUP}" ]]; then
        sudo nft flush ruleset
        sudo nft -f "${NFT_BACKUP}"
        log "INFO" "Network rules restored from backup"
        echo "Network rules restored from: ${NFT_BACKUP}"
    elif [[ -f "/etc/nftables.conf" ]]; then
        sudo nft flush ruleset
        sudo nft -f /etc/nftables.conf
        log "INFO" "Network rules restored from /etc/nftables.conf"
        echo "Network rules restored from system default."
    else
        sudo nft flush ruleset
        log "WARN" "No backup found, flushed all rules (fully open)"
        echo "WARNING: No backup found. All firewall rules cleared."
    fi

    send_alert "Network isolation lifted"
}

action_restore_executor() {
    confirm "RESTORE EXECUTOR (resume Jr task execution)"
    log "INFO" "Restoring Jr executor"

    rm -f "${SANCTUARY_FILE}"
    log "INFO" "Sanctuary state deactivated"

    sudo systemctl start jr-queue-worker 2>/dev/null || true
    log "INFO" "Jr queue worker started"

    send_alert "Jr executor restored from sanctuary state"
    echo "Jr executor restored and running."
}

action_status() {
    echo ""
    echo "==========================================="
    echo " Security Status Report"
    echo " Time: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "==========================================="
    echo ""

    # Sanctuary state
    if [[ -f "${SANCTUARY_FILE}" ]]; then
        echo "[!!] SANCTUARY STATE: ACTIVE"
    else
        echo "[OK] Sanctuary State: inactive"
    fi
    echo ""

    # Key services
    echo "Service Status:"
    local services=(
        "postgresql"
        "jr-queue-worker"
        "llm-gateway"
        "vetassist-backend"
        "vetassist-frontend"
        "telegram-chief"
        "security-monitor"
    )
    for svc in "${services[@]}"; do
        if systemctl is-active --quiet "${svc}" 2>/dev/null; then
            echo "  [OK] ${svc}: running"
        else
            echo "  [!!] ${svc}: STOPPED"
        fi
    done
    echo ""

    # Network
    echo "Network:"
    local nft_rules
    nft_rules=$(sudo nft list ruleset 2>/dev/null | wc -l || echo "0")
    echo "  nft rules: ${nft_rules} lines"
    echo ""

    # PostgreSQL connections
    local pg_count
    pg_count=$(psql -h localhost -U claude -d cherokee -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ' || echo "N/A")
    echo "  PostgreSQL connections: ${pg_count}"
    echo ""

    # Recent break glass actions
    if [[ -f "${LOG_FILE}" ]]; then
        echo "Recent break glass actions (last 10):"
        tail -10 "${LOG_FILE}" | while IFS= read -r line; do
            echo "  ${line}"
        done
    else
        echo "No break glass log found."
    fi
    echo ""
}

# --- Help ---
show_help() {
    echo "Break Glass Script - Emergency Incident Response"
    echo ""
    echo "Usage: $0 <action> [--force]"
    echo ""
    echo "Actions:"
    echo "  isolate-network    Block all network traffic except localhost"
    echo "  stop-database      Emergency PostgreSQL shutdown"
    echo "  stop-executor      Pause Jr executor and stop queue worker"
    echo "  stop-llm           Stop LLM Gateway"
    echo "  stop-all           Emergency full stop of all services"
    echo "  restore-network    Restore network rules from saved config"
    echo "  restore-executor   Resume Jr executor"
    echo "  status             Show current security state"
    echo ""
    echo "Options:"
    echo "  --force            Skip confirmation prompts (USE WITH CAUTION)"
    echo "  --help, -h         Show this help message"
    echo ""
    echo "REQUIRES SUDO for most actions."
    echo ""
    echo "Log file: ${LOG_FILE}"
    echo ""
    echo "Examples:"
    echo "  $0 status                    # Check current state"
    echo "  $0 stop-executor             # Halt Jr execution (with confirmation)"
    echo "  $0 isolate-network --force   # Emergency network isolation"
}

# --- Main ---
FORCE="false"
ACTION=""

for arg in "$@"; do
    case "${arg}" in
        --force)
            FORCE="true"
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            ACTION="${arg}"
            ;;
    esac
done

if [[ -z "${ACTION}" ]]; then
    show_help
    exit 1
fi

case "${ACTION}" in
    isolate-network)
        action_isolate_network
        ;;
    stop-database)
        action_stop_database
        ;;
    stop-executor)
        action_stop_executor
        ;;
    stop-llm)
        action_stop_llm
        ;;
    stop-all)
        action_stop_all
        ;;
    restore-network)
        action_restore_network
        ;;
    restore-executor)
        action_restore_executor
        ;;
    status)
        action_status
        ;;
    *)
        echo "Unknown action: ${ACTION}"
        echo ""
        show_help
        exit 1
        ;;
esac
SHEOF

chmod +x /ganuda/scripts/break_glass.sh
```

### Expected Output
- Script created at `/ganuda/scripts/break_glass.sh`
- Script is executable
- Supports all break-glass actions: isolate-network, stop-database, stop-executor, stop-llm, stop-all, restore-network, restore-executor, status
- All actions logged to `/ganuda/logs/security/break_glass.log`
- Sends Telegram alerts on execution
- Requires confirmation (or --force flag)
- Has --help output

---

## Step 4: Validation

Run validation checks to confirm all files are correctly created.

```bash
# Verify all files exist
echo "=== File Existence Check ==="
files=(
    "/ganuda/docs/protocols/INCIDENT-RESPONSE-PLAYBOOK-FEB02-2026.md"
    "/ganuda/scripts/collect_incident_evidence.sh"
    "/ganuda/scripts/break_glass.sh"
)
for f in "${files[@]}"; do
    if [[ -f "$f" ]]; then
        echo "  OK: $f"
    else
        echo "  MISSING: $f"
    fi
done

# Verify scripts are executable
echo ""
echo "=== Executable Check ==="
for f in "/ganuda/scripts/collect_incident_evidence.sh" "/ganuda/scripts/break_glass.sh"; do
    if [[ -x "$f" ]]; then
        echo "  OK: $f is executable"
    else
        echo "  FAIL: $f is NOT executable"
    fi
done

# Verify evidence directory exists
echo ""
echo "=== Directory Check ==="
for d in "/ganuda/security/evidence" "/ganuda/logs/security" "/ganuda/docs/protocols"; do
    if [[ -d "$d" ]]; then
        echo "  OK: $d"
    else
        echo "  MISSING: $d"
    fi
done

# Verify break_glass.sh --help output
echo ""
echo "=== break_glass.sh --help ==="
/ganuda/scripts/break_glass.sh --help

# Verify collect_incident_evidence.sh usage output
echo ""
echo "=== collect_incident_evidence.sh usage ==="
/ganuda/scripts/collect_incident_evidence.sh 2>&1 || true

echo ""
echo "=== VALIDATION COMPLETE ==="
```

### Expected Output
- All 3 files exist
- Both scripts are executable
- Evidence and log directories exist
- break_glass.sh shows help output with all available actions
- collect_incident_evidence.sh shows usage when run without arguments

---

## Success Criteria

1. Incident Response Playbook created with all 7 sections (Severity, Escalation, Containment, Evidence, Recovery, Communication, Break Glass)
2. Evidence collection script automates gathering of system state, network state, logs, database state, and application state
3. Evidence collection script generates SHA-256 manifest of all collected files
4. Break glass script supports all emergency actions: isolate-network, stop-database, stop-executor, stop-llm, stop-all
5. Break glass script also supports restore actions: restore-network, restore-executor
6. Break glass script requires confirmation before executing (with --force override)
7. Break glass script logs all actions and sends Telegram alerts
8. Both scripts have proper --help/usage output
9. All required directories created
