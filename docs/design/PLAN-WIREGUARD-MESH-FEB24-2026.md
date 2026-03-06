# PLAN: WireGuard Mesh for Inter-Node LAN Encryption

**Kanban**: #1876 (8 SP)
**Author**: TPM (Claude Opus 4.6)
**Date**: 2026-02-24
**Status**: DRAFT -- Awaiting Council Review

---

## Problem Statement

All inter-node traffic within the Cherokee AI Federation traverses the 192.168.132.0/24 LAN in plaintext. This includes:
- PostgreSQL connections to bluefin (.222:5432) carrying thermal memory, credentials, council votes
- Embedding API calls to greenfin (.224:8003) carrying raw text for vectorization
- vLLM inference calls to redfin (.223:8000) carrying full prompts and completions
- SSH sessions between all nodes
- MLX inference calls to bmasass (.21:8800)

Any device on the LAN segment (managed switch, compromised IoT, ARP spoof) can observe this traffic. WireGuard provides authenticated, encrypted tunnels with minimal overhead (~3-5% throughput, <1ms latency on LAN).

---

## 1. Topology: Full Mesh

**Recommendation: Full mesh** for 6 nodes (15 peer connections).

Rationale:
- 6 nodes is well within WireGuard's design sweet spot (it handles thousands of peers)
- Hub-spoke creates a SPOF and doubles latency for cross-node calls (e.g., bluefin->greenfin would route through hub)
- Any node talks to any node today (redfin->bluefin for DB, redfin->greenfin for embeddings, greenfin->bluefin for DB, etc.)
- Config is slightly more verbose but trivially templatable

Each node has 5 peer stanzas. Total unique tunnels: C(6,2) = 15.

---

## 2. IP Scheme

**Overlay network**: `10.100.0.0/24` on interface `wg0`

| Node      | LAN IP           | WireGuard IP  | WG Port |
|-----------|------------------|---------------|---------|
| redfin    | 192.168.132.223  | 10.100.0.1    | 51820   |
| bluefin   | 192.168.132.222  | 10.100.0.2    | 51820   |
| greenfin  | 192.168.132.224  | 10.100.0.3    | 51820   |
| bmasass   | 192.168.132.21   | 10.100.0.4    | 51820   |
| owlfin    | 192.168.132.170  | 10.100.0.5    | 51820   |
| eaglefin  | 192.168.132.84   | 10.100.0.6    | 51820   |

The `.0/24` gives room for future nodes. Port 51820 is WireGuard default.

DNS: Add entries to `/etc/hosts` on each node so `redfin-wg`, `bluefin-wg`, etc. resolve to 10.100.0.x. This allows gradual migration without breaking existing hostnames.

---

## 3. Key Management

Each node generates its own keypair locally. Private keys never leave the node.

```text
# On each node (TPM-direct, requires sudo):
wg genkey | tee /etc/wireguard/privatekey | wg pubkey > /etc/wireguard/publickey
chmod 600 /etc/wireguard/privatekey
```

Public keys are collected and distributed via the WireGuard config files. No PKI infrastructure needed -- WireGuard uses Curve25519 for key exchange (256-bit, post-quantum resistant when combined with PSK).

**Pre-shared keys (PSK)**: Generate one PSK per peer pair for post-quantum defense-in-depth:
```text
wg genpsk > /etc/wireguard/psk-redfin-bluefin
```
This adds a symmetric key layer on top of Curve25519. 15 PSKs total.

---

## 4. Service Migration Plan

### Services requiring config changes

