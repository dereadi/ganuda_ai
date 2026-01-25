# Jr Instructions: Goldfin Inner Sanctum - Identity Authority & PII Vault

**Task ID**: GOLDFIN-SEC-001
**Priority**: HIGH
**Target Node**: goldfin (new node - to be provisioned)
**Council Approval**:
- Initial (PII Alcove): APPROVED 3-0-0 (2025-12-28)
- Inner Sanctum (FreeIPA + PII): APPROVED 6-1-0 (2025-12-28) - 86.2% confidence
**OS Decision**: Linux (Debian 12) - Council vote 4-2-0

---

## Executive Summary

Goldfin is the **Inner Sanctum** of the Cherokee AI Federation - the most secured node hosting both the identity authority (FreeIPA) and the PII vault (veteran data alcove). All other nodes authenticate through goldfin.

**Role**: Identity Authority + PII Vault
**Hardware**: Beelink SER7 (Ryzen 7 7840HS, 32GB DDR5, 2x 2TB NVMe RAID0)
**OS**: Debian 12 (Bookworm) with AppArmor
**Services**: FreeIPA Server, PostgreSQL (vetassist_pii)
**Authentication**: YubiKey 5 (hard token) required for all access
**Network**: Tailscale only - no direct internet access

### Why Co-locate FreeIPA and PII?

1. **Highest security posture** - YubiKey, LUKS, AppArmor, Tailscale-only already planned
2. **Separation from compute** - Identity/PII isolated from GPU/daemon workloads
3. **Risk parity** - If goldfin is compromised, attacker has identity anyway; co-location doesn't increase risk
4. **Resource efficiency** - PII is disk-bound, FreeIPA is lightweight; no contention
5. **Single hardened target** - One node to audit, monitor, and protect

### Addressing Crawdad's Concern: Two-Layer Auth Model

Crawdad (REJECT 0.8) raised a valid concern: *"Co-locating FreeIPA and PII increases attack surface; if compromised, attacker gets both identity authority AND PII."*

**Mitigation: Software Partition with Separate Auth Layers**

Even on the same hardware, node access ≠ PII access. Three gates must be passed:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GOLDFIN - INNER SANCTUM                      │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              LAYER 1: NODE ACCESS (FreeIPA)                  │    │
│  │                                                              │    │
│  │  Gate 1: YubiKey + SSH key + IPA credentials                │    │
│  │  • HBAC rules control who reaches the box                   │    │
│  │  • Sudo rules control what they can do                      │    │
│  │  • No root login, no shared accounts                        │    │
│  │  • Audit: who logged in, when, from where                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                    ══════════════════════                            │
│                    SOFTWARE PARTITION                                │
│                    (separate credentials)                            │
│                    ══════════════════════                            │
│                              │                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              LAYER 2: ALCOVE ACCESS                          │    │
│  │                                                              │    │
│  │  Gate 2: YubiKey touch to mount encrypted alcove            │    │
│  │  • Alcove does NOT auto-mount on boot                       │    │
│  │  • Physical YubiKey presence required                       │    │
│  │  • Audit: mount/unmount events logged                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              LAYER 3: PII DATA ACCESS (PostgreSQL)           │    │
│  │                                                              │    │
│  │  Gate 3: PostgreSQL role credentials (NOT unix accounts)   │    │
│  │  • vetassist_app role - app-level access only               │    │
│  │  • pii_auditor role - read-only for compliance              │    │
│  │  • No superuser from app layer                              │    │
│  │  • Credentials separate from node credentials               │    │
│  │  • Audit: every query logged with accessor ID               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Attack Scenario Analysis:**

| Attacker Has | Can They Access PII? | Why Not? |
|--------------|---------------------|----------|
| SSH access (stole YubiKey + IPA creds) | NO | Alcove not mounted, no PG creds |
| SSH + mounted alcove | NO | No PostgreSQL credentials |
| SSH + PG creds (no YubiKey) | NO | Can't mount alcove, data encrypted |
| All three gates | YES | But audit trail captures everything |

This is defense in depth - compromising one layer doesn't cascade to the next.

### Future State: Silverfin Migration

