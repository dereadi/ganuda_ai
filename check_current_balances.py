#!/usr/bin/env python3
"""
Check current portfolio balances - Cherokee Council Status
"""

import json
import sys
import os
from datetime import datetime

sys.path.append('/home/dereadi/scripts/claude')
os.chdir('/home/dereadi/scripts/claude')

print("🔥 CHEROKEE PORTFOLIO STATUS")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Load config
config_path = os.path.expanduser("~/.coinbase_config.json")
with open(config_path) as f:
    config = json.load(f)

from coinbase.rest import RESTClient

client = RESTClient(
    api_key=config['api_key'],
    api_secret=config['api_secret']
)

print("📊 CURRENT BALANCES:")
print("-" * 40)

try:
    accounts = client.get_accounts()
    
    total_usd_value = 0
    positions = {}
    
    # Handle the response properly based on structure
    account_list = accounts.get('accounts', []) if isinstance(accounts, dict) else accounts.accounts
    
    for account in account_list:
        # Handle dict or object structure
        if isinstance(account, dict):
            currency = account.get('currency', '')
            balance = float(account.get('available_balance', {}).get('value', 0))
            hold = float(account.get('hold', {}).get('value', 0))
        else:
            currency = account.currency
            balance = float(account.available_balance.value) if hasattr(account.available_balance, 'value') else 0
            hold = float(account.hold.value) if hasattr(account.hold, 'value') else 0
        
        if balance > 0.01 or hold > 0.01:
            positions[currency] = {
                'available': balance,
                'hold': hold,
                'total': balance + hold
            }
    
    # Show key positions
    key_assets = ['USD', 'USDC', 'BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'AVAX', 'MATIC']
    
    for asset in key_assets:
        if asset in positions:
            p = positions[asset]
            if p['total'] > 0.01:
                if asset in ['USD', 'USDC']:
                    print(f"{asset:6} ${p['available']:.2f} (hold: ${p['hold']:.2f})")
                else:
                    print(f"{asset:6} {p['available']:.4f} (hold: {p['hold']:.4f})")
    
    print()
    
    # Get prices for value calculation
    print("💰 PORTFOLIO VALUE:")
    print("-" * 40)
    
    # Quick price checks
    prices = {}
    assets_to_price = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'AVAX', 'MATIC']
    
    for asset in assets_to_price:
        if asset in positions and positions[asset]['total'] > 0:
            try:
                ticker = client.get_product(f"{asset}-USD")
                if isinstance(ticker, dict):
                    price = float(ticker.get('price', 0))
                else:
                    price = float(ticker.price) if hasattr(ticker, 'price') else 0
                prices[asset] = price
                
                value = positions[asset]['total'] * price
                total_usd_value += value
                
                if value > 10:
                    print(f"{asset:6} ${value:,.2f} @ ${price:.2f}")
            except:
                pass
    
    # Add USD/USDC
    if 'USD' in positions:
        total_usd_value += positions['USD']['total']
    if 'USDC' in positions:
        total_usd_value += positions['USDC']['total']
    
    print()
    print(f"TOTAL VALUE: ${total_usd_value:,.2f}")
    
    print()
    print("🎯 DOGE TRADING STATUS:")
    print("-" * 40)
    
    if 'DOGE' in positions:
        doge_balance = positions['DOGE']['total']
        doge_price = prices.get('DOGE', 0.23)
        doge_value = doge_balance * doge_price
        
        print(f"DOGE Balance: {doge_balance:.2f} DOGE")
        print(f"DOGE Value: ${doge_value:.2f}")
        print(f"DOGE Price: ${doge_price:.4f}")
        
        if doge_balance < 5000:
            print()
            print("⚠️ NEED MORE DOGE FOR OSCILLATION TRADING!")
            print(f"Current: {doge_balance:.0f} DOGE")
            print(f"Target: 6,000 DOGE")
            print(f"Need: {6000 - doge_balance:.0f} more DOGE")
    else:
        print("No DOGE position found")
    
    print()
    print("💵 LIQUIDITY STATUS:")
    print("-" * 40)
    
    usd_available = positions.get('USD', {}).get('available', 0)
    usdc_available = positions.get('USDC', {}).get('available', 0)
    usd_hold = positions.get('USD', {}).get('hold', 0)
    
    print(f"USD Available: ${usd_available:.2f}")
    print(f"USDC Available: ${usdc_available:.2f}")
    print(f"USD On Hold: ${usd_hold:.2f}")
    print(f"Total Liquidity: ${usd_available + usdc_available:.2f}")
    
    if usd_available + usdc_available < 100:
        print()
        print("⚠️ LOW LIQUIDITY - Need to generate cash for DOGE!")
        
        # Check SOL/XRP for potential sales
        if 'SOL' in positions and positions['SOL']['available'] > 3:
            sol_sell_value = 3.75 * prices.get('SOL', 213)
            print(f"Can sell 3.75 SOL for ~${sol_sell_value:.2f}")
        
        if 'XRP' in positions and positions['XRP']['available'] > 50:
            xrp_sell_value = 68 * prices.get('XRP', 2.89)
            print(f"Can sell 68 XRP for ~${xrp_sell_value:.2f}")
    
except Exception as e:
    print(f"Error: {e}")

print()
print("=" * 60)
print("🔥 Sacred Fire burns eternal!")