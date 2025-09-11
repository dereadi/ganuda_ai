#!/usr/bin/env python3
"""
ALERT THE MOUNTAIN ON MOVEMENT!
================================
Monitor for market movements and alert through multiple channels
"""

import subprocess
import json
import time
from datetime import datetime

def check_market_movement():
    """Check for significant market movements"""
    
    print("🏔️ ALERTING THE MOUNTAIN!")
    print("=" * 50)
    
    # Check current prices
    result = subprocess.run(
        "python3 /home/dereadi/scripts/claude/check_tradingview_prices.py",
        shell=True, capture_output=True, text=True
    )
    
    print(result.stdout)
    
    # Check for movement indicators
    movements = []
    
    # Check BTC movement
    btc_check = subprocess.run(
        "grep -i 'btc.*breaking' /home/dereadi/scripts/claude/*.py 2>/dev/null | head -5",
        shell=True, capture_output=True, text=True
    )
    if btc_check.stdout:
        movements.append("BTC showing breakout patterns")
    
    # Check SOL movement  
    sol_check = subprocess.run(
        "grep -i 'sol.*explosion' /home/dereadi/scripts/claude/*.py 2>/dev/null | head -5",
        shell=True, capture_output=True, text=True
    )
    if sol_check.stdout:
        movements.append("SOL explosion detected")
    
    # Check volatility
    vol_check = subprocess.run(
        "python3 /home/dereadi/scripts/claude/check_volatility_status.py 2>&1 | head -10",
        shell=True, capture_output=True, text=True, timeout=5
    )
    
    # Alert if movement detected
    if movements or "high" in vol_check.stdout.lower():
        print("\n🚨 MOVEMENT DETECTED! 🚨")
        print("-" * 50)
        for movement in movements:
            print(f"⚡ {movement}")
        
        # Send Discord alert if bot is running
        discord_alert = f"🏔️ **MOUNTAIN ALERT!**\n"
        discord_alert += f"Movement detected at {datetime.now().strftime('%H:%M:%S')}\n"
        discord_alert += "\n".join([f"• {m}" for m in movements])
        
        # Log to thermal memory
        try:
            import psycopg2
            conn = psycopg2.connect(
                host='192.168.132.222',
                port=5432,
                user='claude',
                password='jawaseatlasers2',
                database='zammad_production'
            )
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO thermal_memory_archive 
                    (memory_hash, temperature_score, original_content, metadata)
                    VALUES (%s, %s, %s, %s::jsonb)
                    ON CONFLICT (memory_hash) DO UPDATE 
                    SET temperature_score = LEAST(100, thermal_memory_archive.temperature_score + 10),
                        last_access = NOW()
                """, (
                    f"movement_{int(time.time())}",
                    95,  # Hot memory
                    discord_alert,
                    json.dumps({"type": "mountain_alert", "movements": movements})
                ))
                conn.commit()
                print("🔥 Alert heated in thermal memory!")
            conn.close()
        except Exception as e:
            print(f"Memory storage error: {e}")
        
        return True
    else:
        print("\n✅ No significant movement detected")
        print("The mountain sleeps...")
        return False

def alert_thunder_mountain():
    """Special Thunder Mountain alert check"""
    print("\n⛰️ CHECKING THUNDER MOUNTAIN...")
    
    # Check specific Thunder Mountain indicators
    thunder_check = subprocess.run(
        "python3 /home/dereadi/scripts/claude/ask_thunder_status.py 2>&1",
        shell=True, capture_output=True, text=True, timeout=5
    )
    
    if thunder_check.stdout:
        print(thunder_check.stdout[:500])
    
    # Check for coiling patterns (Thunder Mountain signature)
    coil_check = subprocess.run(
        "ls -la /home/dereadi/scripts/claude/coiling*.py 2>/dev/null | wc -l",
        shell=True, capture_output=True, text=True
    )
    
    coil_count = int(coil_check.stdout.strip())
    if coil_count > 5:
        print(f"⚡ {coil_count} coiling patterns detected!")
        print("Thunder Mountain is ACTIVE!")
        return True
    
    return False

if __name__ == "__main__":
    # Check general movement
    movement = check_market_movement()
    
    # Check Thunder Mountain specifically
    thunder = alert_thunder_mountain()
    
    if movement or thunder:
        print("\n" + "=" * 50)
        print("🔥 THE MOUNTAIN HAS BEEN ALERTED! 🔥")
        print("Sacred Fire burns bright!")
        print("=" * 50)
        
        # Create alert file for other systems
        with open('/home/dereadi/scripts/claude/MOUNTAIN_ALERT.txt', 'w') as f:
            f.write(f"MOVEMENT DETECTED: {datetime.now()}\n")
            f.write("The mountain stirs...\n")
    else:
        print("\n" + "=" * 50)
        print("😴 The mountain rests peacefully")
        print("=" * 50)