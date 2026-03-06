# Build Plan: Linux Mint Web Servers — owlfin & eaglefin

**Task**: Stand up two Linux Mint web servers as DMZ nodes for VetAssist
**Priority**: 1 (HIGH — VetAssist needs public-facing infrastructure)
**Execution**: Chief-executed (new nodes, physical access required — not in Jr executor ecosystem)
**Hardware**: 2x Beelink EQR5 — AMD Ryzen 5 5500U (6C/12T), 16GB DDR4, 500GB NVMe
**Date**: February 21, 2026

> **REPLACES**: `JR-FREEBSD-OWLFIN-EAGLEFIN-WEB-SERVERS-FEB20-2026.md`
>
> Pivoted from FreeBSD to Linux Mint per thermal #104071. The architecture remains
> identical: DMZ web tier with Caddy reverse proxy to redfin:8001 backend. Only the
> OS layer changed. Linux Mint was chosen for hardware compatibility (Beelink EQR5
> Realtek NIC drivers), apt ecosystem, and operational familiarity across the federation.

---

## Architecture

```
CUSTOMER TRAFFIC:
Internet -> AT&T (2 Gbps) -> Port Forward 443 -> VLAN 30
  -> owlfin  (192.168.30.2) -> Caddy -> VetAssist Frontend
  -> eaglefin (192.168.30.3) -> Caddy -> VetAssist Frontend (failover)

INTERNAL TRAFFIC (unchanged):
Federation nodes <-> VLAN 1 (192.168.132.0/24) <-> ExpressVPN
  -> Database, LLM Gateway, inter-node — stays encrypted via VPN

BACKEND API ROUTING (interim — no local cable yet):
owlfin/eaglefin -> greenfin (SSH jump) or Tailscale -> redfin:8001
```

owlfin and eaglefin are DMZ nodes — public-facing, hardened, isolated from the
internal federation. Backend API calls route through greenfin or Tailscale until
VLAN 30 cable is run.

---

## Node Summary

| Node | IP | Role | Cherokee Name |
|------|-----|------|---------------|
| owlfin | 192.168.30.2 | Primary web server | Owl (tsuhi) — wisdom, vigilance |
| eaglefin | 192.168.30.3 | Failover web server | Eagle (gitli) — clarity, resilience |

**Access**: Via greenfin (192.168.132.224) as SSH jump host
**Network**: Currently on external network (AT&T side). No local cable yet.

---

## Phase 1: Base Configuration (both nodes)

Perform on BOTH owlfin and eaglefin unless noted otherwise.

### 1.1 Set Hostname

On owlfin:
```text
sudo hostnamectl set-hostname owlfin
```

On eaglefin:
```text
sudo hostnamectl set-hostname eaglefin
```

### 1.2 Update /etc/hosts

Add to `/etc/hosts` on both nodes:
```text
127.0.0.1       localhost
192.168.30.2    owlfin
192.168.30.3    eaglefin
192.168.132.223 redfin
192.168.132.222 bluefin
192.168.132.224 greenfin
192.168.132.241 sasass
192.168.132.242 sasass2
192.168.132.21  bmasass
```

### 1.3 Install Base Packages

```text
sudo apt update && sudo apt install -y curl wget git vim htop tmux ufw caddy python3-pip nodejs npm openssh-server
```