When budget allows (~$1,020 for identical hardware), we split goldfin into two nodes:

```
┌─────────────────────┐              ┌─────────────────────┐
│      SILVERFIN      │              │      GOLDFIN        │
│   (Identity Only)   │              │    (PII Only)       │
│                     │              │                     │
│  • FreeIPA Server   │◄────────────►│  • PostgreSQL       │
│  • LDAP Directory   │   Kerberos   │  • vetassist_pii    │
│  • Kerberos KDC     │    auth      │  • Audit logs       │
│  • Certificate CA   │              │  • Encrypted alcove │
│  • HBAC/Sudo rules  │              │                     │
│                     │              │                     │
│  IP: 192.168.132.226│              │  IP: 192.168.132.225│
└─────────────────────┘              └─────────────────────┘
```

**Migration Path:**

1. Purchase identical Beelink SER7 + 2x 2TB NVMe + YubiKeys
2. Install silverfin as FreeIPA replica first (IPA supports replication)
3. Promote silverfin to primary FreeIPA server
4. Demote goldfin's FreeIPA to client-only
5. Uninstall FreeIPA server components from goldfin
6. Goldfin becomes pure PII vault

**Benefits of Split:**
- Fully addresses Crawdad's least-privilege concern
- Physical separation of identity and data
- Can update/reboot identity server without PII downtime
- Silverfin can have HA replica (future: bronzefin?)

**Until Then:**
- Two-layer auth model provides software separation
- Extra audit rigor on goldfin
- Document that this is Phase 1, split is Phase 2

---

## Hardware Specifications

| Component | Specification |
|-----------|---------------|
| Model | Beelink SER7 |
| CPU | AMD Ryzen 7 7840HS (8C/16T, up to 5.1GHz) |
| RAM | 32GB DDR5-5600 (dual channel) |
| Storage 1 | 2TB NVMe PCIe 4.0 (replace stock 1TB) |
| Storage 2 | 2TB NVMe PCIe 4.0 |
| Storage Config | RAID0 stripe across both drives (I/O distribution) |
| Network | 2.5GbE RJ45 + WiFi 6 (WiFi disabled) |
| Ports | 2x USB4, HDMI 2.1, DP 1.4, USB-A |

**Note**: Both drives are 2TB to enable striping. This distributes I/O load and prevents "cooking" one drive as database grows.

**Tailscale IP**: To be assigned (100.x.x.x)
**Local IP**: 192.168.132.225 (reserved)

### Updated Shopping List

| Item | Est. Cost |
|------|-----------|
| Beelink SER7 (32GB/1TB) | ~$650 |
| 2TB NVMe PCIe 4.0 x2 (replace 1TB + add) | ~$260 |
| YubiKey 5 NFC x2 | ~$110 |
| **Total** | **~$1,020** |

---

## Phase 1: Base OS Installation

### 1.1 Debian 12 Installation

1. Download Debian 12 netinst ISO
2. Create bootable USB
3. Install with following options:
   - **Hostname**: goldfin
   - **Domain**: cherokee.local
   - **Root password**: Set strong password (store in password manager)
   - **User**: dereadi (consistent with other nodes)
   - **Partitioning**: See disk layout below
   - **Software**: SSH server, standard system utilities (NO desktop)

### 1.2 Disk Layout (Drive 1 - 1TB OS Drive)

```
/dev/nvme0n1 (1TB - OS Drive)
├── /dev/nvme0n1p1  512MB   /boot/efi  (EFI System)
├── /dev/nvme0n1p2  1GB     /boot      (ext4, unencrypted for GRUB)
└── /dev/nvme0n1p3  ~998GB  LUKS encrypted
    └── LVM inside LUKS
        ├── vg0-root    50GB   /         (ext4)
        ├── vg0-var     100GB  /var      (ext4) - logs, PostgreSQL
        ├── vg0-tmp     10GB   /tmp      (ext4, noexec,nosuid)
        ├── vg0-home    20GB   /home     (ext4)
        └── vg0-free    ~818GB (unallocated for future)
```

### 1.3 Disk Layout (Drive 2 - 2TB Data Alcove)

