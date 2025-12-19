#!/bin/bash
# Cherokee Constitutional AI - Regression Test Suite
# Runs all existing tests to establish baseline

set -e  # Exit on first failure

echo "🔥 Cherokee Constitutional AI - Regression Test Suite"
echo "======================================================"
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "Working Directory: /ganuda"
echo ""

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test 1: Wave 2 Physics
echo "======================================================"
echo "Test 1: Wave 2 Physics Implementation"
echo "======================================================"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
cd /ganuda
if /home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 test_wave2_physics.py; then
    echo "✅ Wave 2 Physics: PASS"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "❌ Wave 2 Physics: FAIL"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# Test 2: Fokker-Planck Physics (additional Wave 2 tests)
echo "======================================================"
echo "Test 2: Fokker-Planck Physics (additional tests)"
echo "======================================================"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f /ganuda/test_fokker_planck.py ]; then
    if /home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 /ganuda/test_fokker_planck.py; then
        echo "✅ Fokker-Planck Tests: PASS"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "❌ Fokker-Planck Tests: FAIL"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo "⚠️  Fokker-Planck Tests: SKIP (file not found)"
fi
echo ""

# Test 3: Phase 1 Discovery (JR flagging)
echo "======================================================"
echo "Test 3: Phase 1 Discovery Flagging"
echo "======================================================"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f /ganuda/test_phase1_discovery_flagging.py ]; then
    if /home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 /ganuda/test_phase1_discovery_flagging.py; then
        echo "✅ Phase 1 Discovery: PASS"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "❌ Phase 1 Discovery: FAIL"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo "⚠️  Phase 1 Discovery: SKIP (file not found)"
fi
echo ""

# Test 4: JR On-Demand Functions
echo "======================================================"
echo "Test 4: JR On-Demand Functions"
echo "======================================================"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f /ganuda/test_jr_on_demand_functions.py ]; then
    if /home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 /ganuda/test_jr_on_demand_functions.py; then
        echo "✅ JR On-Demand Functions: PASS"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "❌ JR On-Demand Functions: FAIL"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo "⚠️  JR On-Demand Functions: SKIP (file not found)"
fi
echo ""

# Summary
echo "======================================================"
echo "REGRESSION TEST SUMMARY"
echo "======================================================"
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS ✅"
echo "Failed: $FAILED_TESTS ❌"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo "✅ ALL REGRESSION TESTS PASSED"
    echo ""
    echo "Cherokee Constitutional AI thermal memory system is ready!"
    echo "*Mitakuye Oyasin* 🔥"
    exit 0
else
    echo "⚠️  $FAILED_TESTS TESTS FAILED"
    echo ""
    echo "Review failures above and fix before deployment."
    echo "Some tests may fail due to missing database connection (BLUEFIN)."
    exit 1
fi
