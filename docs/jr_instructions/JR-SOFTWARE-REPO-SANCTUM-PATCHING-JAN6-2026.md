# Jr Task: Software Repository for Sanctum VLAN Patching

**Date**: January 6, 2026
**Priority**: HIGH
**Storage**: bluefin (192.168.132.222)
**Management**: greenfin (192.168.132.224) via Ansible
**TPM**: Flying Squirrel (dereadi)

## Background

Sanctum VLANs (goldfin/silverfin) are air-gapped by design - no internet access.
We need a local package repository for security patching.

### Architecture
```
Internet → greenfin (sync) → bluefin (repo storage) → Sanctum nodes (pull)
                ↓
           Ansible pushes
```

## Phase 1: Set Up apt-mirror on bluefin

### Task 1.1: Install apt-mirror

```bash
# On bluefin
sudo apt update
sudo apt install apt-mirror apache2 -y
```

### Task 1.2: Configure apt-mirror

```bash
# /etc/apt/mirror.list
set base_path    /ganuda/repo/apt-mirror
set nthreads     10
set _tilde       0

# Ubuntu 22.04 LTS (jammy) - Main repos only for minimal footprint
deb http://archive.ubuntu.com/ubuntu jammy main restricted universe
deb http://archive.ubuntu.com/ubuntu jammy-updates main restricted universe
deb http://archive.ubuntu.com/ubuntu jammy-security main restricted universe

# Skip source packages to save space
# deb-src lines omitted

clean http://archive.ubuntu.com/ubuntu
```

### Task 1.3: Create Directory Structure

```bash
# On bluefin
sudo mkdir -p /ganuda/repo/apt-mirror
sudo chown -R dereadi:dereadi /ganuda/repo
```

### Task 1.4: Initial Sync (Run on greenfin, stores on bluefin)

```bash
# On greenfin - SSH to bluefin and run mirror
ssh bluefin "sudo apt-mirror"

# This will take a while - Ubuntu repos are ~100GB for main/restricted/universe
# Consider starting with just main + security (~30GB)
```

### Task 1.5: Serve Repo via Apache

```bash
# On bluefin - /etc/apache2/sites-available/apt-repo.conf
<VirtualHost *:80>
    ServerName repo.cherokee.local
    DocumentRoot /ganuda/repo/apt-mirror/mirror

    <Directory /ganuda/repo/apt-mirror/mirror>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/apt-repo-error.log
    CustomLog ${APACHE_LOG_DIR}/apt-repo-access.log combined
</VirtualHost>
```

```bash
sudo a2ensite apt-repo
sudo systemctl reload apache2
```

---

## Phase 2: Configure Sanctum Nodes to Use Local Repo

### Task 2.1: Create sources.list for Sanctum

```bash
# /etc/apt/sources.list on silverfin/goldfin
# Local Cherokee AI Federation Repository
deb http://192.168.132.222/ubuntu jammy main restricted universe
deb http://192.168.132.222/ubuntu jammy-updates main restricted universe
deb http://192.168.132.222/ubuntu jammy-security main restricted universe
```

### Task 2.2: Ansible Playbook for Repo Config

Create `/ganuda/ansible/playbooks/configure_local_repo.yml`:

```yaml
---
- name: Configure Sanctum nodes to use local apt repository
  hosts: sanctum
  become: yes
  vars:
    repo_server: "192.168.132.222"
    ubuntu_codename: "jammy"

  tasks:
    - name: Backup original sources.list
      copy:
        src: /etc/apt/sources.list
        dest: /etc/apt/sources.list.backup
        remote_src: yes
        force: no

    - name: Configure local repository
      template:
        src: templates/sanctum_sources.list.j2
        dest: /etc/apt/sources.list
        mode: '0644'

    - name: Update apt cache
      apt:
        update_cache: yes

    - name: Verify repository connectivity
      command: apt-cache policy
      register: apt_policy
      changed_when: false

    - name: Display repo status
      debug:
        var: apt_policy.stdout_lines
```

### Task 2.3: Update Ansible Inventory

Add to `/ganuda/ansible/inventory_federation.ini`:

```ini
[sanctum]
silverfin ansible_host=192.168.10.10 ansible_user=dereadi
goldfin ansible_host=192.168.20.10 ansible_user=dereadi

[sanctum:vars]
# No internet - use local repo
ansible_python_interpreter=/usr/bin/python3
```

---

## Phase 3: Automated Sync Schedule

### Task 3.1: Cron Job on greenfin for Mirror Sync

