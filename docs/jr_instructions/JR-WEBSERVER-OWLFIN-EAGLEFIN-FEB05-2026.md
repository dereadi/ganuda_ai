# JR-WEBSERVER-OWLFIN-EAGLEFIN-FEB05-2026

## Priority: P1
## Assignee: Infrastructure Jr.
## Estimated Effort: 3-4 hours (both nodes)

## Context

Two new Beelink EQR5 mini PCs joining the federation as web servers:

| Node | Role | Status |
|------|------|--------|
| owlfin | Web Server 1 | Pending installation |
| eaglefin | Web Server 2 | Pending installation |

**Hardware Specs (both identical):**
- CPU: AMD Ryzen 5 5500U (6C/12T, up to 4.0GHz)
- RAM: 16GB DDR4
- Storage: 500GB NVMe PCIe 3.0x4 SSD
- Network: 1000Mbps Ethernet, WiFi6, BT5.2
- OS: Ubuntu Server (fresh install by Chief)

## Network Planning

Suggested IP assignments (VLAN 132 - Production):
- owlfin: 192.168.132.225
- eaglefin: 192.168.132.226

Alternative: Create DMZ VLAN for public-facing web services.

## Deliverables

### Phase 1: Base OS Configuration (Chief performs initial install)

Chief will install Ubuntu Server. After first boot, Jr configures:

**1.1 Hostname and Hosts**
```bash
hostnamectl set-hostname owlfin  # or eaglefin
echo "192.168.132.225 owlfin" >> /etc/hosts
echo "192.168.132.226 eaglefin" >> /etc/hosts
```

**1.2 User Setup**
```bash
# Ensure dereadi user exists with sudo
usermod -aG sudo dereadi

# SSH key deployment (copy from existing nodes)
mkdir -p /home/dereadi/.ssh
# Copy authorized_keys from redfin
```

**1.3 Ganuda Directory Structure**
```bash
mkdir -p /ganuda/{docs,lib,scripts,config,logs,www}
chown -R dereadi:dereadi /ganuda
```

### Phase 2: Web Server Stack

**2.1 Caddy Installation**

Caddy for automatic HTTPS and simple config:
```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install caddy
```

**2.2 Caddyfile Template**
```
/etc/caddy/Caddyfile:

# Placeholder - update with actual domains
:80 {
    respond "owlfin operational" 200
}
```

**2.3 Node.js (for frontend builds)**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
```

### Phase 3: Monitoring Integration

**3.1 Promtail for Log Shipping**
```bash
# Ship logs to Loki on greenfin
# Install promtail, configure to watch /var/log and /ganuda/logs
```

**3.2 Node Exporter for Metrics**
```bash
apt install prometheus-node-exporter
systemctl enable prometheus-node-exporter
```

**3.3 Register with SAG**

Update SAG unified interface to show owlfin/eaglefin status.

### Phase 4: Service Deployment Prep

Potential services for these nodes:
- **VetAssist Frontend** (Next.js static build)
- **SSIDAssist Frontend** (when ready)
- **TribeAssist Frontend** (when ready)
- **Static content / CDN edge**

Create deployment directories:
```bash
mkdir -p /ganuda/www/{vetassist,ssidassist,tribeassist,static}
```

### Phase 5: Load Balancer Configuration

If both nodes serve same content, configure upstream:

**On greenfin (or dedicated LB):**
```
upstream web_cluster {
    server 192.168.132.225:80;  # owlfin
    server 192.168.132.226:80;  # eaglefin
}
```

Or use Caddy's built-in load balancing.

## Security Checklist

- [ ] UFW enabled, only 22/80/443 open
- [ ] Fail2ban installed
- [ ] No root SSH login
- [ ] SSH key auth only (disable password)
- [ ] Automatic security updates enabled
- [ ] No unnecessary services running

## Ansible Playbook

Create `/ganuda/ansible/playbooks/webserver-base.yml`:
- Idempotent configuration for both nodes
- Can run on fresh Ubuntu Server install
- Tags for selective execution

## Verification

1. SSH access works for dereadi
2. `/ganuda/` directory structure exists
3. Caddy responds on port 80
4. Node.js 20.x installed
5. Promtail shipping logs
6. Node exporter metrics available
7. UFW blocking unexpected ports

## CMDB Updates

After installation complete:
```sql
UPDATE hardware_inventory 
SET online_status = true,
    network_interfaces = '{"eth0": "192.168.132.22X"}',
    os_info = 'Ubuntu Server 24.04 LTS'
WHERE hostname IN ('owlfin', 'eaglefin');
```

## Federation Naming

Following the council animal theme:
- 🦉 **owlfin** — Owl sees in darkness, wisdom
- 🦅 **eaglefin** — Eagle Eye, vigilance and clarity

Both are Cherokee sacred animals. The naming honors the council.

---
*Cherokee AI Federation — Infrastructure*
*ᎤᏂᎪᎵᏰᏗ ᎤᎾᏓᏡᎬ — New eyes join the watch*
