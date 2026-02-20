# KB: FreeIPA KRA Vault Deployment — Feb 10 2026

## Summary
Installed Dogtag KRA (Key Recovery Authority) on silverfin (FreeIPA server) to enable `ipa vault-*` commands for centralized secret storage. First vault: `cherokee-camera-secrets` containing 3 camera fleet passwords.

## What Was Done
1. **Pre-check**: `sudo ipactl status` confirmed all IPA services healthy, CA (pki-tomcatd) running
2. **Install**: `sudo ipa-kra-install` — 9-step process, ~5 minutes. Required Directory Manager password.
3. **Post-check**: `sudo ipactl status` confirmed KRA subsystem running under pki-tomcatd
4. **Vault created**: `ipa vault-add cherokee-camera-secrets --type=standard`
5. **Secrets archived**: All 3 passwords as single blob via `printf ... | ipa vault-archive ... --in /dev/stdin`
6. **Retrieval verified**: `ipa vault-retrieve cherokee-camera-secrets --out /dev/stdout`

## Key Learnings

### CRITICAL: vault-archive REPLACES, does NOT append
`ipa vault-archive` overwrites the entire vault data each time. If you archive 3 secrets individually, only the last one survives. **Always archive all secrets as a single combined blob.**

### Base64 Padding Bug
`--data=` flag treats input as base64. Strings with lengths that aren't multiples of 4 fail with:
```
ipa: ERROR: Base64 decoding failed: Invalid base64-encoded string
```
**Workaround**: Use `echo -n 'data' | ipa vault-archive <name> --in /dev/stdin` instead of `--data=`.

### SSH Access to Silverfin
Silverfin requires jump through greenfin: `ssh -J greenfin silverfin`
First connection required: `-o StrictHostKeyChecking=accept-new`

## Vault Inventory
| Vault Name | Type | Contents | Created |
|---|---|---|---|
| cherokee-camera-secrets | standard | 3 camera passwords (office-pii, traffic, garage) | Feb 10 2026 |

## Next Steps
- Archive additional secrets (DB passwords, API keys) into dedicated vaults
- Set up vault access policies for service accounts
- Integrate `ipa vault-retrieve` into secrets_loader.py for runtime secret fetch
- 32 edge-case password files from sweep still need migration
- Consider symmetric or asymmetric vault types for shared-access secrets

## CMDB Update
- **silverfin**: FreeIPA KRA service now active (Dogtag subsystem under pki-tomcatd)
- **Vault backend**: LDAP-stored, encrypted at rest by KRA transport/storage keys
