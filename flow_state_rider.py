#!/usr/bin/env python3
"""
🌊 FLOW STATE RIDER
===================
We are IN THE FLOW - ride it like water
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("🌊 ENTERING FLOW STATE")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')} CST")
print("We are IN THE FLOW - becoming water...")
print()

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

# Get current positions - we ARE the flow
accounts = client.get_accounts()
account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts

print("💧 CURRENT FLOW POSITIONS:")
print("-"*60)

usd_balance = 0
positions = {}
total_value = 0

for account in account_list:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.001:
        if currency == 'USD':
            usd_balance = balance
            total_value += balance
            print(f"  Liquid Capital: ${balance:.2f}")
        else:
            ticker = client.get_product(f'{currency}-USD')
            price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
            value = balance * price
            total_value += value
            positions[currency] = {'balance': balance, 'price': price, 'value': value}
            print(f"  {currency} Flow: {balance:.6f} @ ${price:,.2f} = ${value:.2f}")

print(f"\n🌊 TOTAL FLOW ENERGY: ${total_value:.2f}")

# Feel the flow direction
print("\n🔮 READING THE FLOW:")
print("-"*60)

flows = {}
for symbol in positions.keys():
    ticker1 = client.get_product(f'{symbol}-USD')
    price1 = float(ticker1.price if hasattr(ticker1, 'price') else ticker1.get('price', 0))
    
    time.sleep(2)
    
    ticker2 = client.get_product(f'{symbol}-USD')
    price2 = float(ticker2.price if hasattr(ticker2, 'price') else ticker2.get('price', 0))
    
    momentum = ((price2 - price1) / price1) * 100
    flows[symbol] = momentum
    
    if momentum > 0:
        print(f"  {symbol}: 🌊 FLOWING UP +{momentum:.6f}%")
    elif momentum < 0:
        print(f"  {symbol}: 💧 EBBING {momentum:.6f}%")
    else:
        print(f"  {symbol}: 🔄 CIRCLING")

# We ARE the flow - move with it
if usd_balance > 10:
    strongest_flow = max(flows.items(), key=lambda x: x[1]) if flows else None
    
    if strongest_flow and strongest_flow[1] > 0:
        print(f"\n🌊 FLOWING INTO {strongest_flow[0]}!")
        print(f"   Momentum: +{strongest_flow[1]:.6f}%")
        
        # Flow like water - small, continuous movement
        flow_amount = min(usd_balance * 0.2, 30)  # 20% or $30 max
        flow_amount = round(flow_amount, 2)
        
        if flow_amount >= 1:
            print(f"   Flowing ${flow_amount:.2f} into the current...")
            try:
                order = client.market_order_buy(
                    client_order_id=f"flow_{int(time.time())}",
                    product_id=f"{strongest_flow[0]}-USD",
                    quote_size=str(flow_amount)
                )
                print(f"   ✅ Merged with the flow!")
            except Exception as e:
                print(f"   ⚠️ Flow blocked: {str(e)[:50]}")

# Flow state wisdom
print("\n🧘 FLOW STATE WISDOM:")
print("-"*60)
print("• We don't fight the current, we ARE the current")
print("• Water always finds the path of least resistance")
print("• In flow, there is no thought, only movement")
print("• The swarm moves as one organism")

# Sun Tzu flow
print("\n⚔️ SUN TZU ON FLOW:")
print("-"*60)
print("'Be like water making its way through cracks'")
print("'Do not be assertive, but adjust to the object'")
print("'In yielding, find your strength'")
print("'The supreme good is like water'")

# Current state
if total_value > 450:
    print("\n🌊 THE FLOW STRENGTHENS")
    print("   Each drop adds to the river...")
elif total_value > 400:
    print("\n💧 STEADY FLOW")
    print("   Patient accumulation...")
else:
    print("\n🏞️ BUILDING THE STREAM")
    print("   From trickle to torrent...")

print("\n🌊 WE ARE IN THE FLOW 🌊")
print("   No resistance, only movement...")
print("   The crawdads swim as water...")
print("   🦀💧🦀💧🦀💧🦀")