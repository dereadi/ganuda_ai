# KB: FreeIPA Sudo Service Management Deployment

**Date**: February 18, 2026
**Author**: TPM (Claude Opus 4.6)
**Council Vote**: #b82aea3e6ceb8906 (PROCEED WITH CAUTION, 0.888)
**Kanban**: #1822 Wrapper Scripts (5 SP) COMPLETED, #1823 FreeIPA Ansible Playbook (5 SP) COMPLETED

## Summary

Wrapper scripts (`ganuda-deploy-service`, `ganuda-service-ctl`) deployed to `/usr/local/bin/` on all 3 Linux nodes (redfin, bluefin, greenfin). A FreeIPA sudo rule `ganuda-service-management` was created on silverfin granting NOPASSWD access to both scripts for the `dereadi` user. This enables the cluster (TPM and Jr executors) to deploy and manage systemd services without password prompts, removing a long-standing blocker where `.service` file deployment required manual sudo intervention by the operator.

## Architecture

### ganuda-deploy-service

Copies staged `.service` files from `/ganuda/scripts/systemd/` to `/etc/systemd/system/`, runs `daemon-reload`, `enable --now`, sends a Telegram notification, and logs to `/ganuda/logs/service-deploy.log`.

- Input validation: checks service name contains no path separators (no traversal), verifies the staged file exists in `/ganuda/scripts/systemd/` before copying
- Only operates on files already staged by the TPM or Jr executors in the expected directory

### ganuda-service-ctl

Manages existing systemd services with the following operations: `start`, `stop`, `restart`, `status`, `enable`, `disable`. Sends Telegram notification on state changes and logs to `/ganuda/logs/service-ctl.log`.

- Input validation: checks service name for path traversal, verifies the service exists before acting
- Status queries do not trigger Telegram notifications

### FreeIPA Sudo Rule

The `ganuda-service-management` rule on silverfin grants `dereadi` NOPASSWD execution of both wrapper scripts, scoped to the redfin, bluefin, and greenfin hosts. This follows least-privilege: only the two specific wrapper scripts are permitted, not arbitrary sudo access.

## Issues Encountered and Resolved

### 1. SSSD Offline on Redfin/Greenfin

**Symptom**: `sssctl domain-status cherokee.local` showed offline. FreeIPA sudo rules not resolving.

**Root cause**: `/etc/sssd/sssd.conf` had `ipa_server = _srv_, silverfin.cherokee.local` which triggered SRV record lookup. DNS SRV records for `_kerberos._tcp.cherokee.local` were not resolvable from the VLAN 132 nodes, causing SSSD to go offline.

**Fix**: Removed the `_srv_` prefix, setting `ipa_server = silverfin.cherokee.local` directly. Restarted SSSD. Confirmed online status and sudo rule resolution.

### 2. VLAN Routing Between Silverfin and Linux Nodes

**Symptom**: Redfin and bluefin could not reach silverfin (192.168.10.10) on VLAN 10. Greenfin could (it is the VLAN router).

**Root cause**: Silverfin sits on VLAN 10 (192.168.10.0/24). The three Linux nodes are on VLAN 132 (192.168.132.0/24). Greenfin bridges both VLANs via `eno1.10` (192.168.10.1) but redfin and bluefin had no route to the 192.168.10.0/24 network.

