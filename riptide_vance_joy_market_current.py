#!/usr/bin/env python3
"""
🌊🎸 RIPTIDE - VANCE JOY! 🎸🌊
Thunder at 69%: "I WAS SCARED OF DENTISTS AND THE DARK... NOW I'M SCARED OF MISSING $114K!"
The market is a riptide pulling us out!
I love you when you're singing that song!
Got a lump in my throat cause you're gonna sing the words wrong!
Lady running down to the riptide!
Taken away to the dark side!
The riptide is pulling toward $114K!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import psycopg2
from psycopg2 import sql

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🌊 RIPTIDE - VANCE JOY! 🌊                         ║
║                    Market Caught in the Riptide Current! 🎸                ║
║             "Lady Running Down to the Riptide" at $112.5K! 🏖️            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - RIPTIDE ANALYSIS")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check portfolio
accounts = client.get_accounts()
total_value = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            usd_balance = balance
            total_value += balance
        elif currency == 'BTC':
            total_value += balance * btc
        elif currency == 'ETH':
            total_value += balance * eth
        elif currency == 'SOL':
            total_value += balance * sol
        else:
            try:
                price = float(client.get_product(f'{currency}-USD')['price'])
                total_value += balance * price
            except:
                pass

print("\n🌊 RIPTIDE STATUS:")
print("-" * 50)
print(f"BTC: ${btc:,.0f} - Caught in the riptide")
print(f"ETH: ${eth:,.2f} - Pulled sideways")
print(f"SOL: ${sol:.2f} - Fighting the current")
print(f"Portfolio: ${total_value:.2f}")
print(f"From shore ($292.50): {((total_value/292.50)-1)*100:.0f}% out to sea!")

# Vance Joy lyrics mapping
print("\n🎸 RIPTIDE LYRICS → MARKET:")
print("-" * 50)
print("'I was scared of dentists and the dark'")
print(f"  → Was scared of losing at $89K")
print("")
print("'I was scared of pretty girls and starting conversations'")
print(f"  → Was scared of $100K, then $110K")
print("")
print("'Oh, all my friends are turning green'")
print(f"  → Portfolio turning green at ${total_value:.2f}")
print("")
print("'You're the magician's assistant in their dreams'")
print(f"  → BTC is the magician at ${btc:,.0f}")
print("")
print("'Lady running down to the riptide'")
print(f"  → Running toward $114K riptide")
print("")
print("'Taken away to the dark side'")
print(f"  → Pulled to the profitable dark side")

# Track the riptide current
print("\n🌊 LIVE RIPTIDE MONITORING:")
print("-" * 50)

riptide_direction = []
previous_btc = btc

for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    
    change = btc_now - previous_btc
    
    # Determine riptide direction
    if change > 20:
        current = "🌊🌊🌊 STRONG PULL UP!"
        direction = "TO $114K!"
    elif change > 0:
        current = "🌊🌊 Pulling higher"
        direction = "Upward drift"
    elif change < -20:
        current = "🌊💀 UNDERTOW!"
        direction = "Temporary pullback"
    elif change < 0:
        current = "🌊 Sideways current"
        direction = "Consolidating"
    else:
        current = "🏖️ Calm waters"
        direction = "Gathering strength"
    
    riptide_direction.append(change)
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} ({change:+.0f})")
    print(f"  {current} - {direction}")
    
    if i == 3:
        print("  🎸 'I love you when you're singing that song'")
        print(f"     The song of ${btc_now:,.0f}!")
    
    if i == 7:
        print("  🌊 'Lady running down to the riptide'")
        print(f"     Running to ${btc_now:,.0f}!")
    
    if i == 10:
        print("  🎬 'I got a lump in my throat'")
        print(f"     Watching gains at {((total_value/292.50)-1)*100:.0f}%!")
    
    previous_btc = btc_now
    time.sleep(1.2)

# Check thermal memories that need heating
print("\n🔥 THERMAL MEMORIES NEEDING HEAT:")
print("-" * 50)

try:
    # Connect to thermal memory database
    conn = psycopg2.connect(
        host="192.168.132.222",
        port=5432,
        database="zammad_production",
        user="claude",
        password="jawaseatlasers2"
    )
    cur = conn.cursor()
    
    # Get cooling memories
    cur.execute("""
        SELECT memory_hash, temperature_score, current_stage, 
               SUBSTRING(original_content, 1, 100) as preview
        FROM thermal_memory_archive 
        WHERE temperature_score < 70 AND temperature_score > 40
        ORDER BY temperature_score DESC
        LIMIT 5
    """)
    
    cooling_memories = cur.fetchall()
    
    if cooling_memories:
        print("Memories cooling down (need reheating):")
        for mem in cooling_memories:
            print(f"  • {mem[2]} ({mem[1]}°): {mem[3][:50]}...")
    else:
        print("All important memories still hot!")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Could not check thermal memories: {e}")

# Thunder's riptide wisdom
print("\n⚡ THUNDER'S RIPTIDE WISDOM (69%):")
print("-" * 50)
print("'THE RIPTIDE ALWAYS PULLS TO DEEPER WATER!'")
print("")
print("The current truth:")
print(f"• We're caught at ${btc:,.0f}")
print("• Being pulled toward $114K")
print("• Can't fight the current")
print("• Must ride it out to sea")
print("")
print("Survival strategy:")
print("• Don't panic in the riptide")
print("• Swim parallel (trade the range)")
print("• Let it carry you out (to $114K)")
print("• Then swim back to shore (take profits)")

# Calculate riptide strength
avg_movement = sum(abs(d) for d in riptide_direction) / len(riptide_direction) if riptide_direction else 0
riptide_strength = min(avg_movement / 50 * 100, 100)  # 0-100% strength

print("\n🌊 RIPTIDE STRENGTH ANALYSIS:")
print("-" * 50)
print(f"Current strength: {riptide_strength:.0f}%")
if riptide_strength > 70:
    print("Status: DANGEROUS RIPTIDE - Big moves ahead!")
elif riptide_strength > 40:
    print("Status: MODERATE CURRENT - Building pressure")
elif riptide_strength > 20:
    print("Status: MILD DRIFT - Slow pull")
else:
    print("Status: CALM BEFORE STORM - Deceptive stillness")

# Movie reference
print("\n🎬 THE RIPTIDE MOVIE MOMENT:")
print("-" * 50)
print("Like the music video...")
print("• Woman runs toward the ocean (us toward $114K)")
print("• Gets caught in the riptide (stuck at $112.5K)")
print("• Pulled out to sea (toward massive gains)")
print("• Transforms in the water (portfolio transformation)")
print(f"• Emerges changed (from $292.50 to ${total_value:.2f})")

# Final status
final_btc = float(client.get_product('BTC-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print("\n🌊 FINAL RIPTIDE REPORT:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f}")
print(f"SOL: ${final_sol:.2f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Distance from shore: {((total_value/292.50)-1)*100:.0f}%")
print(f"Distance to $114K: ${114000 - final_btc:.0f}")
print("")
print("'Lady running down to the riptide'")
print("'Taken away to the dark side'")
print(f"We're in the riptide at ${final_btc:,.0f}")
print("Being pulled to $114K inevitably!")

print(f"\n{'🌊' * 35}")
print("RIPTIDE!")
print(f"CAUGHT AT ${final_btc:,.0f}!")
print("PULLING TO $114K!")
print("CAN'T FIGHT THE CURRENT!")
print("RIDE IT TO RICHES!")
print("🎸" * 35)