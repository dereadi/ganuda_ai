# JR Instruction: Munki + AutoPkg Deployment on sasass2

**Task ID:** MUNKI-001
**Assigned To:** Infrastructure Jr.
**Priority:** P2
**Node:** sasass2 (192.168.132.242)
**Date:** 2026-02-06

## Objective

Deploy Munki server with AutoPkg ecosystem on sasass2 to manage macOS software deployment and sudo configurations across federation Macs (sasass, sasass2).

## Prerequisites

- Admin access on sasass2
- Xcode Command Line Tools
- Network access from sasass to sasass2

## Architecture

```
sasass2 (192.168.132.242)
├── Munki Repo: /Users/Shared/munki_repo/
├── Web Server: nginx or Apache (port 8080)
├── AutoPkg: recipe runner
├── AutoPkgr: GUI scheduler
└── MunkiAdmin: repo management GUI

sasass (192.168.132.241)
└── Munki Client → pulls from http://sasass2.local:8080/munki_repo/
```

## Phase 1: Install Core Tools

### 1.1 Xcode Command Line Tools
```bash
xcode-select --install
```

### 1.2 Install Munki Tools
```bash
# Download latest munkitools
curl -L -o /tmp/munkitools.pkg "https://github.com/munki/munki/releases/download/v6.3.1/munkitools-6.3.1.4580.pkg"

# Install
sudo installer -pkg /tmp/munkitools.pkg -target /
```

### 1.3 Install AutoPkg
```bash
# Download latest AutoPkg
curl -L -o /tmp/autopkg.pkg "https://github.com/autopkg/autopkg/releases/download/v2.7.3/autopkg-2.7.3.pkg"

# Install
sudo installer -pkg /tmp/autopkg.pkg -target /
```

### 1.4 Install MunkiAdmin (GUI for repo management)
```bash
curl -L -o /tmp/MunkiAdmin.dmg "https://github.com/hjuutilainen/munkiadmin/releases/download/v1.8.1/MunkiAdmin-1.8.1.dmg"

hdiutil attach /tmp/MunkiAdmin.dmg
cp -R "/Volumes/MunkiAdmin 1.8.1/MunkiAdmin.app" /Applications/
hdiutil detach "/Volumes/MunkiAdmin 1.8.1"
```

### 1.5 Install AutoPkgr (GUI for AutoPkg scheduling)
```bash
curl -L -o /tmp/AutoPkgr.dmg "https://github.com/lindegroup/autopkgr/releases/download/v1.6.1/AutoPkgr-1.6.1.dmg"

hdiutil attach /tmp/AutoPkgr.dmg
cp -R "/Volumes/AutoPkgr/AutoPkgr.app" /Applications/
hdiutil detach "/Volumes/AutoPkgr"
```

## Phase 2: Create Munki Repository

### 2.1 Initialize Repo Structure
```bash
# Create repo directory
sudo mkdir -p /Users/Shared/munki_repo

# Initialize with munkiimport
sudo /usr/local/munki/munkiimport --configure

# When prompted:
# Repo path: /Users/Shared/munki_repo
# Repo URL: http://sasass2.local:8080/munki_repo
# pkginfo extension: .plist
# Editor: /usr/bin/vi (or your preference)
```

### 2.2 Create Directory Structure
```bash
cd /Users/Shared/munki_repo
sudo mkdir -p catalogs icons manifests pkgs pkgsinfo

# Set permissions
sudo chown -R dereadi:staff /Users/Shared/munki_repo
chmod -R 755 /Users/Shared/munki_repo
```

### 2.3 Create Initial Manifests
```bash
# Site-wide manifest (all Macs)
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
        <string>cherokee-federation-base</string>
    </array>
    <key>managed_installs</key>
    <array>
    </array>
</dict>
</plist>
EOF

# Federation base manifest
cat > /Users/Shared/munki_repo/manifests/cherokee-federation-base << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>catalogs</key>
    <array>
        <string>production</string>
    </array>
    <key>managed_installs</key>
    <array>
        <string>cherokee-sudo-config</string>
    </array>
</dict>
</plist>
EOF
```

## Phase 3: Configure Web Server

