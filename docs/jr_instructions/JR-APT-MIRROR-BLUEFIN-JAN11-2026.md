# Jr Instruction: Federated Software Repository on bluefin

**Date**: January 11, 2026
**Priority**: HIGH
**Target Node**: bluefin (17TB drive)
**TPM**: Flying Squirrel (dereadi)
**Council Approval**: ULTRATHINK 7f3a91c2d8e4b5f0

## Problem

All Linux nodes pull packages directly from internet repositories. This creates:
- Internet dependency (against air-gap mission)
- Bandwidth waste (same packages downloaded multiple times)
- No control over package versions
- Risk of upstream repo compromise

## Solution

Set up apt-mirror on bluefin's 17TB drive to create a federated software repository for:
- Ubuntu (bluefin, redfin, greenfin)
- Rocky Linux (goldfin, future silverfin)

---

## Prerequisites

- bluefin 17TB drive mounted (verify: `df -h | grep 17T`)
- Network access from all nodes to bluefin
- Approximately 500GB-1TB space needed for mirrors

---

## Phase 1: Install apt-mirror

```bash
# On bluefin
sudo apt install -y apt-mirror nginx

# Create mirror directory structure
sudo mkdir -p /mnt/17tb/apt-mirror/{mirror,skel,var}
sudo chown -R apt-mirror:apt-mirror /mnt/17tb/apt-mirror
```

---

## Phase 2: Configure apt-mirror

```bash
sudo tee /etc/apt/mirror.list << 'EOF'
############# config #############
set base_path    /mnt/17tb/apt-mirror
set mirror_path  $base_path/mirror
set skel_path    $base_path/skel
set var_path     $base_path/var
set postmirror_script $var_path/postmirror.sh
set run_postmirror 0
set nthreads     20
set _tilde 0

############# Ubuntu 22.04 (jammy) #############
deb http://archive.ubuntu.com/ubuntu jammy main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu jammy-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu jammy-security main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse

############# Ubuntu 24.04 (noble) - if needed #############
# deb http://archive.ubuntu.com/ubuntu noble main restricted universe multiverse
# deb http://archive.ubuntu.com/ubuntu noble-updates main restricted universe multiverse
# deb http://archive.ubuntu.com/ubuntu noble-security main restricted universe multiverse

############# Clean up old packages #############
clean http://archive.ubuntu.com/ubuntu
EOF
```

---

## Phase 3: Configure nginx to serve mirror

```bash
sudo tee /etc/nginx/sites-available/apt-mirror << 'EOF'
server {
    listen 8888;
    server_name bluefin.cherokee.local;

    root /mnt/17tb/apt-mirror/mirror;

    location / {
        autoindex on;
    }

    # Access logging for audit
    access_log /var/log/nginx/apt-mirror-access.log;
    error_log /var/log/nginx/apt-mirror-error.log;
}
EOF

sudo ln -sf /etc/nginx/sites-available/apt-mirror /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## Phase 4: Initial Mirror Sync

```bash
# This will take several hours and download ~300-500GB
# Run in tmux/screen!
tmux new -s apt-mirror
sudo su - apt-mirror -c apt-mirror

# Or run in background with logging
sudo su - apt-mirror -c "apt-mirror 2>&1 | tee /mnt/17tb/apt-mirror/var/sync-$(date +%Y%m%d).log" &
```

---

## Phase 5: Schedule Daily Sync

```bash
# Add to apt-mirror user's crontab
sudo tee /etc/cron.d/apt-mirror-sync << 'EOF'
# Mirror sync at 2 AM daily
0 2 * * * apt-mirror /usr/bin/apt-mirror >> /mnt/17tb/apt-mirror/var/cron.log 2>&1
EOF
```

---

## Phase 6: Configure Client Nodes

### Ubuntu nodes (redfin, greenfin)

```bash
# Backup original sources
sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup

# Point to bluefin mirror
sudo tee /etc/apt/sources.list << 'EOF'
# Cherokee AI Federation Local Mirror
deb http://192.168.132.222:8888/archive.ubuntu.com/ubuntu jammy main restricted universe multiverse
deb http://192.168.132.222:8888/archive.ubuntu.com/ubuntu jammy-updates main restricted universe multiverse
deb http://192.168.132.222:8888/archive.ubuntu.com/ubuntu jammy-security main restricted universe multiverse
deb http://192.168.132.222:8888/archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse
EOF

