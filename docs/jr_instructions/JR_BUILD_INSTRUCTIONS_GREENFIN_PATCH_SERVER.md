# Jr Build Instructions: Federation Patching Server (Split Architecture)

**Priority**: HIGH
**Phase**: 3 - Hardening & Packaging
**Assigned To**: IT Triad Jr
**Date**: December 13, 2025

## Objective

Configure a split-architecture patching server:
- **greenfin (192.168.132.224)** - Runs apt-cacher-ng service (CPU/network load)
- **redfin (192.168.132.223)** - Hosts repository storage on `/sag_data` (1.1TB available)

This offloads CPU from redfin (GPU node) while utilizing its large storage.

## Architecture

```
Internet (apt repos)
        │
        ▼
┌─────────────────┐
│   greenfin      │  ◄── apt-cacher-ng service (port 3142)
│ 192.168.132.224 │      Proxy/caching logic
└────────┬────────┘
         │
         │ NFS mount
         ▼
┌─────────────────┐
│   redfin        │  ◄── /sag_data/apt-cache (1.1TB storage)
│ 192.168.132.223 │      Repository storage only
└─────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
 bluefin   sasass/sasass2
  .222      .241/.242
```

## Step 1: Create Repository Directory on Redfin

```bash
ssh dereadi@192.168.132.223

# Create cache directory on the 1.1TB /sag_data partition
sudo mkdir -p /sag_data/apt-cache
sudo chown nobody:nogroup /sag_data/apt-cache
sudo chmod 755 /sag_data/apt-cache

# Verify space
df -h /sag_data
```

## Step 2: Configure NFS Export on Redfin

```bash
ssh dereadi@192.168.132.223

# Install NFS server if not present
sudo apt install nfs-kernel-server -y

# Add export for greenfin
echo '/sag_data/apt-cache 192.168.132.224(rw,sync,no_subtree_check,no_root_squash)' | sudo tee -a /etc/exports

# Apply exports
sudo exportfs -ra

# Verify
sudo exportfs -v
```

## Step 3: Mount NFS on Greenfin

```bash
ssh dereadi@192.168.132.224

# Install NFS client
sudo apt install nfs-common -y

# Create mount point
sudo mkdir -p /var/cache/apt-cacher-ng

# Test mount
sudo mount -t nfs 192.168.132.223:/sag_data/apt-cache /var/cache/apt-cacher-ng

# Verify
df -h /var/cache/apt-cacher-ng

# Make permanent - add to fstab
echo '192.168.132.223:/sag_data/apt-cache /var/cache/apt-cacher-ng nfs defaults,_netdev 0 0' | sudo tee -a /etc/fstab
```

## Step 4: Install apt-cacher-ng on Greenfin

```bash
ssh dereadi@192.168.132.224

# Install apt-cacher-ng
sudo apt update
sudo apt install apt-cacher-ng -y

# Verify service is running
sudo systemctl status apt-cacher-ng
sudo systemctl enable apt-cacher-ng
```

## Step 5: Configure apt-cacher-ng on Greenfin

Edit `/etc/apt-cacher-ng/acng.conf`:

```bash
sudo vim /etc/apt-cacher-ng/acng.conf
```

Key settings:

```ini
# Cache directory (NFS mounted from redfin)
CacheDir: /var/cache/apt-cacher-ng

# Log directory (keep local on greenfin)
LogDir: /var/log/apt-cacher-ng

# Port
Port: 3142

# Allow all federation IPs
BindAddress: 0.0.0.0

# Keep packages for 30 days after last access
ExThreshold: 30

# Enable Ubuntu repos
Remap-ubuntu: file:ubuntu_mirrors

# Enable Debian repos (if needed)
Remap-debrep: file:backends_debian
```

Restart after changes:
```bash
sudo systemctl restart apt-cacher-ng
```

## Step 6: Configure Client Nodes

On bluefin (redfin uses local packages):

```bash
# On bluefin (192.168.132.222)
ssh dereadi@192.168.132.222
echo 'Acquire::http::Proxy "http://192.168.132.224:3142";' | sudo tee /etc/apt/apt.conf.d/02proxy

# On greenfin itself (uses local cache)
ssh dereadi@192.168.132.224
echo 'Acquire::http::Proxy "http://127.0.0.1:3142";' | sudo tee /etc/apt/apt.conf.d/02proxy
```

