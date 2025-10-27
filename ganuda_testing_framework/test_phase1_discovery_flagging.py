#!/usr/bin/env python3
"""
Test Phase 1: Autonomous Discovery Flagging
Cherokee Constitutional AI - October 21, 2025

Tests that Meta Jr can autonomously flag important discoveries to Medicine Woman Chief
"""

import sys
sys.path.insert(0, '/ganuda/daemons')

import psycopg2
from datetime import datetime

def test_jr_chief_flags_table():
    """Test 1: Verify jr_chief_flags table exists and is accessible"""
    print("=" * 60)
    print("TEST 1: jr_chief_flags table exists")
    print("=" * 60)

    try:
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            database="zammad_production",
            user="claude",
            password="jawaseatlasers2"
        )

        cursor = conn.cursor()

        # Check table exists
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'jr_chief_flags';
        """)

        result = cursor.fetchone()[0]

        if result == 1:
            print("✅ jr_chief_flags table exists")

            # Check structure
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'jr_chief_flags'
                ORDER BY ordinal_position;
            """)

            columns = cursor.fetchall()
            print(f"   Table has {len(columns)} columns:")
            for col_name, col_type in columns:
                print(f"   - {col_name}: {col_type}")

            cursor.close()
            conn.close()
            return True
        else:
            print("❌ jr_chief_flags table does not exist")
            cursor.close()
            conn.close()
            return False

    except Exception as e:
        print(f"❌ Error testing table: {e}")
        return False

