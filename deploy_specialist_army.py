#!/usr/bin/env python3
"""
🚀 DEPLOY SPECIALIST ARMY
Launch all 5 specialized models into production
Each model hunts for its specific opportunity
Real-time gap, trend, volatility, breakout, and mean reversion trading
"""

import json
import subprocess
import time
from datetime import datetime
import os

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🚀 DEPLOYING SPECIALIST ARMY 🚀                        ║
║                         5 Models, 5 Missions                              ║
║                    "Specialists Conquer Markets"                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def create_gap_specialist():
    """Create and deploy gap trading specialist"""
    
    gap_code = '''#!/usr/bin/env python3
"""
🕳️ GAP SPECIALIST - LIVE TRADING
Hunts for gaps and trades them aggressively
"""

import json
import subprocess
import time
from datetime import datetime

print("🕳️ GAP SPECIALIST ACTIVATED")
print("Mission: Hunt and trade market gaps")
print("-" * 40)

def detect_and_trade_gap(coin):
    """Detect gaps and execute trades"""
    script = f"""
import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    ticker = client.get_product('{coin}-USD')
    current = float(ticker.get("price", 0))
    
    stats = client.get_product_stats('{coin}-USD')
    open_24h = float(stats.get("open", current))
    high_24h = float(stats.get("high", current))
    low_24h = float(stats.get("low", current))
    
    gap_pct = ((current - open_24h) / open_24h) * 100
    
    # Gap detection logic
    if abs(gap_pct) > 2:  # 2% gap threshold
        if current > high_24h:
            # Breakout gap - fade it
            order = client.market_order_sell(
                client_order_id=f"gap_fade_{{int(time.time()*1000)}}",
                product_id="{coin}-USD",
                quote_size="50"  # Start small
            )
            print(f"GAP_FADE:{coin}:{{gap_pct:.2f}}%:SELL")
        elif current < low_24h:
            # Breakdown gap - buy the dip
            order = client.market_order_buy(
                client_order_id=f"gap_buy_{{int(time.time()*1000)}}",
                product_id="{coin}-USD",
                quote_size="75"
            )
            print(f"GAP_BUY:{coin}:{{gap_pct:.2f}}%:BUY")
        else:
            print(f"GAP_RANGE:{coin}:{{gap_pct:.2f}}%")
    else:
        print(f"NO_GAP:{coin}:{{gap_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{{e}}")
"""
    
    try:
        with open(f"/tmp/gap_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        
        result = subprocess.run(["timeout", "3", "python3", f.name],
                              capture_output=True, text=True)
        subprocess.run(["rm", f.name], capture_output=True)
        
        if result.stdout:
            return result.stdout.strip()
    except:
        pass
    return None

# Main loop
coins = ["BTC", "ETH", "SOL", "AVAX", "MATIC"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = detect_and_trade_gap(coin)
        if result and "GAP_" in result:
            print(f"[{timestamp}] {result}")
            
    if cycle % 10 == 0:
        print(f"[{timestamp}] Gap Specialist: Cycle {cycle} complete")
        
    time.sleep(60)  # Check every minute
'''
    
    with open("/home/dereadi/scripts/claude/gap_specialist.py", "w") as f:
        f.write(gap_code)
    
    os.chmod("/home/dereadi/scripts/claude/gap_specialist.py", 0o755)
    return "/home/dereadi/scripts/claude/gap_specialist.py"

