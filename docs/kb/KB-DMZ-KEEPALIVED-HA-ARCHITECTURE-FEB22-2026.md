# KB-DMZ-KEEPALIVED-HA-ARCHITECTURE-FEB22-2026

**Domain:** Infrastructure / DMZ / High Availability
**Status:** Live (as of Feb 22 2026)
**Nodes:** owlfin, eaglefin
**Last Updated:** Mar 2 2026

---

## Overview

The Cherokee AI Federation DMZ web layer is a dual-node high-availability cluster serving ganuda.us. Two identical Beelink EQR5 nodes (owlfin and eaglefin) run Caddy web servers behind a keepalived VRRP virtual IP (VIP). Customer traffic arrives at the VIP; internal cluster communication and Ansible management use a separate management network. Failover between master and backup is automatic and seamless.

---

## Hardware

Both nodes are identical:

- **Model:** Beelink EQR5
- **CPU:** AMD Ryzen 5 5500U (6-core)
- **RAM:** 16GB
- **Storage:** 500GB NVMe
- **OS:** Linux Mint

---

## Node Inventory

| Node | Role | Management NIC (eno1) | DMZ NIC (enp1s0) | WireGuard (wg0) |
|---|---|---|---|---|
| owlfin | keepalived MASTER | 192.168.132.170 | 192.168.30.2 | 10.100.0.5 |
| eaglefin | keepalived BACKUP | 192.168.132.84 | 192.168.30.3 | 10.100.0.6 |
| VIP (shared) | — | — | 192.168.30.10 | — |

---

## Network Architecture

### Dual-Homed Design

Each node has two network interfaces serving distinct purposes:

- **eno1 (192.168.132.x):** Management plane. Used for SSH, Ansible deployments, cluster-internal communication. Not exposed to customer traffic.
- **enp1s0 (192.168.30.x):** DMZ plane. Carries customer-facing web traffic. Caddy listens here. Keepalived VRRP operates on this interface.

This separation means operator access and customer traffic never share the same path. Ansible runs against `.132` addresses; DNS points to the external IP which forwards to `.30`.

### Virtual IP

The VIP `192.168.30.10` is owned by whichever node is currently the keepalived master. Under normal operation this is owlfin. DNS for ganuda.us resolves to the external IP, which is port-forwarded by the upstream router to `192.168.30.10:80/443`.

### Firewall

Neither owlfin nor eaglefin run nftables. Both nodes are open by default on the DMZ interface. The upstream router and Cloudflare (if in use) provide the external boundary.

---

## Keepalived VRRP Failover

Keepalived implements VRRP (Virtual Router Redundancy Protocol) between owlfin and eaglefin.

**Normal state:**
- owlfin holds the VIP 192.168.30.10 (MASTER)
- eaglefin monitors but does not hold the VIP (BACKUP)
- All inbound web traffic flows to owlfin

**Failover event:**
- If owlfin becomes unreachable (node down, Caddy crash, network fault), keepalived on eaglefin detects the VRRP heartbeat loss
- eaglefin promotes itself to MASTER
- eaglefin claims the VIP 192.168.30.10
- DNS continues to resolve correctly — the VIP address did not change
- Traffic begins flowing to eaglefin with no DNS propagation delay

**Recovery:**
- When owlfin returns, it resumes MASTER status (higher priority) and reclaims the VIP
- This preemption is configurable — current config uses standard priority-based preemption

**Failover is seamless** because both nodes always have current web content (see Web Content Synchronization below).

---

## Caddy Web Server

Both owlfin and eaglefin run Caddy serving ganuda.us content.

- **Webroot:** `/home/dereadi/www/ganuda.us`
- **Caddyfile:** Managed via Ansible, deployed to both nodes

Since both nodes serve from the same webroot path and both have current content via the materializer, either node can handle traffic at any time.

---

## Web Content Synchronization

Both nodes run `web-materializer.service`, which polls the PostgreSQL database on bluefin every 30 seconds and writes content to the local webroot.

- **DB source:** bluefin (192.168.132.222)
- **Poll interval:** 30 seconds
- **Write target:** `/home/dereadi/www/ganuda.us`
- **Config:** `/opt/ganuda/secrets.env` holds DB credentials on each node

Content is always current on both nodes. When failover occurs, eaglefin already has the latest content. There is no replication lag or sync delay at failover time.

Related: KB-WEB-CONTENT-MATERIALIZER-PIPELINE-FEB27-2026.md

---

## WireGuard Mesh Integration

owlfin and eaglefin are members of the federation WireGuard mesh (`wg0`):

- **owlfin:** 10.100.0.5
- **eaglefin:** 10.100.0.6
- **Mesh peers:** redfin (10.100.0.1), bluefin (10.100.0.2), greenfin (10.100.0.3)
- **Interface:** wg0, port 51820/udp, subnet 10.100.0.0/24

This allows owlfin and eaglefin to reach bluefin's PostgreSQL (for the materializer) and other cluster services over an encrypted tunnel rather than the raw management network.

Related: KB-WIREGUARD-MESH-DEPLOYMENT-FEB24-2026.md

---

## Ansible Management

The DMZ nodes are managed from redfin via the `[dmz]` inventory group.

- **Inventory group:** `[dmz]`
- **Members:** owlfin (192.168.132.170), eaglefin (192.168.132.84)
- **SSH target:** `.132` management addresses (direct, no greenfin proxy)
- **Deploy from:** redfin

Historical note: DMZ nodes previously required SSH proxying through greenfin. This was removed. Direct SSH on `.132` is the current and correct method.

---

## DNS and External Routing

```
User browser
    |
    v
ganuda.us (DNS → external IP)
    |
    v
Router (port-forward 80/443 → 192.168.30.10)
    |
    v
VIP 192.168.30.10 (held by keepalived MASTER)
    |
    v
Caddy on owlfin (or eaglefin during failover)
    |
    v
/home/dereadi/www/ganuda.us
```

---

## Operational Notes

- **SSH into nodes:** Always use `.132` management addresses. Do not use `.30` DMZ addresses for operator access.
- **No nftables:** Do not attempt to apply nftables rulesets to these nodes. They are intentionally open; boundary control is upstream.
- **Ansible deploys:** Run from redfin. Target `[dmz]` group. Both nodes get identical config.
- **Caddy restarts:** If Caddy needs to be restarted on the MASTER, traffic briefly fails over to BACKUP. This is expected behavior and resolves automatically when Caddy comes back up.
- **WireGuard on these nodes:** No nftables `51820/udp` rule exists (since no nftables). Port is open by default. The persistent nftables TODO does not apply here.

---

## Related Knowledge Bases

- **KB-WEB-CONTENT-MATERIALIZER-PIPELINE-FEB27-2026.md** — How content flows from DB to webroot
- **KB-WIREGUARD-MESH-DEPLOYMENT-FEB24-2026.md** — Full mesh deployment details, PSKs, per-node configs

---

## Change Log

| Date | Change |
|---|---|
| Feb 22 2026 | Initial DMZ HA cluster deployed. owlfin MASTER, eaglefin BACKUP. |
| Feb 24 2026 | Ansible [dmz] group switched to direct .132 SSH (greenfin proxy removed). |
| Feb 24 2026 | WireGuard mesh deployed. owlfin=10.100.0.5, eaglefin=10.100.0.6. |
| Feb 27 2026 | web-materializer.service deployed on both nodes. Content sync live. |
| Mar 2 2026 | KB document created. |
