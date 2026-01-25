# Jr Instruction: Software Inventory and Version Compliance Audit

**Date**: January 11, 2026
**Priority**: HIGH
**Target Nodes**: All Federation nodes
**TPM**: Flying Squirrel (dereadi)
**Council Approval**: ULTRATHINK 7f3a91c2d8e4b5f0
**Council Consultation**: January 11, 2026 - Recommends osquery agents over shell scripts

---

## Problem

We need continuous visibility into:
1. What software is installed on each node
2. What version is running
3. Whether newer versions are available
4. Which nodes need patching

Currently this is manual and inconsistent.

---

## Solution

Build custom system using **osquery** for collection, store in our existing PostgreSQL, integrate with Ansible and Telegram.

**Why osquery (per Council recommendation):**
- Structured data collection (SQL-like queries)
- Scalable across many machines
- Built-in tables: `deb_packages`, `rpm_packages`, `homebrew_packages`, `python_packages`
- Security-focused design
- Integrates well with Ansible
- Works on Linux AND macOS

**Air-gap considerations:**
- Download osquery binaries to bluefin local mirror
- Distribute via Ansible from internal repo
- No external network calls needed after initial setup

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        bluefin (Hub)                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ PostgreSQL      │  │ Version Check   │  │ Council/Telegram│  │
│  │ software_       │  │ (compare to     │  │ Notification    │  │
│  │ inventory table │  │ apt-mirror)     │  │                 │  │
│  └────────▲────────┘  └────────▲────────┘  └────────▲────────┘  │
└───────────┼─────────────────────┼─────────────────────┼──────────┘
            │                     │                     │
            │    ┌────────────────┴─────────────────────┘
            │    │
     ┌──────┴────┴──────┐
     │  osquery-to-pg   │  (Custom Python: query osquery, write to PG)
     │  collector.py    │
     └──────────────────┘
            ▲
            │ (runs on each node)
            │
┌───────────┴───────────────────────────────────────────────────────┐
│                         All Nodes                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ osqueryi │  │ osqueryi │  │ osqueryi │  │ osqueryi │           │
│  │ redfin   │  │ greenfin │  │ goldfin  │  │ sasass*  │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└───────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Database Schema

### Create tables on bluefin (192.168.132.222)

```sql
-- Software inventory table
CREATE TABLE IF NOT EXISTS software_inventory (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    node_name VARCHAR(50) NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    installed_version VARCHAR(100),
    latest_version VARCHAR(100),
    version_status VARCHAR(20) DEFAULT 'unknown', -- current, outdated, unknown
    package_manager VARCHAR(20), -- apt, dnf, brew, pip, npm
    is_critical BOOLEAN DEFAULT FALSE,
    last_checked TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(node_name, package_name, package_manager)
);

-- Critical packages to track (beyond system packages)
CREATE TABLE IF NOT EXISTS tracked_packages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    package_name VARCHAR(255) NOT NULL,
    package_manager VARCHAR(20) NOT NULL,
    description TEXT,
    is_critical BOOLEAN DEFAULT TRUE,
    check_frequency VARCHAR(20) DEFAULT 'daily', -- daily, weekly, hourly
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(package_name, package_manager)
);

-- Patch schedule queue
CREATE TABLE IF NOT EXISTS patch_queue (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    node_name VARCHAR(50) NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    current_version VARCHAR(100),
    target_version VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'normal', -- critical, high, normal, low
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, scheduled, completed, failed
    council_notified BOOLEAN DEFAULT FALSE,
    council_approved BOOLEAN DEFAULT FALSE,
    scheduled_time TIMESTAMP,
    completed_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_inventory_node ON software_inventory(node_name);
CREATE INDEX idx_inventory_status ON software_inventory(version_status);
CREATE INDEX idx_patch_queue_status ON patch_queue(status);
```

### Seed critical packages to track