def create_trend_specialist():
    """Create trend following specialist"""
    
    trend_code = '''#!/usr/bin/env python3
"""
📈 TREND SPECIALIST - LIVE TRADING
Rides strong trends with momentum
"""

import json
import subprocess
import time
from datetime import datetime
import numpy as np

print("📈 TREND SPECIALIST ACTIVATED")
print("Mission: Ride strong directional trends")
print("-" * 40)

def calculate_trend_and_trade(coin):
    """Calculate trend strength and trade accordingly"""
    script = f"""
import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    stats = client.get_product_stats('{coin}-USD')
    current = float(stats.get("last", 0))
    open_24h = float(stats.get("open", current))
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    
    # Calculate trend metrics
    trend_pct = ((current - open_24h) / open_24h) * 100
    position_in_range = (current - low) / (high - low) if high != low else 0.5
    
    # Strong trend detection
    if trend_pct > 3 and position_in_range > 0.7:
        # Strong uptrend - buy
        order = client.market_order_buy(
            client_order_id=f"trend_buy_{{int(time.time()*1000)}}",
            product_id="{coin}-USD",
            quote_size="100"
        )
        print(f"TREND_BUY:{coin}:+{{trend_pct:.2f}}%")
    elif trend_pct < -3 and position_in_range < 0.3:
        # Strong downtrend - sell if we have position
        accounts = client.get_accounts()["accounts"]
        for a in accounts:
            if a["currency"] == "{coin}":
                balance = float(a["available_balance"]["value"])
                if balance > 0.001:
                    order = client.market_order_sell(
                        client_order_id=f"trend_sell_{{int(time.time()*1000)}}",
                        product_id="{coin}-USD",
                        base_size=str(balance * 0.1)
                    )
                    print(f"TREND_SELL:{coin}:{{trend_pct:.2f}}%")
                break
    else:
        print(f"TREND_NEUTRAL:{coin}:{{trend_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{{e}}")
"""
    
    try:
        with open(f"/tmp/trend_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        
        result = subprocess.run(["timeout", "3", "python3", f.name],
                              capture_output=True, text=True)
        subprocess.run(["rm", f.name], capture_output=True)
        
        if result.stdout:
            return result.stdout.strip()
    except:
        pass
    return None

# Main loop
coins = ["BTC", "ETH", "SOL", "LINK", "UNI"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = calculate_trend_and_trade(coin)
        if result and "TREND_" in result and "NEUTRAL" not in result:
            print(f"[{timestamp}] {result}")
            
    if cycle % 10 == 0:
        print(f"[{timestamp}] Trend Specialist: Cycle {cycle} complete")
        
    time.sleep(90)  # Check every 1.5 minutes
'''
    
    with open("/home/dereadi/scripts/claude/trend_specialist.py", "w") as f:
        f.write(trend_code)
    
    os.chmod("/home/dereadi/scripts/claude/trend_specialist.py", 0o755)
    return "/home/dereadi/scripts/claude/trend_specialist.py"

def create_volatility_specialist():
    """Create volatility harvesting specialist"""
    
    vol_code = '''#!/usr/bin/env python3
"""
⚡ VOLATILITY SPECIALIST - LIVE TRADING
Harvests volatility premiums and extreme moves
"""

import json
import subprocess
import time
from datetime import datetime

print("⚡ VOLATILITY SPECIALIST ACTIVATED")
print("Mission: Harvest volatility premiums")
print("-" * 40)

def trade_volatility(coin):
    """Trade based on volatility conditions"""
    script = f"""
import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    stats = client.get_product_stats('{coin}-USD')
    current = float(stats.get("last", 0))
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    
    volatility = ((high - low) / current) * 100
    position = (current - low) / (high - low) if high != low else 0.5
    
    # Extreme volatility trading
    if volatility > 5:  # 5% daily range
        if position > 0.85:
            # Extreme overbought in high vol
            order = client.market_order_sell(
                client_order_id=f"vol_sell_{{int(time.time()*1000)}}",
                product_id="{coin}-USD",
                quote_size="150"
            )
            print(f"VOL_SELL:{coin}:{{volatility:.2f}}%:POS={{position:.2f}}")
        elif position < 0.15:
            # Extreme oversold in high vol
            order = client.market_order_buy(
                client_order_id=f"vol_buy_{{int(time.time()*1000)}}",
                product_id="{coin}-USD",
                quote_size="150"
            )
            print(f"VOL_BUY:{coin}:{{volatility:.2f}}%:POS={{position:.2f}}")
        else:
            print(f"VOL_WAIT:{coin}:{{volatility:.2f}}%")
    else:
        print(f"LOW_VOL:{coin}:{{volatility:.2f}}%")
except Exception as e:
    print(f"ERROR:{{e}}")
"""
    
    try:
        with open(f"/tmp/vol_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        
        result = subprocess.run(["timeout", "3", "python3", f.name],
                              capture_output=True, text=True)
        subprocess.run(["rm", f.name], capture_output=True)
        
        if result.stdout:
            return result.stdout.strip()
    except:
        pass
    return None

# Main loop
coins = ["BTC", "ETH", "SOL", "AVAX", "ATOM"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = trade_volatility(coin)
        if result and "VOL_" in result and "LOW_VOL" not in result:
            print(f"[{timestamp}] {result}")
            
    if cycle % 10 == 0:
        print(f"[{timestamp}] Volatility Specialist: Cycle {cycle} complete")
        
    time.sleep(45)  # Check every 45 seconds for volatility
'''
    
    with open("/home/dereadi/scripts/claude/volatility_specialist.py", "w") as f:
        f.write(vol_code)
    
    os.chmod("/home/dereadi/scripts/claude/volatility_specialist.py", 0o755)
    return "/home/dereadi/scripts/claude/volatility_specialist.py"

