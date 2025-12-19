# Jr Build Instructions: Software CMDB Maintenance

**Priority**: MEDIUM (Ongoing)
**Phase**: 3 - Hardening & Packaging
**Assigned To**: IT Triad Jr
**Date**: December 13, 2025

## Objective

Maintain a complete Software Configuration Management Database (CMDB) for the Cherokee AI Federation, tracking all software, versions, and dependencies across all 6 nodes.

## Database Tables

### software_cmdb
Tracks all installed software across the federation:

| Column | Type | Description |
|--------|------|-------------|
| hostname | VARCHAR(50) | Node name (redfin, bluefin, etc.) |
| package_name | VARCHAR(200) | Software name |
| version | VARCHAR(100) | Installed version |
| package_type | VARCHAR(50) | apt, pip, npm, brew, systemd, custom |
| source | VARCHAR(200) | Repository or source URL |
| auto_update | BOOLEAN | Can be auto-updated |
| security_critical | BOOLEAN | Security-critical package |
| dependencies | TEXT[] | Package dependencies |
| config_files | TEXT[] | Configuration file paths |
| data_directories | TEXT[] | Data directory paths |

### software_repository
Tracks what's cached on greenfin for distribution:

| Column | Type | Description |
|--------|------|-------------|
| package_name | VARCHAR(200) | Package name |
| package_type | VARCHAR(50) | Package type |
| current_version | VARCHAR(100) | Latest version in cache |
| cached_versions | TEXT[] | All cached versions |
| local_path | TEXT | Path on greenfin |
| is_cached | BOOLEAN | Currently in cache |

### node_critical_apps
Already exists - tracks critical applications for patching decisions.

## Query Examples

### List all software on a node
```sql
SELECT package_name, version, package_type, security_critical, auto_update
FROM software_cmdb
WHERE hostname = 'redfin'
ORDER BY package_type, package_name;
```

### Find security-critical packages needing manual updates
```sql
SELECT hostname, package_name, version, package_type
FROM software_cmdb
WHERE security_critical = true AND auto_update = false
ORDER BY hostname;
```

### Check deployment status (what needs updates)
```sql
SELECT * FROM software_deployment_status
WHERE status = 'UPDATE AVAILABLE';
```

### Count software by type across federation
```sql
SELECT hostname, package_type, COUNT(*) as count
FROM software_cmdb
GROUP BY hostname, package_type
ORDER BY hostname, count DESC;
```

## Automated Discovery Scripts

### Discover apt packages (Linux nodes)
```bash
#!/bin/bash
# Run on each Linux node, insert into CMDB
HOSTNAME=$(hostname)
dpkg-query -W -f='${Package}|${Version}\n' | while IFS='|' read pkg ver; do
  echo "INSERT INTO software_cmdb (hostname, package_name, version, package_type)
        VALUES ('$HOSTNAME', '$pkg', '$ver', 'apt')
        ON CONFLICT (hostname, package_name, package_type) DO UPDATE SET version = '$ver';"
done
```

### Discover pip packages
```bash
#!/bin/bash
HOSTNAME=$(hostname)
pip3 list --format=freeze | while IFS='==' read pkg ver; do
  echo "INSERT INTO software_cmdb (hostname, package_name, version, package_type)
        VALUES ('$HOSTNAME', '$pkg', '$ver', 'pip')
        ON CONFLICT (hostname, package_name, package_type) DO UPDATE SET version = '$ver';"
done
```

### Discover systemd services
```bash
#!/bin/bash
HOSTNAME=$(hostname)
systemctl list-unit-files --type=service --state=enabled | grep -v '@' | tail -n +2 | head -n -1 | while read svc state preset; do
  echo "INSERT INTO software_cmdb (hostname, package_name, version, package_type)
        VALUES ('$HOSTNAME', '${svc%.service}', 'enabled', 'systemd')
        ON CONFLICT (hostname, package_name, package_type) DO NOTHING;"
done
```

