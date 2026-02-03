#!/usr/bin/env bash
#
# Security Hardening Deployment Script
# Cherokee AI Federation - Security Phase 3
# Generated: 2026-02-02
#
# REQUIRES ADMIN (sudo) for all deployment actions.
#
# Usage:
#   sudo bash /ganuda/scripts/deploy_security_hardening.sh [--dry-run] [--component COMPONENT]
#
# Components: nftables, fail2ban, caddy, postgresql, pgaudit, all
#
set -euo pipefail

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
CONFIG_DIR="/ganuda/config"
SCRIPTS_DIR="/ganuda/scripts"
DRY_RUN=false
COMPONENT="all"
NODE_NAME="$(hostname -s)"
LOG_FILE="/tmp/security-hardening-deploy-$(date +%Y%m%d-%H%M%S).log"

# -------------------------------------------------------------------
# Argument parsing
# -------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --component)
            COMPONENT="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 [--dry-run] [--component nftables|fail2ban|caddy|postgresql|pgaudit|all]"
            exit 1
            ;;
    esac
done

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "${msg}" | tee -a "${LOG_FILE}"
}

run_cmd() {
    if ${DRY_RUN}; then
        log "[DRY-RUN] Would execute: $*"
    else
        log "[EXEC] $*"
        "$@" 2>&1 | tee -a "${LOG_FILE}"
    fi
}

check_tool() {
    if ! command -v "$1" &>/dev/null; then
        log "[ERROR] Required tool not found: $1"
        log "        Install with: sudo apt-get install $2"
        return 1
    fi
    log "[OK] Found $1: $(command -v "$1")"
    return 0
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log "[ERROR] This script must be run as root (sudo)."
        exit 1
    fi
}

# -------------------------------------------------------------------
# Component: nftables
# -------------------------------------------------------------------
deploy_nftables() {
    log "=== Deploying nftables firewall rules ==="

    check_tool nft nftables || return 1

    local CONF_FILE=""
    case "${NODE_NAME}" in
        redfin*)  CONF_FILE="nftables-redfin.conf" ;;
        bluefin*) CONF_FILE="nftables-bluefin.conf" ;;
        *)
            log "[WARN] No nftables config for node '${NODE_NAME}'. Defaulting to redfin rules."
            CONF_FILE="nftables-redfin.conf"
            ;;
    esac

    if [[ ! -f "${CONFIG_DIR}/${CONF_FILE}" ]]; then
        log "[ERROR] Config file not found: ${CONFIG_DIR}/${CONF_FILE}"
        return 1
    fi

    # Validate syntax first
    log "Validating nftables config syntax..."
    run_cmd nft -c -f "${CONFIG_DIR}/${CONF_FILE}"

    # Deploy
    run_cmd cp "${CONFIG_DIR}/${CONF_FILE}" /etc/nftables.conf
    run_cmd systemctl restart nftables
    run_cmd systemctl enable nftables

    log "[OK] nftables deployed from ${CONF_FILE}"
}

# -------------------------------------------------------------------
# Component: fail2ban
# -------------------------------------------------------------------
deploy_fail2ban() {
    log "=== Deploying fail2ban configuration ==="

    check_tool fail2ban-client fail2ban || return 1

    if [[ ! -f "${CONFIG_DIR}/fail2ban-jail.local" ]]; then
        log "[ERROR] Config file not found: ${CONFIG_DIR}/fail2ban-jail.local"
        return 1
    fi

    # Deploy jail config
    run_cmd cp "${CONFIG_DIR}/fail2ban-jail.local" /etc/fail2ban/jail.local

    # Deploy custom filters
    if [[ -f "${CONFIG_DIR}/fail2ban-filter-caddy-auth.conf" ]]; then
        run_cmd cp "${CONFIG_DIR}/fail2ban-filter-caddy-auth.conf" /etc/fail2ban/filter.d/caddy-auth.conf
    fi
    if [[ -f "${CONFIG_DIR}/fail2ban-filter-postgresql.conf" ]]; then
        run_cmd cp "${CONFIG_DIR}/fail2ban-filter-postgresql.conf" /etc/fail2ban/filter.d/postgresql.conf
    fi

    # Deploy telegram action
    if [[ -f "${CONFIG_DIR}/fail2ban-action-telegram.conf" ]]; then
        run_cmd cp "${CONFIG_DIR}/fail2ban-action-telegram.conf" /etc/fail2ban/action.d/telegram.conf
    fi

    # Validate
    log "Validating fail2ban configuration..."
    run_cmd fail2ban-client --test

    # Restart
    run_cmd systemctl restart fail2ban
    run_cmd systemctl enable fail2ban

    log "[OK] fail2ban deployed"
}

