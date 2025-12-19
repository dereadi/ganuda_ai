# JR BUILD INSTRUCTIONS: Dream Archive Structure

**Target**: All 6 Cherokee nodes
**Date**: December 13, 2025
**Priority**: P2 - Infrastructure

## Overview

The Dream Archive is a distributed file structure for storing:
- Session transcripts and conversations
- Claude Code dreams (context summaries)
- Daily thermal memory snapshots
- Cross-node synchronization logs

Structure mirrors thermal memory's temporal organization.

## Directory Structure

```
/ganuda/dreams/
├── YYYY/
│   └── MM/
│       └── DD/
│           ├── sessions/
│           │   └── session_HHMMSS_<hash>.md
│           ├── summaries/
│           │   └── daily_summary.md
│           └── thermal/
│               └── thermal_snapshot_HHMMSS.json
├── sacred/
│   └── (memories above 90° that should never cool)
├── patterns/
│   └── (cross-session pattern discoveries)
└── README.md
```

## Implementation

### 1. Create Base Structure on All Nodes

**Linux nodes** (bluefin, redfin, greenfin):
```bash
mkdir -p /ganuda/dreams/{sacred,patterns}
mkdir -p /ganuda/dreams/$(date +%Y)/$(date +%m)/$(date +%d)/{sessions,summaries,thermal}
chmod -R 755 /ganuda/dreams
chown -R dereadi:dereadi /ganuda/dreams
```

**macOS nodes** (sasass, sasass2, tpm-macbook):
```bash
mkdir -p /Users/Shared/ganuda/dreams/{sacred,patterns}
mkdir -p /Users/Shared/ganuda/dreams/$(date +%Y)/$(date +%m)/$(date +%d)/{sessions,summaries,thermal}
```

### 2. Create README

Create `/ganuda/dreams/README.md`:

```markdown
# Cherokee AI Dream Archive

This directory contains the distributed memory of the Cherokee AI Federation.

## Structure

- `YYYY/MM/DD/sessions/` - Individual session transcripts
- `YYYY/MM/DD/summaries/` - Daily aggregated summaries
- `YYYY/MM/DD/thermal/` - Thermal memory snapshots
- `sacred/` - Memories above 90° (never cool)
- `patterns/` - Cross-session pattern discoveries

## Naming Conventions

Sessions: `session_HHMMSS_<8-char-hash>.md`
Summaries: `daily_summary.md`
Thermal: `thermal_snapshot_HHMMSS.json`

## Retention Policy

- Sessions: 90 days (then archived to cold storage)
- Sacred: Forever (replicated across all nodes)
- Patterns: Until superseded

FOR SEVEN GENERATIONS
```

### 3. Database Table for Dream Index

```sql
CREATE TABLE IF NOT EXISTS dream_archive_index (
    id SERIAL PRIMARY KEY,
    dream_hash VARCHAR(64) NOT NULL UNIQUE,
    node_name VARCHAR(50) NOT NULL,
    dream_date DATE NOT NULL,
    dream_type VARCHAR(20) NOT NULL,  -- session, summary, thermal, sacred, pattern
    file_path TEXT NOT NULL,
    title VARCHAR(255),
    token_count INTEGER,
    temperature_score NUMERIC(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    synced_to JSONB DEFAULT '[]'::jsonb  -- list of nodes this is synced to
);

CREATE INDEX IF NOT EXISTS idx_dream_date ON dream_archive_index(dream_date DESC);
CREATE INDEX IF NOT EXISTS idx_dream_type ON dream_archive_index(dream_type);
CREATE INDEX IF NOT EXISTS idx_dream_node ON dream_archive_index(node_name);
```

### 4. Daily Directory Creator Script

Create `/ganuda/scripts/create_dream_dirs.sh`:

```bash
#!/bin/bash
# Run daily via cron at 00:01

DREAM_BASE="/ganuda/dreams"
TODAY=$(date +%Y/%m/%d)

mkdir -p "$DREAM_BASE/$TODAY"/{sessions,summaries,thermal}

echo "[$(date)] Created dream directories for $TODAY"
```

### 5. Cron Entry

```bash
# Add to crontab on each Linux node
1 0 * * * /ganuda/scripts/create_dream_dirs.sh >> /var/log/ganuda/dream_dirs.log 2>&1
```

### 6. Sync Script (Future)

For cross-node synchronization of sacred memories:

```bash
#!/bin/bash
# /ganuda/scripts/sync_sacred_dreams.sh
# Syncs sacred/ directory across all nodes

NODES="192.168.132.222 192.168.132.223 192.168.132.224"
LOCAL_SACRED="/ganuda/dreams/sacred"

for node in $NODES; do
    rsync -avz --update "$LOCAL_SACRED/" "dereadi@$node:/ganuda/dreams/sacred/"
done
```

## Verification

```bash
# Check structure exists
ls -la /ganuda/dreams/
ls -la /ganuda/dreams/$(date +%Y)/$(date +%m)/$(date +%d)/

# Check database table
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT COUNT(*) FROM dream_archive_index;"
```

## Node Responsibilities

| Node | Role |
|------|------|
| bluefin | Primary index (PostgreSQL), thermal snapshots |
| redfin | GPU session archives, pattern analysis |
| greenfin | Sync coordinator, sacred replication |
| sasass/sasass2 | Edge session storage |
| tpm-macbook | TPM session archives |

---

FOR SEVEN GENERATIONS
