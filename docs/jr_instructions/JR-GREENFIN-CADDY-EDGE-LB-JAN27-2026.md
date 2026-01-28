# JR Instruction: Set Up Caddy Edge LB on Greenfin

**JR ID:** JR-GREENFIN-CADDY-EDGE-LB
**Priority:** P1 (Infrastructure)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Assigned To:** Infrastructure Jr.
**Effort:** Medium (2-4 hours)
**Council Review:** Approved with concerns noted (SECURITY, PERF, 7GEN)

---

## Objective

Install Caddy on greenfin as the edge load balancer for VetAssist and other Cherokee AI Federation services. Greenfin is the inter-VLAN gateway - all traffic flows through it.

---

## Architecture

```
Internet → nachocheese (ISP) → greenfin (Caddy LB)
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
    VLAN 132                    VLAN 10                    VLAN 20
   ┌─────────┐               ┌─────────┐               ┌─────────┐
   │ redfin  │               │silverfin│               │ goldfin │
   │ API+GPU │               │ FreeIPA │               │   PII   │
   └─────────┘               └─────────┘               └─────────┘

Caddy Routes:
  vetassist.cherokee.local → redfin:3000 (Next.js)
  api.vetassist.cherokee.local → redfin:8001 (FastAPI)
  llm.cherokee.local → redfin:8080 (LLM Gateway)
  sag.cherokee.local → redfin:4000 (SAG UI)
```

---

## Greenfin Current State

| Component | Value |
|-----------|-------|
| IP (VLAN 132) | 192.168.132.224 |
| IP (VLAN 10) | 192.168.10.1 |
| IP (VLAN 20) | 192.168.20.1 |
| OS | Ubuntu 24.04.3 LTS |
| CPU | AMD Ryzen AI MAX+ 395 |
| RAM | 128 GB |
| Current Services | nftables, Squid (3128), Promtail |

---

## Phase 1: Install Caddy

### 1.1 Install via apt

```bash
# On greenfin
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

### 1.2 Verify Installation

```bash
caddy version
systemctl status caddy
```

---

## Phase 2: Configure Caddyfile

### 2.1 Create Caddyfile

```bash
sudo tee /etc/caddy/Caddyfile << 'EOF'
# Cherokee AI Federation - Edge Load Balancer
# Greenfin - Inter-VLAN Gateway
# Updated: 2026-01-27

# Global options
{
    admin off
    log {
        output file /var/log/caddy/access.log
        format json
    }
}

# VetAssist Frontend
vetassist.cherokee.local {
    reverse_proxy redfin:3000 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }

    # Health check
    handle /health {
        respond "OK" 200
    }

    log {
        output file /var/log/caddy/vetassist.log
    }
}

# VetAssist API
api.vetassist.cherokee.local {
    reverse_proxy redfin:8001 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}

# LLM Gateway
llm.cherokee.local {
    reverse_proxy redfin:8080 {
        header_up X-Real-IP {remote_host}
    }
}

# SAG Unified Interface
sag.cherokee.local {
    reverse_proxy redfin:4000 {
        header_up X-Real-IP {remote_host}
    }
}

# Kanban Board
kanban.cherokee.local {
    reverse_proxy redfin:3001 {
        header_up X-Real-IP {remote_host}
    }
}

# Direct IP access (fallback)
:80 {
    respond "Cherokee AI Federation - Use proper hostname" 404
}
EOF
```

### 2.2 Create Log Directory

```bash
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy
```

---

## Phase 3: DNS Configuration

### 3.1 Add DNS Records (FreeIPA on silverfin)

```bash
# From a node with FreeIPA client
kinit admin
ipa dnsrecord-add cherokee.local vetassist --a-rec=192.168.132.224
ipa dnsrecord-add cherokee.local api.vetassist --a-rec=192.168.132.224
ipa dnsrecord-add cherokee.local llm --a-rec=192.168.132.224
ipa dnsrecord-add cherokee.local sag --a-rec=192.168.132.224
ipa dnsrecord-add cherokee.local kanban --a-rec=192.168.132.224
```

### 3.2 Alternative: /etc/hosts (for testing)

```bash
# On client machines
echo "192.168.132.224 vetassist.cherokee.local api.vetassist.cherokee.local llm.cherokee.local sag.cherokee.local" | sudo tee -a /etc/hosts
```

---

## Phase 4: Firewall Configuration

### 4.1 Allow HTTP/HTTPS on greenfin

```bash
# Add to nftables rules
sudo nft add rule inet filter input tcp dport 80 accept
sudo nft add rule inet filter input tcp dport 443 accept

# Or using ufw if enabled
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## Phase 5: Start and Verify

### 5.1 Start Caddy

```bash
sudo systemctl enable caddy
sudo systemctl start caddy
sudo systemctl status caddy
```

### 5.2 Test Routes

```bash
# From any federation node
curl -H "Host: vetassist.cherokee.local" http://192.168.132.224/health
curl -H "Host: api.vetassist.cherokee.local" http://192.168.132.224/docs
curl -H "Host: llm.cherokee.local" http://192.168.132.224/health
```

---

## Phase 6: SSL/TLS (Optional - Internal)

For internal use with self-signed certs:

```bash
# Caddy auto-generates certs for HTTPS
# Update Caddyfile to use tls internal:
vetassist.cherokee.local {
    tls internal
    reverse_proxy redfin:3000
}
```

---

## Success Criteria

- [ ] Caddy installed on greenfin
- [ ] Caddyfile configured with all routes
- [ ] DNS records created (or /etc/hosts for testing)
- [ ] Firewall allows 80/443
- [ ] All routes responding:
  - vetassist.cherokee.local → redfin:3000
  - api.vetassist.cherokee.local → redfin:8001
  - llm.cherokee.local → redfin:8080
  - sag.cherokee.local → redfin:4000

---

## Council Concerns Addressed

| Concern | Mitigation |
|---------|------------|
| SECURITY | Caddy on gateway provides single entry point; easier to monitor/firewall |
| PERF | Greenfin has 128GB RAM, Caddy is lightweight |
| 7GEN | Documented architecture, easy to add nodes later |

---

## Future Scaling

When load increases beyond greenfin's capacity:
1. Move Next.js to dedicated web nodes
2. Caddy on greenfin becomes pure LB
3. Add more backend nodes if needed

---

## References

- KB-INFRASTRUCTURE-STATUS-JAN27-2026.md
- CHEROKEE-FEDERATION-HARDWARE-INVENTORY-JAN2026.md
- Council vote audit_hash: 4089513d037220db

---

FOR SEVEN GENERATIONS
