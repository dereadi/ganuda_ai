# Jr Instruction: Unattended Upgrades for Linux Nodes

**Date**: January 11, 2026
**Priority**: CRITICAL
**Target Nodes**: redfin, bluefin, greenfin, goldfin
**TPM**: Flying Squirrel (dereadi)
**Council Approval**: ULTRATHINK 7f3a91c2d8e4b5f0

## Problem

Linux nodes are showing package update notifications. Security patches are not being applied automatically. This creates security debt and audit risk for VetAssist PII handling.

## Solution

Configure unattended-upgrades on all Linux nodes with appropriate settings per node criticality.

---

## Node-Specific Configuration

### bluefin (Database - CONSERVATIVE)
```bash
# Install unattended-upgrades
sudo apt install -y unattended-upgrades apt-listchanges

# Configure for security-only, no auto-reboot
sudo tee /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::Package-Blacklist {
    "postgresql*";
    "linux-image*";
    "linux-headers*";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Mail "root";
Unattended-Upgrade::MailReport "on-change";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::SyslogEnable "true";
Unattended-Upgrade::Automatic-Reboot-WithUsers "false";
EOF

# TPM DIRECTIVE: If reboot required, notify via Telegram. Do NOT auto-reboot.
# See /ganuda/scripts/reboot-notify.sh

# Enable automatic updates
sudo tee /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF

# Verify configuration
sudo unattended-upgrades --dry-run --debug
```

### redfin (GPU/Inference - CONSERVATIVE)
```bash
# Same install
sudo apt install -y unattended-upgrades apt-listchanges

# Configure - blacklist CUDA and kernel
sudo tee /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::Package-Blacklist {
    "cuda*";
    "nvidia*";
    "linux-image*";
    "linux-headers*";
    "vllm*";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::SyslogEnable "true";
EOF

sudo tee /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
```

### greenfin (Daemons - MODERATE)
```bash
sudo apt install -y unattended-upgrades apt-listchanges

sudo tee /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}:${distro_codename}-updates";
};
Unattended-Upgrade::Package-Blacklist {
    "linux-image*";
    "linux-headers*";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::SyslogEnable "true";
EOF

sudo tee /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
```

### goldfin (Rocky Linux - DNF-AUTOMATIC)
```bash
# Rocky Linux uses dnf-automatic instead
sudo dnf install -y dnf-automatic

# Configure for security updates only
sudo tee /etc/dnf/automatic.conf << 'EOF'
[commands]
upgrade_type = security
random_sleep = 360
download_updates = yes
apply_updates = yes

[emitters]
emit_via = stdio

[email]
email_from = root@goldfin.cherokee.local
email_to = root

[base]
debuglevel = 1
EOF

# Enable timer
sudo systemctl enable --now dnf-automatic.timer

# Verify
sudo systemctl status dnf-automatic.timer
```

---

## Telegram Reboot Notification Script

Create on all nodes:
```bash
sudo tee /ganuda/scripts/reboot-notify.sh << 'EOF'
#!/bin/bash
# Notify TPM via Telegram if reboot is required
# Cherokee AI Federation

HOSTNAME=$(hostname)
REBOOT_FILE="/var/run/reboot-required"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

# Load credentials from config
if [ -f /ganuda/config/telegram.conf ]; then
    source /ganuda/config/telegram.conf
fi

if [ -f "$REBOOT_FILE" ]; then
    PKGS=$(cat /var/run/reboot-required.pkgs 2>/dev/null || echo "unknown packages")
    MESSAGE="🔄 REBOOT REQUIRED: ${HOSTNAME}

Packages requiring reboot:
${PKGS}

Run when ready:
sudo reboot

-- Cherokee AI Federation"

    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_CHAT_ID}" \
            -d text="${MESSAGE}" \
            -d parse_mode="Markdown"
        echo "Telegram notification sent for ${HOSTNAME}"
    else
        echo "Telegram credentials not configured. Reboot required on ${HOSTNAME}"
    fi
fi
EOF

sudo chmod +x /ganuda/scripts/reboot-notify.sh

# Add to cron - check every hour
echo "0 * * * * root /ganuda/scripts/reboot-notify.sh" | sudo tee /etc/cron.d/reboot-notify
```

### Telegram Configuration

The Federation already has Telegram bots configured:
- **Token Vault**: `/Users/Shared/ganuda/home/dereadi/.telegram_vault.enc`
- **Bots available**: `alert_bot`, `assistant_bot`
- **Chief Jr Bot**: `/Users/Shared/ganuda/telegram_bot/telegram_chief.py`

For Linux nodes, create credentials file using the `alert_bot` token:
```bash
# Get token from vault (on a Mac with cryptography installed)
# Or ask TPM for the alert_bot token

sudo tee /ganuda/config/telegram.conf << 'EOF'
# Cherokee AI Federation Telegram Bot
# alert_bot from vault
TELEGRAM_BOT_TOKEN="<get from TPM or vault>"
TELEGRAM_CHAT_ID="<TPM's chat ID>"
EOF

sudo chmod 600 /ganuda/config/telegram.conf
```

**Note**: The Chief Jr bot (`telegram_chief.py`) can also receive these notifications if integrated.

---

## Verification Commands

```bash
# Check if unattended-upgrades ran (Debian/Ubuntu)
sudo cat /var/log/unattended-upgrades/unattended-upgrades.log

# Check pending updates
apt list --upgradable

# Force a dry run
sudo unattended-upgrades --dry-run -v

# Rocky Linux - check dnf-automatic
sudo systemctl status dnf-automatic.timer
sudo journalctl -u dnf-automatic
```

---

## Ansible Playbook Integration

Add to existing patch_nodes.yml or create new:

```yaml
- name: Ensure unattended-upgrades configured
  hosts: spokes_linux
  become: yes
  tasks:
    - name: Install unattended-upgrades (Debian)
      apt:
        name:
          - unattended-upgrades
          - apt-listchanges
        state: present
      when: ansible_os_family == "Debian"

    - name: Install dnf-automatic (RedHat)
      dnf:
        name: dnf-automatic
        state: present
      when: ansible_os_family == "RedHat"
```

---

## Thermal Memory Archive

After completion:
```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'UNATTENDED-UPGRADES CONFIGURED - January 11, 2026

  Nodes configured:
  - bluefin: security-only, postgres/kernel blacklisted, no auto-reboot
  - redfin: security-only, cuda/nvidia/kernel blacklisted, no auto-reboot
  - greenfin: security+updates, kernel blacklisted, no auto-reboot
  - goldfin: dnf-automatic security, timer enabled

  All nodes now auto-patching security updates.
  Manual reboot coordination still required.

  For Seven Generations.',
  92, 'it_triad_jr',
  ARRAY['unattended-upgrades', 'security', 'patching', 'infrastructure', 'january-2026'],
  'federation'
);
```

---

## Rollback

If issues occur:
```bash
# Disable on Debian/Ubuntu
sudo dpkg-reconfigure -plow unattended-upgrades
# Select "No"

# Disable on Rocky
sudo systemctl disable --now dnf-automatic.timer
```

---

For Seven Generations.
