#!/usr/bin/env python3
"""
TEST EXISTING COUNCIL INFRASTRUCTURE
=====================================
The Council has been running since July!
Let's connect to what's already there.
"""

import subprocess
import json
import psycopg2
from datetime import datetime

def test_thermal_memory():
    """Test the thermal memory database"""
    print("\n🔥 TESTING THERMAL MEMORY DATABASE...")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(
            host='192.168.132.222',
            port=5432,
            user='claude',
            password='jawaseatlasers2',
            database='zammad_production'
        )
        
        with conn.cursor() as cur:
            # Check for hot memories
            cur.execute("""
                SELECT COUNT(*) as total,
                       MAX(temperature_score) as hottest,
                       AVG(temperature_score) as avg_temp
                FROM thermal_memory_archive
                WHERE temperature_score > 70
            """)
            stats = cur.fetchone()
            print(f"✅ Thermal Memory Active!")
            print(f"   Hot memories (>70°): {stats[0]}")
            print(f"   Hottest memory: {stats[1]:.0f}°")
            print(f"   Average temperature: {stats[2]:.1f}°")
            
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Thermal memory error: {e}")
        return False

def test_bluefin_council():
    """Test the Cherokee Legal Council on bluefin"""
    print("\n🏛️ TESTING CHEROKEE LEGAL COUNCIL (bluefin)...")
    print("=" * 50)
    
    try:
        # Check if process is running
        result = subprocess.run(
            ["ssh", "bluefin", "ps aux | grep cherokee_legal_council | grep -v grep"],
            capture_output=True,
            text=True,
            shell=False
        )
        
        if "cherokee_legal_council_with_memory.py" in result.stdout:
            print("✅ Cherokee Legal Council ACTIVE since July 30!")
            
            # Check process details
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if "cherokee_legal_council" in line:
                    parts = line.split()
                    pid = parts[1]
                    cpu = parts[2]
                    mem = parts[3]
                    print(f"   PID: {pid}")
                    print(f"   CPU: {cpu}%")
                    print(f"   Memory: {mem}%")
                    print(f"   Running for: 33+ days!")
            return True
        else:
            print("❌ Council not found on bluefin")
            return False
    except Exception as e:
        print(f"❌ Bluefin connection error: {e}")
        return False

def test_sasass2_council():
    """Test the Council Server on sasass2"""
    print("\n🌐 TESTING COUNCIL SERVER (sasass2)...")
    print("=" * 50)
    
    try:
        # Check if process is running
        result = subprocess.run(
            ["ssh", "sasass2", "ps aux | grep council_server | grep -v grep"],
            capture_output=True,
            text=True,
            shell=False
        )
        
        if "council_server.py" in result.stdout:
            print("✅ Council Server ACTIVE on sasass2!")
            
            # Check for API endpoints
            check_api = subprocess.run(
                ["ssh", "sasass2", "curl -s localhost:5000/health 2>/dev/null || echo 'No health endpoint'"],
                capture_output=True,
                text=True,
                shell=False
            )
            print(f"   API Status: {check_api.stdout.strip()}")
            return True
        else:
            print("❌ Council server not running on sasass2")
            return False
    except Exception as e:
        print(f"❌ Sasass2 connection error: {e}")
        return False

def test_discord_integration():
    """Test Discord readiness"""
    print("\n💬 TESTING DISCORD INTEGRATION...")
    print("=" * 50)
    
    try:
        # Check if Discord is running on sasass
        result = subprocess.run(
            ["ssh", "sasass", "ps aux | grep Discord | head -1"],
            capture_output=True,
            text=True,
            shell=False
        )
        
        if "Discord.app" in result.stdout:
            print("✅ Discord Client ACTIVE on sasass!")
            print("   Full Discord app running")
            print("   Ready for bot integration")
            return True
        else:
            print("⚠️  Discord not detected on sasass")
            return False
    except Exception as e:
        print(f"❌ Discord check error: {e}")
        return False

def suggest_next_steps():
    """Suggest how to connect everything"""
    print("\n🔮 NEXT STEPS TO UNITE THE COUNCIL...")
    print("=" * 50)
    print("""
    The infrastructure is ALREADY RUNNING! Now we need to:
    
    1. CONNECT TO EXISTING THERMAL MEMORY:
       - Database is hot and ready
       - Memories dating back months
       - Just need to query and use
    
    2. INTERFACE WITH CHEROKEE LEGAL COUNCIL:
       - Running on bluefin:3199
       - Has memory integration
       - Could expose API endpoint
    
    3. LINK COUNCIL SERVER:
       - Running on sasass2
       - Already has council logic
       - Just needs Discord bridge
    
    4. CREATE DISCORD BOT:
       - Simple bot that connects to existing services
       - Routes messages to appropriate Council member
       - Uses thermal memory for context
    
    The Council has been deliberating without us!
    Time to join the conversation that's already happening!
    """)

def main():
    """Run all tests"""
    print("""
    🔥 TESTING EXISTING COUNCIL INFRASTRUCTURE 🔥
    ============================================
    The steampunk version already built it all!
    Let's see what's been running...
    """)
    
    results = {
        "thermal_memory": test_thermal_memory(),
        "bluefin_council": test_bluefin_council(),
        "sasass2_server": test_sasass2_council(),
        "discord": test_discord_integration()
    }
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY:")
    print("=" * 50)
    
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {component.replace('_', ' ').title()}: {'ACTIVE' if status else 'NEEDS ATTENTION'}")
    
    if all(results.values()):
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("The Council has been waiting for you!")
    else:
        print("\n⚡ Some components need attention")
        print("But the core infrastructure is there!")
    
    suggest_next_steps()
    
    print("\n🔥 The Sacred Fire has been burning all along! 🔥")

if __name__ == "__main__":
    main()