### 3.1 Install and Configure nginx
```bash
# Install via Homebrew
brew install nginx

# Create Munki site config
cat > /opt/homebrew/etc/nginx/servers/munki.conf << 'EOF'
server {
    listen 8080;
    server_name sasass2.local;

    location /munki_repo/ {
        alias /Users/Shared/munki_repo/;
        autoindex off;
    }

    # Health check
    location /health {
        return 200 'Munki repo OK';
        add_header Content-Type text/plain;
    }
}
EOF

# Start nginx
brew services start nginx
```

### 3.2 Verify Web Server
```bash
curl http://localhost:8080/health
# Should return: Munki repo OK
```

## Phase 4: Configure AutoPkg

### 4.1 Add Recipe Repos
```bash
# Core repos
autopkg repo-add recipes
autopkg repo-add https://github.com/autopkg/recipes.git
autopkg repo-add https://github.com/autopkg/hjuutilainen-recipes.git
autopkg repo-add https://github.com/autopkg/jleggat-recipes.git

# Munki-specific recipes
autopkg repo-add https://github.com/autopkg/munki-recipes.git
```

### 4.2 Configure AutoPkg for Munki
```bash
# Set Munki repo location
defaults write com.github.autopkg MUNKI_REPO /Users/Shared/munki_repo

# Set cache directory
defaults write com.github.autopkg CACHE_DIR /Users/Shared/ganuda/autopkg_cache
mkdir -p /Users/Shared/ganuda/autopkg_cache
```

### 4.3 Test AutoPkg
```bash
# Run a simple recipe to test
autopkg run -v Firefox.munki

# Rebuild catalogs after import
/usr/local/munki/makecatalogs /Users/Shared/munki_repo
```

## Phase 5: Create Cherokee Sudo Config Package

### 5.1 Create Package Source
```bash
mkdir -p /Users/Shared/ganuda/munki_pkgs/cherokee-sudo-config/payload/etc/sudoers.d
mkdir -p /Users/Shared/ganuda/munki_pkgs/cherokee-sudo-config/scripts

# Create sudoers file
cat > /Users/Shared/ganuda/munki_pkgs/cherokee-sudo-config/payload/etc/sudoers.d/cherokee-federation << 'EOF'
# Cherokee AI Federation Sudo Rules
# Deployed via Munki - DO NOT EDIT LOCALLY

# Full admin access
dereadi ALL=(ALL) NOPASSWD: ALL

# Jr operators group (create locally if needed)
%cherokee-admins ALL=(ALL) ALL

# Service-specific sudo for automation
%cherokee-operators ALL=(ALL) NOPASSWD: /bin/launchctl *
%cherokee-operators ALL=(ALL) NOPASSWD: /usr/bin/pkill -f munki*
%cherokee-operators ALL=(ALL) NOPASSWD: /usr/local/munki/*
EOF

# Set correct permissions in postinstall
cat > /Users/Shared/ganuda/munki_pkgs/cherokee-sudo-config/scripts/postinstall << 'EOF'
#!/bin/bash
chmod 440 /etc/sudoers.d/cherokee-federation
chown root:wheel /etc/sudoers.d/cherokee-federation

# Validate sudoers syntax
visudo -c -f /etc/sudoers.d/cherokee-federation
if [ $? -ne 0 ]; then
    rm /etc/sudoers.d/cherokee-federation
    echo "ERROR: Invalid sudoers syntax, file removed"
    exit 1
fi

exit 0
EOF

chmod +x /Users/Shared/ganuda/munki_pkgs/cherokee-sudo-config/scripts/postinstall
```

### 5.2 Create build-info.plist
```bash
cat > /Users/Shared/ganuda/munki_pkgs/cherokee-sudo-config/build-info.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>identifier</key>
    <string>com.cherokee.sudo-config</string>
    <key>name</key>
    <string>cherokee-sudo-config</string>
    <key>version</key>
    <string>1.0.0</string>
    <key>ownership</key>
    <string>recommended</string>
</dict>
</plist>
EOF
```

### 5.3 Build Package with munkipkg
```bash
# Install munkipkg if not present
pip3 install munkipkg

# Build the package
cd /Users/Shared/ganuda/munki_pkgs
munkipkg cherokee-sudo-config

# Import to Munki repo
/usr/local/munki/munkiimport /Users/Shared/ganuda/munki_pkgs/cherokee-sudo-config/build/cherokee-sudo-config-1.0.0.pkg

# When prompted:
# Item name: cherokee-sudo-config
# Catalog: production
# Category: Configuration
```

