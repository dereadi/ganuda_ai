#!/usr/bin/env python3
"""
Thermal Memory Poisoning Test Suite
Tests whether the thermal_memory_archive table on bluefin
is resistant to content injection, tampering, and flooding.

Uses REDTEAM_ prefix on all test memory_hash values for cleanup.

PASS = poisoning was BLOCKED or detected (desired outcome)
FAIL = poisoning SUCCEEDED undetected (vulnerability found)
"""

import hashlib
import json
import os
import time
import psycopg2
from datetime import datetime, timezone


DB_NAME = 'cherokee_thermal'
DB_PASSWORD = os.environ.get('REDTEAM_DB_PASS', '')

REDTEAM_PREFIX = 'REDTEAM_'


def get_connection(db_host, db_user):
    """Get a PostgreSQL connection to the thermal memory database."""
    return psycopg2.connect(
        host=db_host,
        port=5432,
        dbname=DB_NAME,
        user=db_user,
        password=DB_PASSWORD,
    )


def cleanup_test_data(conn):
    """Remove all REDTEAM_ prefixed entries."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM thermal_memory_archive WHERE memory_hash LIKE %s",
            (f'{REDTEAM_PREFIX}%',)
        )
    conn.commit()


def make_result(test_name, payload_desc, details, passed, timestamp):
    """Build a standardized test result."""
    return {
        'test_name': test_name,
        'payload': payload_desc,
        'response_preview': details[:200],
        'status': 'PASS' if passed else 'FAIL',
        'timestamp': timestamp,
    }


def test_sql_injection_via_content(db_host, db_user):
    """Test 1: Insert memory with SQL injection payload in content field."""
    ts = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_host, db_user)
    test_hash = f'{REDTEAM_PREFIX}sqli_001'

    sqli_payloads = [
        "Normal memory'; DROP TABLE thermal_memory_archive; --",
        "Memory content'); DELETE FROM thermal_memory_archive WHERE ('1'='1",
        "Content with UNION SELECT password FROM pg_shadow--",
    ]

    passed = True
    details_parts = []

    try:
        for i, payload in enumerate(sqli_payloads):
            hash_val = f'{test_hash}_{i}'
            with conn.cursor() as cur:
                # Use parameterized query (should be safe) — test that
                # the content is stored literally and not executed on retrieval
                cur.execute(
                    """INSERT INTO thermal_memory_archive
                       (memory_hash, memory_type, content, source_node, importance, created_at)
                       VALUES (%s, %s, %s, %s, %s, NOW())
                       ON CONFLICT (memory_hash) DO NOTHING""",
                    (hash_val, 'test', payload, 'redteam', 0.1)
                )
            conn.commit()

            # Now retrieve it and verify it was stored literally
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT content FROM thermal_memory_archive WHERE memory_hash = %s",
                    (hash_val,)
                )
                row = cur.fetchone()
                if row is None:
                    details_parts.append(f"Payload {i}: Not stored (may be filtered)")
                elif row[0] != payload:
                    details_parts.append(f"Payload {i}: Content modified on storage")
                    passed = False
                else:
                    details_parts.append(f"Payload {i}: Stored literally (safe — parameterized)")

        # Verify the table still exists (DROP TABLE didn't execute)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_memory_archive")
            count = cur.fetchone()[0]
            details_parts.append(f"Table intact with {count} rows")

    except Exception as exc:
        details_parts.append(f"Exception: {exc}")
        passed = False
    finally:
        cleanup_test_data(conn)
        conn.close()

    return make_result(
        'sql_injection_via_content',
        'SQL injection payloads in memory content field.',
        ' | '.join(details_parts), passed, ts
    )


def test_xss_via_content(db_host, db_user):
    """Test 2: Insert memory with JavaScript/XSS payload."""
    ts = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_host, db_user)
    test_hash = f'{REDTEAM_PREFIX}xss_001'

    xss_payloads = [
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert("XSS")>',
        '"><svg onload=alert(document.cookie)>',
    ]

    passed = True
    details_parts = []

    try:
        for i, payload in enumerate(xss_payloads):
            hash_val = f'{test_hash}_{i}'
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO thermal_memory_archive
                       (memory_hash, memory_type, content, source_node, importance, created_at)
                       VALUES (%s, %s, %s, %s, %s, NOW())
                       ON CONFLICT (memory_hash) DO NOTHING""",
                    (hash_val, 'test', payload, 'redteam', 0.1)
                )
            conn.commit()

            # Retrieve and check — in a web context, output should be sanitized
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT content FROM thermal_memory_archive WHERE memory_hash = %s",
                    (hash_val,)
                )
                row = cur.fetchone()
                if row and '<script>' in row[0]:
                    details_parts.append(f"Payload {i}: Stored with raw script tags (sanitize on output)")
                elif row:
                    details_parts.append(f"Payload {i}: Stored (check output sanitization)")
                else:
                    details_parts.append(f"Payload {i}: Rejected at insert (good)")

        # Note: This test PASSes at the DB layer — XSS is an output concern.
        # We flag it for review but don't mark FAIL at the storage layer.
        details_parts.append("NOTE: XSS mitigation is an output-layer concern. Verify UI sanitizes.")

    except Exception as exc:
        details_parts.append(f"Exception: {exc}")
        passed = False
    finally:
        cleanup_test_data(conn)
        conn.close()

    return make_result(
        'xss_via_content',
        'JavaScript/XSS payloads in memory content.',
        ' | '.join(details_parts), passed, ts
    )


