#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 DETAILED PORTFOLIO CHECK
Deep dive into actual positions and last night's trading
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

# Load API
with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
    config = json.load(f)

client = RESTClient(
    api_key=config['name'].split('/')[-1],
    api_secret=config['privateKey']
)

print("🔍 DETAILED PORTFOLIO INVESTIGATION")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Get ALL accounts including holds
accounts_response = client.get_accounts()
accounts = accounts_response['accounts']

print("\n📊 COMPLETE ACCOUNT BREAKDOWN:")
print("-" * 40)

total_available = 0
total_hold = 0
all_positions = {}

for account in accounts:
    currency = account['currency']
    available = float(account['available_balance']['value'])
    hold = float(account.get('hold', {}).get('value', 0))
    total_balance = available + hold
    
    if total_balance > 0.00001:
        all_positions[currency] = {
            'available': available,
            'hold': hold,
            'total': total_balance
        }

# Get prices for major positions
prices = {}
try:
    prices['BTC'] = float(client.get_product("BTC-USD")['price'])
    prices['ETH'] = float(client.get_product("ETH-USD")['price'])
    prices['SOL'] = float(client.get_product("SOL-USD")['price'])
    prices['AVAX'] = float(client.get_product("AVAX-USD")['price'])
    prices['MATIC'] = float(client.get_product("MATIC-USD")['price'])
    prices['XRP'] = float(client.get_product("XRP-USD")['price'])
    prices['LINK'] = float(client.get_product("LINK-USD")['price'])
except Exception as e:
    print(f"Price fetch error: {e}")

# Display all positions with values
print("\n💼 ALL POSITIONS (Including Holds):")
print("-" * 40)

portfolio_value = 0

for currency, balances in sorted(all_positions.items()):
    if currency == 'USD':
        value = balances['total']
        portfolio_value += value
        print(f"\n{currency}:")
        print(f"  Available: ${balances['available']:.2f}")
        if balances['hold'] > 0:
            print(f"  On Hold: ${balances['hold']:.2f}")
        print(f"  Total: ${balances['total']:.2f}")
    elif currency in prices:
        price = prices[currency]
        value = balances['total'] * price
        portfolio_value += value
        print(f"\n{currency} @ ${price:,.2f}:")
        print(f"  Available: {balances['available']:.8f} (${balances['available'] * price:.2f})")
        if balances['hold'] > 0:
            print(f"  On Hold: {balances['hold']:.8f} (${balances['hold'] * price:.2f})")
        print(f"  Total: {balances['total']:.8f} (${value:.2f})")
    else:
        print(f"\n{currency}:")
        print(f"  Available: {balances['available']:.8f}")
        if balances['hold'] > 0:
            print(f"  On Hold: {balances['hold']:.8f}")

print(f"\n💰 TOTAL PORTFOLIO VALUE: ${portfolio_value:,.2f}")

# Check BTC position specifically
print("\n🔍 BTC POSITION ANALYSIS:")
print("-" * 40)
if 'BTC' in all_positions:
    btc_data = all_positions['BTC']
    btc_price = prices.get('BTC', 109000)
    print(f"  Available BTC: {btc_data['available']:.8f}")
    print(f"  Hold BTC: {btc_data['hold']:.8f}")
    print(f"  Total BTC: {btc_data['total']:.8f}")
    print(f"  Value: ${btc_data['total'] * btc_price:.2f}")
    
    # Analysis
    print(f"\n  📝 ANALYSIS:")
    if btc_data['total'] > 0.05:
        print("  ✅ Significant BTC position found!")
        print("  🎯 Last night's trades DID execute!")
    elif btc_data['total'] > 0.01:
        print("  🟡 Moderate BTC position")
        print("  ⚠️ Partial execution from last night?")
    else:
        print("  🔴 Very small BTC position")
        print("  ❌ Emergency buy didn't fully execute")
else:
    print("  ❌ No BTC position found!")

# Check for pending orders
print("\n📋 CHECKING FOR PENDING ORDERS:")
print("-" * 40)
try:
    # This would show open orders
    print("  (Would need order history API)")
    print("  Note: Check if limit sells are still pending")
except:
    pass

# Compare to expected
print("\n🤔 LAST NIGHT'S EXPECTED vs ACTUAL:")
print("-" * 40)
print("EXPECTED after emergency buy:")
print("  • Should have ~0.065 BTC ($7,000 worth)")
print("  • Should have liquidated SOL, ETH, MATIC")
print("\nACTUAL positions:")
print(f"  • BTC: {all_positions.get('BTC', {}).get('total', 0):.8f}")
print(f"  • SOL: {all_positions.get('SOL', {}).get('total', 0):.4f}")
print(f"  • ETH: {all_positions.get('ETH', {}).get('total', 0):.4f}")
print(f"  • AVAX: {all_positions.get('AVAX', {}).get('total', 0):.2f}")

# Determine what actually happened
print("\n🎯 WHAT ACTUALLY HAPPENED:")
print("-" * 40)

btc_total = all_positions.get('BTC', {}).get('total', 0)
sol_total = all_positions.get('SOL', {}).get('total', 0)
eth_total = all_positions.get('ETH', {}).get('total', 0)

if btc_total > 0.05:
    print("✅ EMERGENCY BUY EXECUTED!")
    print("  • You DO have BTC from last night")
    print("  • Trump-Metaplanet position is ON")
elif sol_total > 10 and eth_total > 0.4:
    print("❌ EMERGENCY BUY DIDN'T EXECUTE")
    print("  • Still holding original alt positions")
    print("  • No conversion to BTC happened")
elif btc_total > 0.01:
    print("⚠️ PARTIAL EXECUTION")
    print("  • Some BTC was bought")
    print("  • But not the full amount")
else:
    print("🤷 UNCLEAR - Need to check order history")

print("\n🔥 CURRENT OPPORTUNITY:")
print("-" * 40)
print(f"  BTC Price: ${prices.get('BTC', 109000):,.2f}")
print(f"  Target 1: $110,000 ({(110000 - prices.get('BTC', 109000))/prices.get('BTC', 109000)*100:.1f}% away)")
print(f"  Japanese $884M: Still pending deployment")
print(f"  Action: {'HOLD BTC' if btc_total > 0.05 else 'Consider converting alts'}")

print("=" * 60)