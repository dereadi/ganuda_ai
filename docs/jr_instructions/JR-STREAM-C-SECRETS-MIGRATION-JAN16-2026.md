# JR Instruction: Stream C - Secrets Migration to silverfin

## Metadata
```yaml
task_id: stream_c_secrets_migration
priority: 1
parallel_stream: C
assigned_to: Infrastructure Jr.
target_node: silverfin
```

## Overview

Migrate API keys and secrets to FreeIPA vault on silverfin for centralized secrets management.

## Tasks

### Task 1: Create Vault Container

```bash
ssh silverfin << 'REMOTE'
echo "jawaseatlasers2" | kinit admin
ipa vault-add cherokee-ai-secrets --type=standard --desc="Cherokee AI Federation API Keys and Secrets"
REMOTE
```

### Task 2: Store Initial Secrets

```bash
ssh silverfin << 'REMOTE'
# Store LLM Gateway admin key
echo "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" | ipa vault-archive cherokee-ai-secrets --name=llm_gateway_admin --in=-

# Store database credentials reference
echo "jawaseatlasers2" | ipa vault-archive cherokee-ai-secrets --name=bluefin_claude_password --in=-

echo "Secrets stored in vault"
REMOTE
```

### Task 3: Create Service Account for VetAssist

```bash
ssh silverfin << 'REMOTE'
# Check if user exists, create if not
ipa user-show vetassist-svc 2>/dev/null || ipa user-add vetassist-svc \
  --first=VetAssist \
  --last=Service \
  --homedir=/nonexistent \
  --shell=/sbin/nologin \
  --random

echo "Service account ready"
REMOTE
```

### Task 4: Create Secrets Retrieval Script

Create `/ganuda/scripts/get-vault-secret.sh`:

```bash
#!/bin/bash
# Retrieve a secret from silverfin FreeIPA vault
# Usage: get-vault-secret.sh <secret-name>

SECRET_NAME=$1

if [ -z "$SECRET_NAME" ]; then
    echo "Usage: $0 <secret-name>"
    exit 1
fi

# Ensure we have a valid ticket
klist -s || kinit -k -t /etc/krb5.keytab

# Retrieve secret
ssh silverfin "ipa vault-retrieve cherokee-ai-secrets --name=$SECRET_NAME --out=-" 2>/dev/null
```

## Verification

```bash
ssh silverfin "ipa vault-show cherokee-ai-secrets"
```

```bash
ssh silverfin "ipa vault-find --all"
```

---

*Cherokee AI Federation - For the Seven Generations*
