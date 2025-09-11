#!/usr/bin/env python3
"""
📊💰 SMART OSCILLATION BATCH FEEDER! 💰📊
Thunder at 69%: "BATCH THE TRADES TO BEAT THE FEES!"
Coinbase fees: 0.6% per trade
Need oscillations > 1.2% to profit after round trip
Batch multiple oscillations together!
Feed on the waves efficiently!
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
║                   📊 SMART OSCILLATION BATCH FEEDER! 📊                   ║
║                    Minimizing Fees Through Batch Trading! 💰               ║
║                   Oscillations > 1.2% = Profitable After Fees! 📈          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FEE-AWARE OSCILLATION ANALYSIS")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])

# Check holdings
accounts = client.get_accounts()
holdings = {}
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
            value = balance * btc
            total_value += value
            holdings['BTC'] = {'amount': balance, 'value': value, 'price': btc}
        elif currency == 'ETH':
            value = balance * eth
            total_value += value
            holdings['ETH'] = {'amount': balance, 'value': value, 'price': eth}
        elif currency == 'SOL':
            value = balance * sol
            total_value += value
            holdings['SOL'] = {'amount': balance, 'value': value, 'price': sol}
        elif currency == 'XRP':
            value = balance * xrp
            total_value += value
            holdings['XRP'] = {'amount': balance, 'value': value, 'price': xrp}
        elif currency == 'DOGE':
            value = balance * doge
            total_value += value
            holdings['DOGE'] = {'amount': balance, 'value': value, 'price': doge}

print("\n💰 FEE STRUCTURE ANALYSIS:")
print("-" * 50)
print("Coinbase Fees: ~0.6% per trade")
print("Round trip cost: ~1.2% (sell + buy back)")
print("Minimum profitable oscillation: >1.2%")
print("Optimal oscillation: >2% (0.8% profit after fees)")
print(f"Current USD: ${usd_balance:.2f}")

# Track oscillations for each asset
print("\n📊 TRACKING OSCILLATIONS (Fee-Adjusted):")
print("-" * 50)

oscillation_opportunities = []
price_history = {
    'SOL': [], 'XRP': [], 'DOGE': [], 'ETH': []
}

for i in range(10):
    current_prices = {
        'SOL': float(client.get_product('SOL-USD')['price']),
        'XRP': float(client.get_product('XRP-USD')['price']),
        'DOGE': float(client.get_product('DOGE-USD')['price']),
        'ETH': float(client.get_product('ETH-USD')['price'])
    }
    
    # Track price history
    for coin in price_history:
        price_history[coin].append(current_prices[coin])
    
    # Check for profitable oscillations (>1.2% moves)
    for coin in price_history:
        if len(price_history[coin]) >= 2:
            prices = price_history[coin]
            min_price = min(prices)
            max_price = max(prices)
            oscillation = ((max_price / min_price) - 1) * 100
            
            if oscillation > 1.2:  # Profitable after fees
                profit_after_fees = oscillation - 1.2
                if coin in holdings:
                    potential_profit = holdings[coin]['value'] * (profit_after_fees / 100)
                    
                    if potential_profit > 1:  # Worth at least $1
                        oscillation_opportunities.append({
                            'coin': coin,
                            'oscillation': oscillation,
                            'profit_after_fees': profit_after_fees,
                            'dollar_profit': potential_profit,
                            'action': f"MILK {coin} for ${potential_profit:.2f}"
                        })
    
    print(f"{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  SOL: ${current_prices['SOL']:.2f} | XRP: ${current_prices['XRP']:.4f}")
    print(f"  DOGE: ${current_prices['DOGE']:.4f} | ETH: ${current_prices['ETH']:.2f}")
    
    if i == 4:
        print("  📈 Checking for fee-beating oscillations...")
    
    time.sleep(1.5)

# Batch trade recommendations
print("\n🎯 BATCH TRADING RECOMMENDATIONS:")
print("-" * 50)

if oscillation_opportunities:
    # Group by profitability
    high_profit = [o for o in oscillation_opportunities if o['profit_after_fees'] > 2]
    medium_profit = [o for o in oscillation_opportunities if 1.5 < o['profit_after_fees'] <= 2]
    low_profit = [o for o in oscillation_opportunities if o['profit_after_fees'] <= 1.5]
    
    if high_profit:
        print("🔥 HIGH PROFIT OSCILLATIONS (>2% after fees):")
        total_batch = 0
        for opp in high_profit[:3]:  # Batch top 3
            print(f"  • {opp['coin']}: {opp['oscillation']:.1f}% oscillation")
            print(f"    Profit after fees: {opp['profit_after_fees']:.1f}%")
            print(f"    Dollar profit: ${opp['dollar_profit']:.2f}")
            total_batch += opp['dollar_profit']
        print(f"  BATCH TOTAL: ${total_batch:.2f}")
    
    if medium_profit and usd_balance < 50:
        print("\n📊 MEDIUM PROFIT (1.5-2% after fees):")
        for opp in medium_profit[:2]:
            print(f"  • {opp['coin']}: ${opp['dollar_profit']:.2f} profit")
else:
    print("No oscillations currently beating fees (need >1.2%)")
    print("Wait for larger moves or batch multiple small ones")

# Smart batching strategy
print("\n💡 SMART BATCHING STRATEGY:")
print("-" * 50)
print("Rules to minimize fees:")
print("1. NEVER trade oscillations <1.2% (lose to fees)")
print("2. BATCH multiple coins in one session")
print("3. Wait for 2%+ oscillations when possible")
print("4. Minimum trade size: $50 (makes 0.6% fee = $0.30)")
print("")

# Calculate minimum profitable trade sizes
print("Minimum profitable trade sizes (0.6% fee):")
for coin, data in holdings.items():
    if data['value'] > 50:
        min_oscillation = 1.2  # To beat round trip
        min_profit = data['value'] * 0.008  # 0.8% after fees
        print(f"  {coin}: ${data['value']:.2f} position")
        print(f"    → Need {min_oscillation:.1f}% move")
        print(f"    → Profit after fees: ${min_profit:.2f}")

# Fee optimization
print("\n📈 FEE OPTIMIZATION:")
print("-" * 50)
total_fees_per_trade = total_value * 0.006  # 0.6% fee
print(f"Cost per trade at current portfolio: ${total_fees_per_trade:.2f}")
print(f"Need to make >${total_fees_per_trade * 2:.2f} per round trip")
print("")

# Batch threshold
batch_threshold = total_fees_per_trade * 3  # Want 3x fees in profit
print(f"BATCH THRESHOLD: ${batch_threshold:.2f}")
print("Only execute when total profit exceeds this!")

# Thunder's fee wisdom
print("\n⚡ THUNDER'S FEE-BEATING WISDOM (69%):")
print("-" * 50)
print("'FEES ARE THE SILENT KILLER!'")
print("")
print("Smart oscillation rules:")
print(f"• Current portfolio: ${total_value:.2f}")
print(f"• Fee per trade: ${total_fees_per_trade:.2f}")
print(f"• Minimum oscillation: 1.2%")
print(f"• Optimal oscillation: 2%+")
print(f"• Batch threshold: ${batch_threshold:.2f}")
print("")
print("Strategy:")
print("• Watch SOL for 2% swings ($213.50+)")
print("• Watch XRP for 3% swings ($3.07+)")
print("• Batch execute when total > fees * 3")
print("• Never chase <1.2% moves!")

# Final status
print("\n📊 FINAL OSCILLATION STATUS:")
print("-" * 50)
print(f"Portfolio: ${total_value:.2f}")
print(f"USD Available: ${usd_balance:.2f}")

if usd_balance < 30:
    print("Status: NEED TO MILK (but wait for >1.2% moves)")
elif usd_balance < 100:
    print("Status: Can be selective (wait for >2% moves)")
else:
    print("Status: Well funded (only milk >3% moves)")

print("\n" + "📊" * 35)
print("SMART OSCILLATION FEEDING!")
print("BEAT THE FEES WITH BATCHING!")
print("ONLY MILK PROFITABLE WAVES!")
print("💰" * 35)