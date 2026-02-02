# JR-VLAN30-DIRECT-INTERNET-JAN30-2026
## Direct AT&T Internet via VLAN 30 on TP-Link Switch

**Priority:** High
**Target Node:** All fins (TP-Link switch + redfin, bluefin, greenfin)
**Prerequisites:** Physical cable from AT&T router to TP-Link switch port 17

### Background

The federation currently routes all internet traffic through the ExpressVPN XV Router
at 192.168.132.1. With the AT&T 2 Gbps upgrade, we need a direct path for
customer-facing web services and high-bandwidth operations that bypasses VPN overhead.
The ExpressVPN path remains for internal/private traffic.

Current measured throughput via ExpressVPN: ~350-412 Mbps
Target throughput via direct AT&T: ~900+ Mbps (1 GbE NIC cap)

### Dual-Purpose Design

VLAN 30 serves two roles:
1. **Inbound customer traffic** — AT&T router forwards ports 80/443 to web servers on VLAN 30
2. **Outbound high-bandwidth** — Model downloads, package updates, large transfers bypass VPN

```
CUSTOMER TRAFFIC FLOW:
Internet → AT&T (2 Gbps) → Port Forward 443 → VLAN 30
  → bluefin (192.168.30.222) → Caddy → VetAssist Frontend :3000 + API :8001
  → [future nodes on 192.168.30.x as traffic grows]

INTERNAL TRAFFIC FLOW (unchanged):
Federation nodes ↔ VLAN 1 (192.168.132.0/24) ↔ ExpressVPN (private)
  → Database, LLM Gateway, inter-node — stays encrypted via VPN
```

### Network Design

```
VLAN 30 (Direct Internet): 192.168.30.0/24
- Port 17: AT&T router uplink (untagged VLAN 30)
- Ports 1-4: Tagged VLAN 30 (trunk ports where fins are connected)
- Gateway: 192.168.30.1 (AT&T router LAN IP on this subnet)
```

### Step 1: Configure AT&T Router

On the AT&T BGW320 or similar gateway:
1. Access admin panel (usually 192.168.1.254)
2. Under Home Network > Subnets & DHCP:
   - Add a new LAN subnet: 192.168.30.0/24
   - Or configure the LAN port to use IP 192.168.30.1/24
3. If the AT&T router doesn't support multiple subnets:
   - Set the secondary LAN port IP to 192.168.30.1
   - Or use IP Passthrough to assign a direct WAN IP

### Step 2: Configure TP-Link Switch

Access switch management interface (192.168.99.x or via console).

```
# Create VLAN 30
vlan 30
name "DirectInternet"
exit

# Port 17 - AT&T uplink (untagged VLAN 30)
interface ethernet 1/0/17
switchport access vlan 30
exit

# Trunk ports for fins - ADD VLAN 30 as tagged
# Assuming redfin=port 1, bluefin=port 2, greenfin=port 3
# Adjust port numbers to match actual physical layout

interface ethernet 1/0/1
switchport trunk allowed vlan add 30
exit

interface ethernet 1/0/2
switchport trunk allowed vlan add 30
exit

interface ethernet 1/0/3
switchport trunk allowed vlan add 30
exit
```

If using TP-Link web GUI instead of CLI:
1. VLAN > 802.1Q VLAN > Create VLAN ID 30
2. Set port 17 as Untagged member of VLAN 30
3. Set fin ports (1, 2, 3) as Tagged members of VLAN 30
4. Remove port 17 from VLAN 1

### Step 3: Configure Fin Nodes

On each fin, create a VLAN 30 tagged interface.

**redfin (Ubuntu/netplan):**
Create `/etc/netplan/61-direct-internet.yaml`:
```yaml
network:
  version: 2
  vlans:
    vlan30:
      id: 30
      link: enp6s0
      addresses:
        - 192.168.30.223/24
      routes:
        - to: 0.0.0.0/0
          via: 192.168.30.1
          table: 30
          metric: 200
      routing-policy:
        - from: 192.168.30.223
          table: 30
```

Apply: `sudo netplan apply`