```sql
INSERT INTO tracked_packages (package_name, package_manager, description, is_critical) VALUES
-- System packages
('postgresql', 'apt', 'PostgreSQL database server', TRUE),
('postgresql', 'dnf', 'PostgreSQL database server', TRUE),
('nginx', 'apt', 'Web server', TRUE),
('nginx', 'dnf', 'Web server', TRUE),
('openssh-server', 'apt', 'SSH server', TRUE),
('openssh-server', 'dnf', 'SSH server', TRUE),

-- Python packages
('vllm', 'pip', 'LLM inference engine', TRUE),
('fastapi', 'pip', 'API framework', TRUE),
('uvicorn', 'pip', 'ASGI server', TRUE),
('psycopg2-binary', 'pip', 'PostgreSQL driver', TRUE),
('python-telegram-bot', 'pip', 'Telegram bot library', TRUE),

-- Security packages
('aide', 'apt', 'File integrity checker', TRUE),
('aide', 'dnf', 'File integrity checker', TRUE),
('fail2ban', 'apt', 'Intrusion prevention', TRUE),

-- Node.js (if used)
('pm2', 'npm', 'Process manager', FALSE),

-- Mac packages
('python', 'brew', 'Python interpreter', TRUE),
('postgresql', 'brew', 'PostgreSQL client', FALSE)
ON CONFLICT (package_name, package_manager) DO NOTHING;
```

---

## Phase 2: Install osquery on All Nodes

### Download osquery to local mirror (bluefin)

```bash
# On bluefin - download osquery packages for air-gap distribution
mkdir -p /mnt/17tb/software-mirror/osquery

# Ubuntu/Debian
wget -O /mnt/17tb/software-mirror/osquery/osquery_5.11.0-1.linux_amd64.deb \
  https://pkg.osquery.io/deb/osquery_5.11.0-1.linux_amd64.deb

# Rocky/RHEL
wget -O /mnt/17tb/software-mirror/osquery/osquery-5.11.0-1.linux.x86_64.rpm \
  https://pkg.osquery.io/rpm/osquery-5.11.0-1.linux.x86_64.rpm

# macOS (pkg)
wget -O /mnt/17tb/software-mirror/osquery/osquery-5.11.0.pkg \
  https://pkg.osquery.io/darwin/osquery-5.11.0.pkg
```

### Ansible playbook to deploy osquery

```yaml
# playbooks/deploy-osquery.yml
---
- name: Deploy osquery to Federation nodes
  hosts: all
  become: yes
  vars:
    osquery_version: "5.11.0"
    mirror_url: "http://192.168.132.222:8888/osquery"

  tasks:
    - name: Download osquery (Debian/Ubuntu)
      get_url:
        url: "{{ mirror_url }}/osquery_{{ osquery_version }}-1.linux_amd64.deb"
        dest: "/tmp/osquery.deb"
      when: ansible_os_family == "Debian"

    - name: Install osquery (Debian/Ubuntu)
      apt:
        deb: "/tmp/osquery.deb"
      when: ansible_os_family == "Debian"

    - name: Download osquery (RedHat/Rocky)
      get_url:
        url: "{{ mirror_url }}/osquery-{{ osquery_version }}-1.linux.x86_64.rpm"
        dest: "/tmp/osquery.rpm"
      when: ansible_os_family == "RedHat"

    - name: Install osquery (RedHat/Rocky)
      dnf:
        name: "/tmp/osquery.rpm"
        disable_gpg_check: yes
      when: ansible_os_family == "RedHat"

    - name: Install osquery (macOS)
      shell: |
        curl -O {{ mirror_url }}/osquery-{{ osquery_version }}.pkg
        installer -pkg osquery-{{ osquery_version }}.pkg -target /
      args:
        chdir: /tmp
      when: ansible_os_family == "Darwin"
      become: no

    - name: Verify osquery installed
      command: osqueryi --version
      register: osquery_version_check
      changed_when: false

    - name: Display osquery version
      debug:
        msg: "osquery installed: {{ osquery_version_check.stdout }}"
```

---

## Phase 3: osquery Collection Script (Stealing from osquery tables)

### Create on each node: `/ganuda/scripts/osquery-inventory-collector.py`

This script uses osquery's built-in tables instead of custom parsing:

