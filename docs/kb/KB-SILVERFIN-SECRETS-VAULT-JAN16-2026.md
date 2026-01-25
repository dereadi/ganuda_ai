# KB: Silverfin FreeIPA Secrets Vault

**Date:** January 16, 2026
**Category:** Security / Identity
**Node:** silverfin
**Status:** Active

---

## Overview

FreeIPA vault on silverfin provides centralized secrets management for the Cherokee AI Federation.

## Vault Details

| Item | Value |
|------|-------|
| Vault Name | cherokee-ai-secrets |
| Type | standard |
| Realm | CHEROKEE.LOCAL |
| Access | Kerberos authenticated |

## Service Account

| Item | Value |
|------|-------|
| Account | vetassist-svc@CHEROKEE.LOCAL |
| UID | 1658400009 |
| Shell | /sbin/nologin |
| Initial Password | 3Pq,%_zTLO6dGBqYU*yN_] |

**Note:** Rotate to keytab-based auth for production.

## Stored Secrets

| Secret Name | Purpose |
|-------------|---------|
| llm_gateway_admin | LLM Gateway API key |
| bluefin_claude_password | PostgreSQL credentials |

## Usage

### Store a Secret
```bash
kinit admin  # Authenticate
echo "secret_value" | ipa vault-archive cherokee-ai-secrets --name=secret_name --in=-
```

### Retrieve a Secret
```bash
kinit admin
ipa vault-retrieve cherokee-ai-secrets --name=secret_name --out=-
```

### List Vault Contents
```bash
ipa vault-show cherokee-ai-secrets
```

## Retrieval Script

Location: `/ganuda/scripts/get-vault-secret.sh`

```bash
#!/bin/bash
SECRET_NAME=$1
klist -s || kinit -k -t /etc/krb5.keytab
ssh silverfin "ipa vault-retrieve cherokee-ai-secrets --name=$SECRET_NAME --out=-"
```

## Deployment Script

Location: `/ganuda/scripts/deploy-secrets-silverfin.sh`

## Security Notes

1. Vault access requires valid Kerberos ticket
2. silverfin is on VLAN 10 (Identity tier)
3. Access via Tailscale or through greenfin router
4. All secrets LUKS encrypted at rest

## Related

- JR Instruction: `/ganuda/docs/jr_instructions/JR-STREAM-C-SECRETS-MIGRATION-JAN16-2026.md`
- FreeIPA Setup: Check thermal memory for silverfin configuration

---

*Cherokee AI Federation - For the Seven Generations*
