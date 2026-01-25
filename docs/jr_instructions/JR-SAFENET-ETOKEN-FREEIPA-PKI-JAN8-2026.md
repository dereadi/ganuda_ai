# Jr Instruction: SafeNet eToken JC + FreeIPA PKI Integration

**Date**: January 8, 2026
**Assigned To**: Infrastructure Jr, Security Jr
**Node**: silverfin (192.168.132.57)
**Priority**: High
**Status**: Ready for execution
**Council Vote**: 82.3% confidence, Option 1 (Full PKI) approved

---

## Overview

Integrate SafeNet eToken JC hardware security token with FreeIPA for 2FA access to the Sanctum (goldfin). This implements the Council-approved Option 1: Full PKI integration with smartcard authentication.

**Security Requirement**: Access to goldfin (PII Sanctum) requires:
- Human users: FreeIPA account + hardware token
- Service accounts: mTLS certificates + IP whitelist + audit logging

**Current State**:
- Token detected: `Bus 001 Device 004: ID 0529:0620 Aladdin Knowledge Systems Token JC`
- FreeIPA: v4.12.2 running on Rocky Linux 10
- Realm: CHEROKEE.LOCAL
- pcscd: Installed but inactive (socket-activated)
- OpenSC: Available in repos, not yet installed

---

## Phase 1: Install PKCS#11 Support

```bash
# Install OpenSC and supporting packages
sudo dnf install -y opensc opensc-libs

# Install PAM smartcard module
sudo dnf install -y pam_pkcs11 pam_pkcs11-tools

# Install certificate enrollment tools (if not present)
sudo dnf install -y certmonger

# Start and enable pcscd
sudo systemctl enable --now pcscd.socket
sudo systemctl start pcscd

# Verify pcscd is running
systemctl status pcscd
```

---

## Phase 2: Verify Token Detection

```bash
# Check token visibility with OpenSC
opensc-tool -l

# Expected output:
# Detected readers (pcsc)
# Nr.  Card  Features  Name
# 0    Yes             SafeNet eToken [...]

# Get token info
pkcs11-tool --module /usr/lib64/opensc-pkcs11.so --list-slots

# Read token serial and capabilities
pkcs11-tool --module /usr/lib64/opensc-pkcs11.so --list-objects
```

---

## Phase 3: Initialize Token (If Needed)

**WARNING**: This will erase all data on the token. Skip if token already has keys/certs.

```bash
# Check if token needs initialization
pkcs11-tool --module /usr/lib64/opensc-pkcs11.so --show-info

# If token is uninitialized:
pkcs11-tool --module /usr/lib64/opensc-pkcs11.so --init-token \
  --label "CHEROKEE-TPM" \
  --so-pin 12345678

# Set user PIN (change these!)
pkcs11-tool --module /usr/lib64/opensc-pkcs11.so --init-pin \
  --login --pin 123456
```

**Important**: Use secure PINs. The SO-PIN is for administrator recovery, User PIN is for daily use.

---

## Phase 4: Generate Key Pair on Token

```bash
# Generate RSA 2048 key pair on token
pkcs11-tool --module /usr/lib64/opensc-pkcs11.so \
  --login --pin <USER_PIN> \
  --keypairgen --key-type rsa:2048 \
  --id 01 --label "Cherokee AI TPM Key"

# Verify key was created
pkcs11-tool --module /usr/lib64/opensc-pkcs11.so \
  --login --pin <USER_PIN> \
  --list-objects --type privkey
```

---

## Phase 5: Request Certificate from FreeIPA CA

```bash
# First, get Kerberos ticket as admin
kinit admin

# Generate CSR from token key
pkcs11-tool --module /usr/lib64/opensc-pkcs11.so \
  --login --pin <USER_PIN> \
  --read-object --type pubkey --id 01 > /tmp/pubkey.der

# Convert to PEM
openssl rsa -pubin -inform DER -in /tmp/pubkey.der -outform PEM -out /tmp/pubkey.pem

# Request certificate from FreeIPA
# (Alternative: Use FreeIPA web UI for certificate request)
ipa cert-request --principal=admin@CHEROKEE.LOCAL \
  --certificate-out=/tmp/admin-cert.pem \
  --profile-id=caIPAserviceCert \
  /tmp/csr.pem

# Or use getcert for automatic enrollment
sudo getcert request -I smartcard-admin \
  -c IPA \
  -N "CN=admin,O=CHEROKEE.LOCAL" \
  -T /usr/lib64/opensc-pkcs11.so \
  -i 01
```

---

## Phase 6: Configure FreeIPA for Smartcard Authentication

