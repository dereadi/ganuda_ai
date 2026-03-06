"""
Backfill entity links from existing thermal metadata JSONB.
Scans thermal_memory_archive.metadata for known entity references
and creates corresponding thermal_entity_links rows.

Safe to run multiple times (idempotent — checks for existing links).
"""

import psycopg2
import psycopg2.extras
import json
import re
import os
import sys

def get_connection():
    try:
        sys.path.insert(0, '/ganuda/lib')
        from ganuda_db import get_db_config
        return psycopg2.connect(**get_db_config())
    except Exception:
        return psycopg2.connect(
            host='192.168.132.222',
            dbname='zammad_production',
            user='claude',
            password=os.environ.get('CHEROKEE_DB_PASS', '')
        )

def backfill():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    insert_cur = conn.cursor()

    linked = 0
    skipped = 0

    # Pattern: metadata contains council_vote hash
    cur.execute("""
        SELECT id, metadata FROM thermal_memory_archive
        WHERE metadata IS NOT NULL
        AND (metadata::text LIKE '%council_vote%' OR metadata::text LIKE '%audit_hash%'
             OR metadata::text LIKE '%task_id%' OR metadata::text LIKE '%kanban%'
             OR metadata::text LIKE '%parent_thermal%')
        ORDER BY id
    """)

    for row in cur:
        meta = row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'])
        thermal_id = row['id']

        links_to_insert = []

        # Council vote references
        for key in ('council_vote', 'audit_hash', 'vote_hash'):
            if key in meta and meta[key]:
                links_to_insert.append(('council_vote', str(meta[key]), 'references'))

        # Jr task references
        for key in ('task_id', 'jr_task_id', 'jr_task'):
            if key in meta and meta[key]:
                links_to_insert.append(('jr_task', str(meta[key]), 'references'))

        # Kanban references
        for key in ('kanban_id', 'kanban', 'ticket_id'):
            if key in meta and meta[key]:
                links_to_insert.append(('kanban_ticket', str(meta[key]), 'references'))

        # Parent thermal references
        if 'parent_thermal' in meta and meta['parent_thermal']:
            links_to_insert.append(('thermal', str(meta['parent_thermal']), 'caused_by'))

        for entity_type, entity_id, link_type in links_to_insert:
            # Idempotent: skip if link already exists
            insert_cur.execute("""
                INSERT INTO thermal_entity_links (thermal_id, entity_type, entity_id, link_type, created_by)
                SELECT %s, %s, %s, %s, 'backfill'
                WHERE NOT EXISTS (
                    SELECT 1 FROM thermal_entity_links
                    WHERE thermal_id = %s AND entity_type = %s AND entity_id = %s
                )
            """, (thermal_id, entity_type, entity_id, link_type,
                  thermal_id, entity_type, entity_id))
            if insert_cur.rowcount > 0:
                linked += 1
            else:
                skipped += 1

    # Also scan original_content for council vote hash patterns
    cur.execute("""
        SELECT id, original_content FROM thermal_memory_archive
        WHERE original_content LIKE '%COUNCIL VOTE%'
        AND original_content ~ '[0-9a-f]{16}'
        ORDER BY id
    """)

    vote_hash_pattern = re.compile(r'#([0-9a-f]{16})')
    for row in cur:
        thermal_id = row['id']
        for match in vote_hash_pattern.finditer(row['original_content']):
            vote_hash = match.group(1)
            insert_cur.execute("""
                INSERT INTO thermal_entity_links (thermal_id, entity_type, entity_id, link_type, created_by)
                SELECT %s, 'council_vote', %s, 'references', 'backfill_content_scan'
                WHERE NOT EXISTS (
                    SELECT 1 FROM thermal_entity_links
                    WHERE thermal_id = %s AND entity_type = 'council_vote' AND entity_id = %s
                )
            """, (thermal_id, vote_hash, thermal_id, vote_hash))
            if insert_cur.rowcount > 0:
                linked += 1

    conn.commit()
    print(f"Backfill complete: {linked} links created, {skipped} duplicates skipped")

    # Stats
    stats_cur = conn.cursor()
    stats_cur.execute("SELECT entity_type, COUNT(*) FROM thermal_entity_links GROUP BY entity_type ORDER BY COUNT(*) DESC")
    print("\nEntity link distribution:")
    for row in stats_cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()

if __name__ == '__main__':
    backfill()