```
/dev/nvme1n1 (2TB - Veteran Data Alcove)
└── /dev/nvme1n1p1  ~2TB    LUKS encrypted (SEPARATE key from OS!)
    └── /alcove             (ext4, mounted on demand)
        ├── /alcove/veteran_data/
        ├── /alcove/session_data/
        ├── /alcove/audit_logs/
        └── /alcove/backups/
```

**CRITICAL**: The alcove drive uses a DIFFERENT LUKS passphrase than the OS drive. This passphrase is stored on a YubiKey.

---

## Phase 2: Security Hardening

### 2.1 Initial Hardening

```bash
# Update system
apt update && apt upgrade -y

# Install essential security packages
apt install -y \
    ufw \
    fail2ban \
    apparmor \
    apparmor-utils \
    auditd \
    audispd-plugins \
    libpam-yubico \
    yubikey-manager \
    cryptsetup \
    lvm2 \
    unattended-upgrades

# Enable AppArmor
systemctl enable apparmor
systemctl start apparmor

# Enable audit daemon
systemctl enable auditd
systemctl start auditd
```

### 2.2 Firewall Configuration

```bash
# Default deny all
ufw default deny incoming
ufw default deny outgoing

# Allow Tailscale
ufw allow in on tailscale0
ufw allow out on tailscale0

# Allow DNS (for Tailscale)
ufw allow out 53/udp

# Allow Tailscale coordination (outbound only)
ufw allow out 41641/udp

# Enable firewall
ufw enable
```

### 2.3 SSH Hardening

Edit `/etc/ssh/sshd_config`:

```
# Only allow from Tailscale
ListenAddress 100.0.0.0/8

# Disable password auth (YubiKey only)
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication yes

# Require both key AND YubiKey
AuthenticationMethods publickey,keyboard-interactive

# Restrict to dereadi user only
AllowUsers dereadi

# Other hardening
PermitRootLogin no
X11Forwarding no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
```

### 2.4 Fail2Ban Configuration

Create `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400
```

---

## Phase 3: YubiKey Integration

### 3.1 YubiKey PAM Setup

```bash
# Install YubiKey PAM module
apt install -y libpam-yubico libpam-u2f

# Create auth directory
mkdir -p /etc/yubico

# Initialize YubiKey for user
# (Run as dereadi with YubiKey inserted)
pamu2fcfg > /etc/yubico/u2f_keys
chown root:root /etc/yubico/u2f_keys
chmod 600 /etc/yubico/u2f_keys
```

### 3.2 PAM Configuration for SSH

Edit `/etc/pam.d/sshd`, add after @include common-auth:

```
# Require YubiKey U2F
auth required pam_u2f.so authfile=/etc/yubico/u2f_keys cue
```

### 3.3 PAM Configuration for sudo

Edit `/etc/pam.d/sudo`, add at top:

```
# Require YubiKey for sudo
auth required pam_u2f.so authfile=/etc/yubico/u2f_keys cue
```

### 3.4 LUKS YubiKey Integration (Alcove Drive)

```bash
# Install YubiKey LUKS tools
apt install -y yubikey-luks

# Enroll YubiKey for alcove drive
# This stores a challenge-response secret on the YubiKey
yubikey-luks-enroll -d /dev/nvme1n1p1 -s 7

# Test unlock
yubikey-luks-open -d /dev/nvme1n1p1 -n alcove_crypt
```

**Result**: The alcove drive can ONLY be unlocked with physical YubiKey present.

---

## Phase 4: PostgreSQL Setup

### 4.1 Install PostgreSQL

```bash
apt install -y postgresql-15 postgresql-contrib-15

# PostgreSQL data stays on OS drive (/var/lib/postgresql)
# Veteran-specific data goes to alcove via tablespace
```

### 4.2 Create Alcove Tablespace

```bash
# Create directory on alcove drive (after mounting)
mkdir -p /alcove/veteran_data/postgresql
chown postgres:postgres /alcove/veteran_data/postgresql

# Create tablespace (run as postgres)
sudo -u postgres psql -c "CREATE TABLESPACE alcove_ts LOCATION '/alcove/veteran_data/postgresql';"
```

