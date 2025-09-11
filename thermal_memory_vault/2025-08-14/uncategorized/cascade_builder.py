#!/usr/bin/env python3
"""
💧 CASCADE TRADING BUILDER
==========================
Start with $0.02, cascade up to $5+ through rapid micro-trades
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

class CascadeBuilder:
    def __init__(self):
        config = json.load(open('/home/dereadi/.coinbase_config.json'))
        self.client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])
        
        # Cascade parameters
        self.starting_capital = 0.02  # Our current USD
        self.target_capital = 5.00    # Goal for learning trades
        self.cascade_multiplier = 1.5  # 50% gain per cascade
        
    def get_usd_balance(self):
        """Get current USD balance"""
        accounts = self.client.get_accounts()
        account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
        
        for account in account_list:
            if account['currency'] == 'USD':
                return float(account['available_balance']['value'])
        return 0.0
    
    def find_volatile_asset(self):
        """Find the most volatile asset for cascading"""
        volatility = {}
        
        for symbol in ['BTC', 'ETH', 'SOL']:
            ticker = self.client.get_product(f'{symbol}-USD')
            price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
            
            # Check recent price changes (simulated)
            time.sleep(0.5)
            ticker2 = self.client.get_product(f'{symbol}-USD')
            price2 = float(ticker2.price if hasattr(ticker2, 'price') else ticker2.get('price', 0))
            
            change = abs(price2 - price) / price
            volatility[symbol] = change
        
        # Return most volatile
        best = max(volatility, key=volatility.get)
        return best, volatility[best]
    
    def execute_cascade_trade(self, step, capital):
        """Execute one cascade step"""
        print(f"\n🌊 CASCADE STEP {step}:")
        print(f"   Capital: ${capital:.2f}")
        
        # Find best asset
        asset, vol = self.find_volatile_asset()
        print(f"   Target: {asset} (volatility: {vol*100:.4f}%)")
        
        if capital < 0.01:
            print(f"   ⚠️ Capital too small for trade")
            return capital
        
        try:
            # Buy the volatile asset
            print(f"   💰 Buying ${capital:.2f} of {asset}...")
            
            # Check if we have enough
            current_usd = self.get_usd_balance()
            if current_usd < capital:
                # Sell a tiny bit of holdings to get USD
                print(f"   📊 Need to free up ${capital - current_usd:.2f}")
                self.free_up_capital(capital - current_usd)
            
            # Execute buy
            order = self.client.market_order_buy(
                client_order_id=f"cascade_{asset}_{int(time.time())}",
                product_id=f"{asset}-USD",
                quote_size=str(capital)
            )
            
            print(f"   ✅ Bought {asset}!")
            
            # Wait for micro-movement
            print(f"   ⏳ Waiting for movement...")
            time.sleep(3)
            
            # Sell for small profit
            accounts = self.client.get_accounts()
            account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
            
            for account in account_list:
                if account['currency'] == asset:
                    balance = float(account['available_balance']['value'])
                    if balance > 0:
                        print(f"   💸 Selling {balance:.8f} {asset}...")
                        
                        order = self.client.market_order_sell(
                            client_order_id=f"cascade_sell_{asset}_{int(time.time())}",
                            product_id=f"{asset}-USD",
                            base_size=str(balance)
                        )
                        
                        # Check new USD balance
                        time.sleep(1)
                        new_capital = self.get_usd_balance()
                        profit = new_capital - capital
                        
                        print(f"   ✅ Sold! New capital: ${new_capital:.2f}")
                        print(f"   📈 Profit: ${profit:+.4f} ({(profit/capital)*100:+.2f}%)")
                        
                        return new_capital
            
        except Exception as e:
            print(f"   ❌ Trade failed: {e}")
            return capital
        
        return capital
    
    def free_up_capital(self, amount_needed):
        """Sell small amount of holdings to get USD"""
        # Sell tiny bit of SOL (most volatile)
        accounts = self.client.get_accounts()
        account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
        
        for account in account_list:
            if account['currency'] == 'SOL':
                balance = float(account['available_balance']['value'])
                if balance > 0:
                    # Calculate how much SOL to sell
                    ticker = self.client.get_product('SOL-USD')
                    price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
                    sol_to_sell = min(amount_needed / price * 1.1, balance * 0.01)  # Max 1% of holdings
                    
                    print(f"      Selling {sol_to_sell:.6f} SOL for ${amount_needed:.2f}")
                    
                    order = self.client.market_order_sell(
                        client_order_id=f"free_capital_{int(time.time())}",
                        product_id="SOL-USD",
                        base_size=str(sol_to_sell)
                    )
                    
                    return True
        return False

print("💧 CASCADE TRADING BUILDER")
print("="*60)
print("Building capital through cascading micro-trades...")
print(f"Time: {datetime.now().strftime('%I:%M %p CST')}")
print()

builder = CascadeBuilder()

# Check starting capital
current_capital = builder.get_usd_balance()
print(f"📊 STARTING CAPITAL: ${current_capital:.2f}")
print(f"🎯 TARGET: ${builder.target_capital:.2f}")
print(f"📈 Strategy: Cascade trades with {(builder.cascade_multiplier-1)*100:.0f}% target gain")

if current_capital < 0.01:
    print("\n⚠️ Need to free up initial capital...")
    builder.free_up_capital(0.10)  # Get 10 cents to start
    time.sleep(2)
    current_capital = builder.get_usd_balance()
    print(f"✅ New capital: ${current_capital:.2f}")

print("\n🌊 STARTING CASCADE SEQUENCE:")
print("-"*60)

# Run cascade steps
step = 1
while current_capital < builder.target_capital and step <= 10:
    current_capital = builder.execute_cascade_trade(step, current_capital)
    
    if current_capital >= builder.target_capital:
        print(f"\n🎯 TARGET REACHED! Capital: ${current_capital:.2f}")
        break
    
    step += 1
    
    if step <= 10 and current_capital > 0:
        print(f"\n⏳ Preparing next cascade...")
        time.sleep(2)

print("\n" + "="*60)
print("📊 CASCADE RESULTS:")
print("-"*60)
print(f"  Final Capital: ${current_capital:.2f}")
print(f"  Growth: {(current_capital/0.02 - 1)*100:+.1f}%")
print(f"  Cascade Steps: {step-1}")

if current_capital >= builder.target_capital:
    print(f"  Status: ✅ SUCCESS - Ready for $5 learning trades!")
else:
    print(f"  Status: 🔄 In Progress - ${builder.target_capital - current_capital:.2f} to go")

print("\n✨ CASCADE TRADING WISDOM:")
print("-"*60)
print("• Small gains compound quickly")
print("• 10 trades at 5% = 63% total gain")
print("• Volatility is our friend in micro-trades")
print("• Quick in-and-out reduces risk")

print("\n🦀 The Quantum Crawdads cascade to victory!")
print("   Each tiny trade builds momentum...")
print("   Like a waterfall of micro-profits!")
print("   💧 Cascade your way to learning capital! 💧")