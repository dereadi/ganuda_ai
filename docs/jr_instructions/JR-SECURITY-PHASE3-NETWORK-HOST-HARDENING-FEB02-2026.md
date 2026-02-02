# JR Instruction: Security Phase 3 - Network & Host Hardening

**Task ID:** SECURITY-PHASE3-NET-HOST
**Priority:** P1
**Assigned:** DevOps Jr
**Created:** 2026-02-02
**Author:** TPM (Claude Opus 4.5)

---

## Situation

The Cherokee AI Federation operates 6 nodes on the 192.168.132.x subnet. A security audit has identified the following gaps:

- **nftables.conf is essentially empty** -- no firewall rules protecting inter-node or external traffic
- **No fail2ban** -- brute-force and credential-stuffing attacks go undetected
- **Caddy reverse proxy lacks security headers** -- missing HSTS, CSP, X-Frame-Options, etc.
- **PostgreSQL connections are unencrypted** -- credentials and query data traverse the network in plaintext
- **No auditd / pgAudit** -- no audit trail for database operations

This instruction creates all configuration files and deployment scripts to close these gaps. The executor creates files under `/ganuda/config/` and `/ganuda/scripts/`. Actual deployment to system paths requires admin action.

---

## CRITICAL EXECUTOR RULES

1. **NO SEARCH/REPLACE blocks** -- do not use any search-and-replace editing patterns
2. **Use `bash` code blocks only** -- all file creation via heredoc in bash
3. **Commands requiring sudo are marked `REQUIRES ADMIN`** -- the executor cannot sudo
4. **Config files are created under /ganuda/ -- deployment to system paths is a separate admin action**
5. **Do NOT modify any existing system files directly**

---

## Step 1: Create nftables Firewall Rules

### Step 1a: Redfin (Public-Facing Node) Firewall

Create `/ganuda/config/nftables-redfin.conf`:

```bash
mkdir -p /ganuda/config

cat > /ganuda/config/nftables-redfin.conf << 'NFTEOF'
#!/usr/sbin/nft -f
#
# nftables firewall rules for Redfin (public-facing node)
# Cherokee AI Federation - Security Phase 3
# Generated: 2026-02-02
#
# REQUIRES ADMIN: Deploy with:
#   sudo cp /ganuda/config/nftables-redfin.conf /etc/nftables.conf
#   sudo systemctl restart nftables
#   sudo systemctl enable nftables

flush ruleset

table inet filter {

    # ---------------------------------------------------------------
    # Rate-limit sets
    # ---------------------------------------------------------------
    set ssh_meter {
        type ipv4_addr
        flags dynamic
        timeout 1m
    }

    set http_meter {
        type ipv4_addr
        flags dynamic
        timeout 1m
    }

    # ---------------------------------------------------------------
    # INPUT chain - default DROP
    # ---------------------------------------------------------------
    chain input {
        type filter hook input priority 0; policy drop;

        # --- Loopback ---
        iif "lo" accept

        # --- Connection tracking ---
        ct state established,related accept
        ct state invalid drop

        # --- ICMP (internal only) ---
        ip saddr 192.168.132.0/24 icmp type { echo-request, echo-reply, destination-unreachable, time-exceeded } accept

        # --- SSH (internal only, rate limited) ---
        ip saddr 192.168.132.0/24 tcp dport 22 ct state new \
            add @ssh_meter { ip saddr limit rate 3/minute burst 5 packets } accept
        ip saddr 192.168.132.0/24 tcp dport 22 ct state new \
            log prefix "[nft-ssh-ratelimit] " drop

        # --- HTTP/HTTPS (public, rate limited) ---
        tcp dport { 80, 443 } ct state new \
            add @http_meter { ip saddr limit rate 100/minute burst 150 packets } accept
        tcp dport { 80, 443 } ct state new \
            log prefix "[nft-http-ratelimit] " drop

        # --- LLM Gateway 8080 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 8080 accept

        # --- vLLM 8000 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 8000 accept

        # --- Kanban 3001 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 3001 accept

        # --- SAG 4000 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 4000 accept

        # --- Log and drop everything else ---
        log prefix "[nft-input-drop] " flags all counter drop
    }

    # ---------------------------------------------------------------
    # FORWARD chain - default DROP (not a router)
    # ---------------------------------------------------------------
    chain forward {
        type filter hook forward priority 0; policy drop;
    }

    # ---------------------------------------------------------------
    # OUTPUT chain - allow all outbound
    # ---------------------------------------------------------------
    chain output {
        type filter hook output priority 0; policy accept;
    }
}
NFTEOF

chmod 644 /ganuda/config/nftables-redfin.conf
echo "[OK] Created /ganuda/config/nftables-redfin.conf"
```

