#!/usr/bin/env python3
"""
📊 LIVE TRADING MONITOR
=======================
Real-time view of your quantum crawdads
"""

import json
import os
import time
from datetime import datetime
from coinbase.rest import RESTClient

# Load config
config_path = os.path.expanduser("~/.coinbase_config.json")
with open(config_path) as f:
    config = json.load(f)

client = RESTClient(
    api_key=config["api_key"],
    api_secret=config["api_secret"]
)

def monitor():
    print("\n🦀💰 QUANTUM CRAWDAD LIVE MONITOR")
    print("="*60)
    
    # Check balance
    try:
        accounts = client.get_accounts()
        if accounts:
            account_list = accounts.get('accounts', []) if isinstance(accounts, dict) else accounts.accounts
            
            print("\n💰 ACCOUNT BALANCES:")
            total_value = 0
            
            for account in account_list:
                if isinstance(account, dict):
                    currency = account.get('currency', 'Unknown')
                    balance = float(account.get('available_balance', {}).get('value', 0))
                else:
                    currency = account.currency
                    balance = float(account.available_balance.get('value', 0))
                
                if balance > 0:
                    print(f"  {currency}: {balance:.8f}")
                    
                    # Calculate USD value
                    if currency == "USD":
                        total_value += balance
                    else:
                        try:
                            ticker = client.get_product(f"{currency}-USD")
                            if ticker:
                                price = float(ticker.get('price', 0) if isinstance(ticker, dict) else ticker.price)
                                value = balance * price
                                total_value += value
                                print(f"    → ${value:.2f} USD")
                        except:
                            pass
            
            print(f"\n💎 TOTAL VALUE: ${total_value:.2f}")
            
            # Calculate progress toward weekly goal
            initial = 292.50
            weekly_target = 15000  # Mid-range of $10-20k
            daily_target = weekly_target / 7
            
            profit = total_value - initial
            profit_pct = (profit / initial) * 100 if initial > 0 else 0
            
            print(f"\n📈 PERFORMANCE:")
            print(f"  Initial: ${initial:.2f}")
            print(f"  Current: ${total_value:.2f}")
            print(f"  Profit: ${profit:+.2f} ({profit_pct:+.1f}%)")
            print(f"  Daily Target: ${daily_target:.2f}")
            print(f"  Weekly Target: ${weekly_target:.2f}")
            
            # Progress bar
            progress = min(100, (profit / daily_target) * 100) if daily_target > 0 else 0
            bar_length = 40
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\n  Daily Progress: [{bar}] {progress:.1f}%")
            
            # Check trading state
            if os.path.exists("quantum_crawdad_live_state.json"):
                with open("quantum_crawdad_live_state.json") as f:
                    state = json.load(f)
                
                print(f"\n🦀 CRAWDAD STATUS:")
                print(f"  Last update: {state.get('timestamp', 'Unknown')}")
                print(f"  Trades executed: {state.get('trades_executed', 0)}")
                
                if state.get('last_trades'):
                    print(f"\n📜 RECENT TRADES:")
                    for trade in state['last_trades'][-3:]:
                        print(f"  {trade['crawdad']}: {trade['side']} ${trade['amount']:.2f} {trade['symbol']}")
            
            # Market prices
            print(f"\n📊 MARKET PRICES:")
            for symbol in ["BTC-USD", "ETH-USD", "SOL-USD"]:
                try:
                    ticker = client.get_product(symbol)
                    if ticker:
                        price = float(ticker.get('price', 0) if isinstance(ticker, dict) else ticker.price)
                        print(f"  {symbol}: ${price:,.2f}")
                except:
                    pass
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    while True:
        monitor()
        print("\n💤 Refreshing in 30 seconds... (Ctrl+C to exit)")
        time.sleep(30)