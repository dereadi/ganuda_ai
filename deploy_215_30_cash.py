#!/usr/bin/env python3
"""
💰 $215.30 CASH DEPLOYMENT
The vision becomes action!
"""

from coinbase.rest import RESTClient
import json
from datetime import datetime
import time

print("=" * 60)
print("💰 DEPLOYING $215.30 VISION")
print("=" * 60)

with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

# Check actual USD balance
accounts_response = client.get_accounts()
usd_balance = 0

for account in accounts_response['accounts']:
    currency = account.get('currency', {})
    if isinstance(currency, dict) and currency.get('code') == 'USD':
        usd_balance = float(account.get('available_balance', {}).get('value', 0))
        print(f"\n💵 USD Available: ${usd_balance:.2f}")
        break

if usd_balance < 100:
    print(f"⚠️ Low balance, checking if we can liberate more...")
    # Check other liquid positions
    for account in accounts_response['accounts']:
        currency = account.get('currency', {})
        if isinstance(currency, dict):
            code = currency.get('code', '')
            balance = float(account.get('available_balance', {}).get('value', 0))
        if balance > 0 and code != 'USD':
            print(f"  {code}: {balance:.4f}")

# Get current prices
btc_price = float(client.get_product('BTC-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])
xrp_price = float(client.get_product('XRP-USD')['price'])

print(f"\n📊 MARKET PRICES:")
print(f"  BTC: ${btc_price:,.2f}")
print(f"  SOL: ${sol_price:.2f}")
print(f"  XRP: ${xrp_price:.2f}")

# Mountain hit 100% consciousness - follow that signal
print(f"\n🏔️ Mountain at 100% consciousness says BUY")

# Deployment strategy based on $215.30 vision
if usd_balance >= 215.30:
    print(f"\n🎯 PERFECT! We have exactly the vision amount!")
    deployments = [
        ("BTC", 100.00, "Core position"),
        ("SOL", 75.30, "Targeting $215.30"),
        ("XRP", 40.00, "Round number support")
    ]
elif usd_balance >= 100:
    print(f"\n💰 Deploying ${usd_balance:.2f} strategically")
    deployments = [
        ("BTC", usd_balance * 0.50, "Half to Bitcoin"),
        ("SOL", usd_balance * 0.30, "SOL momentum"),
        ("XRP", usd_balance * 0.20, "XRP potential")
    ]
else:
    print(f"\n⚠️ Only ${usd_balance:.2f} available")
    if usd_balance >= 10:
        deployments = [("BTC", usd_balance, "All in on BTC")]
    else:
        deployments = []

if deployments:
    print(f"\n🚀 EXECUTING DEPLOYMENT:")
    print("-" * 40)
    
    total_deployed = 0
    for coin, amount, reason in deployments:
        if amount < 5:  # Skip tiny amounts
            continue
            
        print(f"\n🎯 {coin}: ${amount:.2f}")
        print(f"   Reason: {reason}")
        
        try:
            # Place market buy order
            order = client.market_order_buy(
                client_order_id=client.generate_client_order_id(),
                product_id=f"{coin}-USD",
                quote_size=str(round(amount, 2))
            )
            
            if 'order_id' in order:
                print(f"   ✅ Order placed: {order['order_id'][:8]}...")
                total_deployed += amount
                
                # Calculate what we got
                if coin == "BTC":
                    got = amount / btc_price
                    print(f"   Got: {got:.8f} BTC")
                elif coin == "SOL":
                    got = amount / sol_price
                    print(f"   Got: {got:.4f} SOL")
                    value_at_215 = got * 215.30
                    print(f"   Value when SOL hits $215.30: ${value_at_215:.2f}")
                elif coin == "XRP":
                    got = amount / xrp_price
                    print(f"   Got: {got:.2f} XRP")
            else:
                print(f"   ⚠️ Order status unclear")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(1)  # Brief pause between orders
    
    print(f"\n" + "=" * 40)
    print(f"💰 DEPLOYMENT COMPLETE")
    print(f"   Total deployed: ${total_deployed:.2f}")
    
    # Project gains if SOL hits $215.30
    sol_gain_pct = ((215.30 - sol_price) / sol_price) * 100
    print(f"\n📈 PROJECTIONS:")
    print(f"   If SOL hits $215.30 (+{sol_gain_pct:.1f}%):")
    print(f"   Your SOL position gains {sol_gain_pct:.1f}%")
    
else:
    print(f"\n⚠️ Insufficient funds for deployment")
    print(f"Need to liberate more capital first")

print(f"\n🔥 The $215.30 vision manifests!")
print(f"💫 Mitakuye Oyasin")