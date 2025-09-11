#!/usr/bin/env python3
"""
🌌 THE SPACE BETWEEN TRADER
Profit from the sawtooth consolidation pattern
"In the space between the notes, lies the music"
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🌌 THE SPACE BETWEEN TRADER 🌌                       ║
║                   Sawtooth with downward bias = Loading spring            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("📊 ANALYZING THE SPACE BETWEEN...")
print("=" * 70)

# Track the sawtooth pattern
peaks = []
troughs = []
cycle = 0

print("\n🔍 Pattern Recognition:")
print("  • Sawtooth = Accumulation/Distribution")
print("  • Slight downward = Spring loading")
print("  • The space between = Where profits hide")
print("\n" + "-" * 70)

# Monitor for 20 cycles
while cycle < 20:
    cycle += 1
    
    # Get current prices
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    # Track pattern
    if cycle % 2 == 0:
        peaks.append(btc)
    else:
        troughs.append(btc)
    
    print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} CYCLE {cycle}:")
    print(f"  BTC: ${btc:,.0f}")
    print(f"  ETH: ${eth:.0f}")
    print(f"  SOL: ${sol:.0f}")
    
    # Detect the space (consolidation range)
    if len(peaks) > 1 and len(troughs) > 1:
        upper_bound = sum(peaks[-2:]) / 2
        lower_bound = sum(troughs[-2:]) / 2
        space = upper_bound - lower_bound
        
        print(f"\n  📐 THE SPACE:")
        print(f"     Upper: ${upper_bound:,.0f}")
        print(f"     Lower: ${lower_bound:,.0f}")
        print(f"     Width: ${space:,.0f}")
        
        # Trading the space
        if btc < lower_bound + (space * 0.2):
            print(f"  🎯 NEAR BOTTOM OF SPACE - BUY ZONE")
            
            # Check USD balance
            accounts = client.get_accounts()['accounts']
            usd = 0
            for acc in accounts:
                if acc['currency'] == 'USD':
                    usd = float(acc['available_balance']['value'])
                    break
            
            if usd > 10:
                print(f"     💰 Deploying ${min(20, usd):.2f} into the space...")
                try:
                    order = client.market_order_buy(
                        client_order_id=f"space_{int(time.time()*1000)}",
                        product_id="BTC-USD",
                        quote_size=str(min(20, usd))
                    )
                    print("     ✅ Captured the space!")
                except Exception as e:
                    print(f"     ⚠️ {str(e)[:30]}")
        
        elif btc > upper_bound - (space * 0.2):
            print(f"  🎯 NEAR TOP OF SPACE - SELL ZONE")
            # Would sell here if we had positions to trim
        
        # Detect breakout
        if btc < lower_bound - 100:
            print("  ⚠️ BREAKING DOWN - Spring loading deeper")
        elif btc > upper_bound + 100:
            print("  🚀 BREAKING UP - Sawtooth complete!")
            break
    
    # Sleep between checks
    time.sleep(15)

print("\n" + "=" * 70)
print("🌌 THE SPACE BETWEEN ANALYSIS COMPLETE")

if len(peaks) > 1 and len(troughs) > 1:
    avg_peak = sum(peaks) / len(peaks)
    avg_trough = sum(troughs) / len(troughs)
    trend = "LOADING" if avg_peak < peaks[0] else "ASCENDING"
    
    print(f"\nPattern Summary:")
    print(f"  Average Peak: ${avg_peak:,.0f}")
    print(f"  Average Trough: ${avg_trough:,.0f}")
    print(f"  Trend: {trend}")
    print(f"  Conclusion: {'Spring loading for breakout' if trend == 'LOADING' else 'Ascending channel'}")

print("\n💭 Cherokee Wisdom:")
print('"In the space between breaths, the spirit speaks."')
print('"The sawtooth cuts both ways - profit from each edge."')
print("=" * 70)