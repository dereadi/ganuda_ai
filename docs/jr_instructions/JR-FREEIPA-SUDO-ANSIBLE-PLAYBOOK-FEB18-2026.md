# Jr Instruction: FreeIPA Sudo Rules + Wrapper Script Deployment via Ansible

**Task**: Build an Ansible playbook that configures FreeIPA sudo rules and distributes federation service wrapper scripts to all Linux nodes
**Priority**: 8/10
**Story Points**: 5
**Kanban**: #1823
**Depends on**: #1822 (wrapper scripts must exist first)
**Assigned Jr**: Software Engineer Jr.

## Context

The federation wrapper scripts (`ganuda-deploy-service` and `ganuda-service-ctl`) need to be:
1. Distributed to `/usr/local/bin/` on all enrolled Linux nodes
2. Granted sudo access via FreeIPA sudo rules so the `dereadi` user can run them as root without a password

This playbook completes the Level 5+ autonomous service management pipeline: Jr executor or TPM daemon stages a .service file → calls `sudo ganuda-deploy-service <name>` → service deploys, starts, and notifies the Chief.

Study these existing patterns before building:
- `/ganuda/ansible/` — existing playbook structure and inventory
- `/ganuda/home/dereadi/.ansible/collections/ansible_collections/freeipa/ansible_freeipa/README-sudorule.md` — FreeIPA Ansible module docs
- `/ganuda/home/dereadi/.ansible/collections/ansible_collections/freeipa/ansible_freeipa/plugins/modules/ipasudorule.py` — the actual module
- `/ganuda/docs/kb/KB-ANSIBLE-FOUNDATION-DEPLOYMENT-FEB14-2026.md` — existing Ansible architecture

## Requirements

Create `/ganuda/ansible/playbooks/freeipa-sudo-service-mgmt.yaml`

### Play 1: Distribute wrapper scripts to all Linux nodes

Target hosts: `linux_nodes` group (redfin, bluefin, greenfin — check existing inventory)

Tasks:
1. Copy `/ganuda/scripts/ganuda-deploy-service` to `/usr/local/bin/ganuda-deploy-service` with mode 0755, owner root
2. Copy `/ganuda/scripts/ganuda-service-ctl` to `/usr/local/bin/ganuda-service-ctl` with mode 0755, owner root
3. Ensure `/ganuda/logs/` directory exists with mode 0755, owner dereadi

Use `become: yes` for the copy tasks (requires sudo on target nodes).

### Play 2: Configure FreeIPA sudo rules on silverfin

Target host: `silverfin` (or `freeipa_server` group — check inventory)

**Important**: This play needs `ipaadmin_password` — store it in Ansible Vault or pass as extra var. Do NOT hardcode it.

Tasks:

1. **Register sudo commands** using `freeipa.ansible_freeipa.ipasudocmd`:
   - `/usr/local/bin/ganuda-deploy-service`
   - `/usr/local/bin/ganuda-service-ctl`

2. **Create sudo command group** using `freeipa.ansible_freeipa.ipasudocmdgroup`:
   - Name: `ganuda-service-mgmt`
   - Members: both commands from step 1

3. **Create sudo rule** using `freeipa.ansible_freeipa.ipasudorule`:
   - Name: `ganuda-service-management`
   - Description: "Allow dereadi to deploy and manage federation services via validated wrapper scripts"
   - User: `dereadi`
   - Hosts: all enrolled Linux nodes (redfin, bluefin, greenfin)
   - Allow sudocmd group: `ganuda-service-mgmt`
   - RunAs user: `root`
   - Sudo option: `!authenticate` (NOPASSWD)
   - State: present

### Play 3: Verify

Target hosts: `linux_nodes`

Tasks:
1. Run `sudo -l -U dereadi` and register the output
2. Assert that the output contains `ganuda-deploy-service` and `ganuda-service-ctl`
3. Debug print the verified rules

## Inventory Reference

Check `/ganuda/ansible/inventory/` or `/ganuda/ansible/hosts` for existing group definitions. If `silverfin` isn't in the inventory yet, add it with the connection info:
- Jump host: greenfin
- SSH config likely uses ProxyJump

## Variables

The playbook should accept these variables (via `--extra-vars` or vault):
- `ipaadmin_password` — FreeIPA admin password (REQUIRED, do not default)

## Step 1: Create the playbook

Create `/ganuda/ansible/playbooks/freeipa-sudo-service-mgmt.yaml`

## Step 2: Update inventory if needed

If silverfin is not in the Ansible inventory, add it to the appropriate inventory file.

## Acceptance Criteria

- [ ] Playbook passes `ansible-playbook --syntax-check`
- [ ] Play 1 uses `become: yes` for file copy tasks
- [ ] Play 2 uses the `freeipa.ansible_freeipa` collection modules (not raw CLI commands)
- [ ] `ipaadmin_password` is NOT hardcoded anywhere
- [ ] Sudo option includes `!authenticate` for NOPASSWD
- [ ] Play 3 verifies the rules are visible via `sudo -l`
- [ ] All tasks are idempotent (safe to run multiple times)

## Out of Scope

- Writing the wrapper scripts themselves (Kanban #1822)
- Enrolling bluefin/greenfin in FreeIPA (separate task)
- macOS nodes (not FreeIPA clients)