### Step 1b: Bluefin (Database/Monitoring Node) Firewall

Create `/ganuda/config/nftables-bluefin.conf`:

```bash
cat > /ganuda/config/nftables-bluefin.conf << 'NFTEOF'
#!/usr/sbin/nft -f
#
# nftables firewall rules for Bluefin (database/monitoring node)
# Cherokee AI Federation - Security Phase 3
# Generated: 2026-02-02
#
# REQUIRES ADMIN: Deploy with:
#   sudo cp /ganuda/config/nftables-bluefin.conf /etc/nftables.conf
#   sudo systemctl restart nftables
#   sudo systemctl enable nftables

flush ruleset

table inet filter {

    # ---------------------------------------------------------------
    # Rate-limit sets
    # ---------------------------------------------------------------
    set ssh_meter {
        type ipv4_addr
        flags dynamic
        timeout 1m
    }

    set pg_meter {
        type ipv4_addr
        flags dynamic
        timeout 1m
    }

    # ---------------------------------------------------------------
    # INPUT chain - default DROP
    # ---------------------------------------------------------------
    chain input {
        type filter hook input priority 0; policy drop;

        # --- Loopback ---
        iif "lo" accept

        # --- Connection tracking ---
        ct state established,related accept
        ct state invalid drop

        # --- ICMP (internal only) ---
        ip saddr 192.168.132.0/24 icmp type { echo-request, echo-reply, destination-unreachable, time-exceeded } accept

        # --- SSH (internal only, rate limited) ---
        ip saddr 192.168.132.0/24 tcp dport 22 ct state new \
            add @ssh_meter { ip saddr limit rate 3/minute burst 5 packets } accept
        ip saddr 192.168.132.0/24 tcp dport 22 ct state new \
            log prefix "[nft-ssh-ratelimit] " drop

        # --- PostgreSQL 5432 (internal only, rate limited) ---
        ip saddr 192.168.132.0/24 tcp dport 5432 ct state new \
            add @pg_meter { ip saddr limit rate 50/minute burst 75 packets } accept
        ip saddr 192.168.132.0/24 tcp dport 5432 ct state new \
            log prefix "[nft-pg-ratelimit] " drop

        # --- Grafana 3000 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 3000 accept

        # --- Log and drop everything else ---
        log prefix "[nft-input-drop] " flags all counter drop
    }

    # ---------------------------------------------------------------
    # FORWARD chain - default DROP
    # ---------------------------------------------------------------
    chain forward {
        type filter hook forward priority 0; policy drop;
    }

    # ---------------------------------------------------------------
    # OUTPUT chain - allow all outbound
    # ---------------------------------------------------------------
    chain output {
        type filter hook output priority 0; policy accept;
    }
}
NFTEOF

chmod 644 /ganuda/config/nftables-bluefin.conf
echo "[OK] Created /ganuda/config/nftables-bluefin.conf"
```

---

## Step 2: Create fail2ban Configuration

### Step 2a: Jail Configuration

Create `/ganuda/config/fail2ban-jail.local`:

