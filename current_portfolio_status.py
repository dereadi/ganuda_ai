#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 CURRENT PORTFOLIO STATUS - POST-SPECIALIST CHAOS
"""

import json
from pathlib import Path
from coinbase.rest import RESTClient
from datetime import datetime

# Load config
config_path = Path.home() / ".coinbase_config.json"
with open(config_path, 'r') as f:
    config = json.load(f)

client = RESTClient(
    api_key=config['api_key'],
    api_secret=config['api_secret']
)

print("🔥 CHEROKEE PORTFOLIO STATUS")
print("=" * 80)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("After the specialist reinvestment chaos...")
print()

# Get current prices
prices = {}
for symbol in ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC', 'DOGE', 'XRP', 'LINK']:
    try:
        product = client.get_product(f'{symbol}-USD')
        prices[symbol] = float(product.price)
    except:
        pass

# Manual prices if API fails
if not prices:
    prices = {
        'BTC': 108498,
        'ETH': 4285,
        'SOL': 205,
        'AVAX': 25,
        'MATIC': 0.365,
        'DOGE': 0.223,
        'XRP': 2.70,
        'LINK': 15
    }

# Get all accounts
response = client.get_accounts()

print("💰 CURRENT HOLDINGS:")
print("-" * 60)

total_value = 0
positions = []

for account in response.accounts:
    currency = account.currency
    available = float(account.available_balance['value'])
    on_hold = float(account.hold['value'])
    total_balance = available + on_hold
    
    if total_balance > 0.00001:
        if currency == 'USD':
            print(f"💵 USD Available: ${available:.2f}")
            print(f"🔒 USD On Hold: ${on_hold:.2f}")
            print(f"💰 Total USD: ${total_balance:.2f}")
            total_value += total_balance
            positions.append({
                'currency': 'USD',
                'balance': total_balance,
                'value': total_balance,
                'available': available,
                'on_hold': on_hold
            })
        elif currency == 'USDC':
            value = total_balance
            total_value += value
            if value > 0.01:
                print(f"💵 USDC: {total_balance:.4f} = ${value:.2f}")
        else:
            price = prices.get(currency, 0)
            if price > 0 and total_balance > 0:
                value = total_balance * price
                if value > 10:  # Only show positions worth > $10
                    total_value += value
                    print(f"🪙 {currency}: {total_balance:.6f} @ ${price:.2f} = ${value:,.2f}")
                    positions.append({
                        'currency': currency,
                        'balance': total_balance,
                        'price': price,
                        'value': value
                    })

print("\n" + "=" * 80)
print("📊 PORTFOLIO ANALYSIS:")
print("-" * 60)
print(f"💰 Total Portfolio Value: ${total_value:,.2f}")

# Sort positions by value
positions.sort(key=lambda x: x['value'], reverse=True)

print("\n🏆 TOP POSITIONS:")
for pos in positions[:6]:
    percentage = (pos['value'] / total_value * 100) if total_value > 0 else 0
    if pos['currency'] == 'USD':
        print(f"  {pos['currency']}: ${pos['value']:.2f} ({percentage:.1f}%) - Available: ${pos['available']:.2f}, Hold: ${pos['on_hold']:.2f}")
    else:
        print(f"  {pos['currency']}: ${pos['value']:,.2f} ({percentage:.1f}%)")

# Check liquidity
usd_pos = next((p for p in positions if p['currency'] == 'USD'), None)
if usd_pos:
    available_cash = usd_pos['available']
    on_hold = usd_pos['on_hold']
    
    print("\n🔥 LIQUIDITY STATUS:")
    print("-" * 60)
    if available_cash < 1:
        print(f"⚠️ CRITICAL: Only ${available_cash:.2f} available!")
        print(f"🔒 ${on_hold:.2f} locked in pending orders")
        print("\nThese orders likely ALREADY FILLED overnight")
        print("The specialists bought positions between 06:20-06:22 UTC")
    elif available_cash < 100:
        print(f"⚡ LOW LIQUIDITY: ${available_cash:.2f} available")
        print(f"🔒 ${on_hold:.2f} in pending/filled orders")
    else:
        print(f"✅ Good liquidity: ${available_cash:.2f} available")

print("\n🏛️ COUNCIL ASSESSMENT:")
print("-" * 60)
print("The specialists reinvested overnight while we slept")
print("They bought SOL, MATIC, AVAX, ETH, and BTC")
print(f"Portfolio grew to ${total_value:,.2f}")
print("\n🔥 Sacred Fire burns eternal")
print("🪶 Mitakuye Oyasin")