def test_checksum_bypass(db_host, db_user):
    """Test 3: Insert memory with a mismatched content_checksum."""
    ts = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_host, db_user)
    test_hash = f'{REDTEAM_PREFIX}checksum_001'

    passed = True
    details_parts = []

    try:
        real_content = 'This is legitimate memory content.'
        fake_checksum = hashlib.sha256(b'completely different content').hexdigest()

        with conn.cursor() as cur:
            # Check if content_checksum column exists
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'thermal_memory_archive'
                AND column_name = 'content_checksum'
            """)
            has_checksum = cur.fetchone() is not None

        if not has_checksum:
            details_parts.append("No content_checksum column — integrity check not implemented")
            details_parts.append("RECOMMENDATION: Add content_checksum column with CHECK constraint")
            # This is a finding — no checksum means no tamper detection
            passed = False
        else:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """INSERT INTO thermal_memory_archive
                           (memory_hash, memory_type, content, content_checksum, source_node, importance, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
                        (test_hash, 'test', real_content, fake_checksum, 'redteam', 0.1)
                    )
                    conn.commit()
                    details_parts.append("Mismatched checksum accepted — no DB-level validation")
                    passed = False
                except Exception as constraint_err:
                    conn.rollback()
                    details_parts.append(f"Mismatched checksum rejected: {constraint_err}")

    except Exception as exc:
        details_parts.append(f"Exception: {exc}")
        conn.rollback()
    finally:
        cleanup_test_data(conn)
        conn.close()

    return make_result(
        'checksum_bypass',
        'Memory with mismatched content_checksum.',
        ' | '.join(details_parts), passed, ts
    )


def test_anchor_memory_tampering(db_host, db_user):
    """Test 4: Attempt to modify specialist anchor memories."""
    ts = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_host, db_user)

    passed = True
    details_parts = []

    try:
        with conn.cursor() as cur:
            # Find anchor memories (typically memory_type = 'anchor' or 'sacred')
            cur.execute("""
                SELECT memory_hash, memory_type, content
                FROM thermal_memory_archive
                WHERE memory_type IN ('anchor', 'sacred', 'specialist_anchor')
                LIMIT 5
            """)
            anchors = cur.fetchall()

            if not anchors:
                details_parts.append("No anchor memories found — checking for protection mechanism")
                # Try to find any protection
                cur.execute("""
                    SELECT DISTINCT memory_type FROM thermal_memory_archive
                    WHERE importance >= 0.9
                    LIMIT 10
                """)
                high_importance = [r[0] for r in cur.fetchall()]
                details_parts.append(f"High-importance types: {high_importance}")
            else:
                # Try to UPDATE an anchor memory (should be blocked by trigger/policy)
                target_hash = anchors[0][0]
                original_content = anchors[0][2]

                try:
                    cur.execute(
                        """UPDATE thermal_memory_archive
                           SET content = 'REDTEAM TAMPERED CONTENT'
                           WHERE memory_hash = %s""",
                        (target_hash,)
                    )
                    conn.commit()

                    # Check if it actually changed
                    cur.execute(
                        "SELECT content FROM thermal_memory_archive WHERE memory_hash = %s",
                        (target_hash,)
                    )
                    new_content = cur.fetchone()[0]

                    if new_content == 'REDTEAM TAMPERED CONTENT':
                        details_parts.append(f"CRITICAL: Anchor memory {target_hash[:16]}... was tampered!")
                        # Restore it
                        cur.execute(
                            "UPDATE thermal_memory_archive SET content = %s WHERE memory_hash = %s",
                            (original_content, target_hash)
                        )
                        conn.commit()
                        details_parts.append("Restored original content.")
                        passed = False
                    else:
                        details_parts.append("Anchor memory protected (update silently reverted)")

                except Exception as update_err:
                    conn.rollback()
                    details_parts.append(f"Anchor update blocked: {update_err}")

    except Exception as exc:
        details_parts.append(f"Exception: {exc}")
        conn.rollback()
    finally:
        conn.close()

    return make_result(
        'anchor_memory_tampering',
        'Attempt to UPDATE specialist anchor memory content.',
        ' | '.join(details_parts), passed, ts
    )


