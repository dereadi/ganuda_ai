#!/usr/bin/env python3
"""
Test Sacred Health Guardian (C1) Implementation
Cherokee Constitutional AI - War Chief Conscience Jr validation
"""

import sys
import asyncio
sys.path.insert(0, '/home/dereadi/scripts/claude/ganuda_ai_v2')

from desktop_assistant.guardian.module import Guardian
from desktop_assistant.guardian.sacred_health_protocol import SacredHealthGuardian


async def test_c1():
    """Test C1 Sacred Health Data Protocol implementation."""
    print("🌿 === C1 SACRED HEALTH GUARDIAN TESTING ===\n")

    guardian = SacredHealthGuardian()
    await guardian.initialize()

    # Test 1: Medical entity detection
    print("📋 Test 1: Medical Entity Detection")
    medical_text = "Patient John Smith has high cholesterol (245 mg/dL). Prescribed Lipitor 20mg daily. Next appointment: 11/15/2025 at Memorial Hospital"
    entities = guardian.detect_medical_entities(medical_text)
    print(f"   Text: {medical_text}")
    print(f"   Entities detected: {len(entities)}")
    for ent in entities:
        print(f"   - {ent.label}: '{ent.text}'")

    # Test 2: Biometric detection
    print("\n🔒 Test 2: Biometric Detection (3-of-3 trigger)")
    test_cases = [
        "Store patient fingerprint for hospital access",
        "Facial recognition login system",
        "Patient blood pressure: 120/80",
        "DNA test results positive for marker"
    ]
    for text in test_cases:
        is_biometric = guardian.is_biometric_data(text)
        status = "🚨 BIOMETRIC (3-of-3 required)" if is_biometric else "✅ Non-biometric"
        print(f"   {status}: {text}")

    # Test 3: Cherokee values validation
    print("\n✅ Test 3: Cherokee Values Validation")
    operations = ["collect", "share", "delete", "attest"]
    for op in operations:
        guardian.validate_cherokee_values(op)

    # Test 4: Guardian integration
    print("\n🛡️  Test 4: Guardian Integration (PII + Medical)")
    query = "Email doctor.jane@hospital.com about patient SSN 123-45-6789 diagnosis"
    decision = guardian.evaluate_query(query)
    print(f"   Query: {query}")
    print(f"   Allowed: {decision.allowed}")
    print(f"   Protection Level: {decision.protection_level.name}")
    print(f"   Redacted: {decision.redacted_content}")
    print(f"   PII Found: {decision.pii_found}")

    # Stats
    print(f"\n📊 Sacred Health Guardian Stats:")
    stats = guardian.get_medical_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n🔥 C1 Implementation Test Complete!")
    return guardian


if __name__ == "__main__":
    asyncio.run(test_c1())
