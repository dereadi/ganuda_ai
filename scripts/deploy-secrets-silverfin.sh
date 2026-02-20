#!/bin/bash
# Stream C: Secrets Migration to silverfin FreeIPA Vault
# Run as: sudo bash /ganuda/scripts/deploy-secrets-silverfin.sh

set -e

source /ganuda/config/secrets.env

echo "=== Authenticating to FreeIPA ==="
echo "${FREEIPA_ADMIN_PASS:?Set FREEIPA_ADMIN_PASS in secrets.env}" | kinit admin

echo "=== Creating secrets vault ==="
ipa vault-add cherokee-ai-secrets --type=standard --desc="Cherokee AI Federation API Keys and Secrets" 2>/dev/null && echo "Vault created" || echo "Vault already exists"

echo "=== Storing LLM Gateway admin key ==="
echo "${LLM_GATEWAY_ADMIN_KEY:?Set LLM_GATEWAY_ADMIN_KEY in secrets.env}" | ipa vault-archive cherokee-ai-secrets --name=llm_gateway_admin --in=- 2>/dev/null && echo "Stored: llm_gateway_admin" || echo "Key may already exist"

echo "=== Storing database credentials ==="
echo "${CHEROKEE_DB_PASS:?Set CHEROKEE_DB_PASS in secrets.env}" | ipa vault-archive cherokee-ai-secrets --name=bluefin_claude_password --in=- 2>/dev/null && echo "Stored: bluefin_claude_password" || echo "Key may already exist"

echo "=== Creating VetAssist service account ==="
ipa user-show vetassist-svc 2>/dev/null && echo "Service account already exists" || {
    ipa user-add vetassist-svc \
        --first=VetAssist \
        --last=Service \
        --homedir=/nonexistent \
        --shell=/sbin/nologin \
        --random
    echo "Created: vetassist-svc"
}

echo "=== Verification ==="
echo ""
echo "Vault info:"
ipa vault-show cherokee-ai-secrets 2>/dev/null || echo "Could not show vault"

echo ""
echo "Service account:"
ipa user-show vetassist-svc 2>/dev/null | grep -E "User login|First name|Last name" || echo "Could not show user"

echo "=== Stream C Complete ==="
