# JR Instruction: Set Up On-Site APT Mirror on Bluefin

**JR ID:** JR-APT-MIRROR-SETUP-BLUEFIN
**Priority:** P2 (Infrastructure)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Assigned To:** Infrastructure Jr.
**Effort:** Medium (4-8 hours)

---

## Objective

Set up an on-site APT mirror on bluefin to provide local package repositories for the Cherokee AI Federation nodes, reducing external bandwidth usage and enabling isolated VLAN nodes (goldfin, VLAN 20) to install packages.

## Current State

- Bluefin nginx is serving BookStack on port 8085
- No apt mirror configured
- Ports 8888/8889 are NOT listening
- No /srv/mirror directory exists

## Target State

| Port | Repository | OS |
|------|------------|-----|
| 8888 | Ubuntu mirror | 24.04 LTS |
| 8889 | Rocky mirror | 9.x |
| 8890 | Debian mirror | 12 (Bookworm) |

---

## Phase 1: Create Mirror Storage

### 1.1 Create Mirror Directories

```bash
# On bluefin
sudo mkdir -p /srv/mirror/ubuntu
sudo mkdir -p /srv/mirror/rocky
sudo mkdir -p /srv/mirror/debian
sudo chown -R www-data:www-data /srv/mirror
```

### 1.2 Check Disk Space

```bash
# Mirrors require significant space
# Ubuntu 24.04 main+universe: ~200GB
# Rocky 9 BaseOS+AppStream: ~50GB
# Debian 12 main: ~100GB
df -h /srv
```

---

## Phase 2: Install Mirror Tools

### 2.1 Install apt-mirror for Ubuntu/Debian

```bash
sudo apt install apt-mirror
```

### 2.2 Configure apt-mirror

```bash
# /etc/apt/mirror.list
set base_path    /srv/mirror/ubuntu
set nthreads     20
set _tilde       0

deb http://archive.ubuntu.com/ubuntu noble main restricted universe
deb http://archive.ubuntu.com/ubuntu noble-updates main restricted universe
deb http://archive.ubuntu.com/ubuntu noble-security main restricted universe
```

### 2.3 For Rocky Linux (use rsync)

```bash
# Create sync script
cat > /srv/mirror/sync-rocky.sh << 'EOF'
#!/bin/bash
rsync -avSHP --delete \
  rsync://dl.rockylinux.org/rocky/9/BaseOS/x86_64/os/ \
  /srv/mirror/rocky/9/BaseOS/x86_64/os/

rsync -avSHP --delete \
  rsync://dl.rockylinux.org/rocky/9/AppStream/x86_64/os/ \
  /srv/mirror/rocky/9/AppStream/x86_64/os/
EOF
chmod +x /srv/mirror/sync-rocky.sh
```

---

## Phase 3: Configure Nginx

### 3.1 Create Virtual Host

```bash
# /etc/nginx/sites-available/apt-mirror
server {
    listen 8888;
    server_name localhost;
    root /srv/mirror/ubuntu;
    autoindex on;

    location / {
        try_files $uri $uri/ =404;
    }
}

server {
    listen 8889;
    server_name localhost;
    root /srv/mirror/rocky;
    autoindex on;

    location / {
        try_files $uri $uri/ =404;
    }
}

server {
    listen 8890;
    server_name localhost;
    root /srv/mirror/debian;
    autoindex on;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

### 3.2 Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/apt-mirror /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Phase 4: Initial Sync

### 4.1 Run Initial Sync (takes many hours)

```bash
# Ubuntu (run in screen/tmux)
sudo apt-mirror

# Rocky
sudo /srv/mirror/sync-rocky.sh
```

### 4.2 Set Up Cron for Daily Updates

```bash
# /etc/cron.d/apt-mirror
0 4 * * * root apt-mirror >> /var/log/apt-mirror.log 2>&1
0 5 * * * root /srv/mirror/sync-rocky.sh >> /var/log/rocky-mirror.log 2>&1
```

---

## Phase 5: Client Configuration

### 5.1 Ubuntu Clients (redfin, etc.)

```bash
# /etc/apt/sources.list.d/local-mirror.list
deb http://192.168.132.222:8888/ubuntu noble main restricted universe
deb http://192.168.132.222:8888/ubuntu noble-updates main restricted universe
```

### 5.2 Debian Clients (goldfin)

```bash
# /etc/apt/sources.list.d/local-mirror.list
deb http://192.168.132.222:8890/debian bookworm main
deb http://192.168.132.222:8890/debian bookworm-updates main
```

### 5.3 For VLAN 20 (Goldfin via Squid proxy)

```bash
# Goldfin can use greenfin squid proxy to reach bluefin
# In /etc/apt/apt.conf.d/proxy
Acquire::http::Proxy "http://192.168.20.1:3128";
```

---

## Success Criteria

- [ ] Port 8888 serving Ubuntu packages
- [ ] Port 8889 serving Rocky packages
- [ ] Port 8890 serving Debian packages
- [ ] Initial sync completed
- [ ] Cron jobs configured for daily updates
- [ ] At least one client node configured to use mirror

---

## References

- JR-APT-MIRROR-BLUEFIN-JAN11-2026.md (original planning doc)
- KB-ISOLATED-VLAN-TAILSCALE-VIA-SQUID-JAN15-2026.md

---

FOR SEVEN GENERATIONS