```bash
cat > /ganuda/config/fail2ban-jail.local << 'F2BEOF'
# fail2ban jail configuration
# Cherokee AI Federation - Security Phase 3
# Generated: 2026-02-02
#
# REQUIRES ADMIN: Deploy with:
#   sudo cp /ganuda/config/fail2ban-jail.local /etc/fail2ban/jail.local
#   sudo cp /ganuda/config/fail2ban-action-telegram.conf /etc/fail2ban/action.d/telegram.conf
#   sudo systemctl restart fail2ban
#   sudo systemctl enable fail2ban

[DEFAULT]
# Internal network is whitelisted from bans
ignoreip = 127.0.0.1/8 ::1 192.168.132.0/24

# Default ban action: iptables + telegram notification
banaction = nftables-multiport
action = %(action_)s
         telegram[name=%(__name__)s]

# Default settings
findtime = 10m
bantime = 1h
maxretry = 5

# -------------------------------------------------------------------
# SSH Jail
# 3 failures in 10 minutes = ban 1 hour
# -------------------------------------------------------------------
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
findtime = 10m
bantime = 1h

# -------------------------------------------------------------------
# HTTP Auth Jail (Caddy / generic web auth)
# 5 failures in 5 minutes = ban 30 minutes
# -------------------------------------------------------------------
[caddy-auth]
enabled = true
port = http,https
filter = caddy-auth
logpath = /var/log/caddy/access.log
maxretry = 5
findtime = 5m
bantime = 30m

# -------------------------------------------------------------------
# PostgreSQL Jail
# 3 failures in 5 minutes = ban 1 hour
# -------------------------------------------------------------------
[postgresql]
enabled = true
port = 5432
filter = postgresql
logpath = /var/log/postgresql/postgresql-*-main.log
maxretry = 3
findtime = 5m
bantime = 1h

# -------------------------------------------------------------------
# Recidive Jail (repeat offenders)
# 3 bans in 24 hours = ban 1 week
# -------------------------------------------------------------------
[recidive]
enabled = true
filter = recidive
logpath = /var/log/fail2ban.log
maxretry = 3
findtime = 1d
bantime = 1w
action = %(action_)s
         telegram[name=recidive]
F2BEOF

chmod 644 /ganuda/config/fail2ban-jail.local
echo "[OK] Created /ganuda/config/fail2ban-jail.local"
```

### Step 2b: Caddy Auth Filter (for fail2ban)

Create `/ganuda/config/fail2ban-filter-caddy-auth.conf`:

```bash
cat > /ganuda/config/fail2ban-filter-caddy-auth.conf << 'FILTEREOF'
# fail2ban filter for Caddy authentication failures
# Cherokee AI Federation - Security Phase 3
#
# REQUIRES ADMIN: Deploy with:
#   sudo cp /ganuda/config/fail2ban-filter-caddy-auth.conf /etc/fail2ban/filter.d/caddy-auth.conf

[Definition]
failregex = ^.*"remote_ip":"<HOST>".*"status":401.*$
            ^.*"remote_ip":"<HOST>".*"status":403.*$
ignoreregex =
FILTEREOF

chmod 644 /ganuda/config/fail2ban-filter-caddy-auth.conf
echo "[OK] Created /ganuda/config/fail2ban-filter-caddy-auth.conf"
```

### Step 2c: PostgreSQL Filter (for fail2ban)

Create `/ganuda/config/fail2ban-filter-postgresql.conf`:

```bash
cat > /ganuda/config/fail2ban-filter-postgresql.conf << 'FILTEREOF'
# fail2ban filter for PostgreSQL authentication failures
# Cherokee AI Federation - Security Phase 3
#
# REQUIRES ADMIN: Deploy with:
#   sudo cp /ganuda/config/fail2ban-filter-postgresql.conf /etc/fail2ban/filter.d/postgresql.conf

[Definition]
failregex = ^.*FATAL:  password authentication failed for user .* from <HOST>.*$
            ^.*FATAL:  no pg_hba.conf entry for host "<HOST>".*$
ignoreregex =
FILTEREOF

chmod 644 /ganuda/config/fail2ban-filter-postgresql.conf
echo "[OK] Created /ganuda/config/fail2ban-filter-postgresql.conf"
```

