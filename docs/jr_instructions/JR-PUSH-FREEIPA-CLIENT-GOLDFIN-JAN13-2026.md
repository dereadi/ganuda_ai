# Jr Instructions: Push FreeIPA Client to Goldfin (Air-Gap)

**Task ID**: AIRGAP-FREEIPA-001
**Priority**: HIGH (P1)
**Date**: January 13, 2026
**Target**: goldfin (192.168.20.10) via bluefin
**Assigned To**: TPM (manual)

---

## Problem

Goldfin (PII Sanctum on VLAN 20) cannot reach internet to install freeipa-client.
This is BY DESIGN - Sanctum is air-gapped for PII protection.

## Solution

Download packages on bluefin, push to goldfin through greenfin.

---

## Step 1: Download FreeIPA Client RPMs on Bluefin

```bash
# SSH to bluefin
ssh dereadi@192.168.132.222

# Create staging directory
mkdir -p /ganuda/repo/rocky9/freeipa-client

# Download freeipa-client and ALL dependencies for Rocky 9
# Using dnf on a Rocky container or repotrack
sudo apt install -y dnf

# Or simpler - use a temp Rocky container to download
sudo docker run --rm -v /ganuda/repo/rocky9/freeipa-client:/download rockylinux:9 \
  bash -c "dnf install -y dnf-plugins-core && dnf download --resolve --destdir=/download freeipa-client"
```

**Alternative if no Docker:** Download directly from Rocky mirror:

```bash
cd /ganuda/repo/rocky9/freeipa-client

# Core package
wget https://dl.rockylinux.org/pub/rocky/9/AppStream/x86_64/os/Packages/f/freeipa-client-4.11.0-9.el9_4.x86_64.rpm

# Dependencies (main ones)
wget https://dl.rockylinux.org/pub/rocky/9/AppStream/x86_64/os/Packages/p/python3-ipaclient-4.11.0-9.el9_4.noarch.rpm
wget https://dl.rockylinux.org/pub/rocky/9/AppStream/x86_64/os/Packages/p/python3-ipalib-4.11.0-9.el9_4.noarch.rpm
wget https://dl.rockylinux.org/pub/rocky/9/BaseOS/x86_64/os/Packages/s/sssd-client-2.9.4-6.el9_4.1.x86_64.rpm
wget https://dl.rockylinux.org/pub/rocky/9/BaseOS/x86_64/os/Packages/s/sssd-common-2.9.4-6.el9_4.1.x86_64.rpm
wget https://dl.rockylinux.org/pub/rocky/9/BaseOS/x86_64/os/Packages/s/sssd-ipa-2.9.4-6.el9_4.1.x86_64.rpm
wget https://dl.rockylinux.org/pub/rocky/9/BaseOS/x86_64/os/Packages/s/sssd-krb5-2.9.4-6.el9_4.1.x86_64.rpm
wget https://dl.rockylinux.org/pub/rocky/9/BaseOS/x86_64/os/Packages/k/krb5-workstation-1.21.1-1.el9.x86_64.rpm
```

---

## Step 2: Copy to Goldfin via Greenfin

```bash
# From bluefin, SCP to greenfin first
scp -r /ganuda/repo/rocky9/freeipa-client dereadi@192.168.132.224:/tmp/

# Then from greenfin, SCP to goldfin
ssh dereadi@192.168.132.224
scp -r /tmp/freeipa-client dereadi@192.168.20.10:/tmp/
```

**Or direct with jump host:**

```bash
# From bluefin direct to goldfin via greenfin
scp -o ProxyJump=dereadi@192.168.132.224 -r /ganuda/repo/rocky9/freeipa-client dereadi@192.168.20.10:/tmp/
```

---

## Step 3: Install on Goldfin

```bash
# SSH to goldfin
ssh -J dereadi@192.168.132.224 dereadi@192.168.20.10

# Install all RPMs
cd /tmp/freeipa-client
sudo dnf install -y *.rpm

# If dependency issues, use:
sudo rpm -ivh --nodeps *.rpm
# Then fix with:
sudo dnf install -y --skip-broken
```

---

## Step 4: Join Domain (After Install)

```bash
# Add silverfin to hosts
echo "192.168.10.10 silverfin.cherokee.local silverfin" | sudo tee -a /etc/hosts

# Join FreeIPA domain
sudo ipa-client-install \
  --domain=cherokee.local \
  --realm=CHEROKEE.LOCAL \
  --server=silverfin.cherokee.local \
  --mkhomedir \
  --force-ntpd
```

---

## Long-term: Set Up Local Rocky Mirror

For future air-gap installs, bluefin should mirror Rocky 9 repos:

```bash
# On bluefin - already planned in JR-APT-MIRROR-BLUEFIN-JAN11-2026.md
# Add Rocky 9 to the mirror config
```

---

*For Seven Generations*
