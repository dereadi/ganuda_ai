# KB: SAN Management and Backup Strategy Research

**Date:** January 28, 2026
**Author:** TPM (Claude Opus)
**Status:** Research Complete - Pending Hardware

---

## Executive Summary

Research findings for open source SAN management and backup solutions to support the Cherokee AI Federation's infrastructure backup needs.

---

## SAN/NAS Platform Comparison

### TrueNAS SCALE (Recommended)

| Feature | TrueNAS SCALE |
|---------|---------------|
| Base OS | Debian Linux |
| Filesystem | ZFS (native) |
| Deduplication | Inline (real-time) |
| Snapshots | Native ZFS |
| Replication | Built-in |
| iSCSI (SAN) | Full support |
| NFS/SMB | Full support |
| Min RAM | 16GB recommended |
| License | Open Source |

**Pros:**
- Full ZFS support: RAIDZ, snapshots, compression, encryption, deduplication
- Self-healing capabilities
- Native cloud sync, snapshot replication
- Linux-based (familiar tooling)
- Enterprise-grade features

**Cons:**
- Higher RAM requirements (1GB per TB for dedup tables)
- Inline dedup can slow writes 3-5x on fast pools
- Heavier resource usage

### OpenMediaVault (Alternative)

| Feature | OpenMediaVault |
|---------|----------------|
| Base OS | Debian Linux |
| Filesystem | ext4/btrfs (ZFS via plugin) |
| Deduplication | Not native |
| Snapshots | Via plugin |
| Replication | Rsync |
| iSCSI (SAN) | Limited |
| NFS/SMB | Full support |
| Min RAM | 2GB |
| License | Open Source |

**Pros:**
- Extremely lightweight
- Runs on Raspberry Pi
- Simple web UI
- Low hardware requirements

**Cons:**
- No native deduplication
- ZFS only via plugin
- Limited SAN/iSCSI support
- Lacks advanced snapshot management

### Recommendation

**TrueNAS SCALE** for our federation because:
1. Native ZFS with full deduplication
2. Proper iSCSI for LUN provisioning to nodes
3. Snapshot-based replication between pools
4. Linux-based (matches our infrastructure)

---

## Backup Tool Comparison

### For Database Backups (PostgreSQL)

| Tool | Dedup | Speed | Threading | Cloud Storage |
|------|-------|-------|-----------|---------------|
| Borg | Variable-chunk | Slower | Single | Via rclone |
| Restic | Fixed-chunk | Faster | Multi | Native S3 |
| Kopia | Content-defined | Fast | Multi | Native S3 |

### Recommendation: Hybrid Approach

1. **PostgreSQL**: Use `pg_dump` + Restic
   - Fast multi-threaded backups
   - Native S3 support for off-site
   - Good deduplication

2. **Application Data**: Use Borg
   - Better deduplication for changing files
   - More storage efficient for incremental
   - Lower storage usage long-term

3. **ZFS Snapshots**: For point-in-time recovery
   - Near-instant snapshots
   - Replicate to TrueNAS
   - 15-minute snapshot intervals

---

## Proposed Architecture

```
                    ┌─────────────────┐
                    │   TrueNAS SAN   │
                    │  (new server)   │
                    └────────┬────────┘
                             │ 10GbE
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │ redfin  │         │ bluefin │         │greenfin │
   │ (GPU)   │         │  (DB)   │         │(Daemons)│
   └─────────┘         └─────────┘         └─────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Backup Jobs   │
                    │ • pg_dump daily │
                    │ • Restic hourly │
                    │ • ZFS snapshots │
                    └─────────────────┘
```

---

## Backup Schedule (Proposed)

| Asset | Tool | Schedule | Retention |
|-------|------|----------|-----------|
| zammad_production | pg_dump + Restic | Hourly | 7 days hourly, 30 days daily |
| triad_federation | pg_dump + Restic | Hourly | 7 days hourly, 30 days daily |
| /ganuda | Borg | Daily | 30 days |
| ZFS datasets | Snapshots | 15 min | 24h @ 15min, 7d @ hourly |

---

## Disk Provisioning to Nodes

TrueNAS can provision storage via:

1. **iSCSI LUNs** - Block devices for VMs or direct mount
2. **NFS Shares** - Network filesystem for /ganuda
3. **SMB Shares** - Cross-platform access

### Example LUN Allocation

| Node | LUN | Size | Purpose |
|------|-----|------|---------|
| redfin | iscsi-redfin-models | 500GB | vLLM model cache |
| bluefin | iscsi-bluefin-backup | 2TB | DB backup staging |
| greenfin | iscsi-greenfin-logs | 200GB | Log aggregation |

---

## Sources

- [TrueNAS vs OpenMediaVault 2025](https://optimizeddocs.com/blogs/backups/backup%20hardware/truenas%20vs%20openmediavault)
- [TrueNAS CORE vs SCALE vs OMV](https://hackmag.com/security/truenas-or-truenas)
- [Best Open Source NAS Software 2025](https://www.how2shout.com/tools/best-free-open-source-nas-software.html)
- [Restic vs Borg Comparison](https://ultahost.com/blog/restic-vs-borg/)
- [Restic vs Borg vs Kopia](https://faisalrafique.com/restic-vs-borg-vs-kopia/)
- [Duplicacy vs Restic vs Borg 2025](https://mangohost.net/blog/duplicacy-vs-restic-vs-borg-which-backup-tool-is-right-in-2025/)

---

## Next Steps (When SAN Arrives)

1. Install TrueNAS SCALE on SAN server
2. Create ZFS pool with appropriate RAIDZ level
3. Configure iSCSI targets for each node
4. Set up NFS share for /ganuda (replicated)
5. Install Restic on all nodes
6. Configure pg_dump cron jobs on bluefin
7. Create backup job scripts
8. Test restore procedures

---

FOR SEVEN GENERATIONS