### Step 2d: Telegram Notification Action

Create `/ganuda/config/fail2ban-action-telegram.conf`:

```bash
cat > /ganuda/config/fail2ban-action-telegram.conf << 'ACTIONEOF'
# fail2ban action: Send Telegram notification on ban/unban
# Cherokee AI Federation - Security Phase 3
#
# REQUIRES ADMIN: Deploy with:
#   sudo cp /ganuda/config/fail2ban-action-telegram.conf /etc/fail2ban/action.d/telegram.conf
#
# Environment requirement: TELEGRAM_BOT_TOKEN must be set in
#   /etc/fail2ban/fail2ban.local or /etc/default/fail2ban

[Definition]

# Option: actionstart
# Notes:  Command executed on jail start
actionstart =

# Option: actionstop
# Notes:  Command executed on jail stop
actionstop =

# Option: actioncheck
# Notes:  Command executed before each ban
actioncheck =

# Option: actionban
# Notes:  Command executed when banning an IP
actionban = /usr/bin/curl -s -X POST \
              "https://api.telegram.org/bot<telegram_token>/sendMessage" \
              -d chat_id="<telegram_chat_id>" \
              -d parse_mode="Markdown" \
              -d text="*[FAIL2BAN ALERT]* %0A*Node:* $(hostname) %0A*Jail:* <name> %0A*Action:* BAN %0A*IP:* <ip> %0A*Failures:* <failures> %0A*Time:* $(date '+%%Y-%%m-%%d %%H:%%M:%%S %%Z')" \
              > /dev/null 2>&1

# Option: actionunban
# Notes:  Command executed when unbanning an IP
actionunban = /usr/bin/curl -s -X POST \
                "https://api.telegram.org/bot<telegram_token>/sendMessage" \
                -d chat_id="<telegram_chat_id>" \
                -d parse_mode="Markdown" \
                -d text="*[FAIL2BAN INFO]* %0A*Node:* $(hostname) %0A*Jail:* <name> %0A*Action:* UNBAN %0A*IP:* <ip> %0A*Time:* $(date '+%%Y-%%m-%%d %%H:%%M:%%S %%Z')" \
                > /dev/null 2>&1

[Init]
# Telegram bot token -- override in jail.local or /etc/default/fail2ban
telegram_token = TELEGRAM_BOT_TOKEN_PLACEHOLDER
# Telegram chat ID for security alerts channel
telegram_chat_id = TELEGRAM_CHAT_ID_PLACEHOLDER
ACTIONEOF

chmod 644 /ganuda/config/fail2ban-action-telegram.conf
echo "[OK] Created /ganuda/config/fail2ban-action-telegram.conf"
```

---

## Step 3: Create Caddy Security Headers Config

Create `/ganuda/config/Caddyfile.security-headers`:

```bash
cat > /ganuda/config/Caddyfile.security-headers << 'CADDYEOF'
# Caddy security headers snippet
# Cherokee AI Federation - Security Phase 3
# Generated: 2026-02-02
#
# Usage: Import this snippet in your Caddyfile site blocks:
#
#   import /etc/caddy/Caddyfile.security-headers
#
#   vetassist.ganuda.org {
#       import security_headers
#       reverse_proxy localhost:8000
#   }
#
# REQUIRES ADMIN: Deploy with:
#   sudo cp /ganuda/config/Caddyfile.security-headers /etc/caddy/Caddyfile.security-headers
#   sudo caddy validate --config /etc/caddy/Caddyfile
#   sudo systemctl reload caddy

(security_headers) {
    header {
        # HSTS - enforce HTTPS for 1 year including subdomains
        Strict-Transport-Security "max-age=31536000; includeSubDomains"

        # Prevent MIME-type sniffing
        X-Content-Type-Options "nosniff"

        # Prevent clickjacking
        X-Frame-Options "DENY"

        # XSS protection (legacy browsers)
        X-XSS-Protection "1; mode=block"

        # Control referrer information
        Referrer-Policy "strict-origin-when-cross-origin"

        # Content Security Policy
        Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws: wss:"

        # Disable browser features we do not use
        Permissions-Policy "camera=(), microphone=(), geolocation=()"

        # Remove server identification header
        -Server
    }
}
CADDYEOF

chmod 644 /ganuda/config/Caddyfile.security-headers
echo "[OK] Created /ganuda/config/Caddyfile.security-headers"
```

