# Jr Instruction: PQC Hybrid TLS on Caddy for VetAssist

**Task ID:** PQC-TLS-CADDY
**Kanban:** #1873
**Priority:** 3
**Assigned:** Software Engineer Jr.

---

## Overview

Enable post-quantum hybrid TLS on Caddy for VetAssist. Configures X25519Kyber768 key exchange with TLS 1.3 and HSTS.

---

## Step 1: Create PQC TLS Caddyfile snippet

Create `/ganuda/config/caddy/pqc-tls.caddyfile`

```text
# Post-Quantum Hybrid TLS Configuration for Caddy
# Requires Caddy v2.8+ with PQC support
# X25519Kyber768 hybrid key exchange (NIST ML-KEM + X25519)
#
# Import this in your main Caddyfile:
#   import /ganuda/config/caddy/pqc-tls.caddyfile

(pqc_tls) {
    tls {
        protocols tls1.3
        curves x25519kyber768draft00 x25519 p256
    }
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
}
```

---

## Step 2: Create PQC verification script

Create `/ganuda/scripts/verify_pqc_tls.sh`

```text
#!/bin/sh
# Verify PQC hybrid TLS is active on a given domain
# Usage: ./verify_pqc_tls.sh vetassist.ganuda.us

DOMAIN="${1:-vetassist.ganuda.us}"
echo "Checking PQC TLS for $DOMAIN..."

# Check TLS version and cipher
echo "--- TLS Handshake ---"
echo | openssl s_client -connect "$DOMAIN:443" -tls1_3 2>/dev/null | grep -E "Protocol|Cipher|Server Temp Key"

# Check for Kyber/ML-KEM in key exchange
echo "--- Key Exchange ---"
echo | openssl s_client -connect "$DOMAIN:443" -tls1_3 -groups X25519Kyber768Draft00 2>/dev/null | grep -E "Temp Key|Server public key"

# Check HSTS header
echo "--- HSTS Header ---"
curl -sI "https://$DOMAIN" 2>/dev/null | grep -i strict-transport

echo "Done."
```

---

## Verification

```text
caddy version
# Must be 2.8+ for PQC support
chmod +x /ganuda/scripts/verify_pqc_tls.sh
```

## Notes

- Caddy on owlfin/eaglefin must be v2.8+ for PQC curves
- X25519Kyber768Draft00 is the draft IETF identifier
- Falls back to X25519 if client doesn't support PQC
- HSTS preload requires submission to hstspreload.org after deployment