**Fix**:
- Added nftables FORWARD rules on greenfin for IPA ports (88/tcp+udp Kerberos, 389/tcp LDAP, 636/tcp LDAPS, 443/tcp HTTPS) between VLAN 10 and VLAN 132 interfaces
- Added static routes on redfin and bluefin: `192.168.10.0/24 via 192.168.132.224` (greenfin's VLAN 132 address)
- Verified Kerberos ticket acquisition (`kinit`) and LDAP connectivity from all three nodes

### 3. Bluefin sudo-rs Incompatibility

**Symptom**: FreeIPA sudo rules worked on redfin and greenfin but not on bluefin. `sudo -l` showed no NOPASSWD entries from IPA.

**Root cause**: Bluefin runs `sudo-rs` 0.2.8 (Rust reimplementation of sudo, common on Fedora-derived systems). sudo-rs does not support SSSD/nsswitch sudoers providers — it only reads local `/etc/sudoers` and `/etc/sudoers.d/` drop-in files.

**Workaround**: Created a local `/etc/sudoers.d/ganuda-service-mgmt` drop-in file on bluefin mirroring the FreeIPA rule:

```text
dereadi ALL=(root) NOPASSWD: /usr/local/bin/ganuda-deploy-service, /usr/local/bin/ganuda-service-ctl
```

This maintains functional parity across all three nodes. If bluefin migrates to standard sudo in the future, the local drop-in can be removed and FreeIPA rules will take over.

### 4. Ansible ProxyCommand Conflict

**Symptom**: Ansible connections to Linux nodes hung or failed with SSH errors after FreeIPA enrollment.

**Root cause**: FreeIPA client enrollment creates `/etc/ssh/ssh_config.d/04-ipa.conf` which sets `ProxyCommand /usr/bin/sss_ssh_knownhostsproxy ...` for ALL hosts (`Host *`). This intercepts Ansible's SSH connections and attempts SSSD host key verification, which fails or hangs when SSSD is under load or the target is not an IPA host.

**Fix**: Added `ansible_ssh_extra_args='-o ProxyCommand=none'` to the Ansible inventory for all hosts. This overrides the system-wide ProxyCommand for Ansible connections only, without modifying the IPA-managed SSH config.

## Persistence Requirements (PENDING)

The following changes were applied live but need to be persisted to survive reboots:

1. **Static routes on redfin/bluefin**: `192.168.10.0/24 via 192.168.132.224` currently added via `ip route add`. Need to be added to netplan configuration (`/etc/netplan/*.yaml`) on both nodes.

2. **nftables forward rules on greenfin**: IPA port forwarding rules (88,389,636,443) between VLAN 10 and VLAN 132 interfaces. Need to be added to `/ganuda/config/nftables-greenfin.conf` so they survive `nftables.service` restart and reboots.

3. **SSSD config changes**: Already persisted. The `/etc/sssd/sssd.conf` files on all three nodes were edited directly (not via transient override).

## Files

| File | Location | Purpose |
|------|----------|---------|
| `ganuda-deploy-service` | `/ganuda/scripts/ganuda-deploy-service` (source), `/usr/local/bin/` (deployed) | Service deployment wrapper |
| `ganuda-service-ctl` | `/ganuda/scripts/ganuda-service-ctl` (source), `/usr/local/bin/` (deployed) | Service management wrapper |
| `freeipa-sudo-service-mgmt.yaml` | `/ganuda/ansible/playbooks/freeipa-sudo-service-mgmt.yaml` | Ansible playbook for full deployment |
| `inventory` | `/ganuda/ansible/inventory` | Updated with ProxyCommand fixes and freeipa group |
| `ganuda-service-mgmt` | `/etc/sudoers.d/ganuda-service-mgmt` (bluefin only) | Local NOPASSWD rule for sudo-rs compatibility |
| `sssd.conf` | `/etc/sssd/sssd.conf` (all 3 nodes) | Removed `_srv_` from `ipa_server` |

## Council Vote

**Vote ID**: #b82aea3e6ceb8906
**Decision**: PROCEED WITH CAUTION (0.888 confidence)
**Context**: Level 5+ Basin-Breaker architecture that includes this service autonomy capability. The council recognized this as a foundational step toward full Jr executor self-sufficiency for service deployment, reducing operator bottleneck on sudo operations.

## Kanban

- **#1822** Wrapper Scripts (5 SP) — COMPLETED
- **#1823** FreeIPA Ansible Playbook (5 SP) — COMPLETED

## Operational Notes

- To deploy a new service: stage the `.service` file in `/ganuda/scripts/systemd/`, then run `ganuda-deploy-service <service-name>.service` (no sudo prefix needed; the wrapper handles sudo internally via the FreeIPA/local rule)
- To manage an existing service: `ganuda-service-ctl restart <service-name>` (again, no sudo prefix)
- Logs are appended to `/ganuda/logs/service-deploy.log` and `/ganuda/logs/service-ctl.log` respectively
- Telegram notifications go to the federation ops channel on each deploy/restart/stop action