```bash
# /etc/cron.d/apt-mirror-sync
# Sync Ubuntu repos every Sunday at 2 AM
0 2 * * 0 dereadi ssh bluefin "sudo apt-mirror" >> /var/log/ganuda/apt-mirror-sync.log 2>&1
```

### Task 3.2: Sync Notification to Thermal Memory

```bash
#!/bin/bash
# /ganuda/scripts/apt-mirror-notify.sh
# Run after apt-mirror completes

SYNC_DATE=$(date +%Y-%m-%d)
REPO_SIZE=$(du -sh /ganuda/repo/apt-mirror/mirror | cut -f1)

psql -h 192.168.132.222 -U claude -d zammad_production << EOF
INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, tags, source_triad, source_node, memory_type)
VALUES (
    md5('apt_mirror_sync_${SYNC_DATE}'),
    'APT MIRROR SYNC - ${SYNC_DATE}\nRepo size: ${REPO_SIZE}\nSynced to bluefin:/ganuda/repo/apt-mirror',
    50.0,
    ARRAY['apt-mirror', 'patching', 'sync'],
    'ops',
    'greenfin',
    'operations'
) ON CONFLICT (memory_hash) DO UPDATE SET temperature_score = 50.0;
EOF
```

---

## Phase 4: Ansible Patching Playbook for Sanctum

### Task 4.1: Create Sanctum Patch Playbook

Create `/ganuda/ansible/playbooks/patch_sanctum.yml`:

```yaml
---
- name: Patch Sanctum nodes from local repository
  hosts: sanctum
  become: yes
  serial: 1  # One node at a time

  tasks:
    - name: Update apt cache from local repo
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Check for available updates
      command: apt list --upgradable
      register: updates_available
      changed_when: false

    - name: Display available updates
      debug:
        var: updates_available.stdout_lines

    - name: Apply security updates only
      apt:
        upgrade: safe
        update_cache: yes
      register: upgrade_result

    - name: Check if reboot required
      stat:
        path: /var/run/reboot-required
      register: reboot_required

    - name: Notify if reboot needed
      debug:
        msg: "REBOOT REQUIRED on {{ inventory_hostname }}"
      when: reboot_required.stat.exists

    - name: Log patch result to thermal memory
      shell: |
        psql -h 192.168.132.222 -U claude -d zammad_production -c "
        INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, tags, source_triad, source_node, memory_type)
        VALUES (
            md5('patch_{{ inventory_hostname }}_{{ ansible_date_time.date }}'),
            'PATCH APPLIED - {{ inventory_hostname }} - {{ ansible_date_time.date }}',
            70.0,
            ARRAY['patching', 'security', '{{ inventory_hostname }}'],
            'ops',
            'greenfin',
            'operations'
        ) ON CONFLICT (memory_hash) DO UPDATE SET temperature_score = 70.0;"
      delegate_to: greenfin
      when: upgrade_result.changed
```

---

## Phase 5: Network Connectivity for Patching

Since Sanctum VLANs are isolated, we have two options:

### Option A: Temporary VLAN Trunk (Recommended)

Use a trunk port on the switch to allow greenfin temporary access:
1. Configure port 17 as trunk with VLANs 1, 10, 20 tagged
2. greenfin gets secondary IPs: 192.168.10.1, 192.168.20.1
3. Ansible connects via these IPs
4. After patching, remove trunk or disable secondary IPs

### Option B: USB Sneakernet

For highest security:
1. Download packages on greenfin: `apt download <package>`
2. Copy to USB drive
3. Physically transfer to silverfin/goldfin
4. Install: `sudo dpkg -i *.deb`

### Option C: Dedicated Patch Cable

1. Direct ethernet from greenfin to each Sanctum node (one at a time)
2. Configure temporary IP on greenfin in that subnet
3. Push updates
4. Disconnect

---

## Verification Checklist

- [ ] apt-mirror installed on bluefin
- [ ] Mirror config created at /etc/apt/mirror.list
- [ ] Initial sync completed (~30-100GB)
- [ ] Apache serving repo at http://192.168.132.222/ubuntu
- [ ] Sanctum nodes configured with local sources.list
- [ ] Ansible inventory updated with sanctum group
- [ ] patch_sanctum.yml playbook created
- [ ] Cron job for weekly sync
- [ ] Network path for patching determined

---

## Storage Requirements

| Component | Size Estimate |
|-----------|---------------|
| Ubuntu main | ~15 GB |
| Ubuntu restricted | ~1 GB |
| Ubuntu universe | ~50 GB |
| Ubuntu security | ~5 GB |
| **Total (main+security only)** | **~20 GB** |
| **Total (full)** | **~70 GB** |

Recommend starting with main + security only for Sanctum nodes.

---

## For Seven Generations
