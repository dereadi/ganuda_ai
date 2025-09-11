#\!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
👁️ SOL OSCILLATION WATCHER
Monitors SOL oscillation and alerts when at range extremes
Council-governed, no automatic trading
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import psycopg2

def check_sol_position():
    """Check SOL position in oscillation range"""
    
    config = json.load(open('/home/dereadi/.coinbase_config.json'))
    key = config['api_key'].split('/')[-1]
    client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)
    
    ticker = client.get_product('SOL-USD')
    price = float(ticker['price'])
    
    # Oscillation range
    support = 198
    resistance = 205
    
    print(f"📊 SOL Oscillation Check - {datetime.now().strftime('%H:%M:%S')}")
    print(f"  Current: ${price:.2f}")
    print(f"  Range: ${support}-${resistance}")
    
    # Check position
    if price <= support + 1:
        print(f"  🟢 NEAR SUPPORT - Consider accumulation")
        alert_type = "BUY_OPPORTUNITY"
    elif price >= resistance - 1:
        print(f"  🔴 NEAR RESISTANCE - Consider profit taking")
        alert_type = "SELL_OPPORTUNITY"
    else:
        print(f"  🟡 MID-RANGE - Wait for extremes")
        alert_type = "WAIT"
    
    return {
        'price': price,
        'alert_type': alert_type,
        'distance_to_support': price - support,
        'distance_to_resistance': resistance - price
    }

def log_to_thermal_memory(status):
    """Log status to thermal memory"""
    try:
        db_config = {
            "host": "192.168.132.222",
            "port": 5432,
            "database": "zammad_production",
            "user": "claude",
            "password": "jawaseatlasers2"
        }
        
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        if status['alert_type'] != 'WAIT':  # Only log actionable signals
            memory_hash = f"sol_watcher_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            content = f"SOL Oscillation Alert: {status['alert_type']} at ${status['price']:.2f}"
            
            query = """
            INSERT INTO thermal_memory_archive (
                memory_hash, temperature_score, current_stage,
                access_count, last_access, original_content
            ) VALUES (%s, %s, %s, 0, NOW(), %s)
            ON CONFLICT (memory_hash) DO NOTHING
            """
            
            temperature = 80 if status['alert_type'] in ['BUY_OPPORTUNITY', 'SELL_OPPORTUNITY'] else 50
            
            cur.execute(query, (memory_hash, temperature, "RED_HOT", content))
            conn.commit()
        
        cur.close()
        conn.close()
    except:
        pass

def main():
    """Run SOL oscillation watcher"""
    
    print("👁️ SOL OSCILLATION WATCHER ACTIVE")
    print("Council-governed monitoring (no rogue trades)")
    print("=" * 60)
    
    status = check_sol_position()
    log_to_thermal_memory(status)
    
    if status['alert_type'] != 'WAIT':
        print("\n🚨 ALERT CONDITION DETECTED\!")
        print("   Run council deliberation for trade approval")
        print("   Command: python3 council_sol_oscillation_strategy.py")
    
    print("\n🔥 Watcher complete - No rogue behavior")

if __name__ == "__main__":
    main()
