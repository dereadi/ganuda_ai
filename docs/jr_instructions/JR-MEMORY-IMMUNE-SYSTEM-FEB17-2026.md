# Jr Instruction: Memory Immune System

**Kanban**: #1814
**Priority**: 9
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Sprint**: RC-2026-02E

## Context

On Feb 17 2026, we discovered that 16,820 Grafana false alerts and 52,000+ routine telemetry records at sacred temperatures had contaminated RAG semantic search. All were cleaned manually. The Memory Immune System automates this detection and regulation.

The script scans thermal_memory_archive for:
1. **Bulk patterns**: >50 records with the same content prefix at high temperature (contamination)
2. **Dormant high-temp records**: memories at temp >= 80 with no access in 30+ days

When violations are found, it auto-regulates temperature and logs actions.

## Step 1: Create the immune system script

Create `/ganuda/scripts/memory_immune_system.py`

```python
#!/usr/bin/env python3
"""
Memory Immune System — Cherokee AI Federation

Automated bulk-pattern detection and temperature regulation for
thermal_memory_archive. Prevents contamination loops like the
Grafana-on-bluefin incident (16,820 false alerts at temp 95).

Kanban #1814 — RC-2026-02E
Run: python3 /ganuda/scripts/memory_immune_system.py [--dry-run] [--verbose]

For Seven Generations
"""

import os
import sys
import json
import hashlib
import argparse
import logging
from datetime import datetime, timedelta

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
)
logger = logging.getLogger('immune_system')

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', ''),
    'connect_timeout': 10,
}

# Load password from secrets.env if not in env
if not DB_CONFIG['password']:
    secrets_path = '/ganuda/config/secrets.env'
    if os.path.exists(secrets_path):
        with open(secrets_path) as f:
            for line in f:
                if line.startswith('CHEROKEE_DB_PASS='):
                    DB_CONFIG['password'] = line.strip().split('=', 1)[1]

# Detection thresholds
BULK_PATTERN_THRESHOLD = 50       # >50 records with same prefix = suspicious
BULK_PATTERN_MIN_TEMP = 70        # Only flag high-temp bulk patterns
BULK_PREFIX_LENGTH = 60           # Characters to compare for pattern matching
DORMANT_DAYS = 30                 # Days without access before flagging
DORMANT_MIN_TEMP = 80             # Only flag dormant records at high temp

# Temperature policy: known telemetry patterns and their correct temps
TELEMETRY_PATTERNS = [
    ('vision detection', 30, 'routine vision detection'),
    ('coherence check', 35, 'coherence heartbeat'),
    ('alert:', 50, 'service down alert (not sacred)'),
]


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def scan_bulk_patterns(conn, dry_run=False):
    """Detect bulk content patterns at high temperature."""
    cur = conn.cursor()
    cur.execute("""
        SELECT LEFT(original_content, %s) as prefix,
               COUNT(*) as cnt,
               AVG(temperature_score) as avg_temp,
               MIN(id) as min_id, MAX(id) as max_id
        FROM thermal_memory_archive
        WHERE temperature_score >= %s
          AND sacred_pattern IS NOT TRUE
        GROUP BY LEFT(original_content, %s)
        HAVING COUNT(*) > %s
        ORDER BY COUNT(*) DESC
        LIMIT 20
    """, (BULK_PREFIX_LENGTH, BULK_PATTERN_MIN_TEMP, BULK_PREFIX_LENGTH, BULK_PATTERN_THRESHOLD))

    findings = []
    for prefix, cnt, avg_temp, min_id, max_id in cur.fetchall():
        target_temp = determine_target_temp(prefix)

        finding = {
            'type': 'bulk_pattern',
            'prefix': prefix.strip()[:80],
            'count': cnt,
            'avg_temp': float(avg_temp),
            'target_temp': target_temp,
            'id_range': f'{min_id}-{max_id}',
        }
        findings.append(finding)
        logger.warning(
            f"BULK PATTERN: {cnt} records, avg_temp={avg_temp:.0f}, "
            f"target={target_temp}, prefix='{prefix.strip()[:60]}...'"
        )

        if not dry_run and target_temp < avg_temp:
            cur.execute("""
                UPDATE thermal_memory_archive
                SET temperature_score = %s,
                    metadata = COALESCE(metadata, '{}'::jsonb) ||
                        jsonb_build_object(
                            'immune_regulated', true,
                            'immune_regulated_at', %s,
                            'original_temp', temperature_score,
                            'regulation_reason', 'bulk_pattern_detected'
                        )
                WHERE LEFT(original_content, %s) = %s
                  AND temperature_score >= %s
                  AND sacred_pattern IS NOT TRUE
            """, (target_temp, datetime.now().isoformat(),
                  BULK_PREFIX_LENGTH, prefix, BULK_PATTERN_MIN_TEMP))
            conn.commit()
            logger.info(f"  REGULATED: {cnt} records dropped to temp {target_temp}")

    return findings


def scan_dormant_hot(conn, dry_run=False):
    """Detect high-temperature memories with no recent access."""
    cur = conn.cursor()
    cutoff = datetime.now() - timedelta(days=DORMANT_DAYS)

    cur.execute("""
        SELECT id, LEFT(original_content, 80), temperature_score,
               COALESCE(access_count, 0), last_access
        FROM thermal_memory_archive
        WHERE temperature_score >= %s
          AND sacred_pattern IS NOT TRUE
          AND (last_access IS NULL OR last_access < %s)
          AND COALESCE(access_count, 0) = 0
        ORDER BY temperature_score DESC
        LIMIT 100
    """, (DORMANT_MIN_TEMP, cutoff))

    findings = []
    dormant_ids = []
    for mem_id, content, temp, acc, last_acc in cur.fetchall():
        findings.append({
            'type': 'dormant_hot',
            'id': mem_id,
            'temp': float(temp),
            'access_count': acc,
            'content_preview': content.strip()[:60],
        })
        dormant_ids.append(mem_id)

    if dormant_ids:
        logger.warning(f"DORMANT HOT: {len(dormant_ids)} memories at temp >= {DORMANT_MIN_TEMP} with zero access in {DORMANT_DAYS}+ days")

        if not dry_run:
            cur.execute("""
                UPDATE thermal_memory_archive
                SET temperature_score = GREATEST(temperature_score - 20, 30),
                    metadata = COALESCE(metadata, '{}'::jsonb) ||
                        jsonb_build_object(
                            'immune_regulated', true,
                            'immune_regulated_at', %s,
                            'regulation_reason', 'dormant_hot_no_access'
                        )
                WHERE id = ANY(%s)
                  AND sacred_pattern IS NOT TRUE
            """, (datetime.now().isoformat(), dormant_ids))
            conn.commit()
            logger.info(f"  REGULATED: {len(dormant_ids)} dormant memories cooled by 20 degrees")

    return findings


def determine_target_temp(prefix):
    """Determine the correct temperature for a content pattern."""
    prefix_lower = prefix.lower().strip()

    for pattern_text, target, reason in TELEMETRY_PATTERNS:
        if prefix_lower.startswith(pattern_text):
            return target

    # Default: if bulk pattern at high temp, reduce to 50 (working memory tier)
    return 50


def log_immune_action(conn, findings, dry_run):
    """Store immune system run results as a thermal memory."""
    if not findings:
        return

    content = f"MEMORY IMMUNE SYSTEM RUN — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    content += f"Mode: {'DRY RUN' if dry_run else 'LIVE'}\n"
    content += f"Findings: {len(findings)}\n"
    for f in findings[:10]:
        if f['type'] == 'bulk_pattern':
            content += f"  BULK: {f['count']} records, avg_temp={f['avg_temp']:.0f} -> {f['target_temp']}, '{f['prefix'][:40]}...'\n"
        elif f['type'] == 'dormant_hot':
            content += f"  DORMANT: #{f['id']} temp={f['temp']:.0f} acc={f['access_count']} '{f['content_preview'][:40]}'\n"

    mem_hash = hashlib.sha256(content.encode()).hexdigest()

    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, temperature_score, sacred_pattern, metadata)
            VALUES (%s, %s, %s, false, %s)
        """, (
            mem_hash, content, 60,
            json.dumps({
                'source': 'memory_immune_system',
                'finding_count': len(findings),
                'dry_run': dry_run,
                'timestamp': datetime.now().isoformat(),
            })
        ))
        conn.commit()
        logger.info(f"Immune system run logged to thermal memory")
    except Exception as e:
        logger.warning(f"Failed to log immune action: {e}")
        conn.rollback()


def main():
    parser = argparse.ArgumentParser(description='Memory Immune System')
    parser.add_argument('--dry-run', action='store_true', help='Scan only, do not regulate')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("MEMORY IMMUNE SYSTEM — Cherokee AI Federation")
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    logger.info("=" * 60)

    conn = get_conn()
    all_findings = []

    logger.info("\n[1/2] Scanning for bulk content patterns...")
    bulk = scan_bulk_patterns(conn, dry_run=args.dry_run)
    all_findings.extend(bulk)

    logger.info("\n[2/2] Scanning for dormant high-temperature memories...")
    dormant = scan_dormant_hot(conn, dry_run=args.dry_run)
    all_findings.extend(dormant)

    log_immune_action(conn, all_findings, args.dry_run)

    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Bulk patterns found: {len(bulk)}")
    logger.info(f"Dormant hot memories: {len(dormant)}")
    if args.dry_run:
        logger.info("DRY RUN — no changes made")
    else:
        logger.info("LIVE — temperatures regulated")
    logger.info("For Seven Generations.")

    conn.close()
    return 1 if all_findings else 0


if __name__ == '__main__':
    sys.exit(main())
```

## Notes

- Run with `--dry-run` first to see what it would do
- Sacred memories (sacred_pattern=true) are NEVER regulated
- Bulk pattern detection uses content prefix matching (first 60 chars)
- Dormant detection only flags zero-access memories at temp >= 80
- Temperature reductions logged in metadata with `immune_regulated=true`
- The script logs its own run as a temp-60 thermal memory for audit trail
- Designed for cron or systemd timer (daily is sufficient)
