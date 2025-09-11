#!/usr/bin/env python3
"""
🍴 VOLATILITY EATER
"Sensitive to daily rallies, we feast on every swing"
"""

import json
import time
from datetime import datetime, timedelta
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🍴 VOLATILITY EATER ACTIVE 🍴                       ║
║                    "Every rally has micro-swings to harvest"               ║
║                     "Sensitivity + Patience = Profit"                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

class VolatilityEater:
    def __init__(self):
        self.sensitivity = 0.002  # 0.2% moves trigger action
        self.micro_size = 2.0      # $2 trades to eat volatility
        self.daily_patterns = {
            "pre_market": (6, 9),    # 6-9 AM: Pre-market positioning
            "morning_rally": (9, 11), # 9-11 AM: Morning surge
            "lunch_dip": (11, 13),   # 11-1 PM: Lunch pullback
            "afternoon_run": (13, 15), # 1-3 PM: Afternoon rally
            "close_position": (15, 16), # 3-4 PM: Close positioning
            "after_hours": (16, 18)  # 4-6 PM: After hours moves
        }
        
    def identify_pattern(self):
        """Identify current daily pattern"""
        hour = datetime.now().hour
        
        for pattern, (start, end) in self.daily_patterns.items():
            if start <= hour < end:
                return pattern
        return "off_hours"
    
    def get_micro_volatility(self, product_id):
        """Get micro volatility in last hour"""
        try:
            end = int(time.time())
            start = end - 3600  # Last hour
            
            candles = client.get_candles(product_id, start, end, granularity='FIVE_MINUTE')['candles']
            
            if not candles:
                return 0, 0, 0
            
            prices = [float(c['close']) for c in candles]
            high = max(prices)
            low = min(prices)
            current = prices[-1]
            
            volatility = (high - low) / low if low > 0 else 0
            position = (current - low) / (high - low) if high > low else 0.5
            
            return volatility, position, current
            
        except:
            return 0, 0.5, 0
    
    def calculate_rally_sensitivity(self, pattern):
        """Adjust sensitivity based on time of day"""
        sensitivities = {
            "morning_rally": 1.5,    # More sensitive during rallies
            "afternoon_run": 1.3,
            "lunch_dip": 1.2,        # Sensitive to dips
            "pre_market": 1.0,
            "close_position": 1.1,
            "after_hours": 0.8,
            "off_hours": 0.5
        }
        return sensitivities.get(pattern, 1.0)

# Initialize the eater
eater = VolatilityEater()

# Current pattern
pattern = eater.identify_pattern()
sensitivity_mult = eater.calculate_rally_sensitivity(pattern)

print(f"\n⏰ DAILY PATTERN ANALYSIS:")
print(f"   Current Pattern: {pattern.replace('_', ' ').title()}")
print(f"   Sensitivity Multiplier: {sensitivity_mult}x")
print(f"   Effective Threshold: {eater.sensitivity * sensitivity_mult:.3%}")

# Analyze each coin for volatility eating opportunities
print(f"\n🍴 VOLATILITY TO EAT:")
print("-" * 60)

accounts = client.get_accounts()['accounts']
opportunities = []

# Focus on high-volatility coins
coins_to_check = ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC', 'DOGE', 'LINK']

for coin in coins_to_check:
    product_id = f"{coin}-USD"
    volatility, position, current = eater.get_micro_volatility(product_id)
    
    if volatility > 0:
        print(f"\n{coin}:")
        print(f"   Price: ${current:,.2f}")
        print(f"   1hr Volatility: {volatility:.2%}")
        print(f"   Position in range: {position:.0%}")
        
        # Identify eating opportunity
        effective_threshold = eater.sensitivity * sensitivity_mult
        
        if volatility > effective_threshold:
            if position < 0.3:
                print(f"   🟢 EAT THE DIP! (near bottom of range)")
                opportunities.append(('buy', coin, eater.micro_size, volatility))
            elif position > 0.7:
                print(f"   🔴 EAT THE SPIKE! (near top of range)")
                opportunities.append(('sell', coin, eater.micro_size, volatility))
            else:
                print(f"   ⏸️ Middle of range - wait for extremes")
        else:
            print(f"   💤 Not volatile enough to eat")

