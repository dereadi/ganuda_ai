#!/bin/bash
#
# Cherokee AI Federation - macOS Node Bootstrap
# Run with: sudo bash bootstrap-macos-node.sh [hostname]
# Example:  sudo bash bootstrap-macos-node.sh thunderduck
#
# What it does:
#   1. Creates /Users/Shared/ganuda/ directory structure
#   2. Installs Homebrew (if missing) + common packages
#   3. Deploys launchd wrapper scripts to /usr/local/bin/
#   4. Configures NOPASSWD sudoers for wrapper scripts
#   5. Configures Munki client (pointing to sasass2:8080)
#   6. Installs munkitools (if missing)
#

set -euo pipefail

# --- Configuration ---
MUNKI_SERVER="http://192.168.132.242:8080"
GANUDA_BASE="/Users/Shared/ganuda"
GANUDA_USER="dereadi"
LOGFILE="/Users/Shared/ganuda/logs/bootstrap.log"

# --- Argument parsing ---
HOSTNAME="${1:-}"
if [[ -z "$HOSTNAME" ]]; then
    echo "Usage: sudo bash $0 <hostname>"
    echo "  hostname: Node name (e.g., thunderduck, sasass, sasass2, bmasass)"
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
    echo "Error: Must run as root (sudo)."
    exit 1
fi

# --- Logging ---
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOGFILE" 2>/dev/null || true
}

# ============================================================
# Phase 1: Directory structure
# ============================================================
log "=== Phase 1: Directory structure ==="

for dir in config scripts scripts/launchd logs lib docs; do
    mkdir -p "$GANUDA_BASE/$dir"
done
chown -R "$GANUDA_USER:staff" "$GANUDA_BASE"
mkdir -p /var/log/ganuda
chown "$GANUDA_USER:staff" /var/log/ganuda

log "Created $GANUDA_BASE directory tree"

# ============================================================
# Phase 2: Homebrew + common packages
# ============================================================
log "=== Phase 2: Homebrew + packages ==="

BREW_PATH="/opt/homebrew/bin/brew"
if [[ ! -x "$BREW_PATH" ]] && [[ ! -x "/usr/local/bin/brew" ]]; then
    log "Installing Homebrew..."
    sudo -u "$GANUDA_USER" /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    log "Homebrew already installed"
fi

# Resolve brew path
if [[ -x "/opt/homebrew/bin/brew" ]]; then
    BREW_PATH="/opt/homebrew/bin/brew"
elif [[ -x "/usr/local/bin/brew" ]]; then
    BREW_PATH="/usr/local/bin/brew"
fi

PACKAGES="python3 git curl jq htop rsync postgresql@16 watch"
for pkg in $PACKAGES; do
    if sudo -u "$GANUDA_USER" "$BREW_PATH" list "$pkg" &>/dev/null; then
        log "  $pkg: already installed"
    else
        log "  $pkg: installing..."
        sudo -u "$GANUDA_USER" "$BREW_PATH" install "$pkg" 2>&1 | tail -1
    fi
done

# ============================================================
# Phase 3: Launchd wrapper scripts
# ============================================================
log "=== Phase 3: Launchd wrapper scripts ==="

# --- ganuda-deploy-launchd ---
cat > /usr/local/bin/ganuda-deploy-launchd << 'WRAPPER_DEPLOY'
#!/bin/bash
#
# ganuda-deploy-launchd — Deploy a staged .plist to /Library/LaunchDaemons/
# Usage: sudo ganuda-deploy-launchd <service-label> [--dry-run]
#

STAGING_DIR="/Users/Shared/ganuda/scripts/launchd"
TARGET_DIR="/Library/LaunchDaemons"
LOGFILE="/Users/Shared/ganuda/logs/service-deploy.log"

log_action() {
    local timestamp
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "$timestamp - $1 - $2 - $3" >> "$LOGFILE"
}

# Load secrets for Telegram if available
if [[ -f /Users/Shared/ganuda/config/secrets.env ]]; then
    source /Users/Shared/ganuda/config/secrets.env
fi

send_notification() {
    local message="$1"
    if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]] && [[ -n "${TELEGRAM_CHIEF_CHAT_ID:-}" ]]; then
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d "chat_id=$TELEGRAM_CHIEF_CHAT_ID&text=$message" > /dev/null
    fi
}

SERVICE_LABEL="$1"
DRY_RUN="${2:-}"

if [[ -z "$SERVICE_LABEL" ]]; then
    echo "Usage: sudo ganuda-deploy-launchd <service-label> [--dry-run]"
    exit 1