---

## Step 4: Create PostgreSQL SSL Configuration

### Step 4a: PostgreSQL SSL Settings

Create `/ganuda/config/postgresql-ssl.conf`:

```bash
cat > /ganuda/config/postgresql-ssl.conf << 'PGEOF'
# PostgreSQL SSL configuration
# Cherokee AI Federation - Security Phase 3
# Generated: 2026-02-02
#
# REQUIRES ADMIN: Append to postgresql.conf or include via:
#   include = '/etc/postgresql/16/main/conf.d/ssl.conf'
#
# Deploy:
#   sudo cp /ganuda/config/postgresql-ssl.conf /etc/postgresql/16/main/conf.d/ssl.conf
#   sudo chown postgres:postgres /etc/postgresql/16/main/conf.d/ssl.conf
#   sudo systemctl restart postgresql

# Enable SSL
ssl = on

# Certificate paths (generated by generate_pg_ssl_certs.sh)
ssl_cert_file = '/etc/postgresql/16/main/server.crt'
ssl_key_file = '/etc/postgresql/16/main/server.key'

# Minimum TLS version -- reject anything below TLS 1.2
ssl_min_protocol_version = 'TLSv1.2'

# Strong cipher suites only -- no NULL or MD5
ssl_ciphers = 'HIGH:!aNULL:!MD5'

# Prefer server cipher order
ssl_prefer_server_ciphers = on
PGEOF

chmod 644 /ganuda/config/postgresql-ssl.conf
echo "[OK] Created /ganuda/config/postgresql-ssl.conf"
```

### Step 4b: SSL Certificate Generation Script

Create `/ganuda/scripts/generate_pg_ssl_certs.sh`:

```bash
mkdir -p /ganuda/scripts

cat > /ganuda/scripts/generate_pg_ssl_certs.sh << 'CERTEOF'
#!/usr/bin/env bash
#
# Generate self-signed SSL certificates for PostgreSQL
# Cherokee AI Federation - Security Phase 3
# Generated: 2026-02-02
#
# REQUIRES ADMIN: Run as root or with sudo:
#   sudo bash /ganuda/scripts/generate_pg_ssl_certs.sh
#
set -euo pipefail

PG_CONF_DIR="/etc/postgresql/16/main"
CERT_FILE="${PG_CONF_DIR}/server.crt"
KEY_FILE="${PG_CONF_DIR}/server.key"
DAYS_VALID=3650  # 10 years for internal use

echo "=== PostgreSQL SSL Certificate Generator ==="
echo "Target directory: ${PG_CONF_DIR}"
echo ""

# Check if certs already exist
if [[ -f "${CERT_FILE}" && -f "${KEY_FILE}" ]]; then
    echo "[WARN] Certificates already exist at:"
    echo "  ${CERT_FILE}"
    echo "  ${KEY_FILE}"
    read -rp "Overwrite? (y/N): " CONFIRM
    if [[ "${CONFIRM}" != "y" && "${CONFIRM}" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# Generate private key and self-signed certificate
echo "[1/4] Generating private key and self-signed certificate..."
openssl req -new -x509 -nodes \
    -days ${DAYS_VALID} \
    -keyout "${KEY_FILE}" \
    -out "${CERT_FILE}" \
    -subj "/C=US/ST=NC/L=Cherokee/O=Ganuda Federation/CN=$(hostname -f)" \
    2>/dev/null

echo "[2/4] Setting key permissions to 600 (owner read/write only)..."
chmod 600 "${KEY_FILE}"

echo "[3/4] Setting cert permissions to 644 (world readable)..."
chmod 644 "${CERT_FILE}"

echo "[4/4] Setting ownership to postgres:postgres..."
chown postgres:postgres "${CERT_FILE}" "${KEY_FILE}"

echo ""
echo "=== Certificate Details ==="
openssl x509 -in "${CERT_FILE}" -noout -subject -dates -fingerprint
echo ""
echo "[OK] SSL certificates generated successfully."
echo ""
echo "Next steps:"
echo "  1. Deploy SSL config:  sudo cp /ganuda/config/postgresql-ssl.conf ${PG_CONF_DIR}/conf.d/ssl.conf"
echo "  2. Restart PostgreSQL: sudo systemctl restart postgresql"
echo "  3. Verify SSL:         sudo -u postgres psql -c 'SHOW ssl;'"
CERTEOF

chmod 755 /ganuda/scripts/generate_pg_ssl_certs.sh
echo "[OK] Created /ganuda/scripts/generate_pg_ssl_certs.sh"
```

