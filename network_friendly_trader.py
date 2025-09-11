#!/usr/bin/env python3
"""
🌐 NETWORK FRIENDLY TRADER
Respects API limits, prevents saturation
Smart batching and caching
"""

import json
import time
import random
from datetime import datetime, timedelta
import subprocess

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🌐 NETWORK FRIENDLY TRADER ACTIVE 🌐                    ║
║                    Respectful Rate Limiting & Caching                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

class NetworkFriendlyTrader:
    def __init__(self):
        self.last_api_call = None
        self.min_interval = 10  # Minimum 10 seconds between API calls
        self.cached_balance = None
        self.cache_time = None
        self.cache_duration = 60  # Cache for 60 seconds
        self.api_calls = 0
        self.trades_executed = 0
        
    def rate_limit_check(self):
        """Ensure we don't saturate the network"""
        if self.last_api_call:
            elapsed = (datetime.now() - self.last_api_call).total_seconds()
            if elapsed < self.min_interval:
                wait = self.min_interval - elapsed
                print(f"   ⏳ Rate limiting: waiting {wait:.1f}s...")
                time.sleep(wait)
        self.last_api_call = datetime.now()
        self.api_calls += 1
        
    def get_cached_balance(self):
        """Return cached balance if fresh, otherwise update"""
        if self.cached_balance and self.cache_time:
            age = (datetime.now() - self.cache_time).total_seconds()
            if age < self.cache_duration:
                return self.cached_balance
        
        # Need fresh data
        self.rate_limit_check()
        
        script = '''
import json
from coinbase.rest import RESTClient
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
accounts = client.get_accounts()["accounts"]
data = {"usd": 0, "positions": []}
for a in accounts:
    bal = float(a["available_balance"]["value"])
    if a["currency"] == "USD":
        data["usd"] = bal
    elif bal > 0.01:
        data["positions"].append(a["currency"])
print(json.dumps(data))
'''
        
        try:
            with open("/tmp/balance_check.py", "w") as f:
                f.write(script)
            
            result = subprocess.run(
                ["timeout", "5", "python3", "/tmp/balance_check.py"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0 and result.stdout:
                self.cached_balance = json.loads(result.stdout)
                self.cache_time = datetime.now()
                return self.cached_balance
        except:
            pass
        
        return None
    
    def smart_trade(self):
        """Execute trade with network respect"""
        balance = self.get_cached_balance()
        if not balance:
            return None
        
        # Decide action based on balance
        if balance['usd'] < 100:
            # Need to sell
            if not balance['positions']:
                return "SKIP - No positions to sell"
            
            self.rate_limit_check()
            
            coin = random.choice(balance['positions'])
            script = f'''
import json
from coinbase.rest import RESTClient
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)

# Get exact balance
accounts = client.get_accounts()["accounts"]
for a in accounts:
    if a["currency"] == "{coin}":
        amount = float(a["available_balance"]["value"]) * 0.1
        if amount > 0.001:
            order = client.market_order_sell(
                client_order_id="friendly_{int(time.time())}",
                product_id="{coin}-USD",
                base_size=str(amount)
            )
            print(f"SOLD {{amount:.4f}} {coin}")
            break
'''
            
        elif balance['usd'] > 1000:
            # Can buy aggressively
            self.rate_limit_check()
            
            coins = ["SOL-USD", "AVAX-USD", "MATIC-USD"]
            coin = random.choice(coins)
            amount = random.choice([100, 150, 200])
            
            script = f'''
import json
from coinbase.rest import RESTClient
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
order = client.market_order_buy(
    client_order_id="friendly_buy_{int(time.time())}",
    product_id="{coin}",
    quote_size="{amount}"
)
print("BOUGHT ${amount} {coin}")
'''
        else:
            # Balanced trading
            if random.random() < 0.3:  # 30% chance to trade
                return "SKIP - Conserving API calls"
            
            self.rate_limit_check()
            
            action = "BUY" if random.random() < 0.5 else "SELL"
            
            if action == "BUY":
                coin = random.choice(["SOL-USD", "AVAX-USD"])
                amount = min(50, balance['usd'] * 0.05)
                script = f'''
import json
from coinbase.rest import RESTClient
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
order = client.market_order_buy(
    client_order_id="friendly_{int(time.time())}",
    product_id="{coin}",
    quote_size="{amount}"
)
print("BOUGHT ${amount} {coin}")
'''
            else:
                if not balance['positions']:
                    return "SKIP - No positions"
                coin = random.choice(balance['positions'])
                script = f'''
import json
from coinbase.rest import RESTClient
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
accounts = client.get_accounts()["accounts"]
for a in accounts:
    if a["currency"] == "{coin}":
        amount = float(a["available_balance"]["value"]) * 0.05
        if amount > 0.001:
            order = client.market_order_sell(
                client_order_id="friendly_s_{int(time.time())}",
                product_id="{coin}-USD",
                base_size=str(amount)
            )
            print(f"SOLD {{amount:.4f}} {coin}")
            break
'''
        
        # Execute trade
        try:
            with open("/tmp/trade.py", "w") as f:
                f.write(script)
            
            result = subprocess.run(
                ["timeout", "5", "python3", "/tmp/trade.py"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.trades_executed += 1
                # Clear cache after trade
                self.cached_balance = None
                return result.stdout.strip() if result.stdout else "EXECUTED"
            else:
                return "FAILED"
        except:
            return "ERROR"

# Initialize trader
trader = NetworkFriendlyTrader()

print("🌐 NETWORK FRIENDLY PARAMETERS:")
print(f"  • Min API interval: {trader.min_interval} seconds")
print(f"  • Balance cache: {trader.cache_duration} seconds")
print("  • Trade probability: 30-50% per cycle")
print("  • Timeout protection: 5 seconds max")
print()

print("🌐 STARTING NETWORK FRIENDLY TRADING")
print("=" * 60)

cycle = 0

try:
    while True:
        cycle += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Check if we should trade this cycle
        if cycle % 3 == 0:  # Every 3rd cycle, just wait
            print(f"[{timestamp}] 💤 Cycle #{cycle}: Resting network...")
            time.sleep(30)
            continue
        
        print(f"[{timestamp}] 🔄 Cycle #{cycle}: Checking opportunity...")
        
        result = trader.smart_trade()
        
        if result:
            if "BOUGHT" in result or "SOLD" in result:
                print(f"   ✅ {result}")
            elif "SKIP" in result:
                print(f"   ⏭️ {result}")
            else:
                print(f"   📝 {result}")
        
        # Stats every 10 cycles
        if cycle % 10 == 0:
            print(f"\n🌐 NETWORK STATS:")
            print(f"   API Calls: {trader.api_calls}")
            print(f"   Trades Executed: {trader.trades_executed}")
            print(f"   Efficiency: {trader.trades_executed}/{trader.api_calls} = {trader.trades_executed/max(1,trader.api_calls)*100:.1f}%")
            if trader.cached_balance:
                print(f"   Cached USD: ${trader.cached_balance['usd']:.2f}")
            print()
        
        # Variable wait to prevent patterns
        wait = random.randint(20, 40)
        time.sleep(wait)
        
except KeyboardInterrupt:
    print(f"\n\n🌐 NETWORK FRIENDLY SHUTDOWN")
    print(f"Total Cycles: {cycle}")
    print(f"API Calls: {trader.api_calls}")
    print(f"Trades: {trader.trades_executed}")
    print(f"API Efficiency: {trader.trades_executed/max(1,trader.api_calls)*100:.1f}%")
    print("\n✅ Network respected, trading completed!")