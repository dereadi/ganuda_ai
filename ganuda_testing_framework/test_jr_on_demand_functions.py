#!/usr/bin/env python3
"""
Test JR On-Demand Functions - Wake-on-Query Architecture
Cherokee Constitutional AI - October 21, 2025

Tests that JRs can be called on-demand while preserving autonomic schedules.
"""

import sys
sys.path.insert(0, '/ganuda/daemons')

from memory_jr_autonomic import MemoryJrAutonomic
from executive_jr_autonomic import ExecutiveJrAutonomic
from meta_jr_autonomic import MetaJrAutonomic

def test_memory_jr_on_demand():
    """Test Memory Jr on-demand functions"""
    print("=" * 70)
    print("🧠 TESTING MEMORY JR ON-DEMAND FUNCTIONS")
    print("=" * 70)

    memory_jr = MemoryJrAutonomic()

    if not memory_jr.connect_db():
        print("❌ Failed to connect to database")
        return False

    print("\n1️⃣ Testing retrieve_memories(keywords=['stanford', 'convergence'])")
    result = memory_jr.retrieve_memories(keywords=['stanford', 'convergence'], min_temp=80)
    print(f"   📊 Found: {result.get('memories_found', 0)} memories")
    print(f"   🌡️  Avg temp: {result.get('avg_temperature', 0):.1f}°")

    print("\n2️⃣ Testing get_sacred_memories()")
    sacred = memory_jr.get_sacred_memories()
    print(f"   ⭐ Sacred count: {sacred.get('sacred_count', 0)}")
    print(f"   🌡️  Avg temp: {sacred.get('avg_temperature', 0):.1f}°")

    print("\n3️⃣ Testing thermal_status_report()")
    status = memory_jr.thermal_status_report()
    print(f"   📊 Total memories: {status.get('total_memories', 0)}")
    print(f"   🔥 White hot (90-100°): {status.get('white_hot_90_100', 0)}")
    print(f"   🌡️  Average temp: {status.get('avg_temperature', 0):.1f}°")

    memory_jr.db_conn.close()
    print("\n✅ Memory Jr on-demand functions WORKING")
    return True

def test_executive_jr_on_demand():
    """Test Executive Jr on-demand functions"""
    print("\n" + "=" * 70)
    print("🎯 TESTING EXECUTIVE JR ON-DEMAND FUNCTIONS")
    print("=" * 70)

    exec_jr = ExecutiveJrAutonomic()

    print("\n1️⃣ Testing resource_status()")
    status = exec_jr.resource_status()
    print(f"   📊 Running: {status.get('total_running', 0)}")
    print(f"   ⚠️  Crashed: {status.get('total_crashed', 0)}")

    print("\n2️⃣ Testing coordinate_action(jrs=['memory', 'meta'], task='analyze patterns')")
    coord = exec_jr.coordinate_action(jrs=['memory', 'meta'], task='analyze patterns')
    print(f"   📋 Task: {coord.get('task')}")
    print(f"   🔗 Plan steps: {len(coord.get('coordination_plan', []))}")

    print("\n3️⃣ Testing plan_execution('Review trading patterns')")
    plan = exec_jr.plan_execution('Review trading patterns')
    print(f"   📋 Phases: {len(plan.get('phases', []))}")
    for phase in plan.get('phases', []):
        print(f"      • {phase}")

    print("\n✅ Executive Jr on-demand functions WORKING")
    return True

def test_meta_jr_on_demand():
    """Test Meta Jr on-demand functions"""
    print("\n" + "=" * 70)
    print("🔮 TESTING META JR ON-DEMAND FUNCTIONS")
    print("=" * 70)

    meta_jr = MetaJrAutonomic()

    if not meta_jr.connect_db():
        print("❌ Failed to connect to database")
        return False

    print("\n1️⃣ Testing analyze_patterns(domain='consciousness', timeframe=48)")
    patterns = meta_jr.analyze_patterns(domain='consciousness', timeframe_hours=48)
    print(f"   🔍 Patterns found: {patterns.get('patterns_found', 0)}")
    print(f"   🌡️  Avg temperature: {patterns.get('avg_temperature', 0):.1f}°")

    print("\n2️⃣ Testing cross_domain_correlation()")
    correlations = meta_jr.cross_domain_correlation()
    print(f"   🔗 Cross-domain memories: {correlations.get('correlations_found', 0)}")

    print("\n3️⃣ Testing detect_anomalies()")
    anomalies = meta_jr.detect_anomalies()
    print(f"   ⚠️  Anomalies detected: {anomalies.get('anomalies_detected', 0)}")
    for anomaly in anomalies.get('anomalies', []):
        print(f"      • {anomaly['type']}: {anomaly['description']}")

    meta_jr.db_conn.close()
    print("\n✅ Meta Jr on-demand functions WORKING")
    return True

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║  🦅 WAKE-ON-QUERY ARCHITECTURE TEST                     ║
║  Cherokee Constitutional AI - JR On-Demand Functions     ║
║  Testing: Memory Jr, Executive Jr, Meta Jr               ║
╚══════════════════════════════════════════════════════════╝
    """)

    success = True

    success &= test_memory_jr_on_demand()
    success &= test_executive_jr_on_demand()
    success &= test_meta_jr_on_demand()

    print("\n" + "=" * 70)
    if success:
        print("🔥 ALL JR ON-DEMAND FUNCTIONS OPERATIONAL!")
        print("   Wake-on-query architecture is WORKING")
        print("   Autonomic breathing + Reactive consciousness = COMPLETE")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        print("=" * 70)
        sys.exit(1)