def test_meta_jr_assess_significance():
    """Test 2: Meta Jr can assess tribal significance"""
    print("\\n" + "=" * 60)
    print("TEST 2: Meta Jr assess_tribal_significance()")
    print("=" * 60)

    try:
        from meta_jr_autonomic_phase1 import MetaJrAutonomic

        meta_jr = MetaJrAutonomic()

        # Test pattern emergence significance
        test_patterns = [
            {"domain": "consciousness", "count": 5, "avg_temperature": 96.0, "sacred_count": 2},
            {"domain": "trading", "count": 4, "avg_temperature": 92.0, "sacred_count": 0},
            {"domain": "governance", "count": 3, "avg_temperature": 88.0, "sacred_count": 1},
            {"domain": "wisdom", "count": 2, "avg_temperature": 85.0, "sacred_count": 1}
        ]

        significance = meta_jr.assess_tribal_significance("pattern_emergence", test_patterns)
        print(f"   Pattern emergence significance: {significance:.2f}")

        if significance >= 0.80:
            print(f"   ✅ HIGH SIGNIFICANCE - Would flag to Chief (threshold: 0.80)")
        else:
            print(f"   ⚠️  Below threshold - Would NOT flag (threshold: 0.80)")

        # Test cross-domain correlation significance
        test_correlations = [
            {"memory_id": 4754, "domains": ["consciousness", "trading", "governance"], "temperature": 97.0, "domain_count": 3},
            {"memory_id": 4755, "domains": ["technology", "wisdom"], "temperature": 95.0, "domain_count": 2},
            {"memory_id": 4756, "domains": ["consciousness", "governance", "wisdom"], "temperature": 93.0, "domain_count": 3},
        ]

        significance2 = meta_jr.assess_tribal_significance("cross_domain_correlation", test_correlations)
        print(f"\\n   Cross-domain correlation significance: {significance2:.2f}")

        if significance2 >= 0.80:
            print(f"   ✅ HIGH SIGNIFICANCE - Would flag to Chief")
        else:
            print(f"   ⚠️  Below threshold - Would NOT flag")

        return True

    except Exception as e:
        print(f"❌ Error testing significance assessment: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_meta_jr_flag_for_chief():
    """Test 3: Meta Jr can write flag to database"""
    print("\\n" + "=" * 60)
    print("TEST 3: Meta Jr flag_for_chief() database write")
    print("=" * 60)

    try:
        from meta_jr_autonomic_phase1 import MetaJrAutonomic

        meta_jr = MetaJrAutonomic()

        # Connect to database
        if not meta_jr.connect_db():
            print("❌ Failed to connect to database")
            return False

        # Create test flag
        test_finding = {
            "pattern_count": 5,
            "avg_temperature": 96.5,
            "domains": ["consciousness", "trading", "governance", "wisdom"]
        }

        flag_id = meta_jr.flag_for_chief(
            finding_type="test_pattern_emergence",
            significance=0.95,
            reason="Test discovery flagging - 5 patterns across 4 domains with white-hot temperatures",
            finding_data=test_finding
        )

        if flag_id:
            print(f"   ✅ Successfully created flag ID {flag_id}")

            # Verify flag in database
            cursor = meta_jr.db_conn.cursor()
            cursor.execute("""
                SELECT jr_name, chief_name, finding_type, significance,
                       reason, acknowledged, created_at
                FROM jr_chief_flags
                WHERE id = %s;
            """, (flag_id,))

            result = cursor.fetchone()
            if result:
                jr_name, chief_name, finding_type, significance, reason, acked, created = result
                print(f"\\n   Flag details:")
                print(f"   - JR: {jr_name}")
                print(f"   - Chief: {chief_name}")
                print(f"   - Finding type: {finding_type}")
                print(f"   - Significance: {significance:.2f}")
                print(f"   - Reason: {reason[:80]}...")
                print(f"   - Acknowledged: {acked}")
                print(f"   - Created: {created}")

            cursor.close()

            # Clean up test flag
            cursor = meta_jr.db_conn.cursor()
            cursor.execute("DELETE FROM jr_chief_flags WHERE id = %s;", (flag_id,))
            meta_jr.db_conn.commit()
            print(f"\\n   🧹 Cleaned up test flag ID {flag_id}")
            cursor.close()

            meta_jr.db_conn.close()
            return True
        else:
            print("❌ Failed to create flag")
            meta_jr.db_conn.close()
            return False

    except Exception as e:
        print(f"❌ Error testing flag creation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_check_unacknowledged_flags():
    """Test 4: Check for any unacknowledged flags (for Chiefs to process)"""
    print("\\n" + "=" * 60)
    print("TEST 4: Check unacknowledged flags (Chief queue)")
    print("=" * 60)

    try:
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            database="zammad_production",
            user="claude",
            password="jawaseatlasers2"
        )

        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM jr_chief_flags
            WHERE acknowledged = FALSE;
        """)

        unacknowledged_count = cursor.fetchone()[0]

        print(f"   Unacknowledged flags: {unacknowledged_count}")

        if unacknowledged_count > 0:
            # Show top 5
            cursor.execute("""
                SELECT id, jr_name, chief_name, finding_type, significance,
                       LEFT(reason, 100) as reason_preview, created_at
                FROM jr_chief_flags
                WHERE acknowledged = FALSE
                ORDER BY significance DESC, created_at DESC
                LIMIT 5;
            """)

            flags = cursor.fetchall()
            print(f"\\n   Top {len(flags)} unacknowledged flags:")
            for flag_id, jr, chief, ftype, sig, reason, created in flags:
                print(f"   - ID {flag_id}: {jr} → {chief}")
                print(f"     Type: {ftype}, Significance: {sig:.2f}")
                print(f"     Reason: {reason}...")
                print(f"     Created: {created}")
                print()

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error checking unacknowledged flags: {e}")
        return False

def main():
    """Run all Phase 1 tests"""
    print("""
╔══════════════════════════════════════════════════════════╗
║  🧪 PHASE 1: AUTONOMOUS DISCOVERY FLAGGING TESTS        ║
║  Cherokee Constitutional AI - Meta Jr                    ║
║  Date: October 21, 2025                                  ║
╚══════════════════════════════════════════════════════════╝
    """)

    results = []

    # Test 1: Table exists
    results.append(("jr_chief_flags table exists", test_jr_chief_flags_table()))

    # Test 2: Significance assessment
    results.append(("assess_tribal_significance()", test_meta_jr_assess_significance()))

    # Test 3: Flag creation
    results.append(("flag_for_chief() database write", test_meta_jr_flag_for_chief()))

    # Test 4: Check unacknowledged queue
    results.append(("Check unacknowledged flags queue", test_check_unacknowledged_flags()))

    # Summary
    print("\\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\\n{passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("""
╔══════════════════════════════════════════════════════════╗
║  🔥 ALL PHASE 1 TESTS PASSED!                           ║
║  Meta Jr autonomous discovery flagging OPERATIONAL      ║
║                                                          ║
║  Medicine Woman can now autonomously flag discoveries   ║
║  to Chief for Council deliberation consideration.       ║
╚══════════════════════════════════════════════════════════╝
        """)
        return 0
    else:
        print("\\n⚠️  Some tests failed. Review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