```bash
# Enable certificate authentication in FreeIPA
kinit admin

# Create authentication indicator for smartcard
ipa config-mod --user-auth-type=password --user-auth-type=otp --user-auth-type=pkinit

# Enable PKINIT (Kerberos with X.509)
ipa-pkinit-manage enable

# Verify PKINIT is enabled
ipa-pkinit-manage status

# Configure user for certificate mapping
ipa user-mod admin --certificate="$(cat /tmp/admin-cert.pem)"
```

---

## Phase 7: Configure PAM for Smartcard Login

Edit `/etc/pam.d/smartcard-auth`:

```bash
# Create smartcard PAM configuration
sudo tee /etc/pam.d/smartcard-auth << 'EOF'
auth        required      pam_env.so
auth        [success=done authinfo_unavail=ignore ignore=ignore default=die] pam_pkcs11.so
auth        required      pam_deny.so

account     required      pam_unix.so
account     sufficient    pam_localuser.so
account     sufficient    pam_succeed_if.so uid < 1000 quiet
account     [default=bad success=ok user_unknown=ignore] pam_sss.so
account     required      pam_permit.so

password    requisite     pam_pwquality.so try_first_pass local_users_only
password    sufficient    pam_unix.so sha512 shadow nullok try_first_pass use_authtok
password    sufficient    pam_sss.so use_authtok
password    required      pam_deny.so

session     optional      pam_keyinit.so revoke
session     required      pam_limits.so
-session    optional      pam_systemd.so
session     [success=1 default=ignore] pam_succeed_if.so service in crond quiet use_uid
session     required      pam_unix.so
session     optional      pam_sss.so
EOF
```

---

## Phase 8: Configure pam_pkcs11

```bash
# Create pam_pkcs11 configuration
sudo mkdir -p /etc/pam_pkcs11/cacerts
sudo mkdir -p /etc/pam_pkcs11/crls

# Copy FreeIPA CA certificate
sudo cp /etc/ipa/ca.crt /etc/pam_pkcs11/cacerts/

# Hash the CA cert
sudo c_rehash /etc/pam_pkcs11/cacerts/

# Create pam_pkcs11.conf
sudo tee /etc/pam_pkcs11/pam_pkcs11.conf << 'EOF'
pam_pkcs11 {
  nullok = false;
  debug = false;
  use_first_pass = false;
  use_authtok = false;
  card_only = false;
  wait_for_card = false;
  use_pkcs11_module = opensc;

  pkcs11_module opensc {
    module = /usr/lib64/opensc-pkcs11.so;
    description = "OpenSC PKCS#11 module";
    slot_num = 0;
    ca_dir = /etc/pam_pkcs11/cacerts;
    crl_dir = /etc/pam_pkcs11/crls;
    support_threads = false;
    cert_policy = ca,signature;
  }

  use_mappers = subject;
  mapper_search_path = /usr/lib64/pam_pkcs11;

  mapper subject {
    debug = false;
    module = internal;
    mapfile = file:///etc/pam_pkcs11/subject_mapping;
  }
}
EOF

# Create subject mapping file
sudo tee /etc/pam_pkcs11/subject_mapping << 'EOF'
# Format: certificate_subject -> local_username
# CN=admin,O=CHEROKEE.LOCAL -> admin
EOF
```

---

## Phase 9: Test Smartcard Authentication

```bash
# Test PKCS#11 authentication
pkcs11_inspect

# Test PAM authentication (will prompt for PIN)
pamtester smartcard-auth admin authenticate

# Test SSH with smartcard (requires sshd config)
ssh -I /usr/lib64/opensc-pkcs11.so admin@silverfin.cherokee.local
```

---

## Phase 10: Configure SSH for Smartcard

Edit `/etc/ssh/sshd_config` on silverfin:

```bash
# Add to /etc/ssh/sshd_config
sudo tee -a /etc/ssh/sshd_config.d/smartcard.conf << 'EOF'
# Smartcard authentication
PubkeyAuthentication yes
PKCS11Provider /usr/lib64/opensc-pkcs11.so

# For certificate-based auth with FreeIPA
TrustedUserCAKeys /etc/ipa/ca.crt
AuthorizedPrincipalsFile /etc/ssh/auth_principals/%u
EOF

# Restart sshd
sudo systemctl restart sshd
```

---

## Phase 11: Service Account Security (Non-Token Access)

For services that need to access goldfin without hardware tokens:

### 11.1: Create Service Certificates

```bash
# Create service principal in FreeIPA
ipa service-add vetassist-api/greenfin.cherokee.local

# Request certificate for service
ipa-getcert request \
  -K vetassist-api/greenfin.cherokee.local \
  -k /etc/pki/tls/private/vetassist-api.key \
  -f /etc/pki/tls/certs/vetassist-api.crt
```