# -------------------------------------------------------------------
# Component: caddy
# -------------------------------------------------------------------
deploy_caddy() {
    log "=== Deploying Caddy security headers ==="

    check_tool caddy caddy || return 1

    if [[ ! -f "${CONFIG_DIR}/Caddyfile.security-headers" ]]; then
        log "[ERROR] Config file not found: ${CONFIG_DIR}/Caddyfile.security-headers"
        return 1
    fi

    run_cmd cp "${CONFIG_DIR}/Caddyfile.security-headers" /etc/caddy/Caddyfile.security-headers

    # Validate full Caddy config
    log "Validating Caddy configuration..."
    run_cmd caddy validate --config /etc/caddy/Caddyfile

    # Reload (not restart -- keeps connections alive)
    run_cmd systemctl reload caddy

    log "[OK] Caddy security headers deployed"
    log "[INFO] Remember to add 'import security_headers' to each site block in your Caddyfile"
}

# -------------------------------------------------------------------
# Component: postgresql (SSL)
# -------------------------------------------------------------------
deploy_postgresql() {
    log "=== Deploying PostgreSQL SSL configuration ==="

    local PG_CONF_DIR="/etc/postgresql/16/main"

    if [[ ! -d "${PG_CONF_DIR}" ]]; then
        log "[ERROR] PostgreSQL config directory not found: ${PG_CONF_DIR}"
        return 1
    fi

    # Generate certs if they do not exist
    if [[ ! -f "${PG_CONF_DIR}/server.crt" ]]; then
        log "SSL certificates not found. Generating..."
        run_cmd bash "${SCRIPTS_DIR}/generate_pg_ssl_certs.sh"
    else
        log "[INFO] SSL certificates already exist. Skipping generation."
    fi

    # Deploy SSL config
    run_cmd mkdir -p "${PG_CONF_DIR}/conf.d"
    run_cmd cp "${CONFIG_DIR}/postgresql-ssl.conf" "${PG_CONF_DIR}/conf.d/ssl.conf"
    run_cmd chown postgres:postgres "${PG_CONF_DIR}/conf.d/ssl.conf"

    # Restart PostgreSQL
    run_cmd systemctl restart postgresql

    # Verify SSL is on
    log "Verifying PostgreSQL SSL..."
    if ! ${DRY_RUN}; then
        sudo -u postgres psql -t -c "SHOW ssl;" 2>&1 | tee -a "${LOG_FILE}"
    fi

    log "[OK] PostgreSQL SSL deployed"
}

# -------------------------------------------------------------------
# Component: pgaudit
# -------------------------------------------------------------------
deploy_pgaudit() {
    log "=== Deploying pgAudit configuration ==="

    local PG_CONF_DIR="/etc/postgresql/16/main"

    # Check if pgaudit extension is installed
    if ! dpkg -l | grep -q "postgresql-16-pgaudit"; then
        log "[ERROR] pgaudit not installed. Run: sudo apt-get install postgresql-16-pgaudit"
        return 1
    fi

    # Deploy config
    run_cmd mkdir -p "${PG_CONF_DIR}/conf.d"
    run_cmd cp "${CONFIG_DIR}/pgaudit.conf" "${PG_CONF_DIR}/conf.d/pgaudit.conf"
    run_cmd chown postgres:postgres "${PG_CONF_DIR}/conf.d/pgaudit.conf"

    # Ensure shared_preload_libraries includes pgaudit
    if ! grep -q "pgaudit" "${PG_CONF_DIR}/postgresql.conf"; then
        log "[WARN] pgaudit not in shared_preload_libraries. Add manually:"
        log "       shared_preload_libraries = 'pgaudit'"
    fi

    # Restart and create extension
    run_cmd systemctl restart postgresql
    if ! ${DRY_RUN}; then
        sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS pgaudit;" 2>&1 | tee -a "${LOG_FILE}"
    fi

    log "[OK] pgAudit deployed"
}

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
main() {
    log "=========================================="
    log "Security Hardening Deployment"
    log "Node: ${NODE_NAME}"
    log "Component: ${COMPONENT}"
    log "Dry run: ${DRY_RUN}"
    log "Log file: ${LOG_FILE}"
    log "=========================================="

    if ! ${DRY_RUN}; then
        check_root
    fi

    case "${COMPONENT}" in
        nftables)   deploy_nftables ;;
        fail2ban)   deploy_fail2ban ;;
        caddy)      deploy_caddy ;;
        postgresql) deploy_postgresql ;;
        pgaudit)    deploy_pgaudit ;;
        all)
            deploy_nftables
            deploy_fail2ban
            deploy_caddy
            deploy_postgresql
            deploy_pgaudit
            ;;
        *)
            log "[ERROR] Unknown component: ${COMPONENT}"
            exit 1
            ;;
    esac

    log ""
    log "=========================================="
    log "Deployment complete. Review log: ${LOG_FILE}"
    log "=========================================="
}

main