### 4.3 Database Schema

```sql
-- Veteran data database (uses alcove tablespace)
CREATE DATABASE vetassist_pii TABLESPACE alcove_ts;

\c vetassist_pii

-- Veteran profiles (PII)
CREATE TABLE veteran_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Encrypted fields (application-level encryption on top of disk encryption)
    encrypted_name BYTEA,
    encrypted_ssn_last4 BYTEA,
    encrypted_email BYTEA,
    encrypted_phone BYTEA,
    -- Non-PII metadata
    service_branch VARCHAR(50),
    service_start_year INTEGER,
    service_end_year INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_access TIMESTAMP,
    access_count INTEGER DEFAULT 0
) TABLESPACE alcove_ts;

-- Claim drafts (contains personal statements)
CREATE TABLE claim_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    veteran_id UUID REFERENCES veteran_profiles(id),
    encrypted_content BYTEA,  -- Full draft encrypted
    condition_codes TEXT[],   -- Non-PII condition codes
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
) TABLESPACE alcove_ts;

-- Session data
CREATE TABLE veteran_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    veteran_id UUID REFERENCES veteran_profiles(id),
    encrypted_session_data BYTEA,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
) TABLESPACE alcove_ts;

-- Audit log (who accessed what, when)
CREATE TABLE pii_access_log (
    id BIGSERIAL PRIMARY KEY,
    accessor_id VARCHAR(100),  -- Who accessed
    veteran_id UUID,           -- Whose data
    action VARCHAR(50),        -- read, write, delete
    fields_accessed TEXT[],    -- Which fields
    source_ip INET,
    access_time TIMESTAMP DEFAULT NOW(),
    yubikey_serial VARCHAR(20) -- Which YubiKey was used
) TABLESPACE alcove_ts;

-- Indexes
CREATE INDEX idx_veteran_sessions_expires ON veteran_sessions(expires_at);
CREATE INDEX idx_access_log_veteran ON pii_access_log(veteran_id);
CREATE INDEX idx_access_log_time ON pii_access_log(access_time);
```

### 4.4 PostgreSQL Access Control

Edit `/etc/postgresql/15/main/pg_hba.conf`:

```
# Local socket (require peer auth)
local   vetassist_pii   vetassist_app                   peer

# Tailscale network only (require scram + SSL)
hostssl vetassist_pii   vetassist_app   100.0.0.0/8     scram-sha-256

# Deny all other connections to PII database
host    vetassist_pii   all             0.0.0.0/0       reject
```

---

## Phase 5: FreeIPA Server Installation

Goldfin serves as the identity authority for the entire Federation. All other nodes authenticate through FreeIPA running here.

### 5.1 Install FreeIPA Server

```bash
# Install FreeIPA server packages
apt install -y freeipa-server freeipa-server-dns

# Run the installer (interactive)
ipa-server-install \
    --realm=CHEROKEE.LOCAL \
    --domain=cherokee.local \
    --ds-password=<directory-manager-password> \
    --admin-password=<admin-password> \
    --hostname=goldfin.cherokee.local \
    --no-ntp \
    --no-dns-forwarder \
    --setup-dns \
    --allow-zone-overlap

# This takes 10-15 minutes
```

**Notes:**
- `--no-ntp`: We'll manage NTP separately (air-gap compatible)
- `--setup-dns`: FreeIPA runs internal DNS for cherokee.local
- Passwords stored in password manager, NOT in thermal memory

### 5.2 Create Federation Groups

```bash
# Authenticate as admin
kinit admin

# Create groups
ipa group-add federation-admins --desc="Full cluster access"
ipa group-add pii-admins --desc="PII alcove access (goldfin)"
ipa group-add gpu-operators --desc="GPU/vLLM access (redfin)"
ipa group-add db-operators --desc="Database access (bluefin)"
ipa group-add daemon-operators --desc="Service management (greenfin)"
ipa group-add service-accounts --desc="Jr executors, bots (no interactive login)"
```

### 5.3 Create Users

