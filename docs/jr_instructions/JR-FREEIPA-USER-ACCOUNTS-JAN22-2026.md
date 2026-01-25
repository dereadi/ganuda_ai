# Jr Instructions: FreeIPA User Account Creation

**Date:** January 22, 2026
**Priority:** HIGH
**Assigned To:** TPM (manual sudo required)
**FreeIPA Server:** silverfin.cherokee.local (192.168.10.10)

---

## Overview

Create centralized user accounts in FreeIPA for:
1. **dereadi** - Primary admin
2. **jsdorn** - Joe Dorn
3. **mmwilliams96** - Kensie Williams (k.gossett96@gmail.com)

These accounts will provide SSO access to: bluefin, redfin, greenfin, silverfin, goldfin

---

## Phase 1: Access FreeIPA Admin

### Option A: Web UI
```
https://silverfin.cherokee.local/ipa/ui/
Username: admin
Password: [FreeIPA admin password]
```

### Option B: CLI (from silverfin)
```bash
# SSH to silverfin
ssh dereadi@192.168.10.10

# Get Kerberos ticket
kinit admin
# Enter admin password

# Verify
klist
```

---

## Phase 2: Create User Accounts

### From silverfin CLI:
```bash
# Enter FreeIPA container (if containerized)
sudo podman exec -it freeipa-server bash

# Authenticate as admin
kinit admin

# Create dereadi account
ipa user-add dereadi \
  --first=Darrell \
  --last=Etheridge \
  --email=dereadi@gmail.com \
  --shell=/bin/bash \
  --homedir=/home/dereadi

# Set initial password (user will change on first login)
ipa passwd dereadi

# Create jsdorn account (Joe)
ipa user-add jsdorn \
  --first=Joe \
  --last=Dorn \
  --email=jsdorn@gmail.com \
  --shell=/bin/bash \
  --homedir=/home/jsdorn

ipa passwd jsdorn

# Create mmwilliams96 account (Kensie)
ipa user-add mmwilliams96 \
  --first=Kensie \
  --last=Williams \
  --email=k.gossett96@gmail.com \
  --shell=/bin/bash \
  --homedir=/home/mmwilliams96

ipa passwd mmwilliams96
```

### Verify Users Created:
```bash
ipa user-find
ipa user-show dereadi
ipa user-show jsdorn
ipa user-show mmwilliams96
```

---

## Phase 3: Create User Groups

```bash
# Create groups for access control
ipa group-add cherokee-admins --desc="Cherokee AI Federation Administrators"
ipa group-add cherokee-developers --desc="Cherokee AI Developers"
ipa group-add pii-vault-access --desc="PII Vault Access (goldfin)"

# Add users to groups
ipa group-add-member cherokee-admins --users=dereadi
ipa group-add-member cherokee-admins --users=jsdorn

ipa group-add-member cherokee-developers --users=dereadi
ipa group-add-member cherokee-developers --users=jsdorn
ipa group-add-member cherokee-developers --users=mmwilliams96

# PII vault access (dereadi only for now)
ipa group-add-member pii-vault-access --users=dereadi
```

---

## Phase 4: Enroll Client Nodes

### Nodes to Enroll:

| Node | IP | VLAN | Status |
|------|-----|------|--------|
| bluefin | 192.168.132.222 | Compute | Needs enrollment |
| redfin | 192.168.132.223 | Compute | Needs enrollment |
| greenfin | 192.168.132.224 | Compute | Needs enrollment |
| silverfin | 192.168.10.10 | Sanctum | FreeIPA Server |
| goldfin | 192.168.20.10 | PII | Needs enrollment + OTP |

### For each Debian node (bluefin, redfin, greenfin):
```bash
# Install FreeIPA client
sudo apt update && sudo apt install -y freeipa-client

# Add DNS entry if needed
echo "192.168.10.10 silverfin.cherokee.local silverfin" | sudo tee -a /etc/hosts

# Enroll to domain
sudo ipa-client-install \
  --domain=cherokee.local \
  --realm=CHEROKEE.LOCAL \
  --server=silverfin.cherokee.local \
  --mkhomedir \
  --force-ntpd
```