---

## Step 5: Create pgAudit Configuration

Create `/ganuda/config/pgaudit.conf`:

```bash
cat > /ganuda/config/pgaudit.conf << 'AUDITEOF'
# pgAudit configuration for PostgreSQL
# Cherokee AI Federation - Security Phase 3
# Generated: 2026-02-02
#
# Prerequisites (REQUIRES ADMIN):
#   sudo apt-get install postgresql-16-pgaudit
#   -- Then add to postgresql.conf:
#   shared_preload_libraries = 'pgaudit'
#   -- Then deploy this config:
#   sudo cp /ganuda/config/pgaudit.conf /etc/postgresql/16/main/conf.d/pgaudit.conf
#   sudo chown postgres:postgres /etc/postgresql/16/main/conf.d/pgaudit.conf
#   sudo systemctl restart postgresql
#   -- Then enable the extension:
#   sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS pgaudit;"

# Audit read (SELECT), write (INSERT/UPDATE/DELETE), and DDL operations
pgaudit.log = 'read, write, ddl'

# Do not log access to pg_catalog (reduces noise significantly)
pgaudit.log_catalog = off

# Log the object name for every statement (table/view/function)
pgaudit.log_relation = on

# Log query parameters -- critical for forensics
# WARNING: This will include sensitive values in logs.
# Ensure log files have restricted permissions.
pgaudit.log_parameter = on

# Log the statement text along with the audit entry
pgaudit.log_statement_once = off
AUDITEOF

chmod 644 /ganuda/config/pgaudit.conf
echo "[OK] Created /ganuda/config/pgaudit.conf"
```

---

## Step 6: Create Deployment Script

Create `/ganuda/scripts/deploy_security_hardening.sh`:

```bash
cat > /ganuda/scripts/deploy_security_hardening.sh << 'DEPLOYEOF'
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
DEPLOYEOF

chmod 755 /ganuda/scripts/deploy_security_hardening.sh
echo "[OK] Created /ganuda/scripts/deploy_security_hardening.sh"
```

---

## Step 7: Validation

After all files are created, run the following checks:

```bash
echo "=== Validation: Verify all config files exist ==="
EXPECTED_FILES=(
    "/ganuda/config/nftables-redfin.conf"
    "/ganuda/config/nftables-bluefin.conf"
    "/ganuda/config/fail2ban-jail.local"
    "/ganuda/config/fail2ban-filter-caddy-auth.conf"
    "/ganuda/config/fail2ban-filter-postgresql.conf"
    "/ganuda/config/fail2ban-action-telegram.conf"
    "/ganuda/config/Caddyfile.security-headers"
    "/ganuda/config/postgresql-ssl.conf"
    "/ganuda/config/pgaudit.conf"
    "/ganuda/scripts/generate_pg_ssl_certs.sh"
    "/ganuda/scripts/deploy_security_hardening.sh"
)

ALL_OK=true
for f in "${EXPECTED_FILES[@]}"; do
    if [[ -f "$f" ]]; then
        echo "[OK] $f"
    else
        echo "[MISSING] $f"
        ALL_OK=false
    fi
done

echo ""
echo "=== Validation: Check scripts are executable ==="
for s in /ganuda/scripts/generate_pg_ssl_certs.sh /ganuda/scripts/deploy_security_hardening.sh; do
    if [[ -x "$s" ]]; then
        echo "[OK] $s is executable"
    else
        echo "[FAIL] $s is NOT executable"
        ALL_OK=false
    fi
done

echo ""
if ${ALL_OK}; then
    echo "[PASS] All files created and validated."
else
    echo "[FAIL] Some files missing or misconfigured. Review output above."
fi
```