# Test
sudo apt update
```

### Fallback Configuration (if mirror unavailable)

```bash
# Create fallback script
sudo tee /usr/local/bin/apt-source-fallback << 'EOF'
#!/bin/bash
# Check if local mirror is available, fallback to internet if not

if curl -s --connect-timeout 5 http://192.168.132.222:8888/ > /dev/null; then
    echo "Using local mirror"
    cp /etc/apt/sources.list.local /etc/apt/sources.list
else
    echo "Falling back to internet"
    cp /etc/apt/sources.list.backup /etc/apt/sources.list
fi
EOF
sudo chmod +x /usr/local/bin/apt-source-fallback
```

---

## Phase 7: Rocky Linux Mirror (for goldfin)

```bash
# On bluefin, also mirror Rocky repos
sudo dnf install -y createrepo rsync

# Create Rocky mirror directory
sudo mkdir -p /mnt/17tb/rocky-mirror/9/{BaseOS,AppStream,extras}

# Create sync script
sudo tee /ganuda/scripts/rocky-mirror-sync.sh << 'EOF'
#!/bin/bash
# Rocky Linux 9 Mirror Sync

MIRROR_BASE="/mnt/17tb/rocky-mirror/9"
UPSTREAM="rsync://mirror.facebook.net/rocky/9"

rsync -avz --delete ${UPSTREAM}/BaseOS/ ${MIRROR_BASE}/BaseOS/
rsync -avz --delete ${UPSTREAM}/AppStream/ ${MIRROR_BASE}/AppStream/
rsync -avz --delete ${UPSTREAM}/extras/ ${MIRROR_BASE}/extras/

# Update repo metadata
createrepo --update ${MIRROR_BASE}/BaseOS/
createrepo --update ${MIRROR_BASE}/AppStream/
createrepo --update ${MIRROR_BASE}/extras/
EOF

sudo chmod +x /ganuda/scripts/rocky-mirror-sync.sh

# Add nginx location for Rocky
sudo tee -a /etc/nginx/sites-available/apt-mirror << 'EOF'

server {
    listen 8889;
    server_name bluefin.cherokee.local;

    root /mnt/17tb/rocky-mirror;

    location / {
        autoindex on;
    }

    access_log /var/log/nginx/rocky-mirror-access.log;
}
EOF

sudo nginx -t && sudo systemctl reload nginx
```

### Configure goldfin to use local Rocky mirror

```bash
# On goldfin
sudo tee /etc/yum.repos.d/cherokee-local.repo << 'EOF'
[cherokee-baseos]
name=Cherokee Local - BaseOS
baseurl=http://192.168.132.222:8889/9/BaseOS/
enabled=1
gpgcheck=0
priority=1

[cherokee-appstream]
name=Cherokee Local - AppStream
baseurl=http://192.168.132.222:8889/9/AppStream/
enabled=1
gpgcheck=0
priority=1
EOF

# Disable default repos (optional, for full air-gap)
# sudo dnf config-manager --disable baseos appstream extras
```

---

## Verification

```bash
# Check mirror size
du -sh /mnt/17tb/apt-mirror/

# Check nginx serving
curl -I http://192.168.132.222:8888/

# Test from client node
apt update
apt-cache policy nginx  # Should show local mirror URL
```

---

## Storage Estimate

| Repository | Estimated Size |
|------------|---------------|
| Ubuntu 22.04 (all components) | ~300GB |
| Ubuntu 24.04 (if added) | ~300GB |
| Rocky 9 (BaseOS+AppStream) | ~50GB |
| **Total** | **~650GB** |

17TB drive has plenty of room for future expansion.

---

## Thermal Memory Archive

After setup:
```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'FEDERATED SOFTWARE REPOSITORY ESTABLISHED - January 11, 2026

  Location: bluefin:/mnt/17tb/apt-mirror/

  Mirrors configured:
  - Ubuntu 22.04 (jammy): http://192.168.132.222:8888/
  - Rocky 9: http://192.168.132.222:8889/

  Client nodes configured:
  - redfin: pointing to local mirror
  - greenfin: pointing to local mirror
  - goldfin: pointing to local mirror

  Sync schedule: Daily at 2 AM

  Air-gap capability: Nodes can operate without internet for updates.

  For Seven Generations.',
  91, 'it_triad_jr',
  ARRAY['apt-mirror', 'repository', 'infrastructure', 'air-gap', 'january-2026'],
  'federation'
);
```

---

For Seven Generations.
