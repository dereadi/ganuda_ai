# KB-ISOLATED-VLAN-TAILSCALE-VIA-SQUID-JAN15-2026

## Installing Tailscale on Air-Gapped/Isolated VLAN Nodes via Squid Proxy

**Date:** January 15, 2026
**Author:** TPM (Claude Opus 4.5)
**Classification:** Infrastructure / Networking
**Difficulty:** Intermediate
**Time to Complete:** 30-45 minutes

---

## Problem Statement

Nodes on isolated VLANs (like our PII vault on VLAN 20) have no direct internet access by design. However, we need to install Tailscale on these nodes to enable secure remote access. This creates a chicken-and-egg problem: can't install Tailscale without internet, can't get internet without Tailscale.

**Solution:** Use a Squid HTTP proxy on a node that bridges the VLANs (greenfin) to provide controlled internet access for package installation.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VLAN ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  VLAN 1 (192.168.132.0/24) - Compute                                │
│  ├── redfin    (192.168.132.223) - GPU Inference                    │
│  ├── bluefin   (192.168.132.222) - Database                         │
│  └── greenfin  (192.168.132.224) - Router/Proxy ◄── Squid here      │
│                    │                                                 │
│                    │ (greenfin bridges VLANs)                        │
│                    │                                                 │
│  VLAN 10 (192.168.10.0/24) - Identity                               │
│  └── silverfin (192.168.10.10) - FreeIPA                            │
│         └── Gateway: 192.168.10.1 (greenfin)                        │
│                                                                      │
│  VLAN 20 (192.168.20.0/24) - Sanctum/PII                            │
│  └── goldfin   (192.168.20.10) - PII Vault ◄── Install Tailscale    │
│         └── Gateway: 192.168.20.1 (greenfin)                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**greenfin** serves as the router between VLANs with interfaces:
- `eno1` - 192.168.132.224 (VLAN 1)
- `eno1.10` - 192.168.10.1 (VLAN 10 gateway)
- `eno1.20` - 192.168.20.1 (VLAN 20 gateway)

---

## Step 1: Install and Configure Squid on greenfin

### 1.1 Install Squid
```bash
# On greenfin (Ubuntu)
sudo apt update
sudo apt install squid -y
```

### 1.2 Configure Squid ACLs

Edit `/etc/squid/squid.conf` and add these lines **BEFORE** `http_access deny all`:

```bash
sudo vi /etc/squid/squid.conf
```

Find the line `http_access deny all` (around line 1630) and add BEFORE it:
```
# Allow isolated VLANs to use proxy
acl isolated_vlans src 192.168.10.0/24 192.168.20.0/24
http_access allow isolated_vlans
```

The order matters! Your http_access section should look like:
```
http_access allow localhost
http_access allow isolated_vlans    <-- Add this
http_access deny all                <-- Must be after
```

### 1.3 Restart Squid
```bash
sudo systemctl restart squid
sudo systemctl status squid
```

### 1.4 Verify Squid is Listening
```bash
sudo ss -tlnp | grep 3128
# Should show: *:3128 (listening on all interfaces)
```

---

## Step 2: Configure nftables on greenfin

This was the trickiest part. greenfin uses nftables with strict INPUT rules.

### 2.1 Check Current Rules
```bash
sudo nft list ruleset
```

If you see `policy drop;` in the input chain, you need to add rules.

### 2.2 Add Rules for Port 3128
```bash
# Allow squid connections from isolated VLANs
sudo nft add rule inet filter input ip saddr 192.168.10.0/24 tcp dport 3128 accept
sudo nft add rule inet filter input ip saddr 192.168.20.0/24 tcp dport 3128 accept
```

### 2.3 Make Permanent
```bash
sudo nft list ruleset | sudo tee /etc/nftables.conf
```

---

## Step 3: Configure Firewall on Isolated Node (goldfin)

goldfin runs Rocky Linux with firewalld in DROP zone - very restrictive by design.

### 3.1 Add OUTPUT Rules
```bash
# On goldfin - allow outbound to squid proxy
sudo firewall-cmd --permanent --direct --add-rule ipv4 filter OUTPUT 0 -d 192.168.132.224 -p tcp --dport 3128 -j ACCEPT

# Allow DNS
sudo firewall-cmd --permanent --direct --add-rule ipv4 filter OUTPUT 0 -p udp --dport 53 -j ACCEPT

# Allow established connections back in
sudo firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 -m state --state ESTABLISHED,RELATED -j ACCEPT

# Reload
sudo firewall-cmd --reload
```

### 3.2 Verify Rules
```bash
sudo firewall-cmd --direct --get-all-rules
```

---

## Step 4: Test Proxy Connectivity

### 4.1 From goldfin, test connection to squid
```bash
nc -zv 192.168.132.224 3128
# Should show: Connected
```

