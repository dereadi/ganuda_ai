#!/usr/bin/env python3
"""
🐅 TIGER'S BLOOD HUNTER
========================
"I have one speed, I have one gear: GO!"
Finding the adrenaline moves in the market
WINNING!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import random

print("🐅 TIGER'S BLOOD ACTIVATED")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')} CST")
print("I'm not bipolar, I'm bi-WINNING!")
print()

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

class TigerBlood:
    def __init__(self):
        self.winning_streak = 0
        self.tiger_energy = 100
        self.adrenochrome_level = "MAXIMUM"
        
    def scan_for_tiger_blood(self):
        """Find the most volatile, adrenaline-pumping moves"""
        print("🔥 SCANNING FOR TIGER'S BLOOD:")
        print("-"*60)
        
        tiger_targets = {}
        
        for symbol in ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC']:
            # Rapid sampling for volatility
            samples = []
            for i in range(10):
                ticker = client.get_product(f'{symbol}-USD')
                price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
                samples.append(price)
                time.sleep(0.1)
            
            # Calculate the WILDNESS factor
            if len(samples) > 1:
                max_swing = (max(samples) - min(samples)) / min(samples) * 100
                avg_price = sum(samples) / len(samples)
                volatility = sum(abs(p - avg_price) for p in samples) / len(samples) / avg_price * 100
                
                # Tiger Blood Score
                tiger_score = max_swing * 10 + volatility * 100
                
                tiger_targets[symbol] = {
                    'score': tiger_score,
                    'swing': max_swing,
                    'volatility': volatility,
                    'current': samples[-1]
                }
                
                if tiger_score > 1:
                    blood_level = "🩸" * min(int(tiger_score), 5)
                    print(f"  {symbol}: {blood_level} Score: {tiger_score:.2f}")
        
        return tiger_targets
    
    def deploy_tiger_strike(self, targets):
        """WINNING! Deploy with tiger intensity"""
        print("\n🐅 TIGER STRIKE DEPLOYMENT:")
        print("-"*60)
        
        # Find the WILDEST target
        if targets:
            wildest = max(targets.items(), key=lambda x: x[1]['score'])
            symbol = wildest[0]
            data = wildest[1]
            
            print(f"  TARGET: {symbol}")
            print(f"  TIGER SCORE: {data['score']:.2f}")
            print(f"  VOLATILITY: {data['volatility']:.6f}%")
            print()
            
            # Get available ammo
            accounts = client.get_accounts()
            account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
            
            usd_balance = 0
            for account in account_list:
                if account['currency'] == 'USD':
                    usd_balance = float(account['available_balance']['value'])
                    break
            
            print(f"  💰 WAR CHEST: ${usd_balance:.2f}")
            
            # TIGER STRIKE SIZE (aggressive but controlled)
            if data['score'] > 5:  # HIGH OCTANE
                strike_size = min(usd_balance * 0.05, 50)  # 5% or $50
                print(f"  🔥 HIGH OCTANE STRIKE!")
            elif data['score'] > 2:  # MEDIUM HEAT
                strike_size = min(usd_balance * 0.02, 20)  # 2% or $20
                print(f"  ⚡ MEDIUM HEAT STRIKE!")
            else:  # LOW BURN
                strike_size = min(usd_balance * 0.01, 10)  # 1% or $10
                print(f"  💫 LOW BURN STRIKE!")
            
            strike_size = round(strike_size, 2)
            
            if strike_size >= 1.00:
                print(f"\n  🐅 DEPLOYING ${strike_size:.2f} OF TIGER'S BLOOD!")
                print(f"     Target: {symbol}")
                print(f"     Mode: WINNING!")
                
                try:
                    # TIGER STRIKE!
                    order = client.market_order_buy(
                        client_order_id=f"tiger_blood_{int(time.time())}",
                        product_id=f"{symbol}-USD",
                        quote_size=str(strike_size)
                    )
                    
                    print(f"\n  ✅ TIGER'S BLOOD DEPLOYED!")
                    print(f"     WINNING!")
                    self.winning_streak += 1
                    
                    # Victory quotes
                    quotes = [
                        "I'm on a drug called Charlie Sheen!",
                        "I have tiger blood and Adonis DNA!",
                        "Winning isn't everything, it's the only thing!",
                        "I don't sleep, I wait!",
                        "My success rate is 100 percent!",
                        "Boom! Another one bites the dust!",
                        "Can't stop the tiger!",
                        "I'm tired of pretending I'm not special!",
                        "DUH, WINNING!"
                    ]
                    
                    print(f"\n  💬 \"{random.choice(quotes)}\"")
                    
                except Exception as e:
                    print(f"  ❌ BLOCKED BY TROLLS: {str(e)[:50]}")
                    print(f"     (They can't handle the tiger)")
            else:
                print(f"  ⏸️ CONSERVING TIGER ENERGY")
                print(f"     (Need more ammo for proper strike)")

# Initialize the Tiger
tiger = TigerBlood()

# Scan for opportunities
targets = tiger.scan_for_tiger_blood()

# Deploy tiger strike
tiger.deploy_tiger_strike(targets)

print("\n" + "="*60)
print("🐅 TIGER'S BLOOD STATUS:")
print("-"*60)
print(f"  Winning Streak: {tiger.winning_streak}")
print(f"  Tiger Energy: {tiger.tiger_energy}%")
print(f"  Adrenochrome: {tiger.adrenochrome_level}")

# Check portfolio
accounts = client.get_accounts()
account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts

total_value = 0
for account in account_list:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.001:
        if currency == 'USD':
            total_value += balance
        else:
            ticker = client.get_product(f'{currency}-USD')
            price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
            value = balance * price
            total_value += value

print(f"\n  Portfolio: ${total_value:.2f}")
print(f"  Status: {'WINNING!' if total_value > 450 else 'BUILDING MOMENTUM!'}")

print("\n🔥 TIGER WISDOM:")
print("-"*60)
print("\"I'm different. I have a different constitution,")
print(" I have a different brain, I have a different heart.\"")
print()
print("The market can't process me with a normal brain.")
print("I see patterns others can't.")
print("I feel the blood before it spills.")
print("I am the tiger. The tiger is me.")
print()
print("🐅🩸🔥 TIGER'S BLOOD: WINNING! 🔥🩸🐅")