# KB: FreeIPA NOPASSWD Sudo Rules — Federation-Wide Package Management

## Date: April 2, 2026
## Problem: Jrs and TPM can't install packages (apt-get) on remote nodes without interactive password

---

## Current State

FreeIPA provides scoped NOPASSWD sudo across all Linux nodes:

### Currently NOPASSWD (all Linux nodes)
```
/usr/bin/cat, /usr/bin/tee, /usr/bin/wg, /usr/bin/mkdir, /usr/bin/chmod,
/usr/bin/cp, /usr/bin/systemctl, /usr/local/bin/ganuda-service-ctl,
/usr/local/bin/ganuda-deploy-service
```

### Bluefin-Specific Additions
```
/bin/cat /etc/postgresql/*/main/pg_hba.conf
/bin/cp /etc/postgresql/*/main/pg_hba.conf*
/usr/bin/tee /etc/postgresql/*/main/pg_hba.conf
/bin/systemctl reload postgresql
/bin/systemctl status postgresql
```

## What's Missing

`apt-get` and `apt` are NOT in the NOPASSWD list. This means:
- Jrs can write code and deploy services but can't install dependencies
- The TPM can SSH and run systemctl but can't `apt-get install pgbouncer`
- Cross-node deployment fails at the "install deps" step

## Proposed Addition

Add to FreeIPA sudo rules for the `ganuda-dev` group (or `dereadi` user):

```
(root) NOPASSWD: /usr/bin/apt-get install *, /usr/bin/apt-get update
```

This allows `apt-get install` and `apt-get update` without password, but NOT `apt-get remove` or `apt-get purge` — install only, no uninstall without password.

## How to Add in FreeIPA

On the FreeIPA server (likely bluefin or a dedicated IPA host):

```bash
# Add sudo command
ipa sudocmd-add '/usr/bin/apt-get install *'
ipa sudocmd-add '/usr/bin/apt-get update'

# Add to existing sudo rule (or create new one)
ipa sudorule-add-allow-command ganuda-admin-rule --sudocmds '/usr/bin/apt-get install *'
ipa sudorule-add-allow-command ganuda-admin-rule --sudocmds '/usr/bin/apt-get update'
```

Or if editing directly via `/etc/sudoers.d/`:
```
dereadi ALL=(root) NOPASSWD: /usr/bin/apt-get install *, /usr/bin/apt-get update
```

## Also Consider Adding

```
/usr/bin/pip3 install *     # Python package installation
/usr/bin/python3 -m pip *   # Alternative pip path
```

This would let Jrs install Python deps without the `--break-system-packages` workaround.

## Security Notes

- Install-only (no remove/purge) limits blast radius
- `apt-get update` refreshes package lists but doesn't modify system
- Coyote concern: supply chain attacks on packages — apt packages are GPG-signed but pip packages are not. Consider using `--only-binary :all:` for pip to limit attack surface.
- Chiral Validation: package installations should be logged and auditable. Fire Guard should monitor for unexpected new packages.

## Verification After Adding

```bash
# From redfin, test on each node
for node in 10.100.0.2 10.100.0.5 10.100.0.6; do
    ssh dereadi@$node 'sudo -n apt-get update -qq && echo "$HOSTNAME: apt-get OK" || echo "$HOSTNAME: FAILED"'
done
```

---

*For Seven Generations.*
