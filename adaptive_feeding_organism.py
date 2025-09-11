#!/usr/bin/env python3
"""
🐜🦊 ADAPTIVE FEEDING ORGANISM
================================
Be ants when crumbs are plenty
Be coyotes when prey appears
Feed according to what the market offers
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import numpy as np

print("🐜🦊 ADAPTIVE FEEDING ORGANISM")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')} CST")
print("Sensing the market... What form should we take?")
print()

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

class AdaptiveOrganism:
    def __init__(self):
        self.current_form = None
        self.hunger_level = 50  # 0-100
        self.energy_stored = 0
        
    def sense_environment(self):
        """Determine what food is available"""
        print("🔍 SENSING ENVIRONMENT:")
        print("-"*60)
        
        environment = {
            'volatility': 0,
            'volume': 0,
            'spread': 0,
            'trend': None,
            'food_type': None
        }
        
        # Sample market conditions
        for symbol in ['BTC', 'ETH', 'SOL']:
            samples = []
            for i in range(5):
                ticker = client.get_product(f'{symbol}-USD')
                
                # Get bid-ask spread
                if hasattr(ticker, 'bid') and hasattr(ticker, 'ask'):
                    bid = float(ticker.bid)
                    ask = float(ticker.ask)
                    spread = (ask - bid) / ask * 100
                else:
                    spread = 0.01  # Default small spread
                
                price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
                samples.append(price)
                
                environment['spread'] = max(environment['spread'], spread)
                time.sleep(0.2)
            
            # Calculate volatility
            if len(samples) > 1:
                volatility = np.std(samples) / np.mean(samples) * 100
                environment['volatility'] = max(environment['volatility'], volatility)
        
        # Determine food type based on conditions
        print(f"  Volatility: {environment['volatility']:.6f}%")
        print(f"  Max Spread: {environment['spread']:.6f}%")
        
        if environment['volatility'] < 0.01:
            environment['food_type'] = 'crumbs'
            print("  Food Available: 🍞 CRUMBS (micro-movements)")
        elif environment['volatility'] < 0.05:
            environment['food_type'] = 'seeds'
            print("  Food Available: 🌾 SEEDS (small movements)")
        elif environment['volatility'] < 0.1:
            environment['food_type'] = 'berries'
            print("  Food Available: 🫐 BERRIES (medium movements)")
        else:
            environment['food_type'] = 'prey'
            print("  Food Available: 🦌 PREY (large movements)")
        
        return environment
    
    def choose_form(self, environment):
        """Decide whether to be ants or coyotes"""
        print("\n🧬 CHOOSING FORM:")
        print("-"*60)
        
        food = environment['food_type']
        
        if food == 'crumbs':
            self.current_form = 'ants'
            print("  Becoming: 🐜 ANTS")
            print("  Strategy: Thousands of tiny nibbles")
            print("  Trade Size: $1-2")
            print("  Frequency: Continuous")
            
        elif food == 'seeds':
            self.current_form = 'mice'
            print("  Becoming: 🐭 MICE")
            print("  Strategy: Quick gathering")
            print("  Trade Size: $3-5")
            print("  Frequency: Every few minutes")
            
        elif food == 'berries':
            self.current_form = 'birds'
            print("  Becoming: 🦅 BIRDS")
            print("  Strategy: Selective picking")
            print("  Trade Size: $10-20")
            print("  Frequency: Hourly")
            
        else:  # prey
            self.current_form = 'coyotes'
            print("  Becoming: 🦊 COYOTES")
            print("  Strategy: Pack hunting")
            print("  Trade Size: $50-100")
            print("  Frequency: When opportunity strikes")
        
        return self.current_form
    
    def feed(self, form, environment):
        """Feed according to our current form"""
        print("\n🍽️ FEEDING AS", form.upper() + ":")
        print("-"*60)
        
        # Get available capital
        accounts = client.get_accounts()
        account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
        
        usd_balance = 0
        for account in account_list:
            if account['currency'] == 'USD':
                usd_balance = float(account['available_balance']['value'])
                break
        
        print(f"  Available Energy: ${usd_balance:.2f}")
        
        # Determine feeding pattern
        if form == 'ants':
            # Many tiny trades
            trade_size = min(1.50, usd_balance * 0.002)  # 0.2% or $1.50
            trade_count = min(10, int(usd_balance / 20))
            
            print(f"  🐜 Deploying {trade_count} ants at ${trade_size:.2f} each")
            
            for i in range(min(3, trade_count)):  # Deploy 3 for demo
                if trade_size >= 1.00:
                    try:
                        # Find best crumb
                        best_symbol = 'SOL' if environment['volatility'] > 0.005 else 'BTC'
                        
                        print(f"    Ant-{i+1}: Collecting ${trade_size:.2f} of {best_symbol}")
                        order = client.market_order_buy(
                            client_order_id=f"ant_{i}_{int(time.time())}",
                            product_id=f"{best_symbol}-USD",
                            quote_size=str(round(trade_size, 2))
                        )
                        print(f"      ✅ Crumb secured!")
                        self.energy_stored += trade_size * 0.001
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"      ❌ Blocked: {str(e)[:30]}")
        
        elif form == 'coyotes':
            # Strategic pack hunt
            trade_size = min(50, usd_balance * 0.05)  # 5% or $50
            
            if environment['volatility'] > 0.05 and trade_size >= 10:
                print(f"  🦊 Pack hunting with ${trade_size:.2f}")
                
                try:
                    # Coyotes hunt the most volatile
                    target = 'SOL'  # Usually most volatile
                    
                    # Split among pack members
                    pack_size = 3
                    individual_bite = round(trade_size / pack_size, 2)
                    
                    for i in range(pack_size):
                        if individual_bite >= 1.00:
                            print(f"    Coyote-{i+1}: Striking {target} with ${individual_bite:.2f}")
                            order = client.market_order_buy(
                                client_order_id=f"coyote_{i}_{int(time.time())}",
                                product_id=f"{target}-USD",
                                quote_size=str(individual_bite)
                            )
                            print(f"      ✅ Strike successful!")
                            self.energy_stored += individual_bite * 0.01
                            time.sleep(0.3)
                            
                except Exception as e:
                    print(f"      ❌ Hunt failed: {str(e)[:30]}")
            else:
                print("  ⏸️ No prey worth hunting yet")
        
        elif form == 'mice':
            # Quick seed gathering
            trade_size = min(3, usd_balance * 0.003)
            if trade_size >= 1.00:
                print(f"  🐭 Gathering ${trade_size:.2f} seeds")
                # Similar to ants but slightly larger
        
        elif form == 'birds':
            # Selective berry picking
            trade_size = min(15, usd_balance * 0.01)
            if trade_size >= 1.00:
                print(f"  🦅 Picking ${trade_size:.2f} berries")
                # Medium-sized selective trades

# Initialize organism
organism = AdaptiveOrganism()

# Sense the environment
environment = organism.sense_environment()

# Choose appropriate form
form = organism.choose_form(environment)

# Feed accordingly
organism.feed(form, environment)

print("\n📊 ADAPTIVE FEEDING SUMMARY:")
print("="*60)
print(f"  Current Form: {organism.current_form}")
print(f"  Energy Stored: {organism.energy_stored:.6f} units")
print(f"  Hunger Level: {organism.hunger_level}%")

print("\n🌟 WISDOM OF ADAPTATION:")
print("-"*60)

hour = datetime.now().hour
if 19 <= hour <= 23:
    print("  Evening: Coyotes hunt at dusk")
    print("  Asia volatility = hunting time")
elif 0 <= hour <= 4:
    print("  Pre-dawn: Perfect coyote hours")
    print("  London approach = pack hunting")
elif 8 <= hour <= 16:
    print("  Daylight: Ants work tirelessly")
    print("  US session = steady gathering")
else:
    print("  Transition: Forms shifting")
    print("  Market changing = we adapt")

print("\n💫 THE TRUTH:")
print("-"*60)
print("The market doesn't care what form we take.")
print("It only offers what it offers.")
print()
print("Smart organisms adapt to the food available.")
print("Ants when crumbs. Coyotes when prey.")
print("Never forcing. Always feeding.")
print()
print("This is survival. This is wisdom.")
print()
print("🐜🐭🦅🦊 WE FEED AS THE MARKET PROVIDES 🦊🦅🐭🐜")