| Service | Current Endpoint | Config File | Change Needed |
|---------|-----------------|-------------|---------------|
| PostgreSQL | 192.168.132.222:5432 | `/ganuda/config/ganuda.yaml` (database.host) | Change to 10.100.0.2 |
| PostgreSQL | 192.168.132.222:5432 | `pg_hba.conf` on bluefin | Add 10.100.0.0/24 trust/md5 line |
| Embedding | 192.168.132.224:8003 | `specialist_council.py`, `amem_memory.py` | Grep for `.224:8003`, update |
| vLLM (text) | localhost:8000 | `ganuda.yaml` (inference.base_url) | No change (localhost on redfin) |
| vLLM (vision) | 192.168.132.222:8090 | `vlm_routes.py` | Change to 10.100.0.2:8090 |
| MLX DeepSeek | 192.168.132.21:8800 | `gateway.py` (deepseek routing) | Change to 10.100.0.4:8800 |
| OpenObserve | 192.168.132.224:5080 | Promtail configs on each node | Change to 10.100.0.3:5080 |
| SSH | Various .132.x | `~/.ssh/config`, Ansible inventory | Add wg aliases |

### Strategy: Dual-stack transition

During Phase 3, services bind to `0.0.0.0` (both LAN and WG interfaces). Clients switch to WG IPs one at a time. Only in Phase 4 do we restrict to WG-only via nftables.

---

## 5. Phasing

### Phase 1: Linux Nodes (redfin, bluefin, greenfin, owlfin, eaglefin)

**TPM-direct work** (requires sudo on each node):
- Install `wireguard-tools` on all 5 Linux nodes
- Generate keypairs + PSKs on each node
- Write `/etc/wireguard/wg0.conf` per node
- `systemctl enable --now wg-quick@wg0`
- Verify: `wg show` on each node, `ping 10.100.0.x` across all pairs

**Estimated effort**: 2 hours hands-on across 5 nodes.

Config template (redfin example):
```text
[Interface]
PrivateKey = <redfin-private>
Address = 10.100.0.1/24
ListenPort = 51820

[Peer]
# bluefin
PublicKey = <bluefin-public>
PresharedKey = <psk-redfin-bluefin>
AllowedIPs = 10.100.0.2/32
Endpoint = 192.168.132.222:51820

[Peer]
# greenfin
PublicKey = <greenfin-public>
PresharedKey = <psk-redfin-greenfin>
AllowedIPs = 10.100.0.3/32
Endpoint = 192.168.132.224:51820

# ... (owlfin, eaglefin peers)
```

### Phase 2: bmasass (macOS)

- Install WireGuard via `brew install wireguard-tools`
- macOS uses `wireguard-go` userspace implementation (no kernel module)
- Config file at `/usr/local/etc/wireguard/wg0.conf` (or `/opt/homebrew/etc/wireguard/wg0.conf` on Apple Silicon)
- Start: `sudo wg-quick up wg0`
- LaunchDaemon for persistence (TPM creates plist)

