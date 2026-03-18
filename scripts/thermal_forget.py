#!/usr/bin/env python3
"""
Thermal Forgetting Protocol — Active Memory Pruning

Foundation Agents GAP 3. Longhouse c4e68ce0fcea60a3.
DC-9: Waste Heat Limit — every joule becomes heat. Prune what doesn't matter.

Moves cold, non-sacred, low-access thermals older than 30 days to cold_thermal_archive.
Sacred thermals are NEVER touched. This is a hard invariant.

Runs weekly via systemd timer (Sunday 3 AM CT).
"""

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

# Forgetting criteria
TEMP_THRESHOLD = 10          # below this = cold
ACCESS_COUNT_THRESHOLD = 3   # below this = rarely used
AGE_DAYS = 30                # must be this old
REINDEX_THRESHOLD = 1000     # reindex HNSW if more than this many rows removed

# Emergency brake check — respect the kill switch
BRAKE_STATE_FILE = "/ganuda/state/emergency_brake.json"


def load_secrets():
    global DB_PASS
    if not DB_PASS:
        try:
            with open("/ganuda/config/secrets.env") as f:
                for line in f:
                    m = re.match(r"^(\w+)=(.+)$", line.strip())
                    if m:
                        os.environ[m.group(1)] = m.group(2)
            DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
        except FileNotFoundError:
            pass


def check_brake():
    """Respect the emergency brake."""
    try:
        with open(BRAKE_STATE_FILE) as f:
            state = json.load(f)
        if state.get("brake_engaged"):
            print(f"EMERGENCY BRAKE ENGAGED — skipping thermal forgetting. Reason: {state.get('reason')}")
            return True
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return False


def ensure_cold_archive(cur):
    """Create cold_thermal_archive if it doesn't exist."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cold_thermal_archive (
            LIKE thermal_memory_archive INCLUDING DEFAULTS INCLUDING CONSTRAINTS
        )
    """)
    # Drop any HNSW indexes that got copied — that's the whole point of cold storage
    cur.execute("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'cold_thermal_archive' AND indexdef LIKE '%hnsw%'
    """)
    for (idx_name,) in cur.fetchall():
        print(f"  Dropping HNSW index on cold archive: {idx_name}")
        cur.execute(f"DROP INDEX IF EXISTS {idx_name}")

    # Ensure basic btree indexes for retrieval
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_cold_thermal_id ON cold_thermal_archive (id);
        CREATE INDEX IF NOT EXISTS idx_cold_thermal_created ON cold_thermal_archive (created_at);
    """)


def find_eligible_thermals(cur):
    """Find thermals eligible for forgetting. Sacred thermals are EXCLUDED."""
    cur.execute("""
        SELECT t.id
        FROM thermal_memory_archive t
        WHERE t.temperature_score < %s
          AND t.sacred_pattern = false
          AND t.access_count < %s
          AND t.created_at < NOW() - INTERVAL '%s days'
          AND NOT EXISTS (
              SELECT 1 FROM thermal_relationships tr
              WHERE tr.source_memory_id = t.id OR tr.target_memory_id = t.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM thermal_entity_links tel
              WHERE tel.thermal_id = t.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM thermal_heat_map thm
              WHERE thm.memory_id = t.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM memory_chunks mc
              WHERE mc.parent_memory_id = t.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM memory_retrieval_log mrl
              WHERE mrl.memory_id = t.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM jewel_feedback jf
              WHERE jf.jewel_thermal_id = t.id
          )
        ORDER BY t.temperature_score ASC, t.created_at ASC
    """, (TEMP_THRESHOLD, ACCESS_COUNT_THRESHOLD, AGE_DAYS))
    return [row[0] for row in cur.fetchall()]


def archive_thermals(cur, ids):
    """Move thermals to cold archive. Returns count archived."""
    if not ids:
        return 0

    # Safety check: verify NONE are sacred (belt AND suspenders)
    placeholders = ','.join(['%s'] * len(ids))
    cur.execute(f"""
        SELECT COUNT(*) FROM thermal_memory_archive
        WHERE id IN ({placeholders}) AND sacred_pattern = true
    """, ids)
    sacred_count = cur.fetchone()[0]
    if sacred_count > 0:
        print(f"  ABORT: {sacred_count} sacred thermal(s) in candidate set! This should never happen.")
        print("  SACRED THERMALS WERE NOT TOUCHED. Investigate query logic.")
        return 0

    # Copy to cold archive
    cur.execute(f"""
        INSERT INTO cold_thermal_archive
        SELECT * FROM thermal_memory_archive
        WHERE id IN ({placeholders})
        ON CONFLICT DO NOTHING
    """, ids)
    archived = cur.rowcount

    # Delete from hot archive
    cur.execute(f"""
        DELETE FROM thermal_memory_archive
        WHERE id IN ({placeholders})
    """, ids)
    deleted = cur.rowcount

    return deleted


