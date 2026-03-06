# KB-WIREGUARD-MESH-DEPLOYMENT-FEB24-2026

**Status**: DEPLOYED
**Date**: February 24, 2026
**Verified**: March 2, 2026 (post-reboot)
**Design Doc**: /ganuda/docs/design/PLAN-WIREGUARD-MESH-FEB24-2026.md

---

## Summary

WireGuard mesh VPN deployed across all 5 Linux nodes in the Cherokee AI Federation. This adds a third encrypted network plane (10.100.0.0/24) for internal service communication, alongside the existing LAN and Tailscale planes.

---

## Three Network Planes

| Plane | Subnet | Purpose |
|---|---|---|
| LAN | 192.168.132.x | Management, SSH, Ansible, cluster comms |
| WireGuard | 10.100.0.x | Encrypted internal service mesh |
| Tailscale | 100.x.x.x | Remote access, mobile nodes, NAT traversal |

WireGuard fills the gap between LAN (unencrypted) and Tailscale (external relay-dependent). Traffic between Linux nodes that stays on-prem should prefer 10.100.0.x once service migration is complete.

---

## Interface Configuration

- **Interface**: wg0
- **Port**: 51820/udp
- **Subnet**: 10.100.0.0/24
- **Topology**: Full mesh with pre-shared keys (PSK) between all active peers
- **Key management**: Each node pair shares a unique PSK in addition to asymmetric keypairs

---

## Node Assignments

| Node | WireGuard IP | Status |
|---|---|---|
| redfin | 10.100.0.1 | ACTIVE |
| bluefin | 10.100.0.2 | ACTIVE |
| greenfin | 10.100.0.3 | ACTIVE |
| bmasass | 10.100.0.4 | RESERVED — Phase 2, not yet deployed |
| owlfin | 10.100.0.5 | ACTIVE |
| eaglefin | 10.100.0.6 | ACTIVE |

bmasass is an M4 Max macOS node and requires a different deployment path. Phase 2 scope includes adding it as a peer and removing its dependency on Tailscale DERP relay for federation traffic.

---

## File Locations

- **Config source**: `/ganuda/config/wireguard/wg0-<node>.conf` (one file per node)
- **Deployed to**: `/etc/wireguard/wg0.conf` on each node
- **systemd unit**: `wg-quick@wg0` — enabled and started on all 5 Linux nodes

To check status on any node:

```text
systemctl status wg-quick@wg0
wg show
```

---

## Firewall Rules

### redfin, bluefin, greenfin

nftables rule for 51820/udp was added manually at deploy time. It is NOT yet in the persistent nftables config files. A reboot or nftables reload will drop the rule until the persistent configs are updated.

Config files that need the rule added:
- `/ganuda/config/nftables-redfin.conf`
- `/ganuda/config/nftables-bluefin.conf`
- `/ganuda/config/nftables-greenfin.conf`

Rule to add (in the inet filter input chain):

```text
udp dport 51820 accept comment "WireGuard"
```

### owlfin, eaglefin

These nodes have no nftables installed. All ports are open by default. No firewall change needed.

---

## Verification (March 2, 2026 — Post-Reboot)

All 4 active peers healthy with recent handshakes:

- Handshakes within 2 minutes on all peers
- Tailscale ping via WireGuard: bluefin 1ms, greenfin 1ms
- bmasass still routes through Tailscale DERP relay (no WG peer yet — expected)

To verify mesh health after a reboot:

```text
wg show
```

Look for `latest handshake` timestamps on all peers. Handshakes should appear within ~2 minutes of tunnel activity.

---

## TODO / Open Items

| Item | Priority | Phase |
|---|---|---|
| Add 51820/udp to persistent nftables configs on redfin, bluefin, greenfin | HIGH | Now |
| Add bmasass as Phase 2 WireGuard peer | MEDIUM | Phase 2 |
| Migrate internal federation services to 10.100.0.x endpoints | LOW | Phase 2+ |

The nftables persistence issue is the most urgent. If any of the three core nodes reboots or nftables is reloaded without the persistent rule, WireGuard handshakes from peers will be blocked at the firewall and the mesh will silently degrade.

---

## Coyote Notes

- Always verify `wg show` after any reboot of a core node, not just the node you rebooted. Mesh topology means one dropped peer affects routing for others.
- The bmasass DERP relay dependency is a known limitation. Do not assume bmasass is on the WireGuard mesh until Phase 2 is explicitly deployed and verified.
- `wg-quick@wg0 enabled` means it starts on boot. Confirm with `systemctl is-enabled wg-quick@wg0` if in doubt.

---

## Related

- MEMORY.md: WireGuard Mesh section
- /ganuda/docs/design/PLAN-WIREGUARD-MESH-FEB24-2026.md
- /ganuda/config/wireguard/ (node configs)
- /ganuda/config/nftables-*.conf (persistent firewall configs — need update)