```python
#!/usr/bin/env python3
"""
osquery-based Software Inventory Collector
Cherokee AI Federation

Uses osquery's built-in tables:
- deb_packages (Debian/Ubuntu)
- rpm_packages (RedHat/Rocky)
- homebrew_packages (macOS)
- python_packages (all platforms)
- npm_packages (if Node.js installed)

Stolen from osquery's SQL interface - why reinvent the wheel?
"""

import subprocess
import json
import socket
import psycopg2
from datetime import datetime

HOSTNAME = socket.gethostname()

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# osquery queries for each package manager
OSQUERY_QUERIES = {
    'apt': "SELECT name, version, 'apt' as manager FROM deb_packages",
    'dnf': "SELECT name, version, 'dnf' as manager FROM rpm_packages",
    'brew': "SELECT name, version, 'brew' as manager FROM homebrew_packages",
    'pip': "SELECT name, version, 'pip' as manager FROM python_packages",
    'npm': "SELECT name, version, 'npm' as manager FROM npm_packages",
}

def run_osquery(query):
    """Execute osquery and return JSON results"""
    try:
        result = subprocess.run(
            ['osqueryi', '--json', query],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"osquery error: {e}")
    return []

def detect_package_managers():
    """Detect which package managers are available"""
    managers = []

    # Check OS type
    try:
        with open('/etc/os-release', 'r') as f:
            content = f.read().lower()
            if 'debian' in content or 'ubuntu' in content:
                managers.append('apt')
            elif 'rocky' in content or 'rhel' in content or 'centos' in content:
                managers.append('dnf')
    except FileNotFoundError:
        pass

    # macOS
    if subprocess.run(['which', 'brew'], capture_output=True).returncode == 0:
        managers.append('brew')

    # Always check pip and npm
    managers.extend(['pip', 'npm'])

    return managers

def collect_inventory():
    """Collect software inventory using osquery"""

    managers = detect_package_managers()
    all_packages = []

    for mgr in managers:
        if mgr in OSQUERY_QUERIES:
            print(f"Querying {mgr} packages via osquery...")
            packages = run_osquery(OSQUERY_QUERIES[mgr])
            for pkg in packages:
                all_packages.append({
                    'node': HOSTNAME,
                    'name': pkg.get('name', ''),
                    'version': pkg.get('version', ''),
                    'manager': mgr
                })
            print(f"  Found {len(packages)} {mgr} packages")

    return all_packages

def upload_to_database(packages):
    """Upload inventory to PostgreSQL"""

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Clear old entries for this node
    cur.execute("DELETE FROM software_inventory WHERE node_name = %s", (HOSTNAME,))

    # Insert new entries
    for pkg in packages:
        cur.execute("""
            INSERT INTO software_inventory
            (node_name, package_name, installed_version, package_manager, last_checked)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (node_name, package_name, package_manager)
            DO UPDATE SET
                installed_version = EXCLUDED.installed_version,
                last_checked = EXCLUDED.last_checked
        """, (
            pkg['node'],
            pkg['name'],
            pkg['version'],
            pkg['manager'],
            datetime.now()
        ))

    conn.commit()
    print(f"Uploaded {len(packages)} packages for {HOSTNAME}")

    cur.close()
    conn.close()

def main():
    print(f"=== osquery Inventory Collector: {HOSTNAME} ===")
    print(f"Time: {datetime.now().isoformat()}")

    packages = collect_inventory()

    if packages:
        upload_to_database(packages)
    else:
        print("No packages collected - check osquery installation")

if __name__ == "__main__":
    main()
```

### Create Python uploader: `/ganuda/scripts/upload-inventory.py`

```python
#!/usr/bin/env python3
"""
Upload software inventory to hub database
Cherokee AI Federation
"""

import json
import socket
import psycopg2
from datetime import datetime

HOSTNAME = socket.gethostname()
INVENTORY_FILE = f"/tmp/software_inventory_{HOSTNAME}.json"

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def upload_inventory():
    """Upload local inventory to hub database"""

    # Load inventory
    with open(INVENTORY_FILE, 'r') as f:
        inventory = json.load(f)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Clear old entries for this node
    cur.execute("DELETE FROM software_inventory WHERE node_name = %s", (HOSTNAME,))

    # Insert new entries
    for pkg in inventory:
        cur.execute("""
            INSERT INTO software_inventory
            (node_name, package_name, installed_version, package_manager, last_checked)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (node_name, package_name, package_manager)
            DO UPDATE SET
                installed_version = EXCLUDED.installed_version,
                last_checked = EXCLUDED.last_checked
        """, (
            pkg['node'],
            pkg['pkg'],
            pkg['ver'],
            pkg['mgr'],
            datetime.now()
        ))

    conn.commit()
    print(f"Uploaded {len(inventory)} packages for {HOSTNAME}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    upload_inventory()
```

---

## Phase 3: Version Check Script (Run on bluefin)

### Create: `/ganuda/scripts/check-version-updates.py`

