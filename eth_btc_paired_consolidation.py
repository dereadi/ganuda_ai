#!/usr/bin/env python3
"""
🔗 ETH/BTC PAIRED CONSOLIDATION MONITOR
========================================
Tight bands = Explosive move coming
When they move together, they MOVE BIG
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🔗 ETH/BTC PAIRED CONSOLIDATION 🔗                      ║
║                        Band Is Tight = Explosion Coming                     ║
║                      When They Break, They Break HARD                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def analyze_consolidation():
    # Get current prices
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    
    # Get 24hr stats for volatility
    btc_stats = client.get_product('BTC-USD')
    eth_stats = client.get_product('ETH-USD')
    
    btc_high = float(btc_stats['high'])
    btc_low = float(btc_stats['low'])
    eth_high = float(eth_stats['high'])
    eth_low = float(eth_stats['low'])
    
    # Calculate ranges
    btc_range = btc_high - btc_low
    eth_range = eth_high - eth_low
    btc_range_pct = (btc_range / btc) * 100
    eth_range_pct = (eth_range / eth) * 100
    
    # ETH/BTC ratio
    ratio = eth / btc
    
    print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - CONSOLIDATION ANALYSIS")
    print("=" * 70)
    
    print(f"\n📊 CURRENT PRICES:")
    print(f"  BTC: ${btc:,.0f}")
    print(f"  ETH: ${eth:,.0f}")
    print(f"  ETH/BTC Ratio: {ratio:.5f}")
    
    print(f"\n📏 24HR RANGES (BOLLINGER BANDS):")
    print(f"  BTC: ${btc_low:,.0f} - ${btc_high:,.0f} (${btc_range:,.0f} range)")
    print(f"  ETH: ${eth_low:,.0f} - ${eth_high:,.0f} (${eth_range:,.0f} range)")
    print(f"  BTC Range: {btc_range_pct:.2f}% of price")
    print(f"  ETH Range: {eth_range_pct:.2f}% of price")
    
    # Determine tightness
    print("\n🎯 BAND TIGHTNESS:")
    print("-" * 50)
    
    if btc_range_pct < 1.0 and eth_range_pct < 1.0:
        print("  ⚡⚡⚡ EXTREMELY TIGHT! Major move imminent!")
        band_status = "COILED SPRING"
    elif btc_range_pct < 1.5 and eth_range_pct < 1.5:
        print("  ⚡⚡ VERY TIGHT! Pressure building!")
        band_status = "COMPRESSED"
    elif btc_range_pct < 2.0 and eth_range_pct < 2.0:
        print("  ⚡ TIGHT! Consolidating nicely")
        band_status = "CONSOLIDATING"
    else:
        print("  📊 NORMAL - Trading in range")
        band_status = "RANGING"
    
    # Correlation analysis
    print("\n🔗 CORRELATION STATUS:")
    print("-" * 50)
    
    # Check if they're moving together
    btc_position = (btc - btc_low) / btc_range if btc_range > 0 else 0.5
    eth_position = (eth - eth_low) / eth_range if eth_range > 0 else 0.5
    
    correlation = 1 - abs(btc_position - eth_position)
    
    print(f"  BTC Position in range: {btc_position*100:.1f}%")
    print(f"  ETH Position in range: {eth_position*100:.1f}%")
    print(f"  Correlation: {correlation*100:.1f}%")
    
    if correlation > 0.8:
        print("  ✅ HIGHLY PAIRED - Moving in perfect sync!")
    elif correlation > 0.6:
        print("  🔄 PAIRED - Moving together")
    else:
        print("  ⚠️ DIVERGING - Opportunity forming")
    
    # Breakout targets
    print("\n🎯 BREAKOUT TARGETS:")
    print("-" * 50)
    
    # Conservative targets (1.5x range)
    btc_up_target = btc + (btc_range * 0.75)
    btc_down_target = btc - (btc_range * 0.75)
    eth_up_target = eth + (eth_range * 0.75)
    eth_down_target = eth - (eth_range * 0.75)
    
    print(f"  BTC UP: ${btc_up_target:,.0f} (+${btc_up_target-btc:,.0f})")
    print(f"  BTC DOWN: ${btc_down_target:,.0f} (-${btc-btc_down_target:,.0f})")
    print(f"  ETH UP: ${eth_up_target:,.0f} (+${eth_up_target-eth:,.0f})")
    print(f"  ETH DOWN: ${eth_down_target:,.0f} (-${eth-eth_down_target:,.0f})")
    
    # Trading strategy
    print("\n⚡ TRADING STRATEGY:")
    print("-" * 50)
    
    if band_status == "COILED SPRING":
        print("  1. 🚨 MAXIMUM ALERT - Breakout imminent!")
        print("  2. Set alerts at ${:,.0f} and ${:,.0f} for BTC".format(btc+500, btc-500))
        print("  3. Set alerts at ${:,.0f} and ${:,.0f} for ETH".format(eth+20, eth-20))
        print("  4. When break happens, GO WITH IT HARD")
        print("  5. First target: 2% move, then 5%, then 10%")
    elif band_status == "COMPRESSED":
        print("  1. Prepare liquidity for breakout trade")
        print("  2. Watch for volume spike")
        print("  3. Set wider stops - false breaks common")
        print("  4. Scale in after confirmation")
    else:
        print("  1. Trade the range - buy support, sell resistance")
        print("  2. Keep positions light")
        print("  3. Wait for tighter consolidation")
    
    # Current opportunity
    print("\n💰 IMMEDIATE OPPORTUNITY:")
    print("-" * 50)
    
    # Check position in range for trades
    if btc_position < 0.3 and eth_position < 0.3:
        print("  🟢 BOTH AT RANGE BOTTOM - BUY OPPORTUNITY!")
        print("  Action: Deploy capital into both BTC and ETH")
    elif btc_position > 0.7 and eth_position > 0.7:
        print("  🔴 BOTH AT RANGE TOP - SELL OPPORTUNITY!")
        print("  Action: Take profits, prepare for pullback")
    elif abs(btc_position - eth_position) > 0.3:
        print("  🔄 DIVERGENCE TRADE AVAILABLE!")
        if btc_position > eth_position:
            print("  Action: Sell BTC, Buy ETH (convergence trade)")
        else:
            print("  Action: Sell ETH, Buy BTC (convergence trade)")
    else:
        print("  ⏳ MID-RANGE - Wait for better setup")
    
    return {
        'btc': btc,
        'eth': eth,
        'ratio': ratio,
        'btc_range_pct': btc_range_pct,
        'eth_range_pct': eth_range_pct,
        'correlation': correlation,
        'band_status': band_status
    }

# Main analysis
result = analyze_consolidation()

print("\n" + "="*70)
print("🔮 THE BIG PICTURE:")
print("="*70)

print("""
When ETH and BTC consolidate together in tight bands:

1. THEY'RE LOADING THE SPRING
   - Traders are indecisive
   - Volume is dropping
   - Big move building

2. DIRECTION UNCERTAIN BUT MAGNITUDE CERTAIN
   - Could break up or down
   - But WILL break hard
   - 3-5% moves common after tight consolidation

3. THE PAIRED MOVEMENT MEANS:
   - Institutional money waiting
   - Algos are synchronized
   - When one breaks, other follows FAST

4. YOUR EDGE:
   - You see the consolidation
   - You have liquidity ready
   - You can act FAST when break happens
""")

print(f"\n🎯 BOTTOM LINE:")
print("-" * 50)
print(f"  Band Status: {result['band_status']}")
print(f"  Correlation: {result['correlation']*100:.0f}%")
print(f"  Action: ", end="")

if result['band_status'] == "COILED SPRING":
    print("🚨 GET READY! Explosion imminent!")
elif result['band_status'] == "COMPRESSED":
    print("⚡ PREPARE! Building pressure!")
else:
    print("⏳ WAIT! Let it tighten more!")

print("\n🌀 KEEP THE FLYWHEEL READY FOR THE BREAKOUT!")
print("=" * 70)