**Tailscale coexistence**: Tailscale uses `utun` interfaces (utun0, utun1, etc.) and manages its own routing table. WireGuard will create a separate `utun` interface. They do not conflict as long as:
- WireGuard AllowedIPs is scoped to `10.100.0.0/24` only (no default route)
- Tailscale AllowedIPs covers WAN/remote subnets only
- No overlapping IP ranges (10.100.0.0/24 vs Tailscale's 100.64.x.x CGNAT range)

### Phase 3: Service Migration

**Jr-eligible work** (config file edits, no sudo):
- Update `ganuda.yaml` database.host to 10.100.0.2
- Update all hardcoded `192.168.132.x` references in Python services
- Update Ansible inventory with wg IPs as secondary
- Update Promtail configs for OpenObserve endpoint

**TPM-direct work** (sudo required):
- Update `pg_hba.conf` on bluefin
- Update nftables to allow UDP 51820 on all nodes
- Restart PostgreSQL after pg_hba change

### Phase 4: Enforcement via nftables

Add rules to each node's nftables:
```text
# Allow WireGuard handshake on LAN interface
ip saddr 192.168.132.0/24 udp dport 51820 accept

# Allow all traffic on wg0 interface
iif "wg0" accept

# DROP inter-node service traffic on LAN interface (force through WG)
ip saddr 192.168.132.0/24 tcp dport { 5432, 8000, 8003, 8080, 8090, 8800, 5080, 5081 } drop
```

**WARNING**: Phase 4 is the danger zone. If WireGuard drops, all inter-node services break. Only proceed after Phase 3 has been stable for at least 1 week. Keep a rollback script that removes the DROP rules.

---

## 6. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| WireGuard tunnel drops | All inter-node services fail (DB, inference, embedding) | Phase 4 rollback script; `PersistentKeepalive = 25` in peer configs; systemd auto-restart |
| MTU issues | Packet fragmentation, silent throughput drops | Set `MTU = 1420` on wg0 (WireGuard overhead is 60 bytes on IPv4); test with `ping -M do -s 1392` |
| macOS WireGuard instability | bmasass loses mesh connectivity | wireguard-go is mature; LaunchDaemon ensures restart; Tailscale proves userspace WG works fine on this machine |
| Key compromise on one node | Attacker can impersonate that node | PSKs limit blast radius; revoke by removing peer stanza from all other nodes; generate new keypair |
| nftables Phase 4 lockout | Nodes unreachable if WG AND LAN rules both fail | Always allow SSH on LAN as fallback; test nftables changes with `at` job to revert after 5 minutes |
| Performance on DMZ nodes | owlfin/eaglefin are Ryzen 5 5500U -- crypto overhead | WireGuard uses ChaCha20-Poly1305 (optimized for CPUs without AES-NI, though Ryzen 5 has AES-NI). Negligible impact. |

---

## 7. Tailscale Interaction

bmasass currently runs Tailscale for WAN remote access (100.64.x.x range).

- **WireGuard mesh**: LAN encryption between federation nodes on 10.100.0.0/24
- **Tailscale**: Remote access from outside the LAN (phone, travel laptop)
- **No conflict**: Different subnets, different interfaces, different purposes
- **Routing**: WireGuard AllowedIPs MUST NOT include `0.0.0.0/0` (that would fight Tailscale for default route). Scope strictly to `10.100.0.0/24`.

If we later want Tailscale on other nodes for remote access, same principle applies -- Tailscale manages its routes, WireGuard manages the 10.100.0.0/24 mesh.

---

## 8. Work Split

### TPM-Direct (sudo required, security-sensitive)

- Key generation on all 6 nodes
- PSK generation (15 pairs)
- Write `/etc/wireguard/wg0.conf` on each node
- `pg_hba.conf` update on bluefin
- nftables rules for UDP 51820
- Phase 4 enforcement rules + rollback script
- macOS LaunchDaemon plist for bmasass
- Systemd enable/start on Linux nodes

### Jr-Eligible (config edits, no privilege escalation)

- Update `ganuda.yaml` database.host
- Grep + update all `192.168.132.x` hardcoded IPs in Python services
- Update Ansible inventory with wg aliases
- Update Promtail/monitoring configs
- Add `-wg` entries to `/ganuda/config/` host mapping files
- Write health check script: ping all 10.100.0.x peers, alert on failure

---

## 9. Success Criteria

- [ ] `wg show` on all 6 nodes shows active handshakes with all 5 peers
- [ ] `ping -c 3 10.100.0.x` works from every node to every other node
- [ ] PostgreSQL connections work over 10.100.0.2:5432
- [ ] Embedding calls work over 10.100.0.3:8003
- [ ] `tcpdump -i eth0 port 5432` on bluefin shows zero plaintext PG traffic (all goes through wg0)
- [ ] Latency overhead < 1ms (measured via `ping` delta between LAN and WG IPs)
- [ ] WireGuard survives node reboot (systemd/LaunchDaemon persistence)

---

## 10. Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|-------------|
| Phase 1 (Linux mesh) | 1 session (2-3 hrs) | None |
| Phase 2 (bmasass) | 30 min | Phase 1 |
| Phase 3 (service migration) | 2-3 Jr tasks + TPM PG work | Phase 1+2 stable |
| Phase 4 (enforcement) | 1 session | Phase 3 stable for 1 week |

**Total**: ~8 SP across 2 weeks with soak time.