**bluefin (Ubuntu/netplan):**
Create `/etc/netplan/61-direct-internet.yaml`:
```yaml
network:
  version: 2
  vlans:
    vlan30:
      id: 30
      link: enp5s0
      addresses:
        - 192.168.30.222/24
      routes:
        - to: 0.0.0.0/0
          via: 192.168.30.1
          table: 30
          metric: 200
      routing-policy:
        - from: 192.168.30.222
          table: 30
```

**greenfin (Rocky/NetworkManager):**
```bash
nmcli connection add type vlan \
  con-name vlan30 \
  dev eno1 \
  id 30 \
  ipv4.addresses 192.168.30.224/24 \
  ipv4.gateway 192.168.30.1 \
  ipv4.route-metric 200 \
  ipv4.method manual
```

### Step 4: Policy Routing Rules

On each fin, add rules to route specific traffic via the direct AT&T path.

Add to `/etc/iproute2/rt_tables`:
```
30 direct
```

Create `/ganuda/scripts/policy_routing.sh`:
```bash
#!/bin/bash
# Route high-bandwidth targets via direct AT&T (table 30)
# Model registries
ip rule add to 104.18.0.0/16 table 30 priority 100   # Hugging Face CDN
ip rule add to 151.101.0.0/16 table 30 priority 100   # Fastly CDN
ip rule add to 13.0.0.0/8 table 30 priority 100       # AWS (S3 model downloads)
ip rule add to 34.0.0.0/8 table 30 priority 100       # Google Cloud
ip rule add to 140.82.0.0/16 table 30 priority 100    # GitHub
ip rule add to 185.199.0.0/16 table 30 priority 100   # GitHub CDN

# Speed tests
ip rule add to 88.99.0.0/16 table 30 priority 100     # Hetzner
ip rule add to 5.9.0.0/16 table 30 priority 100       # Hetzner

# Default: everything else stays on ExpressVPN (table main)
```

### Step 5: AT&T Router Port Forwarding (Customer Traffic)

On the AT&T router admin panel, forward inbound web traffic to bluefin:

| External Port | Internal IP | Internal Port | Protocol | Service |
|---|---|---|---|---|
| 443 | 192.168.30.222 | 443 | TCP | HTTPS (Caddy on bluefin) |
| 80 | 192.168.30.222 | 80 | TCP | HTTP→HTTPS redirect |

When scaling to multiple web nodes, change these to point at a load balancer IP
or add additional port forwards to new nodes.

### Step 6: Caddy Reverse Proxy on bluefin

Install Caddy on bluefin (if not already installed):
```bash
sudo apt install -y caddy
```

Create `/etc/caddy/Caddyfile`:
```
# Bind ONLY to VLAN 30 interface for customer traffic
# Replace vetassist.example.com with actual domain

vetassist.example.com {
    bind 192.168.30.222

    # Frontend (Next.js)
    handle /api/* {
        reverse_proxy localhost:8001
    }

    handle {
        reverse_proxy localhost:3000
    }

    # Auto HTTPS via Let's Encrypt
    tls {
        dns cloudflare {env.CF_API_TOKEN}
    }

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
    }

    log {
        output file /var/log/caddy/vetassist-access.log
    }
}
```

**Without a domain (IP-only access):**
```
:443 {
    bind 192.168.30.222

    handle /api/* {
        reverse_proxy localhost:8001
    }

    handle {
        reverse_proxy localhost:3000
    }

    tls internal
}

:80 {
    bind 192.168.30.222
    redir https://{host}{uri} permanent
}
```

Start Caddy:
```bash
sudo systemctl enable caddy
sudo systemctl start caddy
```

### Step 7: Start Next.js Frontend on bluefin

```bash
cd /ganuda/vetassist/frontend
npm run build
# Start on port 3000 (Caddy proxies to it)
nohup npm start -- -p 3000 > /ganuda/logs/vetassist_frontend.log 2>&1 &
```

Or as a systemd service:
```ini
# /etc/systemd/system/vetassist-frontend.service
[Unit]
Description=VetAssist Next.js Frontend
After=network.target

[Service]
User=dereadi
WorkingDirectory=/ganuda/vetassist/frontend
ExecStart=/usr/bin/npm start -- -p 3000
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1

[Install]
WantedBy=multi-user.target
```

