# Jr Instruction: goldfin Initial Configuration

**Date**: January 9, 2026
**Assigned To**: TPM (Flying Squirrel) - Interactive Session Required
**Node**: goldfin (192.168.132.174)
**Priority**: High
**Status**: Ready for execution

---

## Overview

goldfin has Rocky Linux 10.1 installed and SSH access is working from tpm-macbook. This Jr instruction covers the initial configuration needed before remote management can continue.

**Current State**:
- OS: Rocky Linux 10.1 (Red Quartz)
- IP: 192.168.132.174/24
- SSH: Working from tpm-macbook and silverfin
- sudo: Requires password (blocking remote management)

---

## Phase 1: Initial Configuration (INTERACTIVE - Run on goldfin directly)

SSH to goldfin and run these commands:

```bash
# SSH to goldfin
ssh dereadi@192.168.132.174

# Set hostname
sudo hostnamectl set-hostname goldfin.cherokee.local

# Add to /etc/hosts
echo "192.168.132.174 goldfin.cherokee.local goldfin" | sudo tee -a /etc/hosts

# Add other federation nodes to /etc/hosts
sudo tee -a /etc/hosts << 'EOF'
192.168.132.223 redfin.cherokee.local redfin
192.168.132.222 bluefin.cherokee.local bluefin
192.168.132.224 greenfin.cherokee.local greenfin
192.168.132.57 silverfin.cherokee.local silverfin
192.168.132.241 sasass.cherokee.local sasass
192.168.132.242 sasass2.cherokee.local sasass2
EOF

# Enable passwordless sudo for dereadi (required for remote management)
echo "dereadi ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/dereadi
sudo chmod 440 /etc/sudoers.d/dereadi

# Verify
sudo hostnamectl
```

---

## Phase 2: Create /ganuda Directory Structure

```bash
# Create ganuda directories
sudo mkdir -p /ganuda/{docs,scripts,config,logs,data}
sudo chown -R dereadi:dereadi /ganuda

# Verify
ls -la /ganuda/
```

---

## Phase 3: Install Essential Packages

```bash
# Update system
sudo dnf update -y

# Install essentials
sudo dnf install -y \
    vim \
    git \
    curl \
    wget \
    htop \
    tmux \
    rsync \
    net-tools \
    bind-utils \
    firewalld \
    python3 \
    python3-pip

# Enable firewalld
sudo systemctl enable --now firewalld
```

---

## Phase 4: Configure Firewall (Sanctum - Restrictive)

goldfin is the PII Sanctum node. Default deny all except:
- SSH from greenfin (VLAN router) and silverfin (identity)
- PostgreSQL from greenfin only (for API access)

```bash
# Get current zone
sudo firewall-cmd --get-default-zone

# Set up restrictive zone
sudo firewall-cmd --permanent --zone=drop --change-interface=enp2s0

# Allow SSH from specific IPs only
sudo firewall-cmd --permanent --zone=drop --add-rich-rule='rule family="ipv4" source address="192.168.132.57" service name="ssh" accept'
sudo firewall-cmd --permanent --zone=drop --add-rich-rule='rule family="ipv4" source address="192.168.132.224" service name="ssh" accept'

# Allow PostgreSQL from greenfin only (when DB is installed)
sudo firewall-cmd --permanent --zone=drop --add-rich-rule='rule family="ipv4" source address="192.168.132.224" port port="5432" protocol="tcp" accept'

# Reload
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --zone=drop --list-all
```

**Note**: This is pre-VLAN configuration. After VLAN migration:
- goldfin IP: 192.168.20.10
- Only silverfin (192.168.10.10) can reach goldfin via greenfin routing

---

## Phase 5: Verify Configuration

```bash
# Check hostname
hostname -f

# Check networking
ip addr show

# Check firewall
sudo firewall-cmd --list-all

# Check ganuda directories
ls -la /ganuda/

# Check sudo works without password
sudo whoami
```

---

## Phase 6: Signal Completion

After all phases complete, signal readiness from goldfin:

```bash
# Create completion marker
echo "goldfin initial config complete $(date -Iseconds)" > /ganuda/logs/init-complete.log

# Test connectivity to other nodes
ping -c 2 192.168.132.223  # redfin
ping -c 2 192.168.132.222  # bluefin
ping -c 2 192.168.132.57   # silverfin
```

---

## Post-Configuration Tasks (Remote via tpm-macbook)

Once sudoers is configured, these can be run remotely:

1. **FreeIPA Client Enrollment**
   - Enroll goldfin to silverfin FreeIPA server
   - Enable centralized authentication

2. **PostgreSQL Installation**
   - Install PostgreSQL 15 for VetAssist PII database
   - Configure for encrypted connections only

3. **VLAN Migration**
   - Change IP to 192.168.20.10
   - Move to switch port 15 or 16 (VLAN 20)
   - Update firewall for new subnet

---

## Verification Checklist

- [ ] Hostname set to goldfin.cherokee.local
- [ ] /etc/hosts contains all federation nodes
- [ ] sudoers configured for passwordless dereadi
- [ ] /ganuda directories created
- [ ] Essential packages installed
- [ ] Firewalld enabled and configured restrictively
- [ ] SSH works from silverfin and greenfin IPs
- [ ] Ping connectivity to other nodes verified

---

## Thermal Memory Archive

Once complete:

```sql
INSERT INTO thermal_memory_archive (
    memory_hash, original_content, temperature_score, tags,
    source_triad, source_node, source_session, valid_from, memory_type
) VALUES (
    md5('goldfin_initial_config_jan9_2026'),
    'GOLDFIN INITIAL CONFIGURATION - January 9, 2026

OS: Rocky Linux 10.1 (Red Quartz)
IP: 192.168.132.174 (pre-VLAN), will become 192.168.20.10
Hostname: goldfin.cherokee.local
Role: PII Sanctum - VetAssist database

FIREWALL: Default DROP zone
- SSH from silverfin (192.168.132.57) and greenfin (192.168.132.224) only
- PostgreSQL from greenfin only

NEXT STEPS:
1. FreeIPA client enrollment
2. PostgreSQL 15 installation
3. VLAN 20 migration

For Seven Generations.',
    95.0,
    ARRAY['goldfin', 'initial-config', 'rocky', 'sanctum', 'pii', 'january-2026'],
    'tpm',
    'goldfin',
    'claude-session-jan9',
    NOW(),
    'cmdb_entry'
)
ON CONFLICT (memory_hash) DO UPDATE SET
    temperature_score = 95.0,
    original_content = EXCLUDED.original_content,
    tags = EXCLUDED.tags;
```

---

For Seven Generations.
