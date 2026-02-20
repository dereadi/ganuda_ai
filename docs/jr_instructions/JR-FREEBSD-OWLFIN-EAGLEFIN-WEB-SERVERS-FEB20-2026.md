# Build Plan: FreeBSD 15.0 Web Servers — owlfin & eaglefin

**Task**: Stand up two FreeBSD 15.0-RELEASE web servers on VLAN 30 (direct AT&T internet)
**Priority**: 1 (HIGH — VetAssist needs public-facing infrastructure)
**Execution**: Chief-executed (new OS, new nodes — not in Jr executor ecosystem)
**Hardware**: 2x Beelink EQR5 — AMD Ryzen 5 5500U (6C/12T), 16GB DDR4, 500GB NVMe

## Architecture

```
CUSTOMER TRAFFIC:
Internet → AT&T (2 Gbps) → Port Forward 443 → VLAN 30
  → owlfin  (192.168.30.225) → Caddy → VetAssist Frontend
  → eaglefin (192.168.30.226) → Caddy → VetAssist Frontend (failover)

INTERNAL TRAFFIC (unchanged):
Federation nodes ↔ VLAN 1 (192.168.132.0/24) ↔ ExpressVPN
  → Database, LLM Gateway, inter-node — stays encrypted via VPN
```

owlfin and eaglefin sit on VLAN 30 ONLY. They do NOT touch VLAN 1/132. They are DMZ nodes — public-facing, hardened, isolated from the internal federation. Backend API calls go through Caddy reverse proxy to redfin on VLAN 1 via a controlled pf rule.

---

## Phase 1: FreeBSD Install (Chief — Physical)

### 1.1 Flash USB

On bmasass:
```text
curl -O https://download.freebsd.org/releases/amd64/amd64/ISO-IMAGES/15.0/FreeBSD-15.0-RELEASE-amd64-memstick.img.xz
xz -d FreeBSD-15.0-RELEASE-amd64-memstick.img.xz
sudo dd if=FreeBSD-15.0-RELEASE-amd64-memstick.img of=/dev/diskN bs=4m status=progress
```

### 1.2 BIOS Settings (Beelink EQR5)