**Note**: redfin can optionally use the proxy or download directly since it hosts the storage.

## Step 7: Test the Setup

```bash
# On bluefin, update and install a test package
ssh dereadi@192.168.132.222
sudo apt update
sudo apt install htop -y --reinstall

# Check cache on redfin
ssh dereadi@192.168.132.223
ls -la /sag_data/apt-cache/
du -sh /sag_data/apt-cache/

# Check apt-cacher-ng logs on greenfin
ssh dereadi@192.168.132.224
tail -f /var/log/apt-cacher-ng/apt-cacher.log
```

## Step 8: Monitor Cache

apt-cacher-ng web interface on greenfin:

```
http://192.168.132.224:3142/acng-report.html
```

Shows:
- Cache hit ratio
- Bandwidth saved
- Package statistics

## Step 9: Firewall Rules

```bash
# On greenfin - allow apt-cacher-ng
sudo ufw allow from 192.168.132.0/24 to any port 3142 proto tcp comment 'apt-cacher-ng'
sudo ufw reload

# On redfin - allow NFS from greenfin
sudo ufw allow from 192.168.132.224 to any port 2049 proto tcp comment 'NFS for apt-cache'
sudo ufw allow from 192.168.132.224 to any port 111 proto tcp comment 'NFS portmapper'
sudo ufw reload
```

## Step 10: Update Software Repository Table

```sql
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production << 'EOSQL'
-- Record split architecture
INSERT INTO software_repository (package_name, package_type, repository_url, local_path, is_cached, notes)
VALUES
('apt-cacher-ng', 'service', 'http://192.168.132.224:3142', '/var/cache/apt-cacher-ng', true, 'Greenfin runs service, storage on redfin /sag_data/apt-cache via NFS'),
('ubuntu-noble', 'repo', 'http://archive.ubuntu.com/ubuntu', 'http://192.168.132.224:3142/archive.ubuntu.com/ubuntu', true, 'Ubuntu 24.04 packages via greenfin proxy'),
('ubuntu-security', 'repo', 'http://security.ubuntu.com/ubuntu', 'http://192.168.132.224:3142/security.ubuntu.com/ubuntu', true, 'Ubuntu security updates via greenfin proxy')
ON CONFLICT (package_name, package_type) DO UPDATE SET local_path = EXCLUDED.local_path, notes = EXCLUDED.notes;
EOSQL
```

## Verification Checklist

- [ ] `/sag_data/apt-cache` created on redfin with proper permissions
- [ ] NFS export configured on redfin
- [ ] NFS mount working on greenfin at `/var/cache/apt-cacher-ng`
- [ ] NFS mount added to greenfin's `/etc/fstab`
- [ ] apt-cacher-ng installed and running on greenfin
- [ ] Port 3142 accessible from federation nodes
- [ ] bluefin configured with apt proxy
- [ ] Test package download populates cache on redfin
- [ ] Web interface accessible at http://192.168.132.224:3142/acng-report.html
- [ ] Firewall rules applied on both nodes

## Maintenance

### Cache Cleanup (run on greenfin)
```bash
sudo /usr/lib/apt-cacher-ng/acngtool maint -c /etc/apt-cacher-ng/acng.conf
```

### Disk Usage Check (on redfin)
```bash
du -sh /sag_data/apt-cache/
df -h /sag_data
```

### NFS Health Check
```bash
# On greenfin
mount | grep apt-cacher
showmount -e 192.168.132.223
```

## Rollback

If issues arise:

```bash
# On greenfin - unmount and use local cache
sudo umount /var/cache/apt-cacher-ng
sudo mkdir -p /var/cache/apt-cacher-ng
sudo systemctl restart apt-cacher-ng

# On client nodes - remove proxy
sudo rm /etc/apt/apt.conf.d/02proxy
sudo apt update
```

## Benefits of Split Architecture

| Component | Node | Benefit |
|-----------|------|---------|
| apt-cacher-ng service | greenfin | Offloads proxy CPU from GPU node |
| Package storage | redfin | Uses 1.1TB /sag_data partition |
| Network routing | greenfin | Central point for all apt traffic |

---

FOR SEVEN GENERATIONS - Distributed architecture maximizes resource utilization.