### Admin-Only Validation (REQUIRES ADMIN)

The following validation commands require sudo and should be run by an admin after deployment:

```bash
# REQUIRES ADMIN: Validate nftables syntax (dry run)
sudo nft -c -f /ganuda/config/nftables-redfin.conf
sudo nft -c -f /ganuda/config/nftables-bluefin.conf

# REQUIRES ADMIN: Validate fail2ban config
sudo fail2ban-client --test

# REQUIRES ADMIN: Validate Caddy config (after snippet is in place)
sudo caddy validate --config /etc/caddy/Caddyfile

# REQUIRES ADMIN: Dry-run the full deployment
sudo bash /ganuda/scripts/deploy_security_hardening.sh --dry-run
```

---

## Admin Deployment Checklist

After the executor completes all steps above, an admin must:

1. **Review all generated config files** in `/ganuda/config/`
2. **Update Telegram credentials** in `fail2ban-action-telegram.conf` (replace placeholders)
3. **Run deployment in dry-run mode first:**
   ```
   sudo bash /ganuda/scripts/deploy_security_hardening.sh --dry-run
   ```
4. **Deploy per-component** (recommended order):
   ```
   sudo bash /ganuda/scripts/deploy_security_hardening.sh --component caddy
   sudo bash /ganuda/scripts/deploy_security_hardening.sh --component postgresql
   sudo bash /ganuda/scripts/deploy_security_hardening.sh --component pgaudit
   sudo bash /ganuda/scripts/deploy_security_hardening.sh --component fail2ban
   sudo bash /ganuda/scripts/deploy_security_hardening.sh --component nftables  # last -- locks down network
   ```
5. **Verify connectivity** from another federation node after nftables deployment
6. **Update Caddyfile** site blocks to include `import security_headers`
7. **Verify PostgreSQL SSL** with: `sudo -u postgres psql -c "SHOW ssl;"`

---

## Rollback

If firewall rules lock you out:

```bash
# REQUIRES ADMIN: Emergency rollback -- connect via console/IPMI
sudo nft flush ruleset
sudo systemctl stop nftables
```

If fail2ban causes issues:

```bash
# REQUIRES ADMIN
sudo systemctl stop fail2ban
sudo fail2ban-client unban --all
```

If PostgreSQL SSL breaks connections:

```bash
# REQUIRES ADMIN
sudo rm /etc/postgresql/16/main/conf.d/ssl.conf
sudo systemctl restart postgresql
```

---

## Success Criteria

- [ ] All 11 config/script files created under `/ganuda/config/` and `/ganuda/scripts/`
- [ ] nftables configs enforce default-drop with explicit allow rules
- [ ] SSH restricted to internal subnet (192.168.132.0/24) on all nodes
- [ ] PostgreSQL port (5432) not exposed to public on any node
- [ ] Rate limiting in place for SSH (3/min) and HTTP (100/min)
- [ ] fail2ban configured with SSH, HTTP auth, PostgreSQL, and recidive jails
- [ ] Telegram alerting configured for ban events
- [ ] Caddy security headers snippet ready for import
- [ ] PostgreSQL SSL enabled with TLS 1.2 minimum
- [ ] pgAudit logging read, write, and DDL operations
- [ ] Deployment script supports dry-run mode and per-component deployment
- [ ] Rollback procedures documented
