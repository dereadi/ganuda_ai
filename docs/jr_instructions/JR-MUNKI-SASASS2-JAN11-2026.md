# Jr Instruction: Munki Server on sasass2

**Date**: January 11, 2026
**Priority**: MEDIUM
**Target Node**: sasass2 (Mac Studio)
**TPM**: Flying Squirrel (dereadi)
**Council Approval**: ULTRATHINK 7f3a91c2d8e4b5f0

## Background

TPM has experience installing Munki on both Ubuntu and macOS. macOS installation is easier due to native support and GUI tools. sasass2 will serve as the Munki server for all Mac nodes in the Federation.

## Problem

Mac nodes (bmasass, sasass, sasass2, tpm-macbook) currently have no centralized:
- Software deployment
- Patch management
- Configuration profiles
- Self-service software catalog

Ansible can run commands on Macs but is not designed for proper Mac management.

## Solution

Deploy Munki on sasass2 as the Mac package management server.

---

## What Munki Provides

| Feature | Description |
|---------|-------------|
| Software deployment | Push .pkg/.dmg to Mac fleet |
| Patch management | Apple software updates + third-party |
| Self-service | Managed Software Center app |
| Manifests | Per-machine or group configurations |
| Catalogs | Testing → Production promotion |
| Reporting | What's installed where |

---

## Architecture

```
                    ┌─────────────────┐
                    │    sasass2      │
                    │  (Munki Server) │
                    ├─────────────────┤
                    │ • munkiimport   │
                    │ • makecatalogs  │
                    │ • Web server    │
                    └────────┬────────┘
                             │ HTTP/HTTPS
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐         ┌──────────┐         ┌─────────┐
   │ bmasass │         │  sasass  │         │tpm-mbp  │
   │         │         │          │         │         │
   │• munki  │         │• munki   │         │• munki  │
   │  client │         │  client  │         │  client │
   └─────────┘         └──────────┘         └─────────┘
```

---

## Phase 1: Server Setup (sasass2)

### Install Munki tools
```bash
# Download latest Munki
curl -L -o /tmp/munkitools.pkg "https://github.com/munki/munki/releases/download/v6.3.1/munkitools-6.3.1.4561.pkg"

# Install
sudo installer -pkg /tmp/munkitools.pkg -target /

# Verify
/usr/local/munki/munkiimport --version
```

### Create repo structure
```bash
# Create Munki repo
sudo mkdir -p /Users/Shared/munki_repo/{catalogs,manifests,pkgs,pkgsinfo,icons}

# Set permissions
sudo chown -R dereadi:staff /Users/Shared/munki_repo
chmod -R 755 /Users/Shared/munki_repo
```

### Configure munkiimport
```bash
/usr/local/munki/munkiimport --configure

# When prompted:
# Repo path: /Users/Shared/munki_repo
# Repo URL: http://sasass2.cherokee.local:8080
# pkginfo extension: .plist
# Editor: /usr/bin/vi (or your preference)
```

---

## Phase 2: Web Server Setup

### Option A: Built-in Python (Quick)
```bash
# Create launch daemon for simple HTTP server
sudo tee /Library/LaunchDaemons/com.cherokee.munkirepo.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cherokee.munkirepo</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-m</string>
        <string>http.server</string>
        <string>8080</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/Shared/munki_repo</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

sudo launchctl load /Library/LaunchDaemons/com.cherokee.munkirepo.plist
```

### Option B: nginx (Production)
```bash
# Install nginx via Homebrew
brew install nginx

# Configure
cat > /opt/homebrew/etc/nginx/servers/munki.conf << 'EOF'
server {
    listen 8080;
    server_name sasass2.cherokee.local;

    root /Users/Shared/munki_repo;

    location / {
        autoindex off;
    }

    # Logging for audit
    access_log /opt/homebrew/var/log/nginx/munki-access.log;
    error_log /opt/homebrew/var/log/nginx/munki-error.log;
}
EOF

# Start nginx
brew services start nginx
```

---

## Phase 3: Import First Package

```bash
# Example: Import Firefox
curl -L -o /tmp/Firefox.dmg "https://download.mozilla.org/?product=firefox-latest&os=osx&lang=en-US"

/usr/local/munki/munkiimport /tmp/Firefox.dmg

# Follow prompts:
# - Name: Firefox
# - Display name: Firefox
# - Catalog: testing
# - etc.

# Rebuild catalogs
/usr/local/munki/makecatalogs /Users/Shared/munki_repo
```

