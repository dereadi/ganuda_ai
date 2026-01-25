# Jr Instructions: FreeIPA Domain Join - All Nodes

**Task ID**: FREEIPA-JOIN-001
**Priority**: HIGH (P1)
**Date**: January 13, 2026
**Target Nodes**: bluefin, redfin, goldfin
**Assigned To**: TPM (manual sudo required)

---

## Prerequisites

- FreeIPA server running on silverfin (192.168.10.10) - VERIFIED UP
- Inter-VLAN routing working through greenfin - VERIFIED
- DNS resolution to silverfin.cherokee.local

---

## Node 1: BLUEFIN (192.168.132.222)

```bash
# SSH to bluefin
ssh dereadi@192.168.132.222

# Install FreeIPA client
sudo apt update
sudo apt install -y freeipa-client

# Add DNS entry for silverfin (if not using FreeIPA DNS)
echo "192.168.10.10 silverfin.cherokee.local silverfin" | sudo tee -a /etc/hosts

# Join the domain
sudo ipa-client-install \
  --domain=cherokee.local \
  --realm=CHEROKEE.LOCAL \
  --server=silverfin.cherokee.local \
  --mkhomedir \
  --force-ntpd

# When prompted:
# - Admin username: admin
# - Admin password: jawaseatlasers2

# Verify enrollment
id admin@cherokee.local
klist
```

---

## Node 2: REDFIN (192.168.132.223)

```bash
# SSH to redfin
ssh dereadi@192.168.132.223

# Install FreeIPA client
sudo apt update
sudo apt install -y freeipa-client

# Add DNS entry for silverfin
echo "192.168.10.10 silverfin.cherokee.local silverfin" | sudo tee -a /etc/hosts

# Join the domain
sudo ipa-client-install \
  --domain=cherokee.local \
  --realm=CHEROKEE.LOCAL \
  --server=silverfin.cherokee.local \
  --mkhomedir \
  --force-ntpd

# Verify enrollment
id admin@cherokee.local
```

---

## Node 3: GOLDFIN (192.168.20.10) - PII Sanctum

```bash
# SSH to goldfin (via greenfin jump)
ssh -J dereadi@192.168.132.224 dereadi@192.168.20.10

# Or if already on greenfin:
ssh dereadi@192.168.20.10

# Install FreeIPA client (Rocky Linux uses dnf)
sudo dnf install -y freeipa-client

# Add DNS entry for silverfin
echo "192.168.10.10 silverfin.cherokee.local silverfin" | sudo tee -a /etc/hosts

# Join the domain
sudo ipa-client-install \
  --domain=cherokee.local \
  --realm=CHEROKEE.LOCAL \
  --server=silverfin.cherokee.local \
  --mkhomedir \
  --force-ntpd

# Verify enrollment
id admin@cherokee.local
```

---

## Post-Enrollment Verification

Run from any enrolled node:

```bash
# Check Kerberos ticket
klist

# Check SSSD status
sudo systemctl status sssd

# Test LDAP lookup
getent passwd admin
```

---

## Unblocks After Completion

1. **VetAssist PII Migration** - goldfin can receive PII database
2. **Centralized Authentication** - all nodes use FreeIPA users
3. **SafeNet eToken Integration** - PKI ready for hardware tokens
4. **Audit Logging** - centralized auth events in FreeIPA

---

*For Seven Generations*