# Intraday patterns to exploit
print(f"\n📈 INTRADAY VOLATILITY PATTERNS:")
print("-" * 60)

patterns_analysis = {
    "Morning Rally (9-11 AM)": "BTC often pumps 0.5-1%",
    "Lunch Dip (11-1 PM)": "Pullback 0.3-0.5% common",
    "Afternoon Run (1-3 PM)": "Second leg up 0.4-0.8%",
    "Close Position (3-4 PM)": "Volatility spike, position for overnight",
    "After Hours (4-6 PM)": "Thin liquidity = larger swings"
}

for time_slot, behavior in patterns_analysis.items():
    status = "🟢 ACTIVE" if time_slot.lower().startswith(pattern.replace('_', ' ')) else "⏸️ Waiting"
    print(f"   {time_slot}: {behavior} {status}")

# Execute the best volatility eating opportunity
print(f"\n🎯 EATING VOLATILITY:")
print("-" * 60)

if opportunities:
    # Sort by volatility, take the highest
    opportunities.sort(key=lambda x: x[3], reverse=True)
    action, coin, size, vol = opportunities[0]
    
    print(f"   EATING: {coin} volatility ({vol:.2%})")
    print(f"   ACTION: {action.upper()} ${size}")
    
    try:
        if action == 'buy':
            # Check USD balance
            usd_balance = 0
            for a in accounts:
                if a['currency'] == 'USD':
                    usd_balance = float(a['available_balance']['value'])
                    break
            
            if usd_balance >= size:
                order = client.market_order_buy(
                    client_order_id=f"eat_vol_{int(time.time()*1000)}",
                    product_id=f"{coin}-USD",
                    quote_size=str(size)
                )
                print(f"   ✅ ATE THE DIP! Bought ${size} of {coin}")
            else:
                print(f"   ⚠️ Only ${usd_balance:.2f} available - need more USD")
                
        else:  # sell
            # Get coin balance
            for a in accounts:
                if a['currency'] == coin:
                    balance = float(a['available_balance']['value'])
                    ticker = client.get_product(f"{coin}-USD")
                    price = float(ticker.price)
                    
                    if balance * price >= size:
                        sell_amount = size / price
                        order = client.market_order_sell(
                            client_order_id=f"eat_spike_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            base_size=str(sell_amount)
                        )
                        print(f"   ✅ ATE THE SPIKE! Sold ${size} of {coin}")
                    else:
                        print(f"   ⚠️ Not enough {coin} to sell")
                    break
                    
    except Exception as e:
        print(f"   ❌ Couldn't eat: {str(e)[:50]}")
else:
    print("   ⏸️ No volatility to eat right now - patience")

# Volatility eating strategy
print(f"\n📚 VOLATILITY EATING WISDOM:")
print("-" * 60)
print(f"""
   During {pattern.replace('_', ' ').title()}:
   
   • Sensitivity at {sensitivity_mult}x normal
   • Look for {eater.sensitivity * sensitivity_mult:.2%}+ moves
   • Use small bites (${eater.micro_size}) to compound
   • Buy dips below 30% of hourly range
   • Sell spikes above 70% of hourly range
   
   Daily Volatility Feast Schedule:
   🌅 6-9 AM: Position for the day
   📈 9-11 AM: Eat the morning rally
   📉 11-1 PM: Feast on lunch dips
   🚀 1-3 PM: Harvest afternoon momentum
   🔔 3-4 PM: Close volatility
   🌙 After 4 PM: Hunt thin liquidity swings
   
   "Small bites of volatility compound into meals"
""")

# Show Greeks eating alongside
print(f"\n🏛️ GREEKS VOLATILITY REPORT:")
print("   Δ Delta: 150 cycles - eating gaps all day")
print("   Θ Theta: 190+ cycles - time decay never stops")
print("   ν Vega: Loves this volatility environment")
print(f"   All Greeks: Optimized for {pattern.replace('_', ' ')}")

print(f"\n🍴 The Volatility Eater continues to feast...")
print("Every micro-rally feeds the river 🌊")