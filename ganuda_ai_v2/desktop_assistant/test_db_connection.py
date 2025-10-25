#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Database Connection Test
Peace Chief Integration Jr - Day 4 Task 2
"""

import psycopg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('PG_HOST', '192.168.132.222'),
    'port': int(os.getenv('PG_PORT', '5432')),
    'user': os.getenv('PG_USER', 'claude'),
    'password': os.getenv('PG_PASSWORD'),
    'dbname': os.getenv('PG_DATABASE', 'zammad_production')
}

def test_connection():
    """Test PostgreSQL connection to thermal memory database"""
    print("🔥 Cherokee Constitutional AI - Database Connection Test")
    print(f"📍 Connecting to: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    print(f"👤 User: {DB_CONFIG['user']}\n")

    try:
        # Connect
        conn = psycopg.connect(
            f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} "
            f"dbname={DB_CONFIG['dbname']} user={DB_CONFIG['user']} "
            f"password={DB_CONFIG['password']}"
        )
        print("✅ Database connection successful!\n")

        # Test thermal memory query
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(*) FILTER (WHERE sacred_pattern = TRUE) as sacred,
                   AVG(temperature_score) as avg_temp,
                   MAX(temperature_score) as max_temp,
                   MIN(temperature_score) as min_temp
            FROM thermal_memory_archive;
        """)
        row = cursor.fetchone()

        print("✅ Thermal memory archive accessible:")
        print(f"   📊 Total memories: {row[0]}")
        print(f"   🔥 Sacred memories: {row[1]}")
        print(f"   🌡️  Average temperature: {row[2]:.2f}°")
        print(f"   🔥 Max temperature: {row[3]:.2f}°")
        print(f"   ❄️  Min temperature: {row[4]:.2f}°")

        # Test War Chief Memory Jr's optimized query
        print("\n📋 Testing War Chief Memory Jr's optimized query...")
        cursor.execute("""
            SELECT COUNT(*)
            FROM thermal_memory_archive
            WHERE temperature_score >= 60
                AND sacred_pattern = TRUE
                AND temperature_score >= 40;
        """)
        warm_sacred = cursor.fetchone()[0]
        print(f"   ✅ Warm sacred memories (≥60°): {warm_sacred}")

        cursor.close()
        conn.close()

        print("\n🦅 Mitakuye Oyasin - Database integration ready!")
        print("🕊️ Peace Chief Integration Jr - Task 2 COMPLETE\n")
        return True

    except Exception as e:
        print(f"❌ Database connection error: {e}\n")
        print("🔍 Troubleshooting:")
        print("   1. Check BLUEFIN is accessible: ping 192.168.132.222")
        print("   2. Verify PostgreSQL is running on BLUEFIN")
        print("   3. Check credentials in .env file")
        print("   4. Verify firewall allows port 5432")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