### 11.2: Configure IP Whitelist on goldfin

Create `/ganuda/config/service_whitelist.conf`:

```ini
# Service account access whitelist
[vetassist-api]
allowed_ips = 192.168.132.224  # greenfin only
cert_cn = vetassist-api/greenfin.cherokee.local
rate_limit = 100/minute

[thermal-memory-sync]
allowed_ips = 192.168.132.223  # redfin only
cert_cn = thermal-sync/redfin.cherokee.local
rate_limit = 50/minute
```

### 11.3: Audit Logging for Service Accounts

All service account access must log to:
1. Local `/var/log/ganuda/service-access.log`
2. thermal_memory_archive with tag `service-audit`
3. FreeIPA audit logs

```bash
# Log format for service access
# timestamp|service_cn|source_ip|action|resource|result
# 2026-01-08T10:30:00|vetassist-api/greenfin|192.168.132.224|READ|veteran_profiles|SUCCESS
```

---

## Verification Checklist

- [ ] OpenSC and pam_pkcs11 installed
- [ ] pcscd running and detecting token
- [ ] Key pair generated on token
- [ ] Certificate issued by FreeIPA CA
- [ ] Certificate mapped to user in FreeIPA
- [ ] PAM configured for smartcard auth
- [ ] SSH configured for PKCS#11
- [ ] pamtester authenticates successfully
- [ ] SSH login with token works
- [ ] Service account certs created
- [ ] IP whitelist configured
- [ ] Audit logging active

---

## Troubleshooting

### Token not detected
```bash
# Check USB
lsusb | grep -i aladdin

# Check pcscd logs
journalctl -u pcscd -f

# Restart pcscd
sudo systemctl restart pcscd
```

### Certificate issues
```bash
# Verify FreeIPA CA
ipa cert-show 1

# Check certificate chain
openssl verify -CAfile /etc/ipa/ca.crt /tmp/admin-cert.pem

# Check certificate on token
pkcs11-tool --module /usr/lib64/opensc-pkcs11.so --list-objects --type cert
```

### PAM failures
```bash
# Enable debug in pam_pkcs11.conf (set debug = true)
# Check auth log
journalctl -u sshd -f
tail -f /var/log/secure
```

---

## Security Notes

1. **PIN Security**: Use strong PINs, implement lockout after 3 failed attempts
2. **Certificate Revocation**: Set up CRL checking in pam_pkcs11
3. **Audit Trail**: All token operations logged to thermal memory
4. **Token Recovery**: Store SO-PIN securely for token reset scenarios
5. **Backup**: FreeIPA CA is the single source of truth for certificates

---

## Thermal Memory Archive

Once complete, archive to thermal memory:

```sql
INSERT INTO thermal_memory_archive (
    memory_hash, original_content, temperature_score, tags,
    source_triad, source_node, source_session, valid_from, memory_type
) VALUES (
    md5('safenet_etoken_freeipa_deployed_jan8_2026'),
    'SAFENET ETOKEN + FREEIPA PKI INTEGRATION - January 8, 2026

DEPLOYMENT:
- Token: SafeNet eToken JC (Aladdin 0529:0620)
- Server: silverfin (Rocky Linux 10, FreeIPA 4.12.2)
- Realm: CHEROKEE.LOCAL
- Auth Methods: PKINIT + PAM smartcard

ARCHITECTURE:
Human → Token + PIN → silverfin FreeIPA → Certificate Auth → goldfin
Service → mTLS + IP whitelist → goldfin

SECURITY:
- Hardware token required for human PII access
- Service accounts use mTLS with IP restrictions
- All access logged to thermal memory

For Seven Generations.',
    98.0,
    ARRAY['security', 'pki', 'smartcard', 'freeipa', 'safenet', 'etoken', 'mfa', 'january-2026'],
    'tpm',
    'silverfin',
    'claude-session-jan8',
    NOW(),
    'operations'
)
ON CONFLICT (memory_hash) DO UPDATE SET
    temperature_score = 98.0,
    original_content = EXCLUDED.original_content,
    tags = EXCLUDED.tags;
```

---

## Related Documents

- KB: /Users/Shared/ganuda/docs/kb/SILVERFIN_FREEIPA_ROCKY9.md
- Jr: JR-FREEIPA-CONTAINER-SILVERFIN-JAN7-2026.md (obsolete - container approach abandoned)
- Jr: JR-SWITCH-HARDENING-VLAN-JAN6-2026.md

---

For Seven Generations.
