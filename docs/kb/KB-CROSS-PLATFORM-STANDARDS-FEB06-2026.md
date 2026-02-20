# KB: Cherokee AI Federation Cross-Platform Standards

**Date:** 2026-02-06
**Owner:** Infrastructure Jr.
**Status:** Active

## Principle

Minimize cognitive load across Linux and macOS. Same patterns, same paths (where possible), same tools (when available), parallel equivalents (when not).

## Filesystem Standards

| Purpose | Linux | macOS |
|---------|-------|-------|
| Federation root | `/ganuda/` | `/Users/Shared/ganuda/` |
| Secrets | `/ganuda/config/secrets.env` | `/Users/Shared/ganuda/config/secrets.env` |
| Scripts | `/ganuda/scripts/` | `/Users/Shared/ganuda/scripts/` |
| Docs | `/ganuda/docs/` | `/Users/Shared/ganuda/docs/` |
| Logs | `/ganuda/logs/` | `/Users/Shared/ganuda/logs/` |
| Lib | `/ganuda/lib/` | `/Users/Shared/ganuda/lib/` |
| Temp (survives reboot) | `/ganuda/tmp/` | `/Users/Shared/ganuda/tmp/` |
| Temp (volatile) | `/tmp/` (avoid) | `/tmp/` (avoid) |

**Rule:** Never use `/tmp` for anything that needs to survive a reboot.

## Common Directory Structure

Both platforms mirror this structure:

```
{root}/
├── config/
│   ├── secrets.env          # Database credentials
│   ├── federation.yaml      # Node configuration
│   └── *.yaml               # Service configs
├── docs/
│   ├── jr_instructions/     # Jr task specs
│   ├── kb/                  # Knowledge base
│   └── ultrathink/          # Deep analysis docs
├── lib/
│   ├── secrets_loader.py    # Credential management
│   └── *.py                 # Shared libraries
├── scripts/
│   ├── *.sh                 # Shell scripts
│   └── *.py                 # Python scripts
├── logs/
│   └── *.log                # Application logs
└── tmp/
    └── (working files)      # Survives reboot
```

## Cross-Platform Tools (Use Same Tool)

| Tool | Linux | macOS | Notes |
|------|-------|-------|-------|
| Python 3 | `python3` | `python3` | Same scripts run on both |
| Git | `git` | `git` | Identical |
| SSH | `ssh` | `ssh` | Identical |
| psql | `psql` | `psql` | Same PostgreSQL client |
| nginx | `apt install nginx` | `brew install nginx` | Same config syntax |
| Ansible | `pip install ansible` | `pip install ansible` | Manages both platforms |
| curl | `curl` | `curl` | Identical |
| jq | `apt install jq` | `brew install jq` | Identical |

## Parallel Tools (Different But Equivalent)

| Function | Linux | macOS | Alignment Strategy |
|----------|-------|-------|-------------------|
| Package mgmt | apt/dnf | Homebrew + Munki | Ansible installs on Linux, Munki on Mac |
| Service mgmt | systemd | launchd | Same service names where possible |
| Init system | systemd units | launchd plists | Mirror structure/naming |
| Identity | FreeIPA (SSSD) | Kerberos + Munki sudo | Same sudo rules via different delivery |
| Config mgmt | Ansible | Ansible + Munki | Ansible for config, Munki for packages |
| Sudo rules | FreeIPA / /etc/sudoers.d | Munki → /etc/sudoers.d | Same sudoers.d file format |

## Sudo Rules (Identical Content)

Both platforms use `/etc/sudoers.d/cherokee-federation` with identical content:

```
# Cherokee AI Federation Sudo Rules
dereadi ALL=(ALL) NOPASSWD: ALL
%cherokee-admins ALL=(ALL) ALL
%cherokee-operators ALL=(ALL) NOPASSWD: /usr/local/munki/*, ...
```

**Delivery:**
- Linux: Ansible or FreeIPA
- macOS: Munki package

## Service Naming Convention

When creating services, use consistent naming:

| Service | Linux (systemd) | macOS (launchd) |
|---------|-----------------|-----------------|
| Jr Executor | `jr-executor.service` | `com.cherokee.jr-executor.plist` |
| Jr Queue Worker | `jr-queue-worker.service` | `com.cherokee.jr-queue-worker.plist` |
| Telegram Bot | `telegram-chief.service` | `com.cherokee.telegram-chief.plist` |

## Python Environment

| Aspect | Linux | macOS |
|--------|-------|-------|
| Venv location | `/home/dereadi/cherokee_venv/` | `/Users/dereadi/cherokee_venv/` |
| Python path | `/home/dereadi/cherokee_venv/bin/python` | `/Users/dereadi/cherokee_venv/bin/python` |
| Site packages | Standard venv | Standard venv |

**Best Practice:** Use `#!/usr/bin/env python3` in scripts for portability.

## Secrets Management

Same pattern on both platforms:

```python
import sys
import os

# Platform-agnostic root detection
if sys.platform == 'darwin':
    GANUDA_ROOT = '/Users/Shared/ganuda'
else:
    GANUDA_ROOT = '/ganuda'

sys.path.insert(0, GANUDA_ROOT)
from lib.secrets_loader import get_db_config
```

Or simpler - `secrets_loader.py` handles this internally.

## Configuration Files

Use YAML for all configuration. Same format on both platforms:

```yaml
# /ganuda/config/federation.yaml (Linux)
# /Users/Shared/ganuda/config/federation.yaml (macOS)

node:
  name: redfin
  role: gpu-inference
  ip: 192.168.132.223

database:
  host: 192.168.132.222
  # credentials from secrets.env
```

## Logging

Same log format, same rotation policy:

| Aspect | Standard |
|--------|----------|
| Format | `%(asctime)s - %(levelname)s - %(name)s - %(message)s` |
| Location | `{root}/logs/{service}.log` |
| Rotation | Daily, 7 days retention |

## Ansible Inventory Structure

```yaml
all:
  children:
    linux:
      hosts:
        redfin:
          ansible_host: 192.168.132.223
        bluefin:
          ansible_host: 192.168.132.222
        greenfin:
          ansible_host: 192.168.132.224
    macos:
      hosts:
        sasass:
          ansible_host: 192.168.132.241
        sasass2:
          ansible_host: 192.168.132.242
  vars:
    ansible_user: dereadi
```

## Enforcement

1. **Infrastructure Jr.** reviews all new services/scripts for cross-platform alignment
2. **Ansible playbooks** should have Linux and macOS tasks where applicable
3. **Munki packages** should mirror Ansible roles for macOS software
4. **Code review** checks for hardcoded paths - use `GANUDA_ROOT` variable

## Migration Checklist

When adding a new service:

- [ ] Linux systemd unit created
- [ ] macOS launchd plist created (if applicable)
- [ ] Same service name pattern
- [ ] Logs go to `{root}/logs/`
- [ ] Config in `{root}/config/`
- [ ] Secrets via `secrets_loader.py`
- [ ] Ansible role for Linux deployment
- [ ] Munki package for macOS deployment (if applicable)

---
*For Seven Generations - Cherokee AI Federation*
