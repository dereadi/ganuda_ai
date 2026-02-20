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