### For goldfin (Rocky Linux):
```bash
# Install FreeIPA client
sudo dnf install -y freeipa-client

# Add DNS entry
echo "192.168.10.10 silverfin.cherokee.local silverfin" | sudo tee -a /etc/hosts

# Enroll to domain
sudo ipa-client-install \
  --domain=cherokee.local \
  --realm=CHEROKEE.LOCAL \
  --server=silverfin.cherokee.local \
  --mkhomedir \
  --force-ntpd
```

---

## Phase 5: Goldfin OTP Token (Additional Security)

Goldfin hosts PII data - requires additional authentication.

### Enable OTP for goldfin access:
```bash
# On FreeIPA server
kinit admin

# Add OTP token for dereadi on goldfin
ipa otptoken-add --owner=dereadi --type=totp

# This will output a QR code or secret key
# Scan with Google Authenticator, Authy, or similar

# Require OTP for pii-vault-access group
ipa hbacrule-add goldfin-otp-required \
  --hostcat=all \
  --servicecat=all

ipa hbacrule-add-user goldfin-otp-required --groups=pii-vault-access
ipa hbacrule-add-host goldfin-otp-required --hosts=goldfin.cherokee.local
```

### Configure goldfin PAM for OTP:
```bash
# On goldfin
sudo authselect select sssd with-mkhomedir with-sudo --force

# Edit /etc/sssd/sssd.conf to require OTP
# Add under [domain/cherokee.local]:
# auth_provider = ipa
# ipa_server = silverfin.cherokee.local
```

---

## Phase 6: SSH Key Distribution (Optional)

```bash
# Add SSH public keys to FreeIPA accounts
ipa user-mod dereadi --sshpubkey="ssh-ed25519 AAAA... dereadi@tpm"

# Users can then SSH without password (Kerberos + SSH key)
```

---

## Phase 7: Sudo Rules

```bash
# Allow cherokee-admins sudo on all hosts
ipa sudorule-add admin-sudo-all \
  --hostcat=all \
  --cmdcat=all

ipa sudorule-add-user admin-sudo-all --groups=cherokee-admins
ipa sudorule-add-option admin-sudo-all --sudooption='!authenticate'
```

---

## Verification Checklist

- [ ] Users created: dereadi, jsdorn, mmwilliams96
- [ ] Groups created: cherokee-admins, cherokee-developers, pii-vault-access
- [ ] bluefin enrolled
- [ ] redfin enrolled
- [ ] greenfin enrolled
- [ ] goldfin enrolled with OTP requirement
- [ ] SSH login works from any node
- [ ] Sudo works for cherokee-admins

---

## Test Login

After enrollment, test from any enrolled node:
```bash
# Login as FreeIPA user
ssh dereadi@cherokee.local@bluefin.cherokee.local

# Or simply (if hostname resolves)
ssh dereadi@bluefin

# Get Kerberos ticket
kinit dereadi
klist

# Test sudo
sudo whoami
```

---

## Troubleshooting

### "Cannot contact KDC"
```bash
# Check DNS resolution
dig silverfin.cherokee.local

# Check Kerberos ports
nc -zv silverfin.cherokee.local 88
```

### "User not found"
```bash
# Clear SSSD cache
sudo sss_cache -E
sudo systemctl restart sssd
```

### Goldfin OTP not working
```bash
# Check OTP token status
ipa otptoken-find --owner=dereadi

# Re-sync token if clock drift
ipa otptoken-sync --token=<token-id>
```

---

## Security Notes

- Kensie (mmwilliams96) is a developer, not an admin - no sudo by default
- Goldfin requires OTP for anyone in pii-vault-access group
- All auth events logged in FreeIPA audit log
- Consider enabling failed login lockout policy

---

## For Seven Generations

Centralized identity management ensures consistent access control across the Federation while maintaining the ability to audit and revoke access when needed.
