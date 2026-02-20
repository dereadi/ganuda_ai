# KB: Memory Immune System Deployment
**Date**: February 17, 2026
**Kanban**: #1814
**Sprint**: RC-2026-02E
**Story Points**: 13

## Summary

The Memory Immune System automates detection and regulation of contaminated thermal memories. Built in response to the Grafana-on-bluefin incident where 16,820 false alerts and 52,000+ routine telemetry records at sacred temperatures contaminated RAG semantic search.

## Script: `/ganuda/scripts/memory_immune_system.py`

### Detection Modes

**1. Bulk Pattern Detection**
- Scans for >50 records with the same content prefix (first 60 chars) at `temperature_score >= 70`
- Groups by prefix, reports count, average temperature, and suggested target temperature
- Known telemetry patterns have predefined target temperatures:
  - "vision detection" → 30
  - "coherence check" → 35
  - "alert:" → 50
- Unknown bulk patterns default to temp 50 (working memory tier)

**2. Dormant Hot Detection**
- Finds memories at `temperature_score >= 80` with zero access (`access_count = 0`) and no access in 30+ days
- These are memories that were stored at high importance but never retrieved — likely noise
- Cools by 20 degrees (minimum 30) rather than fully suppressing

### Safety Guardrails
- Sacred memories (`sacred_pattern=true`) are **NEVER** regulated
- `--dry-run` mode scans without making changes
- All regulations are logged in `metadata` jsonb with `immune_regulated=true`, `original_temp`, and `regulation_reason`
- The script logs its own run as a temp-60 thermal memory for audit trail

### Usage
```bash
# Dry run first — always
python3 /ganuda/scripts/memory_immune_system.py --dry-run --verbose

# Live regulation
python3 /ganuda/scripts/memory_immune_system.py

# Verbose live
python3 /ganuda/scripts/memory_immune_system.py --verbose
```

### Recommended Schedule
- Daily cron or systemd timer is sufficient
- Run as `dereadi` user (has DB access via secrets.env)

## Root Cause: Grafana Contamination Incident (Feb 17 2026)

On Feb 17, thermal memory audit revealed:
- 16,820 Grafana false alert records at temp 95 (sacred temperature tier)
- 52,000+ routine telemetry records (vision detections, coherence checks) at inflated temperatures
- These dominated RAG results because pgvector returns by similarity AND temperature filtering
- Manual cleanup required hours of SQL work

The immune system prevents recurrence by automatically detecting and cooling bulk patterns.

## CMDB Entry
- **Script**: `/ganuda/scripts/memory_immune_system.py`
- **Node**: redfin (runs where DB is accessible)
- **Dependencies**: psycopg2, secrets.env for DB password
- **Status**: Deployed, needs scheduling (cron or systemd timer)

## Lessons Learned
- High temperature does NOT equal high importance — bulk telemetry at temp 95 is contamination
- The immune system respects sacred memories — only TPM/council-protected content is exempt
- Dormant detection requires Phase 0 access logging to work (access_count must be tracked)
- Always run `--dry-run` first to see what would be regulated before going live

For Seven Generations.
