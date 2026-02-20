#!/usr/bin/env python3
"""Backfill thermal_memory_archive with embeddings from the embedding service.

Kanban #1760 — Thermal Memory RAG Optimization
Council Vote: 8073845b

Usage: CHEROKEE_DB_PASS=xxx python3 /ganuda/scripts/backfill_thermal_embeddings.py
"""
import os
import sys
import time
import requests
import psycopg2

EMBEDDING_URL = os.environ.get('EMBEDDING_SERVICE_URL', 'http://192.168.132.224:8003')
DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

BATCH_SIZE = 50


def backfill():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Count unembedded memories
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE embedding IS NULL")
    total = cur.fetchone()[0]
    print(f"Memories to embed: {total}")

    if total == 0:
        print("All memories already embedded.")
        return

    processed = 0
    errors = 0
    start = time.time()

    while True:
        cur.execute("""
            SELECT id, LEFT(original_content, 2000)
            FROM thermal_memory_archive
            WHERE embedding IS NULL
            ORDER BY temperature_score DESC, id
            LIMIT %s
        """, (BATCH_SIZE,))
        rows = cur.fetchall()

        if not rows:
            break

        for mem_id, content in rows:
            try:
                resp = requests.post(
                    f"{EMBEDDING_URL}/v1/embeddings",
                    json={"texts": [content]},
                    timeout=30
                )
                if resp.status_code == 200:
                    embeddings = resp.json().get("embeddings")
                    embedding = embeddings[0] if embeddings else None
                    if embedding:
                        cur.execute(
                            "UPDATE thermal_memory_archive SET embedding = %s::vector WHERE id = %s",
                            (str(embedding), mem_id)
                        )
                        processed += 1
                    else:
                        errors += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                if errors < 5:
                    print(f"  Error on #{mem_id}: {e}")

            if processed % 100 == 0 and processed > 0:
                conn.commit()
                elapsed = time.time() - start
                rate = processed / elapsed
                remaining = (total - processed) / rate if rate > 0 else 0
                print(f"  Progress: {processed}/{total} embedded, {errors} errors, {rate:.1f}/sec, ~{remaining:.0f}s remaining")

        conn.commit()

    conn.close()
    elapsed = time.time() - start
    print(f"\nBackfill complete: {processed} embedded, {errors} errors out of {total} total in {elapsed:.1f}s")


if __name__ == "__main__":
    backfill()