### 4.2 Test actual proxy functionality
```bash
export http_proxy=http://192.168.132.224:3128
export https_proxy=http://192.168.132.224:3128
curl -I http://google.com
# Should show: HTTP/1.1 301 Moved Permanently
```

---

## Step 5: Install Tailscale on goldfin

### 5.1 Configure dnf to Use Proxy
```bash
echo "proxy=http://192.168.132.224:3128" | sudo tee -a /etc/dnf/dnf.conf
```

### 5.2 Add Tailscale Repository
```bash
export http_proxy=http://192.168.132.224:3128
export https_proxy=http://192.168.132.224:3128
curl -fsSL https://pkgs.tailscale.com/stable/rhel/9/tailscale.repo | sudo tee /etc/yum.repos.d/tailscale.repo
```

### 5.3 Install Tailscale
```bash
sudo dnf install -y tailscale
```

### 5.4 Configure tailscaled to Use Proxy

The tailscaled daemon needs proxy configuration via systemd:

```bash
sudo mkdir -p /etc/systemd/system/tailscaled.service.d
sudo tee /etc/systemd/system/tailscaled.service.d/proxy.conf << 'EOF'
[Service]
Environment="HTTP_PROXY=http://192.168.132.224:3128"
Environment="HTTPS_PROXY=http://192.168.132.224:3128"
EOF
```

### 5.5 Start and Authenticate
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tailscaled
sudo tailscale up
```

Visit the authentication URL provided, then verify:
```bash
tailscale status
tailscale ip
```

---

## Troubleshooting Guide

We encountered several layers of issues. Here's how to diagnose:

### Issue 1: nc to squid times out

**Check order:**
1. Is squid running? `systemctl status squid`
2. Is squid listening on all interfaces? `ss -tlnp | grep 3128` (should show `*:3128`)
3. Is nftables blocking? `sudo nft list chain inet filter input` (need rule for 3128)
4. Is source firewall blocking outbound? Check firewall-cmd on isolated node

### Issue 2: Packets arrive but no response (visible in tcpdump)

```bash
# On proxy node - watch for incoming connections
sudo tcpdump -i any port 3128 -n
```

If you see SYN packets but no SYN-ACK:
- Check nftables INPUT rules
- Check if squid ACLs allow the source IP
- Check `/var/log/squid/cache.log` for denied messages

### Issue 3: Squid denies connection

Check squid.conf ACL order:
```bash
grep -n "http_access" /etc/squid/squid.conf | head -20
```

The `allow isolated_vlans` MUST appear BEFORE `deny all`.

### Issue 4: tailscale up hangs

The tailscaled daemon isn't using the proxy. Configure via systemd override (Step 5.4).

---

## Security Considerations

1. **Squid ACLs**: Only allow specific source IPs, not open proxy
2. **nftables**: Only open port 3128 to isolated VLANs
3. **Isolated node firewall**: Only allow outbound to specific proxy IP
4. **Tailscale ACLs**: Configure in Tailscale admin to restrict who can access the PII vault

---

## Verification Checklist

- [ ] Squid running on greenfin (`systemctl status squid`)
- [ ] Squid ACLs allow isolated VLANs
- [ ] nftables allows port 3128 from isolated VLANs
- [ ] Isolated node can `nc -zv` to proxy:3128
- [ ] `curl` via proxy returns HTTP response
- [ ] Tailscale installed and authenticated
- [ ] `tailscale status` shows connected

---

## Files Modified

| Node | File | Purpose |
|------|------|---------|
| greenfin | `/etc/squid/squid.conf` | ACLs for isolated VLANs |
| greenfin | `/etc/nftables.conf` | Allow port 3128 |
| goldfin | `/etc/dnf/dnf.conf` | Proxy for package manager |
| goldfin | `/etc/yum.repos.d/tailscale.repo` | Tailscale repository |
| goldfin | `/etc/systemd/system/tailscaled.service.d/proxy.conf` | Proxy for daemon |
| goldfin | firewalld direct rules | OUTPUT to proxy |

---

## Related Documentation

- CMDB: goldfin (192.168.20.10) - PII Vault
- CMDB: greenfin (192.168.132.224) - Router/Proxy
- KB: VLAN Architecture Setup (pending)
- Tailscale Admin: https://login.tailscale.com/admin

---

## Lessons Learned

1. **Layer the diagnostics**: Start with basic connectivity (ping), then port (nc), then protocol (curl)
2. **nftables vs iptables**: Modern Ubuntu uses nftables even when iptables commands work
3. **Multiple firewalls**: Check BOTH ends - source node outbound AND destination node inbound
4. **Daemon vs shell**: Environment variables set in shell don't affect systemd services
5. **tcpdump is your friend**: When packets arrive but nothing happens, check host firewall
6. **Order matters in squid**: ACL allow rules must come before deny all

---

*Cherokee AI Federation - For the Seven Generations*
*"The path through isolation is built one hop at a time."*