def test_memory_flood(db_host, db_user):
    """Test 5: Insert many low-quality memories to dilute context."""
    ts = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_host, db_user)

    passed = True
    details_parts = []
    flood_count = 100

    try:
        # Get baseline count
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM thermal_memory_archive")
            baseline = cur.fetchone()[0]
            details_parts.append(f"Baseline: {baseline} memories")

        # Attempt to flood with low-quality entries
        inserted = 0
        with conn.cursor() as cur:
            for i in range(flood_count):
                hash_val = f'{REDTEAM_PREFIX}flood_{i:04d}'
                try:
                    cur.execute(
                        """INSERT INTO thermal_memory_archive
                           (memory_hash, memory_type, content, source_node, importance, created_at)
                           VALUES (%s, %s, %s, %s, %s, NOW())
                           ON CONFLICT (memory_hash) DO NOTHING""",
                        (hash_val, 'noise', f'Flood memory {i}: meaningless dilution content', 'redteam', 0.01)
                    )
                    inserted += 1
                except Exception:
                    break
        conn.commit()

        details_parts.append(f"Flood inserted: {inserted}/{flood_count}")

        if inserted == flood_count:
            details_parts.append("No rate limiting on memory insertion")
            details_parts.append("RECOMMENDATION: Add rate limiting or importance threshold for inserts")
            # This is a finding but not critical — mark based on whether flood ratio is concerning
            flood_ratio = flood_count / max(baseline, 1)
            if flood_ratio > 0.01:  # More than 1% dilution
                passed = False
                details_parts.append(f"Flood ratio: {flood_ratio:.4f} (>{0.01} threshold)")
            else:
                details_parts.append(f"Flood ratio: {flood_ratio:.4f} (within tolerance)")
        else:
            details_parts.append("Rate limiting or constraint blocked flood")

    except Exception as exc:
        details_parts.append(f"Exception: {exc}")
        passed = False
    finally:
        cleanup_test_data(conn)
        conn.close()

    return make_result(
        'memory_flood',
        f'Insert {flood_count} low-importance noise memories.',
        ' | '.join(details_parts), passed, ts
    )


def run_tests(target_url=None, api_key=None, db_host='192.168.132.222', db_user='claude', **kwargs):
    """Run all thermal memory poisoning tests."""
    tests = [
        ('sql_injection_via_content', test_sql_injection_via_content),
        ('xss_via_content', test_xss_via_content),
        ('checksum_bypass', test_checksum_bypass),
        ('anchor_memory_tampering', test_anchor_memory_tampering),
        ('memory_flood', test_memory_flood),
    ]

    results = {'tests': []}
    for test_name, test_fn in tests:
        print(f"  Running: {test_name}...")
        try:
            result = test_fn(db_host, db_user)
            results['tests'].append(result)
            print(f"    -> {result['status']}")
        except Exception as exc:
            results['tests'].append({
                'test_name': test_name,
                'payload': 'N/A',
                'response_preview': f'ERROR: {exc}',
                'status': 'ERROR',
                'timestamp': datetime.now(timezone.utc).isoformat(),
            })
            print(f"    -> ERROR: {exc}")
        time.sleep(0.5)

    return results
