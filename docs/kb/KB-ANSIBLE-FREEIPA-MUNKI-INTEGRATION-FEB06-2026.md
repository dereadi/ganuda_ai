# KB: Ansible + FreeIPA + Munki Integration

**Date:** 2026-02-06
**Owner:** Infrastructure Jr.
**Status:** Architecture Defined

## Overview

Three tools, one goal: consistent configuration management across the Cherokee AI Federation.

| Tool | Platform | Primary Role |
|------|----------|--------------|
| **Ansible** | Both | Orchestration, config sync, FreeIPA management |
| **FreeIPA** | Linux | Identity, Kerberos SSO, sudo rules, HBAC |
| **Munki** | macOS | Software deployment, sudo config delivery |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Ansible                                  │
│              (Orchestrator - runs from any node)                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
┌─────────────────────┐   ┌─────────────────────┐
│      FreeIPA        │   │       Munki         │
│  (bluefin:443)      │   │  (sasass2:8080)     │
│                     │   │                     │
│  • Identity (LDAP)  │   │  • Package repo     │
│  • Kerberos KDC     │   │  • Sudo packages    │
│  • Sudo rules       │   │  • Software deploy  │
│  • HBAC policies    │   │                     │
└──────────┬──────────┘   └──────────┬──────────┘
           │                         │
    ┌──────┴──────┐           ┌──────┴──────┐
    ▼             ▼           ▼             ▼
┌───────┐   ┌─────────┐   ┌───────┐   ┌─────────┐
│redfin │   │greenfin │   │sasass │   │sasass2  │
│(SSSD) │   │ (SSSD)  │   │(Munki)│   │ (Munki) │
└───────┘   └─────────┘   └───────┘   └─────────┘
   Linux       Linux        macOS       macOS
```

## How They Work Together

### 1. Identity & Authentication

| Aspect | Linux (FreeIPA) | macOS |
|--------|-----------------|-------|
| User accounts | LDAP via SSSD | Local + Kerberos SSO |
| Authentication | Kerberos | Kerberos (same realm) |
| Groups | FreeIPA groups | Local groups + Kerberos |

**Kerberos SSO works on both platforms** - same `kinit dereadi@CHEROKEE.LOCAL` command.

### 2. Sudo Rules

**Single source of truth:** Ansible playbook `sync-sudo-rules.yml`

| Platform | Delivery | Storage |
|----------|----------|---------|
| Linux | FreeIPA `ipasudorule` | LDAP (real-time) |
| macOS | Munki package | `/etc/sudoers.d/` (check-in) |

**Same rules, different delivery:**

```
# Defined in Ansible (source of truth)
sudo_rules:
  - name: dereadi-full
    users: [dereadi]
    commands: ALL
    nopasswd: true

# Applied to FreeIPA via ansible-freeipa module
# Applied to macOS via Munki package
```

### 3. Software Deployment

| Platform | Tool | Managed By |
|----------|------|------------|
| Linux | apt/dnf | Ansible roles |
| macOS | Homebrew + Munki | Ansible (brew) + Munki (apps) |

### 4. Configuration Files

Ansible syncs common files to both platforms:

```yaml
# playbooks/sync-federation.yml
- name: Sync secrets.env
  copy:
    src: /ganuda/config/secrets.env
    dest: "{{ ganuda_root }}/config/secrets.env"
```

Where `ganuda_root` is `/ganuda` on Linux, `/Users/Shared/ganuda` on macOS.

## Playbook Inventory

| Playbook | Purpose |
|----------|---------|
| `sync-federation.yml` | Sync common files to all nodes |
| `deploy-freeipa.yml` | Deploy FreeIPA server + enroll clients |
| `sync-sudo-rules.yml` | Keep sudo rules consistent across platforms |

## Directory Structure

```
/ganuda/ansible/
├── ansible.cfg              # Ansible configuration
├── requirements.yml         # Galaxy collections needed
├── inventory/
│   └── federation.yml       # All nodes, groups, vars
├── playbooks/
│   ├── sync-federation.yml  # Common file sync
│   ├── deploy-freeipa.yml   # FreeIPA deployment
│   └── sync-sudo-rules.yml  # Sudo rule sync
├── roles/                   # Custom roles (future)
└── group_vars/              # Group-specific variables
```

## Usage

### Initial Setup

```bash
cd /ganuda/ansible

# Install required collections
ansible-galaxy collection install -r requirements.yml

# Test connectivity
ansible all -m ping
```

### Sync Files to All Nodes

```bash
ansible-playbook playbooks/sync-federation.yml
```

### Deploy FreeIPA (when ready)

```bash
# Set admin password
export IPAADMIN_PASSWORD='SecurePassword123'

# Deploy server
ansible-playbook playbooks/deploy-freeipa.yml --tags server

# Enroll clients
ansible-playbook playbooks/deploy-freeipa.yml --tags clients
```

### Sync Sudo Rules

```bash
# Updates both FreeIPA and Munki
ansible-playbook playbooks/sync-sudo-rules.yml
```

## Integration Points

### Ansible → FreeIPA

Uses `freeipa.ansible_freeipa` collection:
- `ipauser` - manage users
- `ipagroup` - manage groups
- `ipasudorule` - manage sudo rules
- `ipahbacrule` - manage host-based access
- `ipahost` - manage hosts
- `ipaclient` - enroll clients

### Ansible → Munki

Uses standard modules + shell:
- `community.general.osx_defaults` - Munki client config
- `copy` - deploy package sources
- `shell` - run `munkipkg`, `makecatalogs`

### FreeIPA → macOS

Kerberos only (no SSSD):
- Macs can get Kerberos tickets from FreeIPA
- Macs cannot pull sudo rules from FreeIPA
- Munki fills the gap for sudo delivery

## Security Notes

1. **Secrets:** Never in playbooks. Use `secrets_loader.py` or Ansible Vault.
2. **Passwords:** FreeIPA admin password via environment variable or vault.
3. **Transport:** SSH for Ansible, HTTPS for FreeIPA, HTTP for Munki (internal only).

## Future Enhancements

1. **Ansible Vault** for secrets management
2. **AWX/Tower** for web UI and scheduling
3. **FreeIPA replicas** for HA
4. **Munki middleware** for reporting/compliance

---
*For Seven Generations - Cherokee AI Federation*
