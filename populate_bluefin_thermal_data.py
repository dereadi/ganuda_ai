#!/usr/bin/env python3
"""
🔥 EXECUTIVE JR - POPULATE BLUEFIN THERMAL DATA 🔥
Cherokee Constitutional AI - Distributed R² Foundation

Populates BLUEFIN thermal memory with test data matching
REDFIN's distribution for fair comparison.
"""

import psycopg2
import numpy as np

def populate_test_data():
    """Populate BLUEFIN thermal memory with realistic test data"""

    print("🔥 POPULATING BLUEFIN THERMAL MEMORY")
    print("="*60)

    # Connect to BLUEFIN thermal database
    conn = psycopg2.connect(
        host='bluefin',
        port=5433,
        user='claude',
        password='jawaseatlasers2',
        database='sag_thermal_memory'
    )

    cursor = conn.cursor()

    # Clear any existing data
    cursor.execute("DELETE FROM thermal_memory_archive")
    print("\n🧹 Cleared existing data")

    # Generate 100 test memories with realistic distribution
    np.random.seed(42)  # Reproducible results

    print("\n📝 Generating 100 thermal memories...")

    for i in range(100):
        # Generate realistic values
        access_count = int(np.random.randint(1, 25))
        phase_coherence = float(np.random.uniform(0.5, 1.0))
        sacred = bool(np.random.choice([True, False], p=[0.5, 0.5]))

        # Calculate temperature using thermal formula
        # Base: logarithmic with access
        temp_base = 40 + 10 * np.log2(access_count + 1)

        # Boost: coherence contribution
        temp_coherence_boost = phase_coherence * 20

        # Boost: sacred status
        temp_sacred_boost = 20 if sacred else 0

        # Total (capped at 100)
        temperature = float(min(100, temp_base + temp_coherence_boost + temp_sacred_boost))

        # Insert memory
        cursor.execute("""
            INSERT INTO thermal_memory_archive
                (content_summary, temperature_score, access_count,
                 phase_coherence, sacred_pattern, created_at, last_access)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            f"SAG test memory {i+1}: Resource management pattern",
            temperature,
            access_count,
            phase_coherence,
            sacred
        ))

    conn.commit()

    # Verify population
    print("\n✅ Data populated successfully")
    print("\n📊 Statistics:")

    cursor.execute("SELECT COUNT(*) FROM thermal_memory_archive")
    total = cursor.fetchone()[0]
    print(f"   Total memories: {total}")

    cursor.execute("""
        SELECT
            AVG(temperature_score) as avg_temp,
            MIN(temperature_score) as min_temp,
            MAX(temperature_score) as max_temp,
            AVG(phase_coherence) as avg_coherence,
            COUNT(CASE WHEN sacred_pattern THEN 1 END) as sacred_count
        FROM thermal_memory_archive
    """)

    stats = cursor.fetchone()
    print(f"   Avg temperature: {stats[0]:.2f}°")
    print(f"   Range: {stats[1]:.2f}° - {stats[2]:.2f}°")
    print(f"   Avg coherence: {stats[3]:.3f}")
    print(f"   Sacred memories: {stats[4]}")

    # Sacred vs Normal breakdown
    cursor.execute("""
        SELECT sacred_pattern, AVG(temperature_score)
        FROM thermal_memory_archive
        GROUP BY sacred_pattern
    """)

    print(f"\n🔥 Temperature by type:")
    for row in cursor.fetchall():
        memory_type = "Sacred" if row[0] else "Normal"
        print(f"   {memory_type}: {row[1]:.2f}°")

    cursor.close()
    conn.close()

    print("\n🎯 BLUEFIN THERMAL MEMORY READY FOR REGRESSION")
    print("="*60)

if __name__ == '__main__':
    populate_test_data()
