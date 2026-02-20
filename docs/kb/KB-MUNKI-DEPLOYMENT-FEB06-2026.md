# KB: Munki Deployment on Cherokee AI Federation

**Date:** 2026-02-06
**Status:** Operational
**Owner:** Infrastructure Jr.

## Overview

Munki provides macOS software deployment and configuration management for federation Macs. Complements Ansible (Linux) and FreeIPA (identity).

## Architecture

```
sasass2 (192.168.132.242) - Munki Server
├── nginx :8080 → /Users/Shared/munki_repo/
├── AutoPkg (recipe runner)
├── MunkiAdmin (GUI)
└── AutoPkgr (scheduler)
        │
        ▼
sasass (192.168.132.241) - Munki Client
└── Pulls from http://sasass2.local:8080/munki_repo/
```

## Components Installed

| Component | Location | Purpose |
|-----------|----------|---------|
| munkitools | /usr/local/munki/ | Core client/server tools |
| AutoPkg | /usr/local/bin/autopkg | Automated package downloads |
| MunkiAdmin | /Applications/ | GUI repo management |
| AutoPkgr | /Applications/ | Scheduled AutoPkg runs |
| nginx | brew services | Web server for repo |

## Repository Structure

```
/Users/Shared/munki_repo/
├── catalogs/
│   ├── all
│   ├── production
│   └── testing
├── icons/
├── manifests/
│   ├── site_default
│   ├── cherokee-federation-base
│   ├── sasass
│   └── sasass2
├── pkgs/
│   └── apps/firefox/Firefox-147.0.3.dmg
└── pkgsinfo/
    └── apps/firefox/Firefox-147.0.3.plist
```

## Manifest Hierarchy

```
sasass / sasass2 (machine-specific)
    └── includes → site_default
                       └── includes → cherokee-federation-base
                                          └── managed_installs: [packages]
```

## Key Commands

**Server (sasass2):**
```bash
# Rebuild catalogs after changes
/usr/local/munki/makecatalogs /Users/Shared/munki_repo

# Import package via AutoPkg
/usr/local/bin/autopkg run Firefox.munki

# List AutoPkg repos
/usr/local/bin/autopkg repo-list
```

**Client (sasass, sasass2):**
```bash
# Check for updates
sudo /usr/local/munki/managedsoftwareupdate --checkonly

# Install pending updates
sudo /usr/local/munki/managedsoftwareupdate --installonly

# View logs
tail -f /Library/Managed\ Installs/Logs/ManagedSoftwareUpdate.log
```

## Client Configuration

Stored in `/Library/Preferences/ManagedInstalls.plist`:

| Key | Value |
|-----|-------|
| SoftwareRepoURL | http://sasass2.local:8080/munki_repo |
| ClientIdentifier | sasass or sasass2 |
| InstallAppleSoftwareUpdates | false (macOS 26 not in Apple catalog yet) |

## Adding New Packages

### Via AutoPkg (automated)
```bash
# Search for recipe
/usr/local/bin/autopkg search Chrome

# Run recipe
/usr/local/bin/autopkg run GoogleChrome.munki

# Rebuild catalogs
/usr/local/munki/makecatalogs /Users/Shared/munki_repo
```

### Via munkiimport (manual)
```bash
/usr/local/munki/munkiimport /path/to/package.pkg
# Follow prompts for name, catalog, category
/usr/local/munki/makecatalogs /Users/Shared/munki_repo
```

### Promote to production
Edit pkgsinfo plist, add `<string>production</string>` to catalogs array, rebuild.

## Integration Points

| System | Integration |
|--------|-------------|
| Ansible | Can trigger `managedsoftwareupdate` on Macs |
| FreeIPA | Macs use Kerberos SSO, Munki deploys sudo configs |
| Infrastructure Jr. | Owns all three systems |

## Pending Work

1. **cherokee-sudo-config package** — deploy federation sudo rules
2. **AutoPkgr scheduling** — nightly package checks
3. **Additional recipes** — VSCode, Slack, etc.

## Files

| Path | Purpose |
|------|---------|
| /Users/Shared/munki_repo/ | Repository root |
| /Users/Shared/ganuda/autopkg_cache/ | AutoPkg download cache |
| /opt/homebrew/etc/nginx/servers/munki.conf | nginx config |
| /Library/Preferences/ManagedInstalls.plist | Client config |

---
*For Seven Generations - Cherokee AI Federation*
