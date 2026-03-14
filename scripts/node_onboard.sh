#!/bin/bash
# node_onboard.sh — Federation node setup for new developers
# Run as: sudo ./node_onboard.sh <username>
# Sets up home dir, sudoers, group access, DB connectivity
# Cherokee AI Federation

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }

if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo: sudo $0 <username>"
    exit 1
fi

if [[ $# -lt 1 ]]; then
    echo "Usage: sudo $0 <username>"
    echo "  Sets up a FreeIPA user on this federation node."
    echo "  User must already exist in FreeIPA (silverfin)."
    exit 1
fi

USER="$1"
HOSTNAME=$(hostname -s)

echo "========================================"
echo " Federation Node Onboard: $USER"
echo " Node: $HOSTNAME"
echo " Date: $(date '+%Y-%m-%d %H:%M %Z')"
echo "========================================"
echo

# --- Step 1: Verify FreeIPA identity ---
echo "--- Step 1: FreeIPA identity ---"
if getent -s sss passwd "$USER" > /dev/null 2>&1; then
    IPA_UID=$(getent -s sss passwd "$USER" | cut -d: -f3)
    IPA_GID=$(getent -s sss passwd "$USER" | cut -d: -f4)
    ok "FreeIPA user $USER found (uid=$IPA_UID, gid=$IPA_GID)"
else
    fail "User $USER not found in FreeIPA. Create them on silverfin first."
    exit 1
fi

# --- Step 2: Remove conflicting local account ---
echo "--- Step 2: Local account conflict check ---"
if grep -q "^${USER}:" /etc/passwd 2>/dev/null; then
    LOCAL_UID=$(grep "^${USER}:" /etc/passwd | cut -d: -f3)
    warn "Local account exists (uid=$LOCAL_UID) — conflicts with FreeIPA (uid=$IPA_UID)"
    cp /etc/passwd /etc/passwd.bak.$(date +%Y%m%d%H%M%S)
    grep -v "^${USER}:" /etc/passwd > /tmp/passwd.clean
    cp /tmp/passwd.clean /etc/passwd
    rm -f /tmp/passwd.clean
    ok "Local account removed. FreeIPA is now authoritative."
else
    ok "No conflicting local account."
fi

# Also clean /etc/shadow and /etc/group if local entries exist
for f in /etc/shadow /etc/group; do
    if grep -q "^${USER}:" "$f" 2>/dev/null; then
        cp "$f" "${f}.bak.$(date +%Y%m%d%H%M%S)"
        grep -v "^${USER}:" "$f" > /tmp/$(basename $f).clean
        cp /tmp/$(basename $f).clean "$f"
        rm -f /tmp/$(basename $f).clean
        ok "Removed stale local entry from $f"
    fi
done

# --- Step 3: Home directory ---
echo "--- Step 3: Home directory ---"
HOMEDIR="/home/$USER"
if [[ -d "$HOMEDIR" ]]; then
    OWNER_UID=$(stat -c '%u' "$HOMEDIR")
    if [[ "$OWNER_UID" != "$IPA_UID" ]]; then
        warn "Home dir owned by uid $OWNER_UID, expected $IPA_UID. Fixing..."
        chown -R "$IPA_UID:$IPA_GID" "$HOMEDIR"
        ok "Chowned $HOMEDIR to $IPA_UID:$IPA_GID"
    else
        ok "Home dir ownership correct."
    fi
else
    mkhomedir_helper "$USER"
    ok "Created $HOMEDIR via mkhomedir_helper"
fi
chmod 750 "$HOMEDIR"
ok "Home dir permissions: 750"

# --- Step 4: Sudoers ---
echo "--- Step 4: Sudoers ---"
SUDOERS_FILE="/etc/sudoers.d/${USER}-admin"
if [[ -f "$SUDOERS_FILE" ]]; then
    ok "Sudoers file already exists: $SUDOERS_FILE"
else
    echo "$USER ALL=(ALL) NOPASSWD: ALL" > "$SUDOERS_FILE"
    chmod 0440 "$SUDOERS_FILE"
    ok "Created $SUDOERS_FILE with NOPASSWD ALL"
fi

# --- Step 5: ganuda-dev group and /ganuda access ---
echo "--- Step 5: /ganuda access ---"
if getent group ganuda-dev > /dev/null 2>&1; then
    if id -nG "$USER" 2>/dev/null | grep -qw ganuda-dev; then
        ok "$USER is in ganuda-dev group"
    else
        warn "$USER not yet in ganuda-dev group — add via FreeIPA:"
        warn "  ipa group-add-member ganuda-dev --users=$USER"
    fi
else
    warn "ganuda-dev group not found. SSSD may need a refresh: systemctl restart sssd"
fi

if [[ -d /ganuda ]]; then
    GANUDA_GRP=$(stat -c '%G' /ganuda)
    if [[ "$GANUDA_GRP" == "ganuda-dev" ]]; then
        ok "/ganuda group is ganuda-dev"
    else
        chgrp ganuda-dev /ganuda
        chmod 2775 /ganuda
        ok "Set /ganuda to ganuda-dev:2775"
    fi
else
    warn "No /ganuda on this node."
fi

# --- Step 6: DB connectivity test ---
echo "--- Step 6: Database connectivity ---"
if command -v psql > /dev/null 2>&1; then
    if timeout 5 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 1" > /dev/null 2>&1; then
        ok "PostgreSQL on bluefin reachable (LAN)"
    elif timeout 5 psql -h 10.100.0.2 -U claude -d zammad_production -c "SELECT 1" > /dev/null 2>&1; then
        ok "PostgreSQL on bluefin reachable (WireGuard)"
    elif timeout 5 psql -h 100.112.254.96 -U claude -d zammad_production -c "SELECT 1" > /dev/null 2>&1; then
        ok "PostgreSQL on bluefin reachable (Tailscale)"
    else
        warn "Cannot reach PostgreSQL on bluefin. Check network/firewall."
    fi
else
    warn "psql not installed. Install: sudo apt install postgresql-client"
fi

# --- Step 7: SSH key check ---
echo "--- Step 7: SSH keys ---"
if [[ -f "$HOMEDIR/.ssh/authorized_keys" ]]; then
    KEY_COUNT=$(wc -l < "$HOMEDIR/.ssh/authorized_keys")
    ok "$KEY_COUNT SSH key(s) in authorized_keys"
else
    warn "No SSH keys configured. User should add their public key to $HOMEDIR/.ssh/authorized_keys"
fi

# --- Summary ---
echo
echo "========================================"
echo " Onboard complete: $USER @ $HOSTNAME"
echo "========================================"
echo " FreeIPA UID:  $IPA_UID"
echo " Home:         $HOMEDIR"
echo " Sudo:         NOPASSWD ALL"
echo " Group:        ganuda-dev"
echo " Next steps:"
echo "   - User should log in and verify: id && ls -la ~"
echo "   - Set FreeIPA password if needed: ipa passwd $USER (from silverfin)"
echo "   - Add SSH key if not present"
echo "========================================"