---

## Phase 4: Create Manifests

### Site-wide manifest
```bash
cat > /Users/Shared/munki_repo/manifests/site_default << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>catalogs</key>
    <array>
        <string>production</string>
    </array>
    <key>included_manifests</key>
    <array>
    </array>
    <key>managed_installs</key>
    <array>
    </array>
    <key>managed_updates</key>
    <array>
    </array>
</dict>
</plist>
EOF
```

### Per-machine manifests
```bash
# Create manifest for each Mac using serial number
# Get serial: system_profiler SPHardwareDataType | grep Serial

# Example for bmasass
cat > /Users/Shared/munki_repo/manifests/bmasass << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>catalogs</key>
    <array>
        <string>production</string>
    </array>
    <key>included_manifests</key>
    <array>
        <string>site_default</string>
    </array>
    <key>managed_installs</key>
    <array>
        <string>Firefox</string>
    </array>
</dict>
</plist>
EOF
```

---

## Phase 5: Client Setup (All Mac Nodes)

```bash
# Install Munki client (same pkg as server)
sudo installer -pkg /tmp/munkitools.pkg -target /

# Configure client
sudo defaults write /Library/Preferences/ManagedInstalls SoftwareRepoURL "http://sasass2.cherokee.local:8080"
sudo defaults write /Library/Preferences/ManagedInstalls ClientIdentifier "$(hostname -s)"
sudo defaults write /Library/Preferences/ManagedInstalls InstallAppleSoftwareUpdates -bool true

# Test
sudo /usr/local/munki/managedsoftwareupdate --checkonly

# Run full update
sudo /usr/local/munki/managedsoftwareupdate --installonly
```

---

## Phase 6: Scheduled Checks

Munki automatically installs LaunchDaemons:
- `/Library/LaunchDaemons/com.googlecode.munki.managedsoftwareupdate-check.plist` - Checks hourly
- `/Library/LaunchDaemons/com.googlecode.munki.managedsoftwareupdate-install.plist` - Installs at logout

---

## Catalog Workflow

```
testing → production

1. Import new package to 'testing' catalog
2. Test on sasass2 (server also runs client)
3. Promote to 'production':
   - Edit pkginfo file
   - Change catalogs from ['testing'] to ['production']
   - Run makecatalogs
```

---

## Integration with Federation

### Report to thermal memory
```bash
# Create script to report Munki status
cat > /ganuda/scripts/munki-status-report.sh << 'EOF'
#!/bin/bash
# Report Munki status to thermal memory

HOSTNAME=$(hostname -s)
REPORT=$(defaults read /Library/Managed\ Installs/ManagedInstallReport)

# Parse and send to thermal memory
# (Implementation depends on how you want to format)
EOF
```

### Ansible can trigger Munki
```yaml
# In Ansible playbook
- name: Trigger Munki check on Macs
  shell: /usr/local/munki/managedsoftwareupdate --checkonly
  when: ansible_os_family == "Darwin"
```

---

## What Munki Does NOT Do

| Need | Solution |
|------|----------|
| Identity/Auth | FreeIPA (Linux) or LDAP binding |
| MDM profiles | Apple Business Manager + MDM |
| Remote lock/wipe | MDM solution |
| FileVault management | MDM or manual |

For full Mac enterprise management, would need MDM (Jamf, Mosyle, etc.). Munki handles software only.

---

## Thermal Memory Archive

After setup:
```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'MUNKI SERVER DEPLOYED - January 11, 2026

  Server: sasass2.cherokee.local:8080
  Repo: /Users/Shared/munki_repo/

  Clients configured:
  - bmasass
  - sasass
  - sasass2
  - tpm-macbook

  Catalogs: testing, production

  Features enabled:
  - Software deployment
  - Apple software updates via Munki
  - Self-service (Managed Software Center)

  Note: Munki handles software only.
  For MDM features, would need separate solution.

  For Seven Generations.',
  88, 'it_triad_jr',
  ARRAY['munki', 'macos', 'software-management', 'infrastructure', 'january-2026'],
  'federation'
);
```

---

## References

- Munki Wiki: https://github.com/munki/munki/wiki
- MunkiAdmin (GUI): https://github.com/hjuutilainen/munkiadmin
- TPM experience: "I've installed it on Ubuntu, and on macOS. It was much easier on macOS"

---

For Seven Generations.
