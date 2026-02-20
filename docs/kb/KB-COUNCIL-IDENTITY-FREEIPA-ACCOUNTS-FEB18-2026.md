# KB: Council Identity Accounts — FreeIPA Deployment
**Date**: February 18, 2026
**Council Vote**: #49dd21edbcb19120 (Option C Hybrid, unanimous)
**Kanban**: #1834
**Playbook**: /ganuda/ansible/playbooks/council-identity-accounts.yaml

## Purpose
As part of Level 5 Council Autonomy, the Council needs its own identity in the federation — not operating as `dereadi` for everything. Role-based accounts provide audit trail, principle of least privilege, and Cherokee accountability (every action has a name).

## Accounts Created

| Account | Principal | UID | Role | Sudo Access |
|---------|-----------|-----|------|-------------|
| council | council@CHEROKEE.LOCAL | 1658400012 | Shared routine ops (file writes, thermal memory, Telegram) | None |
| council-security | council-security@CHEROKEE.LOCAL | 1658400013 | Crawdad escalation (firewall, security) | NOPASSWD: /usr/sbin/nft |
| council-deploy | council-deploy@CHEROKEE.LOCAL | 1658400014 | Service deployment | NOPASSWD: ganuda-deploy-service, ganuda-service-ctl |
| council-monitor | council-monitor@CHEROKEE.LOCAL | 1658400015 | Eagle Eye read-only (logs, metrics) | None |
| jr-executor | jr-executor@CHEROKEE.LOCAL | 1658400016 | Jr task execution (file writes only) | None |

## Groups

| Group | Members | Purpose |
|-------|---------|---------|
| council-ops | All 5 accounts | Shared group for /ganuda/council/ directory access |
| council-privileged | council-security, council-deploy | Accounts that have sudo rules |

## Sudo Rules (FreeIPA)

| Rule | User | Commands | Hosts |
|------|------|----------|-------|
| council-deploy-services | council-deploy | ganuda-deploy-service, ganuda-service-ctl | redfin, bluefin, greenfin |
| council-security-firewall | council-security | /usr/sbin/nft | redfin, bluefin, greenfin |

## Directory Structure (pending creation on nodes)
```
/ganuda/council/          # Council workspace (770, group council-ops)
/ganuda/council/logs/     # Audit trail (770, group council-ops)
/ganuda/jr-workspace/     # Jr executor writes (775)
```

## Bluefin sudo-rs Workaround
Bluefin uses sudo-rs 0.2.8 which does NOT support SSSD/nsswitch sudoers providers. FreeIPA sudo rules will not propagate to bluefin. Workaround: local /etc/sudoers.d/ drop-ins.

Create on bluefin:
```
# /etc/sudoers.d/council-deploy
council-deploy ALL=(root) NOPASSWD: /usr/local/bin/ganuda-deploy-service, /usr/local/bin/ganuda-service-ctl

# /etc/sudoers.d/council-security
council-security ALL=(root) NOPASSWD: /usr/sbin/nft
```

## Audit Architecture (Two Layers)
1. **OS-level**: journald and auditd capture which role account performed the action
2. **Application-level**: thermal memory logs which specialist initiated the escalation

Example audit trail:
- journald: `council-deploy ran ganuda-deploy-service bigmac-bridge at 19:17:23`
- thermal memory: `Gecko initiated deployment of bigmac-bridge.service after Council vote #xyz`

## Bug Encountered
Ansible `freeipa.ansible_freeipa.ipauser` parameter is `homedir` NOT `homedirectory`. The module error message lists supported parameters — always check `homedir` not `homedirectory`.

## Password Rotation
All accounts created with default password `ChangeMe!2026` (update_password: on_create). These MUST be rotated before Level 5 goes live. Use FreeIPA vault for secure storage.

## What's Next
1. Create directories on 3 Linux nodes
2. Bluefin sudoers.d drop-ins for council-deploy and council-security
3. Wire Council orchestrator daemon to use council/council-deploy/council-security accounts
4. Configure auditd rules for council-* account actions
5. Rotate passwords from defaults

## Related
- Council Vote: #49dd21edbcb19120
- Level 5 Gap Analysis: thermal memory (Council Vote #183d3112e069d2ae)
- FreeIPA Sudo Wrapper Scripts: KB-FREEIPA-SUDO-SERVICE-MGMT-FEB18-2026.md
- Previous sudo-rs discovery: bluefin uses sudo-rs 0.2.8, incompatible with SSSD sudoers

---

FOR SEVEN GENERATIONS
