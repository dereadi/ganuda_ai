#!/usr/bin/env python3
"""
🚀👑 DON'T STOP ME NOW - QUEEN! 👑🚀
Thunder at 69%: "I'M HAVING SUCH A GOOD TIME WITH SOL!"
I'm a shooting star leaping through the sky!
Like a tiger defying the laws of gravity!
200 degrees - that's why they call me Mr. Fahrenheit!
SOL sawtooth pattern = milking opportunity!
Don't stop me now, I'm having a good time!
Having a ball with these gains!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🚀 DON'T STOP ME NOW - QUEEN! 🚀                        ║
║                 SOL Sawtooth Pattern = Milking Paradise! ☀️                ║
║             "I'm Having Such a Good Time, I'm Having a Ball!" 🎸          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SUPERSONIC MAN ANALYSIS")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check portfolio
accounts = client.get_accounts()
sol_balance = 0
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
            sol_balance = balance
            total_value += balance * sol
        else:
            # Get other prices
            try:
                price = float(client.get_product(f'{currency}-USD')['price'])
                total_value += balance * price
            except:
                pass

print("\n🚀 TONIGHT I'M GONNA HAVE MYSELF A REAL GOOD TIME:")
print("-" * 50)
print(f"SOL Price: ${sol:.2f}")
print(f"Your SOL: {sol_balance:.4f} = ${sol_balance * sol:.2f}")
print(f"Total Portfolio: ${total_value:.2f}")
print(f"Started with: $292.50")
print(f"Current gains: {((total_value/292.50)-1)*100:.0f}% - HAVING A BALL!")

# Freddie Mercury energy
print("\n🎤 FREDDIE MERCURY MODE:")
print("-" * 50)
print("'Tonight I'm gonna have myself a real good time'")
print(f"  → Trading at ${sol:.2f}")
print("'I feel alive and the world is turning inside out'")
print(f"  → Portfolio at ${total_value:.2f}")
print("'I'm floating around in ecstasy'")
print(f"  → {((total_value/292.50)-1)*100:.0f}% gains!")
print("'So don't stop me now!'")
print(f"  → SOL to the moon!")

# Detect sawtooth pattern
print("\n🦷 SOL SAWTOOTH PATTERN DETECTION:")
print("-" * 50)

sawtooth_peaks = []
sawtooth_valleys = []
previous_sol = sol

for i in range(15):
    sol_now = float(client.get_product('SOL-USD')['price'])
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    change = sol_now - previous_sol
    
    # Detect peaks and valleys
    if change > 0.10:
        sawtooth_peaks.append(sol_now)
        pattern = "🔺 PEAK DETECTED!"
    elif change < -0.10:
        sawtooth_valleys.append(sol_now)
        pattern = "🔻 VALLEY DETECTED!"
    else:
        pattern = "➡️ Sideways"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: SOL ${sol_now:.2f} ({change:+.3f})")
    print(f"  {pattern} | BTC: ${btc_now:,.0f}")
    
    if i == 3:
        print("  🎸 'I'm a shooting star leaping through the sky!'")
        print(f"     SOL leaping from ${sol:.2f}!")
    
    if i == 7:
        print("  🐅 'Like a tiger defying the laws of gravity!'")
        print(f"     Defying gravity at ${sol_now:.2f}!")
    
    if i == 11:
        print("  🔥 '200 degrees, that's why they call me Mr. Fahrenheit!'")
        print(f"     SOL heating up to ${sol_now:.2f}!")
    
    previous_sol = sol_now
    time.sleep(1)

# Milking opportunities
print("\n🥛 SAWTOOTH MILKING OPPORTUNITIES:")
print("-" * 50)

if len(sawtooth_peaks) > 0:
    avg_peak = sum(sawtooth_peaks) / len(sawtooth_peaks)
    print(f"Average peak: ${avg_peak:.2f}")
    print(f"✅ MILK at peaks above ${avg_peak:.2f}")

if len(sawtooth_valleys) > 0:
    avg_valley = sum(sawtooth_valleys) / len(sawtooth_valleys)
    print(f"Average valley: ${avg_valley:.2f}")
    print(f"✅ BUY at valleys below ${avg_valley:.2f}")

if len(sawtooth_peaks) > 0 and len(sawtooth_valleys) > 0:
    spread = avg_peak - avg_valley
    print(f"Sawtooth spread: ${spread:.2f}")
    print(f"Profit per cycle: ${spread * sol_balance:.2f}")
    print(f"Potential daily: ${spread * sol_balance * 10:.2f} (10 cycles)")

# Thunder's Queen wisdom
print("\n⚡ THUNDER'S SUPERSONIC WISDOM (69%):")
print("-" * 50)
print("'DON'T STOP US NOW!'")
print("")
print("The Queen truth:")
print("• We're having such a good time")
print(f"• SOL sawing between peaks and valleys")
print("• Each tooth = milking opportunity")
print(f"• Current position: ${sol_balance * sol:.2f}")
print("")
print("Freddie's strategy:")
print("• 'I'm a rocket ship on my way to Mars' → SOL to $250")
print("• 'Like an atom bomb about to explode' → Breakout coming")
print("• 'I'm burning through the sky' → Riding every pump")

# Milking execution plan
print("\n🎯 SAWTOOTH MILKING PLAN:")
print("-" * 50)

if sol_balance > 1:
    milk_amount = sol_balance * 0.1  # 10% per milk
    print(f"Available to milk: {milk_amount:.4f} SOL")
    print(f"Value per milk: ${milk_amount * sol:.2f}")
    
    print("\nExecution strategy:")
    print(f"• SELL {milk_amount:.4f} SOL at peaks (>${sol + 0.50:.2f})")
    print(f"• BUY back at valleys (<${sol - 0.50:.2f})")
    print(f"• Repeat on each sawtooth")
    print(f"• Compound gains into position")
else:
    print("Need more SOL for effective milking")
    print("Consider converting some profits to SOL")

# Speed of light analysis
print("\n💫 TRAVELING AT THE SPEED OF LIGHT:")
print("-" * 50)
print(f"Current velocity: {((total_value/292.50)-1)*100:.0f}% gains")
print(f"Acceleration: ${(total_value - 292.50)/30:.2f}/day")
print(f"Trajectory to $15K: {15000 - total_value:.2f} away")
print(f"Time to target: {(15000 - total_value) / ((total_value - 292.50)/30):.1f} days")

# Final status
final_sol = float(client.get_product('SOL-USD')['price'])
final_btc = float(client.get_product('BTC-USD')['price'])

print("\n🎸 FINAL SUPERSONIC STATUS:")
print("-" * 50)
print(f"SOL: ${final_sol:.2f}")
print(f"BTC: ${final_btc:,.0f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"SOL position: ${sol_balance * final_sol:.2f}")
print("")
print("'Don't stop me now!'")
print("'I'm having such a good time!'")
print(f"'I'm having a ball' with {((total_value/292.50)-1)*100:.0f}% gains!")

# Queen finale
print(f"\n{'👑' * 35}")
print("DON'T STOP ME NOW!")
print(f"SOL SAWTOOTH AT ${final_sol:.2f}!")
print("MILKING EVERY PEAK!")
print("BUYING EVERY VALLEY!")
print("HAVING SUCH A GOOD TIME!")
print("I'M HAVING A BALL!")
print("🚀" * 35)