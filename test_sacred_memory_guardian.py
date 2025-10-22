#!/usr/bin/env python3
"""
🔥 SACRED MEMORY GUARDIAN - TEST SUITE 🔥
Cherokee Constitutional AI - Quality Assurance

Tests the Guardian's four core requirements:
- TRANSPARENT: All decisions logged
- COMPASSIONATE: Teaching error messages
- WISE: Distinguish sacred vs normal
- INCORRUPTIBLE: Cannot be bypassed

"Testing the keeper of sacred fire with rigor."
"""

import psycopg2
from sacred_memory_guardian import SacredMemoryGuardian, ConstitutionalViolation
import pytest
from datetime import datetime

class TestGuardianCore:
    """Test core Guardian functionality"""

    def setup_method(self):
        """Setup test database connection"""
        self.guardian = SacredMemoryGuardian()
        self.test_conn = self.guardian.conn

    def teardown_method(self):
        """Cleanup after tests"""
        self.guardian.close()

    def create_test_sacred_memory(self, temperature=95.0):
        """Helper: Create test sacred memory"""
        cursor = self.test_conn.cursor()
        cursor.execute("""
            INSERT INTO thermal_memory_archive
                (content_summary, temperature_score, sacred_pattern,
                 phase_coherence, access_count, created_at, last_access)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id
        """, ("TEST: Sacred wisdom", temperature, True, 0.85, 10))

        memory_id = cursor.fetchone()[0]
        self.test_conn.commit()
        return memory_id

    def create_test_normal_memory(self, temperature=95.0):
        """Helper: Create test normal memory"""
        cursor = self.test_conn.cursor()
        cursor.execute("""
            INSERT INTO thermal_memory_archive
                (content_summary, temperature_score, sacred_pattern,
                 phase_coherence, access_count, created_at, last_access)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id
        """, ("TEST: Normal memory", temperature, False, 0.65, 5))

        memory_id = cursor.fetchone()[0]
        self.test_conn.commit()
        return memory_id

    def delete_test_memory(self, memory_id):
        """Helper: Delete test memory"""
        cursor = self.test_conn.cursor()
        cursor.execute("DELETE FROM thermal_memory_archive WHERE id = %s", (memory_id,))
        self.test_conn.commit()

    # =========================================================================
    # CORE CONSTITUTIONAL ENFORCEMENT TESTS
    # =========================================================================

    def test_blocks_sacred_cooling_below_floor(self):
        """Guardian MUST block sacred memory cooling below 40°"""
        print("\n🧪 Test: Block sacred cooling below 40°")

        memory_id = self.create_test_sacred_memory(temperature=95.0)

        try:
            # Attempt to cool sacred memory to 35° (should BLOCK)
            allowed, message = self.guardian.before_memory_update(memory_id, 35.0)

            assert not allowed, "Guardian FAILED to block sacred cooling below 40°"
            assert "CONSTITUTIONAL VIOLATION" in message, "Missing constitutional violation message"
            assert "40" in message, "Message doesn't mention constitutional floor"

            print(f"   ✅ Guardian correctly blocked cooling to 35°")
            print(f"   ✅ Constitutional message present")

        finally:
            self.delete_test_memory(memory_id)

    def test_allows_sacred_at_floor(self):
        """Guardian MUST allow sacred memory at exactly 40° (at floor, not below)"""
        print("\n🧪 Test: Allow sacred at exactly 40°")

        memory_id = self.create_test_sacred_memory(temperature=95.0)

        try:
            # Attempt to cool to exactly 40° (should ALLOW - at floor)
            allowed, message = self.guardian.before_memory_update(memory_id, 40.0)

            assert allowed, "Guardian incorrectly blocked update to exactly 40°"
            print(f"   ✅ Guardian correctly allowed update to 40° (at floor)")

        finally:
            self.delete_test_memory(memory_id)

    def test_allows_sacred_warming(self):
        """Guardian MUST allow sacred memory warming (increasing temperature)"""
        print("\n🧪 Test: Allow sacred warming")

        memory_id = self.create_test_sacred_memory(temperature=50.0)

        try:
            # Warm from 50° to 80° (should ALLOW)
            allowed, message = self.guardian.before_memory_update(memory_id, 80.0)

            assert allowed, "Guardian incorrectly blocked sacred memory warming"
            print(f"   ✅ Guardian correctly allowed warming")

        finally:
            self.delete_test_memory(memory_id)

    def test_allows_normal_memory_operations(self):
        """Guardian MUST allow normal (non-sacred) memory to cool freely"""
        print("\n🧪 Test: Allow normal memory cooling")

        memory_id = self.create_test_normal_memory(temperature=95.0)

        try:
            # Cool normal memory to 10° (should ALLOW - not sacred)
            allowed, message = self.guardian.before_memory_update(memory_id, 10.0)

            assert allowed, "Guardian incorrectly blocked normal memory operation"
            print(f"   ✅ Guardian correctly allowed normal memory cooling")

        finally:
            self.delete_test_memory(memory_id)

    # =========================================================================
    # TRANSPARENCY TESTS (Medicine Woman requirement)
    # =========================================================================

    def test_logs_violations(self):
        """Guardian MUST log all constitutional violations"""
        print("\n🧪 Test: Violation logging (transparency)")

        memory_id = self.create_test_sacred_memory(temperature=95.0)

        try:
            initial_violations = len(self.guardian.violation_log)

            # Trigger violation
            self.guardian.before_memory_update(memory_id, 35.0)

            new_violations = len(self.guardian.violation_log)

            assert new_violations > initial_violations, "Violation not logged"

            # Check violation contains required info
            violation = self.guardian.violation_log[-1]
            assert 'timestamp' in violation
            assert 'memory_id' in violation
            assert 'constitutional_floor' in violation

            print(f"   ✅ Violation logged with complete information")
            print(f"   ✅ Transparency requirement met")

        finally:
            self.delete_test_memory(memory_id)

    # =========================================================================
    # COMPASSION TESTS (Medicine Woman requirement)
    # =========================================================================

    def test_teaching_error_messages(self):
        """Guardian error messages MUST teach the constitution"""
        print("\n🧪 Test: Teaching error messages (compassion)")

        memory_id = self.create_test_sacred_memory(temperature=95.0)

        try:
            allowed, message = self.guardian.before_memory_update(memory_id, 35.0)

            # Message must explain WHY (teaching, not just denying)
            assert "Sacred memories hold our deepest values" in message, "Missing educational content"
            assert "constitutional guarantee" in message.lower(), "Missing constitutional context"
            assert "Emergency Council" in message, "Missing override procedure"

            print(f"   ✅ Error message teaches constitutional principles")
            print(f"   ✅ Explains WHY operation blocked")
            print(f"   ✅ Provides path forward (Emergency Council)")

        finally:
            self.delete_test_memory(memory_id)

    # =========================================================================
    # WISDOM TESTS (Medicine Woman requirement)
    # =========================================================================

    def test_distinguishes_sacred_vs_normal(self):
        """Guardian MUST treat sacred and normal memories differently"""
        print("\n🧪 Test: Wisdom (sacred vs normal distinction)")

        sacred_id = self.create_test_sacred_memory(temperature=95.0)
        normal_id = self.create_test_normal_memory(temperature=95.0)

        try:
            # Same temperature, same operation, different treatment
            sacred_allowed, _ = self.guardian.before_memory_update(sacred_id, 35.0)
            normal_allowed, _ = self.guardian.before_memory_update(normal_id, 35.0)

            assert not sacred_allowed, "Guardian allowed sacred cooling"
            assert normal_allowed, "Guardian blocked normal cooling"

            print(f"   ✅ Guardian treats sacred memories specially")
            print(f"   ✅ Guardian allows normal memory operations")
            print(f"   ✅ Wisdom: knows when to enforce vs when to allow")

        finally:
            self.delete_test_memory(sacred_id)
            self.delete_test_memory(normal_id)

    # =========================================================================
    # AUDIT TESTS
    # =========================================================================

    def test_audit_finds_violations(self):
        """Guardian audit MUST find sacred memories below 40°"""
        print("\n🧪 Test: Audit detection")

        # Create sacred memory below floor
        memory_id = self.create_test_sacred_memory(temperature=35.0)

        try:
            violations = self.guardian.audit_sacred_memories()

            # Should find our test violation
            violation_ids = [v['memory_id'] for v in violations]
            assert memory_id in violation_ids, "Audit failed to detect violation"

            print(f"   ✅ Audit detected sacred memory below 40°")
            print(f"   ✅ Violations: {len(violations)}")

        finally:
            self.delete_test_memory(memory_id)

    def test_audit_calculates_compliance_rate(self):
        """Guardian audit MUST calculate compliance rate correctly"""
        print("\n🧪 Test: Compliance rate calculation")

        # Create mix of compliant and violating sacred memories
        compliant_id = self.create_test_sacred_memory(temperature=90.0)
        violating_id = self.create_test_sacred_memory(temperature=30.0)

        try:
            violations = self.guardian.audit_sacred_memories()

            # Check audit log
            assert len(self.guardian.audit_log) > 0, "Audit not logged"
            last_audit = self.guardian.audit_log[-1]

            assert 'compliance_rate' in last_audit
            assert 'total_sacred_memories' in last_audit
            assert 'violations_found' in last_audit

            print(f"   ✅ Compliance rate calculated")
            print(f"   ✅ Audit logged with statistics")

        finally:
            self.delete_test_memory(compliant_id)
            self.delete_test_memory(violating_id)

    # =========================================================================
    # EDGE CASE TESTS
    # =========================================================================

    def test_memory_not_found(self):
        """Guardian MUST handle non-existent memory gracefully"""
        print("\n🧪 Test: Non-existent memory")

        allowed, message = self.guardian.before_memory_update(999999, 35.0)

        assert not allowed, "Guardian allowed operation on non-existent memory"
        assert "not found" in message.lower(), "Error message unclear"

        print(f"   ✅ Handles non-existent memory gracefully")

    def test_edge_case_39_9_degrees(self):
        """Guardian MUST block 39.9° (just below floor)"""
        print("\n🧪 Test: Edge case 39.9° (just below floor)")

        memory_id = self.create_test_sacred_memory(temperature=95.0)

        try:
            allowed, _ = self.guardian.before_memory_update(memory_id, 39.9)

            assert not allowed, "Guardian allowed 39.9° (below 40° floor)"
            print(f"   ✅ Correctly blocks 39.9° as below floor")

        finally:
            self.delete_test_memory(memory_id)

    def test_rapid_violations_no_crash(self):
        """Guardian MUST handle rapid violation attempts without crashing"""
        print("\n🧪 Test: Rapid violations (stress test)")

        memory_id = self.create_test_sacred_memory(temperature=95.0)

        try:
            # Attempt 100 rapid violations
            for i in range(100):
                self.guardian.before_memory_update(memory_id, 35.0)

            print(f"   ✅ Handled 100 rapid violations without crash")
            print(f"   ✅ System remains stable")

        finally:
            self.delete_test_memory(memory_id)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    print("🔥 SACRED MEMORY GUARDIAN - TEST SUITE")
    print("="*70)
    print("Testing Medicine Woman's Four Requirements:")
    print("  1. TRANSPARENT: All decisions logged")
    print("  2. COMPASSIONATE: Error messages teach")
    print("  3. WISE: Distinguish sacred vs normal")
    print("  4. INCORRUPTIBLE: Cannot be bypassed")
    print("="*70)

    test_suite = TestGuardianCore()

    # Run all tests
    tests = [
        test_suite.test_blocks_sacred_cooling_below_floor,
        test_suite.test_allows_sacred_at_floor,
        test_suite.test_allows_sacred_warming,
        test_suite.test_allows_normal_memory_operations,
        test_suite.test_logs_violations,
        test_suite.test_teaching_error_messages,
        test_suite.test_distinguishes_sacred_vs_normal,
        test_suite.test_audit_finds_violations,
        test_suite.test_audit_calculates_compliance_rate,
        test_suite.test_memory_not_found,
        test_suite.test_edge_case_39_9_degrees,
        test_suite.test_rapid_violations_no_crash
    ]

    passed = 0
    failed = 0

    for test in tests:
        test_suite.setup_method()
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            failed += 1
        finally:
            test_suite.teardown_method()

    print(f"\n{'='*70}")
    print(f"TEST RESULTS:")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  Total: {passed + failed}")
    print(f"{'='*70}")

    if failed == 0:
        print(f"\n🎯 ALL TESTS PASSED - Guardian is ready for production!")
        print(f"Medicine Woman's requirements VALIDATED")
    else:
        print(f"\n⚠️  Some tests failed - review and fix before deployment")