```bash
# TPM admin (Derek)
ipa user-add tpm-derek \
    --first=Derek \
    --last=Admin \
    --shell=/bin/bash \
    --password

# Add to groups
ipa group-add-member federation-admins --users=tpm-derek
ipa group-add-member pii-admins --users=tpm-derek

# Dr. Joe (when ready)
ipa user-add drjoe \
    --first=Joe \
    --last=Admin \
    --shell=/bin/bash \
    --password

ipa group-add-member federation-admins --users=drjoe
```

### 5.4 Create HBAC Rules (Host-Based Access Control)

```bash
# Disable the default "allow_all" rule
ipa hbacrule-disable allow_all

# Rule: federation-admins can access all hosts
ipa hbacrule-add allow_federation_admins
ipa hbacrule-add-user allow_federation_admins --groups=federation-admins
ipa hbacrule-add-host allow_federation_admins --hostgroups=ipaservers
ipa hbacrule-mod allow_federation_admins --hostcat=all

# Rule: pii-admins can access goldfin only
ipa hbacrule-add allow_pii_admins_goldfin
ipa hbacrule-add-user allow_pii_admins_goldfin --groups=pii-admins
ipa hbacrule-add-host allow_pii_admins_goldfin --hosts=goldfin.cherokee.local

# Rule: gpu-operators can access redfin only
ipa hbacrule-add allow_gpu_operators_redfin
ipa hbacrule-add-user allow_gpu_operators_redfin --groups=gpu-operators
ipa hbacrule-add-host allow_gpu_operators_redfin --hosts=redfin.cherokee.local

# Rule: db-operators can access bluefin only
ipa hbacrule-add allow_db_operators_bluefin
ipa hbacrule-add-user allow_db_operators_bluefin --groups=db-operators
ipa hbacrule-add-host allow_db_operators_bluefin --hosts=bluefin.cherokee.local
```

### 5.5 Create Sudo Rules (Centralized)

```bash
# federation-admins get full sudo everywhere
ipa sudorule-add sudo_federation_admins
ipa sudorule-add-user sudo_federation_admins --groups=federation-admins
ipa sudorule-mod sudo_federation_admins --hostcat=all --cmdcat=all

# pii-admins get sudo on goldfin only
ipa sudorule-add sudo_pii_admins
ipa sudorule-add-user sudo_pii_admins --groups=pii-admins
ipa sudorule-add-host sudo_pii_admins --hosts=goldfin.cherokee.local
ipa sudorule-mod sudo_pii_admins --cmdcat=all
```

### 5.6 Enroll YubiKey for FreeIPA User

```bash
# Generate OTP configuration for YubiKey
ipa otptoken-add --type=totp --owner=tpm-derek

# Or use YubiKey's native OTP (Yubico Cloud validation)
# For air-gap: use HOTP/TOTP stored on YubiKey
```

### 5.7 Verify FreeIPA Status

```bash
# Check IPA services
ipactl status

# Test Kerberos
kinit admin
klist

# List users
ipa user-find

# List HBAC rules
ipa hbacrule-find
```

---

## Phase 6: Enroll Other Nodes as IPA Clients

This happens on EACH of the other 6 nodes (redfin, bluefin, greenfin, sasass, sasass2, tpm-macbook).

### 6.1 Linux Nodes (redfin, bluefin, greenfin)

```bash
# Install IPA client
apt install -y freeipa-client

# Enroll with goldfin
ipa-client-install \
    --server=goldfin.cherokee.local \
    --domain=cherokee.local \
    --realm=CHEROKEE.LOCAL \
    --principal=admin \
    --password=<admin-password> \
    --mkhomedir \
    --enable-dns-updates

# Test login with IPA user
su - tpm-derek
```

### 6.2 macOS Nodes (sasass, sasass2, tpm-macbook)

macOS doesn't have native FreeIPA client, but can bind via:

**Option A: LDAP Bind (simpler)**
```bash
# Configure Directory Utility to bind to goldfin LDAP
# System Preferences → Users & Groups → Login Options → Network Account Server
# Add: goldfin.cherokee.local
```

**Option B: sssd (more integrated)**
```bash
# Install via Homebrew
brew install sssd

# Configure /etc/sssd/sssd.conf
# (Complex - save for build session)
```

