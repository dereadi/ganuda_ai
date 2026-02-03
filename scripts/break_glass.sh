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