```python
#!/usr/bin/env python3
"""
Check installed software versions against latest available
Cherokee AI Federation
"""

import subprocess
import psycopg2
import requests
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def get_latest_apt_version(package):
    """Get latest version from apt repository"""
    try:
        result = subprocess.run(
            ['apt-cache', 'policy', package],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split('\n'):
            if 'Candidate:' in line:
                return line.split(':')[1].strip()
    except:
        pass
    return None

def get_latest_pip_version(package):
    """Get latest version from PyPI"""
    try:
        response = requests.get(
            f'https://pypi.org/pypi/{package}/json',
            timeout=10
        )
        if response.ok:
            return response.json()['info']['version']
    except:
        pass
    return None

def check_versions():
    """Check all tracked packages for updates"""

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get tracked packages with installed versions
    cur.execute("""
        SELECT DISTINCT si.node_name, si.package_name, si.installed_version,
               si.package_manager, tp.is_critical
        FROM software_inventory si
        JOIN tracked_packages tp
            ON si.package_name = tp.package_name
            AND si.package_manager = tp.package_manager
    """)

    updates_found = []

    for node, pkg, installed, mgr, critical in cur.fetchall():
        latest = None

        if mgr == 'apt':
            latest = get_latest_apt_version(pkg)
        elif mgr == 'pip':
            latest = get_latest_pip_version(pkg)
        # Add dnf, brew checks as needed

        if latest and latest != installed:
            updates_found.append({
                'node': node,
                'package': pkg,
                'installed': installed,
                'latest': latest,
                'critical': critical
            })

            # Update inventory
            cur.execute("""
                UPDATE software_inventory
                SET latest_version = %s,
                    version_status = 'outdated',
                    last_checked = %s
                WHERE node_name = %s
                  AND package_name = %s
                  AND package_manager = %s
            """, (latest, datetime.now(), node, pkg, mgr))

            # Add to patch queue
            cur.execute("""
                INSERT INTO patch_queue
                (node_name, package_name, current_version, target_version, priority)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                node, pkg, installed, latest,
                'critical' if critical else 'normal'
            ))

    conn.commit()
    cur.close()
    conn.close()

    return updates_found

if __name__ == "__main__":
    updates = check_versions()
    print(f"Found {len(updates)} packages needing updates")
    for u in updates:
        print(f"  {u['node']}: {u['package']} {u['installed']} -> {u['latest']}")
```

---

## Phase 4: Council Notification Script

### Create: `/ganuda/scripts/notify-council-updates.py`

```python
#!/usr/bin/env python3
"""
Notify Council of pending software updates
Cherokee AI Federation
"""

import psycopg2
import requests
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

GATEWAY_URL = "http://192.168.132.223:8080"
API_KEY = "ck-council-7148012bbfa9964e79857e1a7210841b"

TELEGRAM_BOT_TOKEN = ""  # Load from vault
TELEGRAM_CHAT_ID = ""    # TPM's chat ID

def notify_council():
    """Notify Council of pending updates and get approval"""

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get pending updates not yet notified
    cur.execute("""
        SELECT node_name, package_name, current_version, target_version, priority
        FROM patch_queue
        WHERE status = 'pending' AND council_notified = FALSE
        ORDER BY priority DESC, created_at ASC
    """)

    pending = cur.fetchall()

    if not pending:
        print("No pending updates to notify")
        return

    # Build notification message
    message = f"SOFTWARE UPDATE REVIEW REQUIRED - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    message += f"Found {len(pending)} package(s) requiring updates:\n\n"

    critical_count = 0
    by_node = {}

    for node, pkg, current, target, priority in pending:
        if node not in by_node:
            by_node[node] = []
        by_node[node].append({
            'pkg': pkg,
            'current': current,
            'target': target,
            'priority': priority
        })
        if priority == 'critical':
            critical_count += 1

    for node, packages in by_node.items():
        message += f"**{node}:**\n"
        for p in packages:
            flag = "🔴" if p['priority'] == 'critical' else "🟡"
            message += f"  {flag} {p['pkg']}: {p['current']} → {p['target']}\n"
        message += "\n"

    if critical_count > 0:
        message += f"\n⚠️ {critical_count} CRITICAL update(s) require immediate attention.\n"

    message += "\nReply with 'approve all' or specify nodes to patch."

    # Send to Council for vote
    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/council/vote",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "question": message,
                "max_tokens": 1000
            },
            timeout=120
        )

        if response.ok:
            result = response.json()
            print(f"Council notified. Audit hash: {result.get('audit_hash')}")

            # Mark as notified
            cur.execute("""
                UPDATE patch_queue
                SET council_notified = TRUE
                WHERE status = 'pending' AND council_notified = FALSE
            """)
            conn.commit()
    except Exception as e:
        print(f"Council notification failed: {e}")

    # Also send Telegram notification to TPM
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            telegram_msg = f"🔄 Software Updates Pending\n\n{len(pending)} packages need updates"
            if critical_count > 0:
                telegram_msg += f"\n🔴 {critical_count} CRITICAL"
            telegram_msg += "\n\nCouncil has been notified."

            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={
                    'chat_id': TELEGRAM_CHAT_ID,
                    'text': telegram_msg
                }
            )
        except:
            pass

    cur.close()
    conn.close()

if __name__ == "__main__":
    notify_council()
```