def find_unused_indexes(cur):
    """Find indexes on thermal_memory_archive with zero scans."""
    cur.execute("""
        SELECT indexrelname, pg_size_pretty(pg_relation_size(indexrelid)) as size,
               pg_relation_size(indexrelid) as size_bytes
        FROM pg_stat_user_indexes
        WHERE relname = 'thermal_memory_archive'
          AND idx_scan = 0
          AND indexrelname NOT LIKE '%pkey%'
        ORDER BY pg_relation_size(indexrelid) DESC
    """)
    return cur.fetchall()


def run_forgetting(dry_run=False):
    """Execute the forgetting protocol."""
    import psycopg2

    load_secrets()
    if check_brake():
        return

    start = time.time()
    conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME,
                            user=DB_USER, password=DB_PASS, connect_timeout=10)
    conn.autocommit = False
    cur = conn.cursor()

    print(f"Thermal Forgetting Protocol — {datetime.now().isoformat()}")
    print(f"Criteria: temp < {TEMP_THRESHOLD}, access < {ACCESS_COUNT_THRESHOLD}, age > {AGE_DAYS} days, not sacred, no refs")

    # Current state
    cur.execute("SELECT COUNT(*), pg_size_pretty(pg_total_relation_size('thermal_memory_archive')) FROM thermal_memory_archive")
    total_count, total_size = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE sacred_pattern = true")
    sacred_count = cur.fetchone()[0]
    print(f"Current: {total_count} thermals ({total_size}), {sacred_count} sacred")

    # Ensure cold archive exists
    ensure_cold_archive(cur)
    conn.commit()

    # Find eligible thermals
    eligible = find_eligible_thermals(cur)
    print(f"Eligible for forgetting: {len(eligible)}")

    if dry_run:
        print("DRY RUN — no changes made")
        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()
        return

    if not eligible:
        print("Nothing to forget. Memory is lean.")
        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()
        return

    # Archive in batches of 1000
    total_archived = 0
    batch_size = 1000
    for i in range(0, len(eligible), batch_size):
        batch = eligible[i:i + batch_size]
        archived = archive_thermals(cur, batch)
        total_archived += archived
        conn.commit()
        print(f"  Batch {i // batch_size + 1}: archived {archived} thermals")

    # Post-archive state
    cur.execute("SELECT COUNT(*), pg_size_pretty(pg_total_relation_size('thermal_memory_archive')) FROM thermal_memory_archive")
    new_count, new_size = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM cold_thermal_archive")
    cold_count = cur.fetchone()[0]

    print(f"After: {new_count} thermals ({new_size}), {cold_count} in cold archive")
    print(f"Archived: {total_archived} thermals")

    # Find unused indexes
    unused = find_unused_indexes(cur)
    if unused:
        print(f"\nUnused indexes ({len(unused)}):")
        for idx_name, size_pretty, size_bytes in unused:
            print(f"  {idx_name}: {size_pretty} (zero scans)")
            # Only auto-drop small ones (<10MB). Large ones need council approval.
            if size_bytes < 10 * 1024 * 1024:
                cur.execute(f"DROP INDEX IF EXISTS {idx_name}")
                conn.commit()
                print(f"    DROPPED (< 10MB, auto-approved)")
            else:
                print(f"    KEPT (> 10MB, needs council approval)")

    # Reindex HNSW if enough rows were removed
    if total_archived >= REINDEX_THRESHOLD:
        print(f"\nReindexing HNSW (removed {total_archived} rows, threshold {REINDEX_THRESHOLD})...")
        conn.commit()
        conn.autocommit = True
        try:
            cur.execute("REINDEX INDEX CONCURRENTLY idx_thermal_memory_embedding_hnsw")
            print("  HNSW reindex complete")
        except Exception as e:
            print(f"  HNSW reindex skipped: {e}")
        conn.autocommit = False

    # Log to thermal memory
    duration = time.time() - start
    log_content = (f"THERMAL FORGETTING PROTOCOL — {datetime.now().strftime('%Y-%m-%d')}. "
                   f"Archived {total_archived} cold thermals to cold_thermal_archive. "
                   f"Before: {total_count} ({total_size}). After: {new_count} ({new_size}). "
                   f"Sacred untouched: {sacred_count}. Duration: {duration:.1f}s.")
    memory_hash = hashlib.sha256(log_content.encode()).hexdigest()
    try:
        cur.execute("""INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash, metadata)
            VALUES (%s, 75, false, %s, %s::jsonb)
            ON CONFLICT (memory_hash) DO NOTHING""",
            (log_content, memory_hash,
             json.dumps({"source": "thermal_forget", "archived": total_archived,
                         "before": total_count, "after": new_count, "duration_s": round(duration, 1)})))
        conn.commit()
    except Exception:
        pass

    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()
    print(f"\nDone in {duration:.1f}s")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Thermal Forgetting Protocol — DC-9 compliance")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be forgotten without doing it")
    args = parser.parse_args()

    run_forgetting(dry_run=args.dry_run)