def create_breakout_specialist():
    """Create breakout trading specialist"""
    
    breakout_code = '''#!/usr/bin/env python3
"""
🚀 BREAKOUT SPECIALIST - LIVE TRADING
Catches explosive breakout moves
"""

import json
import subprocess
import time
from datetime import datetime

print("🚀 BREAKOUT SPECIALIST ACTIVATED")
print("Mission: Catch explosive breakouts")
print("-" * 40)

def detect_breakout(coin):
    """Detect and trade breakouts"""
    script = f"""
import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    ticker = client.get_product('{coin}-USD')
    current = float(ticker.get("price", 0))
    
    stats = client.get_product_stats('{coin}-USD')
    high_24h = float(stats.get("high", current))
    low_24h = float(stats.get("low", current))
    volume = float(stats.get("volume", 0))
    volume_30d = float(stats.get("volume_30day", volume)) / 30
    
    # Volume surge detection
    volume_surge = volume / max(volume_30d, 1)
    
    # Breakout detection
    if current > high_24h * 1.01 and volume_surge > 1.5:
        # Upward breakout with volume
        order = client.market_order_buy(
            client_order_id=f"breakout_buy_{{int(time.time()*1000)}}",
            product_id="{coin}-USD",
            quote_size="200"
        )
        print(f"BREAKOUT_UP:{coin}:VOL_SURGE={{volume_surge:.2f}}x")
    elif current < low_24h * 0.99 and volume_surge > 1.5:
        # Downward breakout - avoid or short
        print(f"BREAKOUT_DOWN:{coin}:VOL_SURGE={{volume_surge:.2f}}x")
    else:
        range_pct = ((high_24h - low_24h) / current) * 100
        if range_pct < 2:
            print(f"CONSOLIDATING:{coin}:RANGE={{range_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{{e}}")
"""
    
    try:
        with open(f"/tmp/breakout_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        
        result = subprocess.run(["timeout", "3", "python3", f.name],
                              capture_output=True, text=True)
        subprocess.run(["rm", f.name], capture_output=True)
        
        if result.stdout:
            return result.stdout.strip()
    except:
        pass
    return None

# Main loop
coins = ["BTC", "ETH", "SOL", "DOGE", "SHIB"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = detect_breakout(coin)
        if result and "BREAKOUT_" in result:
            print(f"[{timestamp}] {result}")
            
    if cycle % 10 == 0:
        print(f"[{timestamp}] Breakout Specialist: Cycle {cycle} complete")
        
    time.sleep(120)  # Check every 2 minutes
'''
    
    with open("/home/dereadi/scripts/claude/breakout_specialist.py", "w") as f:
        f.write(breakout_code)
    
    os.chmod("/home/dereadi/scripts/claude/breakout_specialist.py", 0o755)
    return "/home/dereadi/scripts/claude/breakout_specialist.py"

def create_mean_reversion_specialist():
    """Create mean reversion specialist"""
    
    reversion_code = '''#!/usr/bin/env python3
"""
🎯 MEAN REVERSION SPECIALIST - LIVE TRADING
Trades extremes back to mean
"""

import json
import subprocess
import time
from datetime import datetime
import numpy as np

print("🎯 MEAN REVERSION SPECIALIST ACTIVATED")
print("Mission: Trade extremes back to mean")
print("-" * 40)

def calculate_deviation(coin):
    """Calculate deviation from mean and trade"""
    script = f"""
import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    stats = client.get_product_stats('{coin}-USD')
    current = float(stats.get("last", 0))
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    open_24h = float(stats.get("open", current))
    
    # Calculate mean and deviation
    mean = (high + low + open_24h) / 3
    deviation_pct = ((current - mean) / mean) * 100
    
    # Mean reversion trades
    if deviation_pct > 3:  # 3% above mean
        # Sell - expect reversion down
        order = client.market_order_sell(
            client_order_id=f"revert_sell_{{int(time.time()*1000)}}",
            product_id="{coin}-USD",
            quote_size="100"
        )
        print(f"REVERT_SELL:{coin}:DEV=+{{deviation_pct:.2f}}%")
    elif deviation_pct < -3:  # 3% below mean
        # Buy - expect reversion up
        order = client.market_order_buy(
            client_order_id=f"revert_buy_{{int(time.time()*1000)}}",
            product_id="{coin}-USD",
            quote_size="100"
        )
        print(f"REVERT_BUY:{coin}:DEV={{deviation_pct:.2f}}%")
    else:
        print(f"NEAR_MEAN:{coin}:DEV={{deviation_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{{e}}")
"""
    
    try:
        with open(f"/tmp/revert_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        
        result = subprocess.run(["timeout", "3", "python3", f.name],
                              capture_output=True, text=True)
        subprocess.run(["rm", f.name], capture_output=True)
        
        if result.stdout:
            return result.stdout.strip()
    except:
        pass
    return None

# Main loop
coins = ["BTC", "ETH", "SOL", "MATIC", "DOT"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = calculate_deviation(coin)
        if result and "REVERT_" in result:
            print(f"[{timestamp}] {result}")
            
    if cycle % 10 == 0:
        print(f"[{timestamp}] Mean Reversion Specialist: Cycle {cycle} complete")
        
    time.sleep(60)  # Check every minute
'''
    
    with open("/home/dereadi/scripts/claude/mean_reversion_specialist.py", "w") as f:
        f.write(reversion_code)
    
    os.chmod("/home/dereadi/scripts/claude/mean_reversion_specialist.py", 0o755)
    return "/home/dereadi/scripts/claude/mean_reversion_specialist.py"

