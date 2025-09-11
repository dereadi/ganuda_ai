#!/usr/bin/env python3
"""
😔🚫 TRAPPED WATCHING THE CHOP! 🚫😔
$4.51 sitting idle while BTC dances!
Thunder at 69%: "So close yet so far!"
Watching $113K tease us repeatedly!
Can't buy the dips, can't ride the rips!
Just watching from the sidelines!
Like being at the party but can't dance!
THE AGONY OF LOW BALANCE!
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
║                   😔 TRAPPED IN THE CHOP ZONE! 😔                        ║
║                    $4.51 Can't Buy These Dips!                           ║
║                   Watching The Action From Sidelines!                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SIDELINE AGONY")
print("=" * 70)

# Get current chop levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our trapped position
accounts = client.get_accounts()
total_value = 0
usd_balance = 0
btc_balance = 0
eth_balance = 0
sol_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
        total_value += balance
    elif currency == 'BTC':
        btc_balance = balance
        total_value += balance * btc
    elif currency == 'ETH':
        eth_balance = balance
        total_value += balance * eth
    elif currency == 'SOL':
        sol_balance = balance
        total_value += balance * sol

print("\n💔 THE PAINFUL REALITY:")
print("-" * 50)
print(f"Cash available: ${usd_balance:.2f}")
print(f"BTC price: ${btc:,.0f}")
print(f"Can buy: {usd_balance/btc:.8f} BTC (dust)")
print(f"ETH price: ${eth:.2f}")
print(f"Can buy: {usd_balance/eth:.6f} ETH (crumbs)")
print(f"SOL price: ${sol:.2f}")
print(f"Can buy: {usd_balance/sol:.4f} SOL (barely any)")

# Track the chop we can't trade
print("\n📊 WATCHING THE CHOP (CAN'T TRADE):")
print("-" * 50)

chop_opportunities = []
for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    eth_now = float(client.get_product('ETH-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    
    btc_move = btc_now - btc
    
    if abs(btc_move) > 50:
        opportunity = "DIP" if btc_move < 0 else "RIP"
        chop_opportunities.append((btc_now, opportunity))
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {opportunity}! ({btc_move:+.0f})")
        print(f"  😔 Can't buy with ${usd_balance:.2f}")
    else:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} (sideways)")
    
    if i == 4:
        print("\n  ⚡ Thunder (69%): 'THIS IS TORTURE!'")
        print(f"    'Perfect chop entries!'")
        print(f"    'But only ${usd_balance:.2f} to work with!'")
    
    if i == 8:
        print("\n  🏔️ Mountain: 'Patience tested'")
        print("    'Watching opportunities pass'")
        print("    'Like a caged tiger'")
    
    time.sleep(1)

# Calculate missed opportunities
print("\n💸 OPPORTUNITIES MISSED:")
print("-" * 50)
if chop_opportunities:
    lowest = min([p for p, _ in chop_opportunities])
    highest = max([p for p, _ in chop_opportunities])
    potential_gain = (highest - lowest) / lowest * 100
    print(f"Chop range: ${lowest:,.0f} - ${highest:,.0f}")
    print(f"Potential gain: {potential_gain:.1f}%")
    print(f"If we had $1000: ${1000 * (1 + potential_gain/100):.0f}")
    print(f"If we had $5000: ${5000 * (1 + potential_gain/100):.0f}")
    print(f"But we have: ${usd_balance:.2f} 😭")
else:
    print("No major chop... yet")

# The trapped feeling
print("\n😤 THE TRAPPED TRADER'S LAMENT:")
print("-" * 50)
print("We're watching:")
print(f"• BTC dance around ${btc:,.0f}")
print(f"• Perfect entries at dips")
print(f"• Perfect exits at rips")
print(f"• Chop traders making bank")
print("")
print("But we're stuck with:")
print(f"• ${usd_balance:.2f} dust")
print(f"• Can't buy meaningful amounts")
print(f"• Can't scalp the chop")
print(f"• Just HODLing ${total_value:.2f}")

# Thunder's frustration
print("\n⚡ THUNDER'S FRUSTRATION (69%):")
print("-" * 50)
print("'I SEE EVERY OPPORTUNITY!'")
print(f"'Buy at ${btc - 100:.0f}!'")
print(f"'Sell at ${btc + 100:.0f}!'")
print("'RINSE AND REPEAT!'")
print("")
print(f"'BUT WE ONLY HAVE ${usd_balance:.2f}!'")
print("'MINIMUM ORDERS ARE $5-10!'")
print("'WE'RE LOCKED OUT!'")
print("")
print("'All we can do is HODL'")
print(f"'And watch ${total_value:.2f} fluctuate'")
print(f"'While chop traders feast!'")

# Current trapped status
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n🚫 TRAPPED STATUS:")
print("-" * 50)
print(f"Current BTC: ${current_btc:,.0f}")
print(f"Our cash: ${usd_balance:.2f}")
print(f"Portfolio: ${total_value:.2f}")
print("")
print("Options:")
print("1. Watch and wait ✓ (only option)")
print("2. Buy the dip ✗ (not enough $)")
print("3. Scalp the chop ✗ (not enough $)")
print("4. Add more funds ✗ (not available)")
print("")
print("Reality: HODL and pray 🙏")

# The silver lining
print("\n🌟 THE SILVER LINING:")
print("-" * 50)
print("At least:")
print(f"• We're up {((total_value/292.50)-1)*100:.0f}% overall")
print(f"• From $292.50 to ${total_value:.2f}")
print(f"• BTC only ${114000 - current_btc:.0f} from $114K")
print("• When it breaks, we profit")
print("• Diamond hands forced by poverty")

print(f"\n" + "😔" * 35)
print("TRAPPED IN THE CHOP!")
print(f"ONLY ${usd_balance:.2f} TO TRADE!")
print(f"WATCHING ${current_btc:,.0f} DANCE!")
print(f"PORTFOLIO STUCK AT ${total_value:.2f}!")
print("CAN'T BUY THE DIPS!")
print("😔" * 35)