### Step 8: Verification

```bash
# Verify VLAN interface is up
ip addr show vlan30

# Verify routing table
ip route show table 30

# Test direct path speed (outbound)
curl --interface vlan30 -s -o /dev/null -w '%{speed_download}' https://ash-speed.hetzner.com/100MB.bin
echo " bytes/sec via direct AT&T"

# Compare with VPN path
curl --interface enp6s0 -s -o /dev/null -w '%{speed_download}' https://ash-speed.hetzner.com/100MB.bin
echo " bytes/sec via ExpressVPN"

# Test customer-facing HTTPS (from outside the network)
curl -k https://<AT&T_PUBLIC_IP>/health
# Expected: {"status":"healthy","service":"vetassist-api","version":"2.0.0"}

# Test from inside via VLAN 30 IP
curl http://192.168.30.222:8001/health
```

### IP Address Assignments for VLAN 30

| Node | VLAN 30 IP | Role | Physical Interface |
|------|-----------|------|-------------------|
| AT&T Router | 192.168.30.1 | Gateway | Port 17 on TP-Link |
| bluefin | 192.168.30.222 | Web Server (VetAssist) | enp5s0.30 (tagged) |
| redfin | 192.168.30.223 | GPU Inference (future API) | enp6s0.30 (tagged) |
| greenfin | 192.168.30.224 | Daemons / Future Web | eno1.30 (tagged) |
| *Reserved* | 192.168.30.225-239 | Future expansion nodes | — |
| *Reserved* | 192.168.30.240-249 | Load balancers / edge | — |
| *Reserved* | 192.168.30.250-254 | Network infrastructure | — |

### Scaling Plan

As customer traffic grows, add web-serving nodes to VLAN 30:

**Phase 1 (Current):** Single node
- bluefin handles frontend + backend on 192.168.30.222
- AT&T forwards 80/443 → bluefin

**Phase 2 (Split frontend/backend):**
- bluefin: Backend API (192.168.30.222)
- New node or greenfin: Frontend (192.168.30.224)
- Caddy load balances between them

**Phase 3 (Dedicated web tier):**
- Add 1-2 web nodes (192.168.30.225, .226)
- Caddy on .222 as load balancer
- Backend cluster behind LB
- Database stays on VLAN 1 (internal only)

**Phase 4 (High availability):**
- Multiple AT&T uplinks or failover ISP
- Keepalived for VIP failover between web nodes
- DNS round-robin or Cloudflare proxy for global CDN

### Traffic Separation Summary

| Traffic Type | VLAN | Path | Encrypted By |
|---|---|---|---|
| Customer web (HTTPS) | 30 | AT&T direct → Caddy → App | TLS (Let's Encrypt) |
| Model downloads | 30 | Outbound direct AT&T | HTTPS |
| Package updates | 30 | Outbound direct AT&T | HTTPS |
| Inter-node compute | 1 | ExpressVPN | VPN + WireGuard |
| Database traffic | 1+20 | ExpressVPN → goldfin tunnel | VPN + SSH tunnel |
| PII/sensitive data | 1 | ExpressVPN | VPN |
| Admin/SSH | 1 | ExpressVPN + Tailscale | VPN + WireGuard |

### Security Notes

- VLAN 30 traffic is NOT encrypted by VPN — TLS handles customer encryption
- Customer-facing services MUST have valid HTTPS certificates
- Caddy auto-provisions Let's Encrypt certs (needs domain DNS pointing to AT&T public IP)
- Rate limiting on Caddy recommended before production launch
- Crawdad review required before opening port forwards
- Never expose database ports (5432, 5433) or LLM Gateway (8080) on VLAN 30
- Only ports 80 and 443 should be forwarded from the AT&T router

### Rollback

To disable VLAN 30 without removing config:
```bash
sudo ip link set vlan30 down
```

To remove completely:
- Delete netplan/nmcli config
- Remove VLAN 30 from switch
- Remove AT&T port forwards
- Stop Caddy or rebind to VLAN 1
- Unplug AT&T cable from port 17