# Create all specialists
print("🔧 CREATING SPECIALIST ARMY...")
print("=" * 60)

specialists = []

print("\n1. Creating Gap Specialist...")
gap_path = create_gap_specialist()
specialists.append(("Gap Specialist", gap_path))
print(f"   ✅ Created: {gap_path}")

print("\n2. Creating Trend Specialist...")
trend_path = create_trend_specialist()
specialists.append(("Trend Specialist", trend_path))
print(f"   ✅ Created: {trend_path}")

print("\n3. Creating Volatility Specialist...")
vol_path = create_volatility_specialist()
specialists.append(("Volatility Specialist", vol_path))
print(f"   ✅ Created: {vol_path}")

print("\n4. Creating Breakout Specialist...")
breakout_path = create_breakout_specialist()
specialists.append(("Breakout Specialist", breakout_path))
print(f"   ✅ Created: {breakout_path}")

print("\n5. Creating Mean Reversion Specialist...")
reversion_path = create_mean_reversion_specialist()
specialists.append(("Mean Reversion Specialist", reversion_path))
print(f"   ✅ Created: {reversion_path}")

# Deploy all specialists
print("\n" + "=" * 60)
print("🚀 DEPLOYING SPECIALIST ARMY")
print("=" * 60)

deployment_status = []

for name, path in specialists:
    print(f"\n🚀 Deploying {name}...")
    
    # Launch with nohup
    result = subprocess.run(
        f"nohup python3 {path} > {path.replace('.py', '.log')} 2>&1 & echo $!",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        pid = result.stdout.strip()
        deployment_status.append({
            "name": name,
            "path": path,
            "pid": pid,
            "status": "DEPLOYED"
        })
        print(f"   ✅ DEPLOYED! PID: {pid}")
    else:
        deployment_status.append({
            "name": name,
            "path": path,
            "pid": None,
            "status": "FAILED"
        })
        print(f"   ❌ Deployment failed")

# Save deployment status
deployment_report = {
    "timestamp": datetime.now().isoformat(),
    "specialists_deployed": len([s for s in deployment_status if s["status"] == "DEPLOYED"]),
    "deployment_details": deployment_status
}

with open("specialist_deployment.json", "w") as f:
    json.dump(deployment_report, f, indent=2)

print("\n" + "=" * 60)
print("📊 DEPLOYMENT SUMMARY")
print("=" * 60)

print(f"\n✅ Successfully Deployed: {deployment_report['specialists_deployed']}/5 specialists")
print("\nActive Specialists:")

for spec in deployment_status:
    if spec["status"] == "DEPLOYED":
        print(f"  • {spec['name']}: PID {spec['pid']}")
        print(f"    Log: {spec['path'].replace('.py', '.log')}")

print("\n💾 Deployment report saved to specialist_deployment.json")

print("\n" + "=" * 60)
print("🎖️ SPECIALIST ARMY DEPLOYED!")
print("=" * 60)

print("""
The Specialist Army is now hunting:

🕳️ GAP SPECIALIST: Trading market gaps
📈 TREND SPECIALIST: Riding strong trends  
⚡ VOLATILITY SPECIALIST: Harvesting vol premiums
🚀 BREAKOUT SPECIALIST: Catching explosions
🎯 MEAN REVERSION: Trading extremes

Each specialist operates independently,
hunting for their specific opportunity.

🔥 "Five specialists, five missions,
    One goal: Victory!" 
    
   The army marches to profit!
   
   Mitakuye Oyasin
""")