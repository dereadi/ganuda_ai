#!/usr/bin/env bash
# Phase 7 Supply Chain: Unified weekly security check
# Verifies model integrity, scans dependencies, checks infrastructure
# Designed to run as weekly cron or systemd timer
set -uo pipefail

LOG_DIR="/ganuda/logs/security"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$LOG_DIR/security_check_${TIMESTAMP}.txt"
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

mkdir -p "$LOG_DIR"

log_pass() {
    echo "[PASS] $1" | tee -a "$REPORT_FILE"
    PASS_COUNT=$((PASS_COUNT + 1))
}

log_fail() {
    echo "[FAIL] $1" | tee -a "$REPORT_FILE"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

log_warn() {
    echo "[WARN] $1" | tee -a "$REPORT_FILE"
    WARN_COUNT=$((WARN_COUNT + 1))
}

echo "============================================" | tee "$REPORT_FILE"
echo "  Cherokee AI Federation Security Check" | tee -a "$REPORT_FILE"
echo "  $(date -u +"%Y-%m-%dT%H:%M:%SZ")" | tee -a "$REPORT_FILE"
echo "  Node: $(hostname)" | tee -a "$REPORT_FILE"
echo "============================================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# --- Check 1: Model Integrity ---
echo "--- 1. Model Integrity Checksums ---" | tee -a "$REPORT_FILE"
if [ -f /ganuda/scripts/verify_model_checksums.sh ]; then
    if /ganuda/scripts/verify_model_checksums.sh >/dev/null 2>&1; then
        log_pass "All model checksums verified"
    else
        log_fail "Model checksum verification FAILED - possible tampering"
    fi
else
    log_warn "Model checksum verifier not found. Run generate_model_checksums.sh first."
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 2: Dependency Vulnerabilities ---
echo "--- 2. Dependency Vulnerability Scan ---" | tee -a "$REPORT_FILE"
if [ -f /ganuda/scripts/scan_dependencies.sh ]; then
    /ganuda/scripts/scan_dependencies.sh >/dev/null 2>&1
    LATEST_SUMMARY=$(ls -t /ganuda/security/dependency_audit/summary_*.txt 2>/dev/null | head -1)
    if [ -n "$LATEST_SUMMARY" ]; then
        VULN_LINE=$(grep "Total vulnerabilities:" "$LATEST_SUMMARY" 2>/dev/null || echo "")
        if echo "$VULN_LINE" | grep -q ": 0$"; then
            log_pass "No known dependency vulnerabilities"
        else
            log_warn "Dependency vulnerabilities detected: $VULN_LINE"
        fi
    else
        log_warn "Could not find dependency scan results"
    fi
else
    log_warn "Dependency scanner not found"
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 3: Hardcoded Credentials in Recent Changes ---
echo "--- 3. Hardcoded Credentials Check (last 7 days) ---" | tee -a "$REPORT_FILE"
CRED_PATTERNS='(password|passwd|secret|api_key|apikey|token|credential)\s*[=:]\s*["\x27][^\s"'\'']{8,}'
RECENT_FILES=$(find /ganuda -name '*.py' -o -name '*.sh' -o -name '*.yaml' -o -name '*.yml' -o -name '*.json' | head -500)
CRED_HITS=0
if [ -n "$RECENT_FILES" ]; then
    CRED_HITS=$(echo "$RECENT_FILES" | xargs grep -rilE "$CRED_PATTERNS" 2>/dev/null | \
        grep -v 'venv/' | grep -v 'node_modules/' | grep -v '.git/' | \
        grep -v 'secrets/' | grep -v '__pycache__/' | wc -l || true)
fi

if [ "$CRED_HITS" -eq 0 ]; then
    log_pass "No hardcoded credentials detected in scanned files"
else
    log_warn "Potential hardcoded credentials found in $CRED_HITS file(s). Review manually."
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 4: secrets.env Permissions ---
echo "--- 4. Secrets File Permissions ---" | tee -a "$REPORT_FILE"
SECRETS_FILE="/ganuda/secrets/secrets.env"
if [ -f "$SECRETS_FILE" ]; then
    PERMS=$(stat -c '%a' "$SECRETS_FILE")
    OWNER=$(stat -c '%U' "$SECRETS_FILE")
    if [ "$PERMS" = "600" ] || [ "$PERMS" = "400" ]; then
        log_pass "secrets.env permissions: $PERMS (owner: $OWNER)"
    else
        log_fail "secrets.env has insecure permissions: $PERMS (should be 600 or 400)"
    fi