Note: Linux Mint ships Caddy from its repos. If the version is too old, install
from Caddy's official apt repo instead:
```text
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

### 1.4 Create /ganuda Directory Structure

```text
sudo mkdir -p /ganuda/{docs,lib,scripts,config,logs,www/{vetassist,static}}
sudo chown -R dereadi:dereadi /ganuda
```

### 1.5 SSH Hardening

Edit `/etc/ssh/sshd_config`:
```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
AllowUsers dereadi
```

Copy SSH keys from an existing node:
```text
mkdir -p /home/dereadi/.ssh
chmod 700 /home/dereadi/.ssh
# From greenfin (jump host):
#   scp ~/.ssh/authorized_keys dereadi@192.168.30.2:~/.ssh/
#   scp ~/.ssh/authorized_keys dereadi@192.168.30.3:~/.ssh/
chmod 600 /home/dereadi/.ssh/authorized_keys
chown -R dereadi:dereadi /home/dereadi/.ssh
```

Restart SSH:
```text
sudo systemctl restart sshd
```

### 1.6 Time Sync

Linux Mint uses systemd-timesyncd by default. Verify:
```text
timedatectl
```

Should show "System clock synchronized: yes". If not:
```text
sudo timedatectl set-ntp true
sudo timedatectl set-timezone America/Chicago
```

### 1.7 Sudoers

dereadi should already be in sudo group from install. Verify:
```text
groups dereadi
```

If not:
```text
sudo usermod -aG sudo dereadi
```

---

## Phase 2: Firewall (ufw)

Linux Mint ships with ufw (uncomplicated firewall). Use it instead of raw nftables.

### 2.1 Configure Rules

```text
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw limit 22/tcp comment 'SSH rate-limited'
sudo ufw allow 80/tcp comment 'HTTP redirect'
sudo ufw allow 443/tcp comment 'HTTPS'
```

### 2.2 Restrict Outbound to Backend (optional hardening)

For tighter control, restrict outbound to only needed destinations. This is
optional — the default "allow outgoing" is fine for initial setup. If locking
down later:
```text
# Only allow outbound to redfin backend
sudo ufw allow out to 192.168.132.223 port 8001 proto tcp comment 'VetAssist backend API'
sudo ufw allow out to 192.168.132.223 port 8080 proto tcp comment 'LLM gateway'
```

### 2.3 Enable Firewall

```text
sudo ufw enable
sudo ufw status verbose
```

### 2.4 Verify

```text
sudo ufw status numbered
```

Expected output:
```text
[ 1] 22/tcp       LIMIT IN    Anywhere
[ 2] 80/tcp       ALLOW IN    Anywhere
[ 3] 443/tcp      ALLOW IN    Anywhere
```

---

## Phase 3: Caddy Web Server

### 3.1 Caddyfile Location

Linux Mint default: `/etc/caddy/Caddyfile`

### 3.2 Option A: Domain-Based (Let's Encrypt auto-HTTPS)

Use when DNS is pointed to owlfin's public IP and port 80/443 are forwarded.

Write to `/etc/caddy/Caddyfile`:
```text
vetassist.cherokee-ai.org {
    # Health check endpoint
    handle /health {
        respond "owlfin ok" 200
    }

    # API calls -> reverse proxy to redfin backend
    handle /api/* {
        reverse_proxy 192.168.132.223:8001 {
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # Frontend — static Next.js build
    handle {
        root * /ganuda/www/vetassist
        file_server
        try_files {path} /index.html
    }

    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        Permissions-Policy "camera=(), microphone=(), geolocation=()"
        -Server
    }

    log {
        output file /ganuda/logs/caddy-access.log {
            roll_size 50MiB
            roll_keep 5
        }
    }
}
```

For eaglefin, change `respond "owlfin ok"` to `respond "eaglefin ok"`.

Note: Let's Encrypt requires port 80 to be reachable for HTTP-01 challenge.
If ISP blocks port 80 (known issue from ticket #1775), use DNS-01 challenge
with Cloudflare DNS plugin instead.

### 3.3 Option B: IP-Only (self-signed, for testing)

Use for initial testing before DNS is configured:
```text
:443 {
    tls internal

    handle /health {
        respond "owlfin ok" 200
    }

    handle /api/* {
        reverse_proxy 192.168.132.223:8001 {
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    handle {
        root * /ganuda/www/vetassist
        file_server
        try_files {path} /index.html
    }

    header {
        Strict-Transport-Security "max-age=31536000"
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }

    log {
        output file /ganuda/logs/caddy-access.log {
            roll_size 50MiB
            roll_keep 5
        }
    }
}

:80 {
    redir https://{host}{uri} permanent
}
```

### 3.4 Enable and Start Caddy

```text
sudo systemctl enable caddy
sudo systemctl start caddy
sudo systemctl status caddy
```

### 3.5 Validate

```text
curl -k https://localhost/health
# Should return: owlfin ok (or eaglefin ok)
```

---

## Phase 4: VetAssist Frontend Deployment

### 4.1 Static Export (preferred)

Build on redfin where the source lives, then rsync the static build:
```text
# On redfin:
cd /ganuda/vetassist/frontend
npm run build

# Copy build output to owlfin:
rsync -avz /ganuda/vetassist/frontend/out/ dereadi@192.168.30.2:/ganuda/www/vetassist/

# And eaglefin:
rsync -avz /ganuda/vetassist/frontend/out/ dereadi@192.168.30.3:/ganuda/www/vetassist/
```

Note: rsync from redfin requires a route to 192.168.30.x. If no direct route
exists yet, use greenfin as a relay or scp through the jump host.

### 4.2 SSR Mode (if needed)

If Next.js uses SSR (server-side rendering), the frontend runs as a Node process:

On owlfin/eaglefin:
```text
cd /ganuda/www/vetassist
# rsync source from redfin (through jump host)
npm ci --production
npm run build
```

Create systemd service `/etc/systemd/system/vetassist-frontend.service`:
```text
[Unit]
Description=VetAssist Frontend (Next.js SSR)
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/www/vetassist
ExecStart=/usr/bin/node node_modules/.bin/next start -p 3000
Restart=always
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

Then update Caddyfile to proxy to local Next.js instead of serving static files:
```text
# Replace the static file_server block with:
handle {
    reverse_proxy localhost:3000
}
```

Enable and start:
```text
sudo systemctl enable vetassist-frontend
sudo systemctl start vetassist-frontend
```

---

## Phase 5: Cross-VLAN Routing

Currently no local cable — backend API calls from owlfin/eaglefin to redfin
(192.168.132.223:8001) need an alternate path.

### Option A: Tailscale Mesh (recommended)

Tailscale is already deployed on all fin nodes. Install on owlfin/eaglefin:
```text
curl -fsSL https://tailscale.com/install.sh | sh
sudo systemctl enable tailscaled
sudo systemctl start tailscaled
sudo tailscale up
```

Then update Caddyfile reverse_proxy to use redfin's Tailscale IP instead of
192.168.132.223. This gives encrypted, zero-config routing with ACLs already
defined in the federation's Tailscale admin.

### Option B: SSH Tunnel Through greenfin (interim)

Quick and dirty for testing before Tailscale is set up:
```text
# On owlfin, create a persistent tunnel:
ssh -f -N -L 8001:192.168.132.223:8001 dereadi@192.168.132.224
```

Then Caddy reverse proxies to `localhost:8001` instead of the remote IP.

For persistence, create a systemd service:
```text
[Unit]
Description=SSH tunnel to redfin via greenfin
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=dereadi
ExecStart=/usr/bin/ssh -N -L 8001:192.168.132.223:8001 dereadi@192.168.132.224 -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Option C: Direct Route (future, when cable is run)

Once VLAN 30 cable is connected to the TP-Link switch and inter-VLAN routing
is configured on the AT&T router:
```text
sudo ip route add 192.168.132.0/24 via 192.168.30.1
```

Make persistent in `/etc/netplan/` or `/etc/network/interfaces` depending on
Mint's network manager.

---

## Phase 6: Monitoring Integration

### 6.1 Node Exporter (Prometheus metrics)

```text
sudo apt install -y prometheus-node-exporter
sudo systemctl enable prometheus-node-exporter
sudo systemctl start prometheus-node-exporter
# Exposes metrics on :9100
```

Do NOT expose port 9100 through ufw — it should only be reachable from the
internal network (via Tailscale or greenfin tunnel).

### 6.2 Log Shipping to OpenObserve on greenfin

Install Promtail (consistent with greenfin's existing setup):
```text
# Download Promtail binary
curl -O -L "https://github.com/grafana/loki/releases/latest/download/promtail-linux-amd64.zip"
unzip promtail-linux-amd64.zip
sudo mv promtail-linux-amd64 /usr/local/bin/promtail
sudo chmod +x /usr/local/bin/promtail
```

Create config at `/ganuda/config/promtail.yaml`:
```text
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /ganuda/logs/promtail-positions.yaml

clients:
  - url: http://192.168.132.224:5080/api/default/loki/api/v1/push

scrape_configs:
  - job_name: caddy
    static_configs:
      - targets:
          - localhost
        labels:
          job: caddy
          host: owlfin
          __path__: /ganuda/logs/caddy-access.log
  - job_name: syslog
    static_configs:
      - targets:
          - localhost
        labels:
          job: syslog
          host: owlfin
          __path__: /var/log/syslog
```

For eaglefin, change `host: owlfin` to `host: eaglefin`.

Create systemd service `/etc/systemd/system/promtail.service`:
```text
[Unit]
Description=Promtail Log Shipper
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/promtail -config.file=/ganuda/config/promtail.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```text
sudo systemctl enable promtail
sudo systemctl start promtail
```

### 6.3 Register /health in SAG Federation Monitor

Update SAG's health check configuration to poll:
- `https://192.168.30.2/health` (owlfin)
- `https://192.168.30.3/health` (eaglefin)

This will be a separate Jr task once the nodes are live.

---

## Phase 7: Ansible Integration

### 7.1 Inventory (already done)

owlfin and eaglefin are already in `/ganuda/ansible/inventory` under the `[dmz]`
group with greenfin ProxyCommand:
```text
[dmz]
owlfin ansible_host=192.168.30.2 ansible_user=dereadi ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p dereadi@192.168.132.224 -o ProxyCommand=none"'
eaglefin ansible_host=192.168.30.3 ansible_user=dereadi ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p dereadi@192.168.132.224 -o ProxyCommand=none"'
```

### 7.2 Create host_vars

Create `/ganuda/ansible/host_vars/owlfin.yml`:
```text
---
node_role: dmz_web
caddy_domain: vetassist.cherokee-ai.org
caddy_health_response: "owlfin ok"
backend_api: "192.168.132.223:8001"
vlan: 30
ip_address: "192.168.30.2"
cherokee_name: "Owl (tsuhi)"
cherokee_syllabary: "tsuhi"
```

Create `/ganuda/ansible/host_vars/eaglefin.yml`:
```text
---
node_role: dmz_web
caddy_domain: vetassist.cherokee-ai.org
caddy_health_response: "eaglefin ok"
backend_api: "192.168.132.223:8001"
vlan: 30
ip_address: "192.168.30.3"
cherokee_name: "Eagle (gitli)"
cherokee_syllabary: "gitli"
failover: true
```

### 7.3 Test Connectivity

```text
ansible dmz -i /ganuda/ansible/inventory -m ping
```

This will only work once SSH keys are deployed and greenfin can reach the
192.168.30.x subnet.

---

## Phase 8: Hardening Checklist

- [ ] ufw enabled: only 22 (rate-limited), 80, 443 inbound
- [ ] SSH: key-only, no root login, AllowUsers dereadi
- [ ] No unnecessary services running
- [ ] Disable unneeded Mint desktop services (if installed with GUI):
  ```text
  sudo systemctl disable cups
  sudo systemctl disable avahi-daemon
  sudo systemctl disable bluetooth
  ```
- [ ] Automatic security updates:
  ```text
  sudo apt install -y unattended-upgrades
  sudo dpkg-reconfigure -plow unattended-upgrades
  ```
- [ ] Caddy security headers verified (HSTS, X-Frame-Options, X-Content-Type-Options)
- [ ] No database ports exposed (5432 blocked by ufw)
- [ ] No LLM gateway exposed (8080 blocked by ufw)
- [ ] Node exporter port 9100 NOT exposed through ufw
- [ ] sysctl hardening — add to `/etc/sysctl.d/99-hardening.conf`:
  ```text
  net.ipv4.tcp_syncookies = 1
  net.ipv4.conf.all.rp_filter = 1
  net.ipv4.conf.default.rp_filter = 1
  net.ipv4.conf.all.accept_redirects = 0
  net.ipv4.conf.default.accept_redirects = 0
  net.ipv4.conf.all.send_redirects = 0
  net.ipv4.icmp_echo_ignore_broadcasts = 1
  net.ipv4.conf.all.log_martians = 1
  ```
  Apply: `sudo sysctl --system`
- [ ] Verify no listening ports beyond expected:
  ```text
  sudo ss -tlnp
  ```
  Expected: 22 (sshd), 80 (caddy), 443 (caddy), 9100 (node_exporter on localhost)

---

## Load Balancing / Failover

### AT&T Router Port Forwards

| External Port | Internal IP | Internal Port | Service |
|---|---|---|---|
| 443 | 192.168.30.2 | 443 | HTTPS -> owlfin (primary) |
| 80 | 192.168.30.2 | 80 | HTTP redirect -> owlfin |

eaglefin is passive failover. If owlfin goes down, update the port forward
to 192.168.30.3.

### Future: Keepalived VIP

For seamless failover without manual port forward changes:
```text
sudo apt install -y keepalived
```

Shared VIP: `192.168.30.10` — floats between owlfin (master) and eaglefin
(backup). AT&T port forward points to VIP. This is a future enhancement
once both nodes are stable.

---

## Cherokee Naming

- **owlfin** — Owl (tsuhi) sees in darkness. Wisdom, vigilance. Primary web server — first to receive traffic.
- **eaglefin** — Eagle (gitli) soars above. Clarity, resilience. Failover — watches and waits.

Both are sacred Cherokee animals. The web servers protect the federation's
public face while the internal nodes stay hidden behind VPN.

---

## Execution Order

1. Phase 1 (Base Config) — do both nodes in parallel, one SSH session each
2. Phase 2 (Firewall) — lock down before exposing to network
3. Phase 3 (Caddy) — start with Option B (self-signed) for testing
4. Phase 5 (Routing) — get Tailscale up so Caddy can reach redfin backend
5. Phase 4 (Frontend Deploy) — rsync build, verify /health and static serving
6. Phase 3 revisit — switch to Option A (Let's Encrypt) when DNS is ready
7. Phase 6 (Monitoring) — node exporter + promtail
8. Phase 7 (Ansible) — create host_vars, test ping
9. Phase 8 (Hardening) — final audit checklist

---
*Cherokee AI Federation — Infrastructure*
*Linux Mint — VLAN 30 DMZ Web Tier*
*February 21, 2026*