fi

# Path traversal check
if [[ "$SERVICE_LABEL" =~ / ]]; then
    echo "Error: Invalid service label. No path traversal allowed."
    exit 1
fi

PLIST_NAME="${SERVICE_LABEL}.plist"
SOURCE_FILE="$STAGING_DIR/$PLIST_NAME"

if [[ ! -f "$SOURCE_FILE" ]]; then
    echo "Error: Plist not found at $SOURCE_FILE"
    exit 2
fi

# Validate plist format
if ! /usr/bin/plutil -lint "$SOURCE_FILE" &>/dev/null; then
    echo "Error: Invalid plist format."
    exit 3
fi

if [[ "$DRY_RUN" == "--dry-run" ]]; then
    echo "Dry run: Would copy $SOURCE_FILE to $TARGET_DIR/"
    echo "Dry run: Would run launchctl bootstrap system $TARGET_DIR/$PLIST_NAME"
    exit 0
fi

# Unload existing if present
if launchctl print "system/$SERVICE_LABEL" &>/dev/null; then
    launchctl bootout "system/$SERVICE_LABEL" 2>/dev/null || true
fi

cp "$SOURCE_FILE" "$TARGET_DIR/$PLIST_NAME"
chown root:wheel "$TARGET_DIR/$PLIST_NAME"
chmod 644 "$TARGET_DIR/$PLIST_NAME"
launchctl bootstrap system "$TARGET_DIR/$PLIST_NAME"

# Verify
sleep 2
if launchctl print "system/$SERVICE_LABEL" &>/dev/null; then
    RESULT="Success"
    log_action "Deployed" "$SERVICE_LABEL" "Success"
    send_notification "Service $SERVICE_LABEL deployed on $(hostname) at $(date) — Success"
    echo "Service $SERVICE_LABEL deployed and running."
    exit 0
else
    RESULT="Failed"
    log_action "Deployed" "$SERVICE_LABEL" "Failed"
    send_notification "Service $SERVICE_LABEL FAILED to start on $(hostname) at $(date)"
    echo "Error: Service $SERVICE_LABEL failed to start."
    exit 5
fi
WRAPPER_DEPLOY

chmod 755 /usr/local/bin/ganuda-deploy-launchd

# --- ganuda-launchd-ctl ---
cat > /usr/local/bin/ganuda-launchd-ctl << 'WRAPPER_CTL'
#!/bin/bash
#
# ganuda-launchd-ctl — Manage launchd services
# Usage: sudo ganuda-launchd-ctl <start|stop|restart|status> <service-label>
#

LOGFILE="/Users/Shared/ganuda/logs/service-ctl.log"

log_action() {
    local timestamp
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "$timestamp - Action: $1, Service: $2, Result: $3" >> "$LOGFILE"
}

if [[ -f /Users/Shared/ganuda/config/secrets.env ]]; then
    source /Users/Shared/ganuda/config/secrets.env
fi

send_notification() {
    local message="$1"
    if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]] && [[ -n "${TELEGRAM_CHIEF_CHAT_ID:-}" ]]; then
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d "chat_id=$TELEGRAM_CHIEF_CHAT_ID&text=$message" > /dev/null
    fi
}

ACTION="$1"
SERVICE_LABEL="$2"

if [[ -z "$ACTION" ]] || [[ -z "$SERVICE_LABEL" ]]; then
    echo "Usage: sudo ganuda-launchd-ctl <start|stop|restart|status> <service-label>"
    exit 1
fi

# Path traversal check
if [[ "$SERVICE_LABEL" =~ / ]]; then
    echo "Error: Invalid service label."
    exit 1
fi

PLIST_PATH="/Library/LaunchDaemons/${SERVICE_LABEL}.plist"