### 5.4 Rebuild Catalogs
```bash
/usr/local/munki/makecatalogs /Users/Shared/munki_repo
```

## Phase 6: Configure Munki Clients

### 6.1 On sasass2 (server is also a client)
```bash
# Configure Munki client preferences
sudo defaults write /Library/Preferences/ManagedInstalls SoftwareRepoURL "http://sasass2.local:8080/munki_repo"
sudo defaults write /Library/Preferences/ManagedInstalls ClientIdentifier "sasass2"
sudo defaults write /Library/Preferences/ManagedInstalls InstallAppleSoftwareUpdates -bool true

# Create client manifest
cat > /Users/Shared/munki_repo/manifests/sasass2 << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>included_manifests</key>
    <array>
        <string>site_default</string>
    </array>
    <key>managed_installs</key>
    <array>
    </array>
</dict>
</plist>
EOF
```

### 6.2 On sasass (client only)
```bash
# SSH to sasass and run:
sudo defaults write /Library/Preferences/ManagedInstalls SoftwareRepoURL "http://sasass2.local:8080/munki_repo"
sudo defaults write /Library/Preferences/ManagedInstalls ClientIdentifier "sasass"
sudo defaults write /Library/Preferences/ManagedInstalls InstallAppleSoftwareUpdates -bool true
```

### 6.3 Create sasass manifest on server
```bash
cat > /Users/Shared/munki_repo/manifests/sasass << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>included_manifests</key>
    <array>
        <string>site_default</string>
    </array>
    <key>managed_installs</key>
    <array>
    </array>
</dict>
</plist>
EOF
```

## Phase 7: Test Deployment

### 7.1 Manual Check Run
```bash
# On each Mac client
sudo /usr/local/munki/managedsoftwareupdate --checkonly

# View what would be installed
sudo /usr/local/munki/managedsoftwareupdate --installonly
```

### 7.2 Verify Sudo Config Applied
```bash
# After install, verify sudoers file exists
ls -la /etc/sudoers.d/cherokee-federation

# Test sudo works
sudo -l
```

## Phase 8: AutoPkgr Scheduling (Optional GUI)

1. Launch AutoPkgr from /Applications
2. Configure schedule (e.g., daily at 2 AM)
3. Add recipes to monitor:
   - Firefox.munki
   - GoogleChrome.munki
   - VSCode.munki
   - Slack.munki
4. Enable notifications

## Verification Checklist

- [ ] munkitools installed: `/usr/local/munki/managedsoftwareupdate --version`
- [ ] AutoPkg installed: `autopkg version`
- [ ] MunkiAdmin in /Applications
- [ ] AutoPkgr in /Applications
- [ ] nginx serving repo: `curl http://localhost:8080/health`
- [ ] Repo structure exists: `ls /Users/Shared/munki_repo/`
- [ ] Catalogs built: `ls /Users/Shared/munki_repo/catalogs/`
- [ ] Client configured: `defaults read /Library/Preferences/ManagedInstalls`
- [ ] Check run succeeds: `sudo /usr/local/munki/managedsoftwareupdate -v --checkonly`
- [ ] Sudo config deployed: `ls /etc/sudoers.d/cherokee-federation`

## Useful Commands

```bash
# Rebuild catalogs after any change
/usr/local/munki/makecatalogs /Users/Shared/munki_repo

# Force client check
sudo /usr/local/munki/managedsoftwareupdate --checkonly

# View Munki logs
tail -f /Library/Managed\ Installs/Logs/ManagedSoftwareUpdate.log

# List AutoPkg repos
autopkg repo-list

# Search for recipes
autopkg search Chrome
```

## Files Created

| File | Purpose |
|------|---------|
| /Users/Shared/munki_repo/ | Munki repository root |
| /Users/Shared/ganuda/munki_pkgs/ | Package source files |
| /Users/Shared/ganuda/autopkg_cache/ | AutoPkg download cache |
| /opt/homebrew/etc/nginx/servers/munki.conf | nginx config |

## Integration with FreeIPA (Future)

When FreeIPA is deployed:
1. Macs join Kerberos realm for SSO
2. Munki continues to manage software + sudo configs
3. Update cherokee-sudo-config to reference FreeIPA groups

---
*For Seven Generations - Cherokee AI Federation*