**Option C: SSH Key Distribution (pragmatic)**
- Macs use local accounts
- SSH keys managed centrally, distributed via Ansible
- Kerberos auth via `kinit` before SSH

---

## Phase 7: Alcove Mount/Unmount Procedures

### 7.1 Mount Script (requires YubiKey)

Create `/usr/local/bin/mount-alcove`:

```bash
#!/bin/bash
# Mount the secure alcove - requires YubiKey

set -e

DEVICE="/dev/nvme1n1p1"
MAPPER_NAME="alcove_crypt"
MOUNT_POINT="/alcove"

# Check if already mounted
if mountpoint -q "$MOUNT_POINT"; then
    echo "Alcove already mounted"
    exit 0
fi

# Check for YubiKey
if ! ykman info > /dev/null 2>&1; then
    echo "ERROR: YubiKey not detected. Insert YubiKey and try again."
    exit 1
fi

echo "YubiKey detected. Touch YubiKey to unlock alcove..."

# Open LUKS with YubiKey
yubikey-luks-open -d "$DEVICE" -n "$MAPPER_NAME"

# Mount
mount /dev/mapper/"$MAPPER_NAME" "$MOUNT_POINT"

# Start PostgreSQL if not running
systemctl start postgresql

echo "Alcove mounted successfully at $MOUNT_POINT"

# Log the mount event
logger -t alcove "Alcove mounted by $(whoami) with YubiKey"
```

### 7.2 Unmount Script

Create `/usr/local/bin/unmount-alcove`:

```bash
#!/bin/bash
# Safely unmount the alcove

set -e

MAPPER_NAME="alcove_crypt"
MOUNT_POINT="/alcove"

# Stop services using alcove
systemctl stop postgresql || true

# Sync and unmount
sync
umount "$MOUNT_POINT"

# Close LUKS
cryptsetup close "$MAPPER_NAME"

echo "Alcove unmounted and encrypted"
logger -t alcove "Alcove unmounted by $(whoami)"
```

### 7.3 Set Permissions

```bash
chmod 750 /usr/local/bin/mount-alcove
chmod 750 /usr/local/bin/unmount-alcove
chown root:sudo /usr/local/bin/mount-alcove
chown root:sudo /usr/local/bin/unmount-alcove
```

---

## Phase 8: Tailscale Integration

### 6.1 Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --ssh
```

### 6.2 Tailscale ACLs (update in admin console)

Add to Tailscale ACL policy:

```json
{
  "acls": [
    // Only redfin gateway can access goldfin
    {
      "action": "accept",
      "src": ["redfin"],
      "dst": ["goldfin:5432", "goldfin:22"]
    },
    // TPM can access for administration
    {
      "action": "accept",
      "src": ["tpm-macbook"],
      "dst": ["goldfin:22"]
    },
    // Deny all other access to goldfin
    {
      "action": "deny",
      "src": ["*"],
      "dst": ["goldfin:*"]
    }
  ]
}
```

---

## Phase 9: Audit Configuration

### 7.1 Auditd Rules

Create `/etc/audit/rules.d/goldfin.rules`:

```
# Monitor alcove directory
-w /alcove -p rwxa -k alcove_access

# Monitor PostgreSQL data
-w /alcove/veteran_data/postgresql -p rwxa -k pg_data_access

# Monitor authentication
-w /etc/pam.d -p wa -k pam_changes
-w /etc/ssh/sshd_config -p wa -k ssh_config

# Monitor YubiKey config
-w /etc/yubico -p rwxa -k yubikey_config

# Log all sudo commands
-w /usr/bin/sudo -p x -k sudo_usage

# Log mount/unmount
-w /usr/local/bin/mount-alcove -p x -k alcove_mount
-w /usr/local/bin/unmount-alcove -p x -k alcove_unmount
```

### 7.2 Restart Auditd

```bash
systemctl restart auditd
```

---

## Phase 10: Integration with Redfin Gateway

### 8.1 API Proxy Pattern

Redfin gateway acts as the only entry point to goldfin:

```
Veteran App → Redfin Gateway (8080) → Goldfin PostgreSQL (5432)
                    │
                    └── Validates request
                    └── Adds audit metadata
                    └── Proxies to goldfin