case "$ACTION" in
    start)
        if [[ ! -f "$PLIST_PATH" ]]; then
            echo "Error: Plist not found at $PLIST_PATH"
            exit 2
        fi
        launchctl bootstrap system "$PLIST_PATH" 2>/dev/null || launchctl kickstart "system/$SERVICE_LABEL"
        log_action "start" "$SERVICE_LABEL" "Issued"
        send_notification "Action: start, Service: $SERVICE_LABEL, Host: $(hostname), Time: $(date)"
        ;;
    stop)
        launchctl bootout "system/$SERVICE_LABEL" 2>/dev/null
        log_action "stop" "$SERVICE_LABEL" "Issued"
        send_notification "Action: stop, Service: $SERVICE_LABEL, Host: $(hostname), Time: $(date)"
        ;;
    restart)
        launchctl bootout "system/$SERVICE_LABEL" 2>/dev/null
        sleep 1
        if [[ -f "$PLIST_PATH" ]]; then
            launchctl bootstrap system "$PLIST_PATH"
        fi
        log_action "restart" "$SERVICE_LABEL" "Issued"
        send_notification "Action: restart, Service: $SERVICE_LABEL, Host: $(hostname), Time: $(date)"
        ;;
    status)
        if launchctl print "system/$SERVICE_LABEL" &>/dev/null; then
            PID=$(launchctl print "system/$SERVICE_LABEL" 2>/dev/null | grep 'pid =' | awk '{print $3}')
            echo "$SERVICE_LABEL: running (PID ${PID:-unknown})"
        else
            echo "$SERVICE_LABEL: not running"
        fi
        ;;
    *)
        echo "Error: Invalid action. Use: start, stop, restart, status"
        exit 1
        ;;
esac
WRAPPER_CTL

chmod 755 /usr/local/bin/ganuda-launchd-ctl

log "Deployed ganuda-deploy-launchd and ganuda-launchd-ctl to /usr/local/bin/"

# ============================================================
# Phase 4: Sudoers NOPASSWD
# ============================================================
log "=== Phase 4: Sudoers configuration ==="

SUDOERS_FILE="/etc/sudoers.d/ganuda-service-mgmt"
SUDOERS_CONTENT="$GANUDA_USER ALL=(root) NOPASSWD: /usr/local/bin/ganuda-deploy-launchd, /usr/local/bin/ganuda-launchd-ctl"

echo "$SUDOERS_CONTENT" > "$SUDOERS_FILE"
chmod 440 "$SUDOERS_FILE"
chown root:wheel "$SUDOERS_FILE"

# Validate
if visudo -cf "$SUDOERS_FILE" &>/dev/null; then
    log "Sudoers rule installed and validated"
else
    log "ERROR: Sudoers validation failed — removing"
    rm -f "$SUDOERS_FILE"
    exit 1
fi

# ============================================================
# Phase 5: Munki client configuration
# ============================================================
log "=== Phase 5: Munki client configuration ==="

# Check if munkitools installed
if [[ -x /usr/local/munki/managedsoftwareupdate ]]; then
    log "munkitools already installed"
else
    log "munkitools not installed — download from https://github.com/munki/munki/releases"
    log "  (Munki requires a signed .pkg, cannot be installed via script)"
    log "  After installing: re-run this script or set prefs manually"
fi

# Configure Munki preferences regardless
defaults write /Library/Preferences/ManagedInstalls SoftwareRepoURL "$MUNKI_SERVER"
defaults write /Library/Preferences/ManagedInstalls ClientIdentifier "$HOSTNAME"
defaults write /Library/Preferences/ManagedInstalls InstallAppleSoftwareUpdates -bool false
defaults write /Library/Preferences/ManagedInstalls SuppressUserNotification -bool true

log "Munki client configured: server=$MUNKI_SERVER, identifier=$HOSTNAME"

# ============================================================
# Phase 6: Set hostname
# ============================================================
log "=== Phase 6: Hostname configuration ==="

scutil --set ComputerName "$HOSTNAME"
scutil --set LocalHostName "$HOSTNAME"
scutil --set HostName "${HOSTNAME}.cherokee.local"

log "Hostname set to $HOSTNAME / ${HOSTNAME}.cherokee.local"

# ============================================================
# Summary
# ============================================================
log ""
log "=== Bootstrap Complete ==="
log "  Node:       $HOSTNAME"
log "  Ganuda:     $GANUDA_BASE"
log "  Sudoers:    $SUDOERS_FILE"
log "  Munki:      $MUNKI_SERVER (id=$HOSTNAME)"
log "  Wrapper:    /usr/local/bin/ganuda-deploy-launchd"
log "  Wrapper:    /usr/local/bin/ganuda-launchd-ctl"
log ""
log "  Next steps:"
log "    1. Install munkitools if not present (signed .pkg from GitHub)"
log "    2. Copy secrets.env to $GANUDA_BASE/config/ for Telegram alerts"
log "    3. Stage .plist files in $GANUDA_BASE/scripts/launchd/"
log "    4. Deploy services: sudo ganuda-deploy-launchd <label>"
log ""
log "  Test NOPASSWD:"
log "    sudo -n ganuda-launchd-ctl status com.cherokee.mlx-deepseek-r1"
