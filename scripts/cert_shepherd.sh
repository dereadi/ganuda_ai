#!/bin/bash
# Cert Shepherd — sync Caddy TLS certs between DMZ nodes
# Task: Jr #1264 — Cert Shepherd — Sync TLS Certs Between DMZ Nodes
# Instruction: /ganuda/docs/jr_instructions/JR-CERT-SHEPHERD-MAR10-2026.md
#
# Design Decision: Option A (rsync over WireGuard)
# Rationale: Simple, uses existing infrastructure (WireGuard mesh, SSH, cron).
#   Option B (shared storage via Consul/MinIO) adds a new service dependency
#   for just 2 nodes — overkill. Option C (HTTP-01 ACME) still only helps the
#   MASTER node; the BACKUP cannot renew because it never holds the VIP on
#   port 80 either. Option A covers the exact failure mode: BACKUP node gets
#   fresh certs from MASTER via rsync, so failover works immediately.
#
# Bidirectional awareness: This script detects which node it's running on
# and syncs FROM the keepalived MASTER to the BACKUP. If roles flip
# permanently, the sync still works — it always pushes from MASTER to BACKUP.
#
# Runs via cron every hour on BOTH owlfin and eaglefin.
# Only the current MASTER actually performs the sync; BACKUP exits cleanly.

set -euo pipefail

# --- Configuration ---
OWLFIN_WG="10.100.0.5"
EAGLEFIN_WG="10.100.0.6"
CADDY_DATA="/var/lib/caddy/.local/share/caddy"
SSH_KEY="/var/lib/caddy/.ssh/id_cert_sync"
REMOTE_USER="root"
LOG_TAG="cert-shepherd"
KEEPALIVED_VIP="192.168.30.10"
DOMAINS=("ganuda.us" "www.ganuda.us" "vetassist.ganuda.us")
LOG_FILE="/var/log/cert-shepherd.log"

# --- Functions ---
log_info() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1"
    logger -t "$LOG_TAG" "$1"
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

log_error() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1"
    logger -t "$LOG_TAG" "ERROR: $1"
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

# Determine if this node currently holds the VIP (is MASTER)
is_master() {
    ip addr show | grep -q "$KEEPALIVED_VIP"
}

# Determine which node we are
get_local_wg_ip() {
    if ip addr show wg0 2>/dev/null | grep -q "$OWLFIN_WG"; then
        echo "$OWLFIN_WG"
    elif ip addr show wg0 2>/dev/null | grep -q "$EAGLEFIN_WG"; then
        echo "$EAGLEFIN_WG"
    else
        echo ""
    fi
}

get_remote_wg_ip() {
    local local_ip
    local_ip=$(get_local_wg_ip)
    if [ "$local_ip" = "$OWLFIN_WG" ]; then
        echo "$EAGLEFIN_WG"
    elif [ "$local_ip" = "$EAGLEFIN_WG" ]; then
        echo "$OWLFIN_WG"
    else
        echo ""
    fi
}

# --- Preflight checks ---

# Must be run as root (for access to Caddy data and systemctl)
if [ "$(id -u)" -ne 0 ]; then
    log_error "Must be run as root"
    exit 1
fi

# Identify ourselves
LOCAL_IP=$(get_local_wg_ip)
if [ -z "$LOCAL_IP" ]; then
    log_error "Cannot determine local WireGuard IP — not owlfin or eaglefin?"
    exit 1
fi

REMOTE_IP=$(get_remote_wg_ip)
if [ -z "$REMOTE_IP" ]; then
    log_error "Cannot determine remote WireGuard IP"
    exit 1
fi

# Only the MASTER syncs certs to the BACKUP
if ! is_master; then
    log_info "This node ($LOCAL_IP) is BACKUP — skipping sync (MASTER syncs to us)"
    exit 0
fi

log_info "This node ($LOCAL_IP) is MASTER — syncing certs to BACKUP ($REMOTE_IP)"

# Verify cert storage directory exists
if [ ! -d "$CADDY_DATA" ]; then
    log_error "Caddy data directory not found at $CADDY_DATA"
    exit 1
fi

# Verify SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    log_error "SSH key not found at $SSH_KEY — run setup first"
    exit 1
fi

# --- Sync certs ---
RSYNC_EXIT=0
rsync -az --delete \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes" \
    "$CADDY_DATA/" \
    "${REMOTE_USER}@${REMOTE_IP}:${CADDY_DATA}/" || RSYNC_EXIT=$?

if [ "$RSYNC_EXIT" -ne 0 ]; then
    log_error "rsync to ${REMOTE_IP} failed with exit code $RSYNC_EXIT"
    exit 1
fi

log_info "rsync complete — reloading Caddy on BACKUP ($REMOTE_IP)"

# Reload Caddy on the remote node to pick up synced certs
RELOAD_EXIT=0
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes \
    "${REMOTE_USER}@${REMOTE_IP}" "systemctl reload caddy" || RELOAD_EXIT=$?

if [ "$RELOAD_EXIT" -ne 0 ]; then
    log_error "Caddy reload on ${REMOTE_IP} failed with exit code $RELOAD_EXIT"
    exit 1
fi

log_info "Cert sync complete. Certs pushed from $LOCAL_IP (MASTER) to $REMOTE_IP (BACKUP), Caddy reloaded."
exit 0