### Discover Homebrew packages (macOS)
```bash
#!/bin/bash
HOSTNAME=$(hostname)
brew list --versions | while read pkg ver; do
  echo "INSERT INTO software_cmdb (hostname, package_name, version, package_type)
        VALUES ('$HOSTNAME', '$pkg', '$ver', 'brew')
        ON CONFLICT (hostname, package_name, package_type) DO UPDATE SET version = '$ver';"
done
```

## Update Procedures

### Add New Software to CMDB
When installing new software:

```sql
INSERT INTO software_cmdb (
  hostname, package_name, version, package_type,
  security_critical, auto_update, notes
) VALUES (
  'redfin', 'new-package', '1.0.0', 'apt',
  false, true, 'Installed for feature X'
);
```

### Update Version After Patching
```sql
UPDATE software_cmdb
SET version = '1.1.0', last_updated = now()
WHERE hostname = 'redfin' AND package_name = 'some-package';
```

### Mark Package as Security Critical
```sql
UPDATE software_cmdb
SET security_critical = true, auto_update = false
WHERE package_name = 'openssl';
```

### Remove Deprecated Software
```sql
DELETE FROM software_cmdb
WHERE hostname = 'redfin' AND package_name = 'old-package';
```

## Integration with Patching

The intelligent patching playbook queries the CMDB:

```yaml
# In patch_nodes_intelligent.yml
- name: Query software needing updates
  shell: |
    PGPASSWORD=jawaseatlasers2 psql -h {{ postgres_host }} -U {{ postgres_user }} -d {{ postgres_db }} -t -A -c "
    SELECT package_name FROM software_cmdb
    WHERE hostname = '{{ inventory_hostname }}'
      AND auto_update = true
      AND security_critical = false;
    "
```

## Thermal Memory Integration

Log CMDB updates to thermal memory:

```sql
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score)
VALUES (
  'CMDB-UPDATE-' || to_char(now(), 'YYYYMMDDHH24MI'),
  'Software CMDB updated: [list changes here]',
  'FRESH',
  75.0
);
```

## Scheduled Tasks

### Weekly CMDB Audit
Add to cron on bluefin:

```bash
# Weekly CMDB audit - Sundays at 1 AM
0 1 * * 0 /ganuda/scripts/cmdb_audit.sh >> /var/log/ganuda/cmdb_audit.log 2>&1
```

### cmdb_audit.sh
```bash
#!/bin/bash
# Audit CMDB against actual installed software

NODES="redfin bluefin greenfin"
for NODE in $NODES; do
  echo "=== Auditing $NODE ==="
  ssh dereadi@$NODE "dpkg-query -W -f='\${Package}\n'" > /tmp/${NODE}_actual.txt
  PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -t -A -c \
    "SELECT package_name FROM software_cmdb WHERE hostname='$NODE' AND package_type='apt'" > /tmp/${NODE}_cmdb.txt

  echo "Packages in CMDB but not installed:"
  comm -23 <(sort /tmp/${NODE}_cmdb.txt) <(sort /tmp/${NODE}_actual.txt)

  echo "Packages installed but not in CMDB:"
  comm -13 <(sort /tmp/${NODE}_cmdb.txt) <(sort /tmp/${NODE}_actual.txt) | head -20
done
```

## Current CMDB Status (as of December 13, 2025)

| Node | Total Packages | Security Critical | Auto-Update |
|------|----------------|-------------------|-------------|
| redfin | 14 | 4 | 10 |
| bluefin | 10 | 4 | 9 |
| greenfin | 5 | 2 | 4 |
| sasass | 4 | 0 | 4 |
| sasass2 | 3 | 0 | 3 |

## Success Criteria

- [ ] All nodes have software inventory in CMDB
- [ ] Security-critical packages identified and flagged
- [ ] Auto-update policies defined per package
- [ ] Integration with patching playbooks working
- [ ] Weekly audit script running
- [ ] Thermal memory logging implemented

---

FOR SEVEN GENERATIONS - Complete software inventory enables consistent deployments.