```

### 8.2 Connection String (for redfin services)

```python
# Only accessible from redfin via Tailscale
GOLDFIN_PII_DB = "postgresql://vetassist_app@goldfin.tailnet:5432/vetassist_pii?sslmode=require"
```

### 8.3 Gateway Middleware (add to gateway.py)

```python
# Pseudo-code for PII access routing
@app.route('/v1/vetassist/pii/<action>', methods=['POST'])
async def pii_access(action):
    # Verify request authentication
    # Log access attempt
    # Proxy to goldfin
    # Log result
    pass
```

---

## Validation Checklist

### Hardware Setup
- [ ] Beelink SER7 received and unpacked
- [ ] 2TB NVMe drive installed in slot 2
- [ ] Connected to network (Ethernet, WiFi disabled)

### OS Installation
- [ ] Debian 12 installed with LUKS on both drives
- [ ] Separate LUKS keys for OS and alcove drives
- [ ] LVM configured per layout

### Security Hardening
- [ ] AppArmor enabled and enforcing
- [ ] UFW configured (Tailscale only)
- [ ] SSH hardened (key + YubiKey only)
- [ ] Fail2ban active
- [ ] Auditd configured

### YubiKey Integration
- [ ] YubiKey enrolled for user authentication
- [ ] YubiKey enrolled for alcove LUKS
- [ ] SSH requires YubiKey touch
- [ ] sudo requires YubiKey touch
- [ ] Alcove mount requires YubiKey

### PostgreSQL
- [ ] PostgreSQL 15 installed
- [ ] Alcove tablespace created
- [ ] vetassist_pii database created
- [ ] Tables created per schema
- [ ] pg_hba.conf restricts to Tailscale

### Network
- [ ] Tailscale installed and connected
- [ ] Tailscale ACLs restrict access to redfin + tpm-macbook
- [ ] No direct internet access (UFW blocks)
- [ ] 2.5GbE connected to local network

### Integration
- [ ] Redfin can connect to goldfin PostgreSQL via Tailscale
- [ ] TPM can SSH to goldfin with YubiKey
- [ ] Mount/unmount scripts tested
- [ ] Audit logs capturing access

---

## Maintenance Procedures

### Daily (Automated)
- Audit log rotation
- Session expiry cleanup
- Backup verification

### Weekly
- Review audit logs for anomalies
- Check disk space on alcove
- Verify backup integrity

### Monthly
- Security updates (unattended-upgrades handles most)
- Review Tailscale ACLs
- YubiKey serial verification

### On Reboot
- Alcove does NOT auto-mount (by design)
- Admin must SSH in with YubiKey and run `mount-alcove`
- This is intentional - cold boot protection

---

## Emergency Procedures

### Lost YubiKey
1. Use backup YubiKey (enroll 2 keys initially!)
2. If both lost, LUKS recovery key is needed
3. Recovery key stored in secure offline location

### Suspected Breach
1. Immediately: `unmount-alcove`
2. Disconnect from Tailscale: `tailscale down`
3. Power off if necessary
4. Review audit logs from backup
5. Contact TPM

### Data Recovery
1. LUKS recovery requires passphrase OR YubiKey
2. Backups encrypted with separate key
3. Recovery procedure documented offline

---

## Related Documents

- KB-0022: MetaController Research (context on security posture)
- VetAssist-PRD.md: Product requirements this secures
- JR-PGHBA-Tailscale-Fix.md: PostgreSQL Tailscale pattern

---

## Council Approval

**Question**: Goldfin dedicated secure node for veteran PII?
**Vote**: APPROVED 3-0-0 (2025-12-28)
- Raven (0.8): Best practices, addresses Crawdad concerns
- Crawdad (0.9): "Significantly enhances security and protects sacred knowledge"
- Turtle (0.8): Serves Seven Generations

**OS Question**: Which OS for goldfin?
**Vote**: Linux (Debian) - 4-2-0 (2025-12-28)
- Consensus: Consistency with bluefin/greenfin, SELinux/AppArmor support

---

*For Seven Generations - Protecting those who served*