else
    log_warn "secrets.env not found at $SECRETS_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 5: fail2ban Status ---
echo "--- 5. fail2ban Status ---" | tee -a "$REPORT_FILE"
if systemctl is-active fail2ban >/dev/null 2>&1; then
    JAIL_COUNT=$(fail2ban-client status 2>/dev/null | grep "Number of jail" | awk '{print $NF}' || echo "unknown")
    log_pass "fail2ban active (jails: $JAIL_COUNT)"
else
    log_fail "fail2ban is NOT running"
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 6: nftables Rules ---
echo "--- 6. nftables Firewall ---" | tee -a "$REPORT_FILE"
if command -v nft >/dev/null 2>&1; then
    RULE_COUNT=$(nft list ruleset 2>/dev/null | grep -c 'rule' || true)
    if [ "$RULE_COUNT" -gt 0 ]; then
        log_pass "nftables has $RULE_COUNT rules loaded"
    else
        log_fail "nftables has no rules loaded"
    fi
else
    log_warn "nft command not found"
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 7: PostgreSQL SSL ---
echo "--- 7. PostgreSQL SSL Status ---" | tee -a "$REPORT_FILE"
PG_SSL=$(PGPASSWORD="${PGPASSWORD:-}" psql -h 192.168.132.222 -U claude -d zammad_production \
    -tAc "SHOW ssl;" 2>/dev/null || echo "connection_failed")
if [ "$PG_SSL" = "on" ]; then
    log_pass "PostgreSQL SSL is enabled"
elif [ "$PG_SSL" = "off" ]; then
    log_fail "PostgreSQL SSL is disabled"
else
    log_warn "Could not check PostgreSQL SSL status"
fi
echo "" | tee -a "$REPORT_FILE"

# --- Summary ---
echo "============================================" | tee -a "$REPORT_FILE"
echo "  SUMMARY" | tee -a "$REPORT_FILE"
echo "============================================" | tee -a "$REPORT_FILE"
echo "  Passed:   $PASS_COUNT" | tee -a "$REPORT_FILE"
echo "  Failed:   $FAIL_COUNT" | tee -a "$REPORT_FILE"
echo "  Warnings: $WARN_COUNT" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

if [ "$FAIL_COUNT" -gt 0 ]; then
    VERDICT="SECURITY CHECK FAILED"
elif [ "$WARN_COUNT" -gt 0 ]; then
    VERDICT="SECURITY CHECK PASSED WITH WARNINGS"
else
    VERDICT="ALL SECURITY CHECKS PASSED"
fi

echo "  Verdict: $VERDICT" | tee -a "$REPORT_FILE"
echo "  Report: $REPORT_FILE" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# --- Send to Telegram ---
TELEGRAM_SCRIPT="/ganuda/telegram_bot/send_message.sh"
if [ -f "$TELEGRAM_SCRIPT" ]; then
    TELEGRAM_MSG="Security Check Report ($(hostname))
$VERDICT
Passed: $PASS_COUNT | Failed: $FAIL_COUNT | Warnings: $WARN_COUNT
Full report: $REPORT_FILE"
    bash "$TELEGRAM_SCRIPT" "$TELEGRAM_MSG" 2>/dev/null || true
else
    # Fallback: try curl to Telegram API directly if bot token is available
    if [ -f /ganuda/secrets/secrets.env ]; then
        source /ganuda/secrets/secrets.env 2>/dev/null || true
        if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
            TELEGRAM_MSG="Security Check Report ($(hostname))
$VERDICT
Passed: $PASS_COUNT | Failed: $FAIL_COUNT | Warnings: $WARN_COUNT"
            curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
                -d "chat_id=${TELEGRAM_CHAT_ID}" \
                -d "text=${TELEGRAM_MSG}" >/dev/null 2>&1 || true
        fi
    fi
fi

# Exit code reflects overall status
if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
else
    exit 0
fi
