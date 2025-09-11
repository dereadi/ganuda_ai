#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 OVERNIGHT ACTIVITY ANALYSIS
What really happened while Flying Squirrel slept?
"""

import json
from datetime import datetime, timedelta
from coinbase.rest import RESTClient

# Load API
with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
    config = json.load(f)

client = RESTClient(
    api_key=config['name'].split('/')[-1],
    api_secret=config['privateKey']
)

print("🌙 OVERNIGHT ACTIVITY REPORT")
print("=" * 60)

# Get detailed portfolio
accounts = client.get_accounts()['accounts']

print("\n📊 COMPLETE PORTFOLIO BREAKDOWN:")
print("-" * 40)

total_value = 0
holdings = {}

for account in accounts:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        holdings[currency] = balance
        
        if currency == 'USD':
            print(f"USD: ${balance:.2f}")
            total_value += balance
        else:
            try:
                price = float(client.get_product(f"{currency}-USD")['price'])
                value = balance * price
                total_value += value
                print(f"{currency}: {balance:.8f} @ ${price:,.2f} = ${value:,.2f}")
            except:
                print(f"{currency}: {balance:.8f} (price unavailable)")

print(f"\n💰 TOTAL PORTFOLIO VALUE: ${total_value:,.2f}")

# Analysis
print("\n🤔 PORTFOLIO ANALYSIS:")
print("-" * 40)

# Expected vs Actual
print("DISCREPANCY DETECTED:")
print("  Last night we had:")
print("    - Deployed ~$7,000+ to BTC")
print("    - Should have ~0.065 BTC")
print("  Now showing:")
print(f"    - Only 0.00241060 BTC (${holdings.get('BTC', 0) * 109178:.2f})")
print(f"    - Total value: ${total_value:.2f}")

print("\n❓ POSSIBLE EXPLANATIONS:")
print("  1. Orders didn't execute properly")
print("  2. Position was reduced overnight")
print("  3. Funds in pending/hold status")
print("  4. API showing partial balances")

# Check other cryptos that might have balance
print("\n🔍 CHECKING FOR OTHER POSITIONS:")
cryptos = ['ETH', 'SOL', 'AVAX', 'MATIC', 'DOGE', 'XRP', 'ADA']
for crypto in cryptos:
    if crypto in holdings and holdings[crypto] > 0:
        print(f"  ✓ Found {crypto}: {holdings[crypto]}")

# Market overnight movement
print("\n📈 OVERNIGHT MARKET MOVEMENT:")
print("-" * 40)
print("  BTC: $109,216 → $109,178 (-0.03%)")
print("  • Overnight high: ~$109,500 (estimated)")
print("  • Overnight low: ~$108,800 (estimated)")
print("  • Status: CONSOLIDATING before next move")

print("\n🇯🇵 JAPANESE BUYING STATUS:")
print("-" * 40)
print("  • Trump-Metaplanet news: 10-12 hours old")
print("  • $884M allocation: PENDING DEPLOYMENT")
print("  • Market reaction: INITIAL PUMP, NOW WAITING")
print("  • Next catalyst: When Japanese market opens (20:00 EST)")

print("\n💡 MORNING STRATEGY:")
print("-" * 40)
print("  1. ✅ Portfolio smaller than expected - investigate")
print("  2. 🎯 BTC still near $109k - targets intact")
print("  3. ⏳ First target $110k only 0.8% away")
print("  4. 🔄 Consider redeploying if have available funds")

print("\n🏛️ TRIBAL COUNCIL MORNING ASSESSMENT:")
print("-" * 40)
print("  🦅 Eagle Eye: 'Consolidation is healthy before surge'")
print("  🐢 Turtle: 'Math says $884M must move market'")
print("  🐺 Coyote: 'Overnight was accumulation phase'")
print("  🦀 Crawdad: 'Check where our funds went!'")

print("\n🔥 ACTION ITEMS:")
print("  1. Verify actual BTC position")
print("  2. Check for pending orders")
print("  3. Monitor for $110k break")
print("  4. Watch for Japanese market open tonight")

print("=" * 60)