---

## Phase 5: Daily Cron Jobs

### On each node (collect inventory)
```bash
# /etc/cron.d/software-inventory
0 4 * * * root /ganuda/scripts/collect-software-inventory.sh && python3 /ganuda/scripts/upload-inventory.py
```

### On bluefin (check versions and notify)
```bash
# /etc/cron.d/version-check
30 4 * * * dereadi python3 /ganuda/scripts/check-version-updates.py
0 5 * * * dereadi python3 /ganuda/scripts/notify-council-updates.py
```

---

## Phase 6: Ansible Integration

### Create playbook: `playbooks/apply-approved-patches.yml`

```yaml
---
# Apply approved patches from patch_queue
- name: Apply Approved Software Updates
  hosts: all
  become: yes
  vars:
    db_host: 192.168.132.222
    db_user: claude
    db_pass: jawaseatlasers2
    db_name: triad_federation

  tasks:
    - name: Get approved patches for this node
      shell: |
        PGPASSWORD={{ db_pass }} psql -h {{ db_host }} -U {{ db_user }} -d {{ db_name }} -t -A -c "
        SELECT package_name, target_version
        FROM patch_queue
        WHERE node_name = '{{ inventory_hostname }}'
          AND status = 'approved'
          AND council_approved = TRUE
        "
      register: approved_patches
      delegate_to: localhost

    - name: Apply apt patches
      apt:
        name: "{{ item.split('|')[0] }}={{ item.split('|')[1] }}"
        state: present
      loop: "{{ approved_patches.stdout_lines }}"
      when: ansible_os_family == "Debian"

    - name: Mark patches as completed
      shell: |
        PGPASSWORD={{ db_pass }} psql -h {{ db_host }} -U {{ db_user }} -d {{ db_name }} -c "
        UPDATE patch_queue
        SET status = 'completed', completed_time = NOW()
        WHERE node_name = '{{ inventory_hostname }}'
          AND status = 'approved'
        "
      delegate_to: localhost
```

---

## Verification Queries

```sql
-- Check inventory status
SELECT node_name, COUNT(*) as packages,
       MAX(last_checked) as last_check
FROM software_inventory
GROUP BY node_name;

-- Find outdated packages
SELECT node_name, package_name, installed_version, latest_version
FROM software_inventory
WHERE version_status = 'outdated';

-- View patch queue
SELECT node_name, package_name, current_version, target_version,
       priority, status, council_approved
FROM patch_queue
ORDER BY priority DESC, created_at;

-- Pending Council approval
SELECT * FROM patch_queue
WHERE council_notified = TRUE
  AND council_approved = FALSE;
```

---

## Thermal Memory Archive

After implementation:
```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'SOFTWARE INVENTORY AND VERSION COMPLIANCE SYSTEM - January 2026

  Tables created:
  - software_inventory: Per-node package inventory
  - tracked_packages: Critical packages to monitor
  - patch_queue: Updates pending approval

  Daily process:
  1. 4:00 AM - Each node collects inventory
  2. 4:30 AM - bluefin checks versions against repos
  3. 5:00 AM - Council notified of pending updates
  4. TPM approves via Telegram or Council vote
  5. Ansible applies approved patches

  Scripts:
  - /ganuda/scripts/collect-software-inventory.sh
  - /ganuda/scripts/upload-inventory.py
  - /ganuda/scripts/check-version-updates.py
  - /ganuda/scripts/notify-council-updates.py

  For Seven Generations.',
  92, 'it_triad_jr',
  ARRAY['software-inventory', 'patching', 'compliance', 'audit', 'january-2026'],
  'federation'
);
```

---

## Related

- JR-UNATTENDED-UPGRADES-LINUX-JAN11-2026.md (auto security patches)
- JR-APT-MIRROR-BLUEFIN-JAN11-2026.md (local repository)
- KB-TELEGRAM-VAULT-003.md (notification credentials)

---

For Seven Generations.