- Boot: UEFI mode (not Legacy)
- Secure Boot: OFF (FreeBSD doesn't sign with Microsoft key by default)
- Wake on LAN: ON (for remote power management)
- Boot order: USB first (for install), NVMe after

### 1.3 Install Options

- **Filesystem**: ZFS (mirror not possible with single disk — use stripe/single vdev)
  - Pool name: `zroot`
  - Swap: 4GB zvol
  - Compression: lz4 (default)
  - Encryption: optional (adds CPU overhead, Ryzen 5 has AES-NI so minimal)
- **Partitioning**: Auto ZFS, entire disk
- **Network**: Configure during install if possible, or post-boot
- **Services to enable at install**: sshd
- **User**: Create `dereadi` user, add to `wheel` group
- **Root password**: Set it, then disable root SSH login post-boot
- **Time zone**: America/Chicago (CST)

Repeat for both nodes. Same config, different hostname.

---

## Phase 2: Post-Boot Base Configuration

### 2.1 Hostname

owlfin:
```text
sysrc hostname="owlfin"
hostname owlfin
```

eaglefin:
```text
sysrc hostname="eaglefin"
hostname eaglefin
```

### 2.2 /etc/hosts

```text
127.0.0.1       localhost
192.168.30.225  owlfin
192.168.30.226  eaglefin
192.168.132.223 redfin
192.168.132.222 bluefin
192.168.132.224 greenfin
```

### 2.3 Package Bootstrap

```text
pkg bootstrap
pkg update
pkg install -y sudo bash git curl wget nano vim htop tmux node20 npm-node20 caddy py311-pip python311
```

### 2.4 sudo for dereadi

```text
visudo
# Add line:
dereadi ALL=(ALL:ALL) ALL
```

Or:
```text
echo 'dereadi ALL=(ALL:ALL) ALL' > /usr/local/etc/sudoers.d/dereadi
chmod 440 /usr/local/etc/sudoers.d/dereadi
```

### 2.5 SSH Hardening

Edit `/etc/ssh/sshd_config`:
```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
AllowUsers dereadi
```

Copy SSH keys from redfin:
```text
mkdir -p /home/dereadi/.ssh
chmod 700 /home/dereadi/.ssh
# From redfin: scp ~/.ssh/authorized_keys dereadi@192.168.30.225:~/.ssh/
chmod 600 /home/dereadi/.ssh/authorized_keys
chown -R dereadi:dereadi /home/dereadi/.ssh
```

Restart sshd:
```text
service sshd restart
```

### 2.6 Ganuda Directory Structure

```text
mkdir -p /ganuda/{docs,lib,scripts,config,logs,www/{vetassist,static}}
chown -R dereadi:dereadi /ganuda
```

### 2.7 Time Sync (NTP)

```text
sysrc ntpd_enable="YES"
service ntpd start
```

### 2.8 Automatic Security Updates

```text
pkg install -y FreeBSD-Update
# freebsd-update is built-in on 15.0
# Add to crontab:
echo '0 3 * * * root freebsd-update cron' >> /etc/crontab
```

For pkg updates:
```text
pkg install -y periodic
# /etc/periodic.conf:
echo 'daily_status_security_pkgaudit_enable="YES"' >> /etc/periodic.conf
```

---

## Phase 3: VLAN 30 Networking

### 3.1 Identify NIC

```text
ifconfig
# Beelink EQR5 likely shows re0 or igc0 for the Realtek/Intel 1GbE
# Note the interface name — substitute below
```

### 3.2 Static IP on VLAN 30

The Beelinks connect directly to TP-Link switch ports assigned to VLAN 30 (untagged). No VLAN tagging needed on the host if the switch port is set to untagged VLAN 30.

Edit `/etc/rc.conf`:

owlfin:
```text
sysrc ifconfig_re0="inet 192.168.30.225 netmask 255.255.255.0"
sysrc defaultrouter="192.168.30.1"
```

eaglefin:
```text
sysrc ifconfig_re0="inet 192.168.30.226 netmask 255.255.255.0"
sysrc defaultrouter="192.168.30.1"
```

If the switch port is TAGGED VLAN 30 (trunk), then create a VLAN interface instead:
```text
sysrc vlans_re0="30"
sysrc ifconfig_re0_30="inet 192.168.30.225 netmask 255.255.255.0"
sysrc defaultrouter="192.168.30.1"
```

Apply:
```text
service netif restart
service routing restart
```

### 3.3 DNS

Edit `/etc/resolv.conf`:
```text
nameserver 8.8.8.8
nameserver 1.1.1.1
```

### 3.4 Verify Connectivity

```text
ping -c 3 192.168.30.1       # AT&T gateway
ping -c 3 8.8.8.8             # Internet via AT&T direct
ping -c 3 google.com          # DNS resolution
```

---

## Phase 4: pf Firewall

### 4.1 Enable pf

```text
sysrc pf_enable="YES"
sysrc pflog_enable="YES"
```

### 4.2 /etc/pf.conf

```text
# owlfin/eaglefin pf.conf — DMZ web server
# Cherokee AI Federation — Feb 2026

ext_if = "re0"  # Adjust to actual NIC name

# Tables
table <bruteforce> persist

# Options
set skip on lo0
set block-policy drop
set loginterface $ext_if

# Scrub
scrub in all

# NAT/RDR — none needed (direct IP)

# Default deny
block all

# Allow outbound
pass out on $ext_if proto { tcp udp } from ($ext_if) to any keep state
pass out on $ext_if proto icmp from ($ext_if) to any keep state

# Allow inbound web traffic
pass in on $ext_if proto tcp from any to ($ext_if) port { 80 443 } keep state

# Allow inbound SSH (rate-limited)
pass in on $ext_if proto tcp from any to ($ext_if) port 22 \
    flags S/SA keep state \
    (max-src-conn 5, max-src-conn-rate 3/30, overload <bruteforce> flush global)

# Block brute-force attackers
block quick from <bruteforce>

# Allow ICMP (ping) — useful for monitoring
pass in on $ext_if proto icmp from any to ($ext_if) icmp-type { echoreq unreach }

# Allow outbound to redfin backend API (VLAN 1 via routing)
# Only if a route exists to 192.168.132.0/24
pass out on $ext_if proto tcp from ($ext_if) to 192.168.132.223 port { 8001 8080 } keep state

# Allow outbound to bluefin DB (ONLY for read-only queries if needed)
# DISABLED by default — uncomment only if web servers need direct DB
# pass out on $ext_if proto tcp from ($ext_if) to 192.168.132.222 port 5432 keep state

# Logging
block log all
```

### 4.3 Load and Verify

```text
pfctl -nf /etc/pf.conf    # Syntax check (dry run)
service pf start
pfctl -sr                  # Show active rules
pfctl -si                  # Show stats
```

### 4.4 Brute-Force Table Management

Add to crontab — expire entries after 24 hours:
```text
# /etc/crontab
0 * * * * root pfctl -t bruteforce -T expire 86400
```

---

## Phase 5: Caddy Web Server

### 5.1 Install

```text
pkg install -y caddy
sysrc caddy_enable="YES"
```

### 5.2 /usr/local/etc/caddy/Caddyfile

#### Option A: With domain (Let's Encrypt auto-HTTPS)

```text
vetassist.cherokee-ai.org {
    # Frontend — static Next.js build served locally
    handle {
        root * /ganuda/www/vetassist
        file_server
        try_files {path} /index.html
    }

    # API calls → reverse proxy to redfin backend
    handle /api/* {
        reverse_proxy 192.168.132.223:8001 {
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        Permissions-Policy "camera=(), microphone=(), geolocation=()"
    }

    log {
        output file /ganuda/logs/caddy-access.log {
            roll_size 50MiB
            roll_keep 5
        }
    }
}
```

#### Option B: IP-only (self-signed, for testing)

```text
:443 {
    tls internal

    handle {
        root * /ganuda/www/vetassist
        file_server
        try_files {path} /index.html
    }

    handle /api/* {
        reverse_proxy 192.168.132.223:8001
    }

    header {
        Strict-Transport-Security "max-age=31536000"
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
    }

    log {
        output file /ganuda/logs/caddy-access.log
    }
}

:80 {
    redir https://{host}{uri} permanent
}
```

### 5.3 Start Caddy

```text
service caddy start
```

### 5.4 Deploy VetAssist Frontend

Build on redfin (where the source lives), then rsync the static build:
```text
# On redfin:
cd /ganuda/vetassist/frontend
npm run build

# Copy build output to owlfin:
rsync -avz /ganuda/vetassist/frontend/out/ dereadi@192.168.30.225:/ganuda/www/vetassist/

# And eaglefin:
rsync -avz /ganuda/vetassist/frontend/out/ dereadi@192.168.30.226:/ganuda/www/vetassist/
```

If Next.js uses SSR (not static export), then Node.js runs on the web servers instead:
```text
# On owlfin/eaglefin:
cd /ganuda/www/vetassist
rsync -avz dereadi@192.168.132.223:/ganuda/vetassist/frontend/ .
npm ci --production
npm run build
```

Then Caddy reverse proxies to the local Next.js:
```text
handle {
    reverse_proxy localhost:3000
}
```

And add to rc.conf:
```text
# /usr/local/etc/rc.d/vetassist-frontend or use daemon(8):
sysrc vetassist_frontend_enable="YES"
```

Create `/usr/local/etc/rc.d/vetassist_frontend`:
```text
#!/bin/sh

# PROVIDE: vetassist_frontend
# REQUIRE: NETWORKING
# KEYWORD: shutdown

. /etc/rc.subr

name="vetassist_frontend"
rcvar="${name}_enable"
pidfile="/var/run/${name}.pid"
command="/usr/sbin/daemon"
command_args="-P ${pidfile} -r -f /usr/local/bin/node /ganuda/www/vetassist/node_modules/.bin/next start -p 3000"

load_rc_config $name
run_rc_command "$1"
```

```text
chmod +x /usr/local/etc/rc.d/vetassist_frontend
sysrc vetassist_frontend_enable="YES"
service vetassist_frontend start
```

---

## Phase 6: Load Balancing (owlfin + eaglefin)

### 6.1 AT&T Router Port Forwards

| External Port | Internal IP | Internal Port | Service |
|---|---|---|---|
| 443 | 192.168.30.225 | 443 | HTTPS → owlfin (primary) |
| 80 | 192.168.30.225 | 80 | HTTP redirect → owlfin |

eaglefin is the failover. If owlfin goes down, change the port forward to .226.

### 6.2 Future: DNS-Based Failover

When a domain is configured:
- A record → owlfin public IP
- Health check script on eaglefin monitors owlfin
- If owlfin down → update DNS (Cloudflare API) to eaglefin
- Or use Cloudflare proxy with both IPs for automatic failover

### 6.3 Future: Keepalived VIP

For seamless failover without DNS propagation delay:
```text
pkg install -y keepalived
```

Shared VIP: `192.168.30.230` — floats between owlfin (master) and eaglefin (backup). AT&T port forward points to VIP.

---

## Phase 7: Monitoring Integration

### 7.1 Node Exporter (Prometheus metrics)

```text
pkg install -y node_exporter
sysrc node_exporter_enable="YES"
service node_exporter start
# Exposes metrics on :9100
```

### 7.2 Log Shipping to OpenObserve on greenfin

Option A — Promtail (if available for FreeBSD):
```text
# Check: pkg search promtail
# If not available, use Vector or Filebeat
pkg install -y vector
```

Option B — Simple rsyslog forwarding:
```text
# /etc/syslog.conf — add line to forward to greenfin:
*.* @192.168.132.224:514
```

Option C — Caddy access logs shipped via cron:
```text
# Cron: ship Caddy logs to greenfin every 5 min
*/5 * * * * rsync -az /ganuda/logs/caddy-access.log dereadi@192.168.132.224:/ganuda/logs/owlfin-caddy.log
```

### 7.3 Health Check Endpoint

Caddy already serves VetAssist. Add a health route to Caddyfile:
```text
handle /health {
    respond "owlfin ok" 200
}
```

### 7.4 Register in SAG

Update SAG's federation monitor to poll owlfin and eaglefin on port 443/health.

---

## Phase 8: Hardening Checklist

- [ ] pf firewall enabled, only 22/80/443 inbound
- [ ] SSH: key-only, no root, AllowUsers dereadi
- [ ] Brute-force table with auto-expire
- [ ] No unnecessary services (sendmail disabled, etc.)
- [ ] `sysrc sendmail_enable="NONE"`
- [ ] `sysrc clear_tmp_enable="YES"`
- [ ] ZFS snapshots scheduled (daily):
  ```text
  pkg install -y zfstools
  # Add to crontab:
  15 0 * * * zfs snapshot -r zroot@auto-$(date +\%Y\%m\%d)
  # Keep 7 days:
  15 1 * * * zfs list -t snapshot -o name -H | grep auto- | head -n -7 | xargs -I {} zfs destroy {}
  ```
- [ ] pkg audit for known vulnerabilities:
  ```text
  pkg audit -F
  ```
- [ ] No database ports exposed (5432 blocked by pf)
- [ ] No LLM gateway exposed (8080 blocked by pf)
- [ ] Caddy security headers set (HSTS, X-Frame-Options, etc.)
- [ ] sysctl hardening:
  ```text
  # /etc/sysctl.conf
  net.inet.tcp.blackhole=2
  net.inet.udp.blackhole=1
  security.bsd.see_other_uids=0
  security.bsd.unprivileged_read_msgbuf=0
  ```

---

## Phase 9: TP-Link Switch Configuration

Two NEW switch ports for owlfin and eaglefin — assign to VLAN 30 untagged:

```text
# Assuming owlfin on port 18, eaglefin on port 19
interface ethernet 1/0/18
switchport access vlan 30
exit

interface ethernet 1/0/19
switchport access vlan 30
exit
```

Or via TP-Link web GUI:
1. VLAN > 802.1Q VLAN > VLAN 30
2. Add port 18 and 19 as Untagged members
3. Remove ports 18 and 19 from VLAN 1

---

## Phase 10: Cross-VLAN Routing (VLAN 30 → VLAN 1 Backend)

The web servers need to reach redfin's VetAssist backend API (192.168.132.223:8001) on VLAN 1. Options:

### Option A: Route via AT&T router (simplest)

If the AT&T router has both subnets (192.168.30.0/24 and 192.168.132.0/24), it can route between them. Add a static route on owlfin/eaglefin:
```text
route add -net 192.168.132.0/24 192.168.30.1
```

Persistent in `/etc/rc.conf`:
```text
sysrc static_routes="vlan1"
sysrc route_vlan1="-net 192.168.132.0/24 192.168.30.1"
```

### Option B: Tailscale (already deployed on fins)

Install Tailscale on owlfin/eaglefin. API calls go over Tailscale mesh — encrypted, no port exposure.
```text
pkg install -y tailscale
sysrc tailscaled_enable="YES"
service tailscaled start
tailscale up
```

Then Caddy reverse proxies to redfin's Tailscale IP instead of 192.168.132.223.

### Option C: WireGuard tunnel (point-to-point)

Dedicated tunnel between owlfin and redfin for API traffic only.

**Recommendation**: Option B (Tailscale) — already in the federation, encrypted, zero-config routing, ACLs already defined.

---

## IP Assignment Summary

| Node | VLAN 30 IP | Switch Port | Role |
|------|-----------|-------------|------|
| AT&T Router | 192.168.30.1 | Port 17 | Gateway |
| owlfin | 192.168.30.225 | Port 18 | Web Server (primary) |
| eaglefin | 192.168.30.226 | Port 19 | Web Server (failover) |
| VIP (future) | 192.168.30.230 | — | Keepalived floating IP |

## Traffic Separation

| Traffic | Path | Encrypted By |
|---------|------|-------------|
| Customer HTTPS | Internet → AT&T → VLAN 30 → Caddy | TLS (Let's Encrypt) |
| API to redfin backend | owlfin → Tailscale → redfin:8001 | WireGuard |
| Federation internal | VLAN 1 (no owlfin/eaglefin access) | VPN |
| Database | VLAN 1 only (blocked from VLAN 30) | VPN |
| SSH admin | VLAN 30 + Tailscale | WireGuard |

## Rollback

To take a node offline:
```text
service caddy stop
pfctl -d        # Disable firewall (or leave up to block everything)
```

To decommission:
```text
# Remove AT&T port forward
# Remove switch port from VLAN 30
# Power off node
```

---

## Cherokee Naming

- 🦉 **owlfin** — Owl (ᏚᎯ, tsuhi) sees in darkness. Wisdom, vigilance. Primary web server — first to receive traffic.
- 🦅 **eaglefin** — Eagle (ᎩᏟ, gitli) soars above. Clarity, resilience. Failover — watches and waits.

Both are sacred Cherokee animals. The web servers protect the federation's public face while the internal nodes stay hidden behind VPN.

---
*Cherokee AI Federation — Infrastructure*
*FreeBSD 15.0-RELEASE — VLAN 30 DMZ Web Tier*
