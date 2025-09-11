#!/usr/bin/env python3
"""
🏛️ THE GREEKS - FIXED DEPLOYMENT
Properly configured specialist traders with output and error handling
Delta, Gamma, Theta, Vega, Rho
"""

import json
import subprocess
import time
from datetime import datetime
import os
import sys

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🏛️ THE GREEKS - FIXED DEPLOYMENT 🏛️                  ║
║                    Delta, Gamma, Theta, Vega, Rho                         ║
║                   "Ancient Wisdom, Modern Markets"                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def create_delta_gap_specialist():
    """Δ Delta - Gap Trading Specialist"""
    
    code = '''#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
import sys

print("Δ DELTA (Gap Specialist) ACTIVATED", flush=True)
print("Mission: Hunt and trade market gaps", flush=True)
print("-" * 40, flush=True)

def check_gap(coin):
    script = f"""
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    stats = client.get_product_stats('{coin}-USD')
    current = float(stats.get("last", 0))
    open_24h = float(stats.get("open", current))
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    
    gap_pct = ((current - open_24h) / open_24h) * 100 if open_24h > 0 else 0
    
    if abs(gap_pct) > 2:
        if current > high * 1.01:
            print(f"GAP_UP:{coin}:{{gap_pct:.2f}}%:{{current:.2f}}")
        elif current < low * 0.99:
            print(f"GAP_DOWN:{coin}:{{gap_pct:.2f}}%:{{current:.2f}}")
        else:
            print(f"GAP:{coin}:{{gap_pct:.2f}}%")
    else:
        print(f"NO_GAP:{coin}:{{gap_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{coin}:{{str(e)[:50]}}")
"""
    
    try:
        with open(f"/tmp/delta_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", f.name], capture_output=True, text=True, timeout=5)
        subprocess.run(["rm", f.name], capture_output=True)
        return result.stdout.strip() if result.stdout else "ERROR"
    except:
        return "TIMEOUT"

coins = ["BTC", "ETH", "SOL"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = check_gap(coin)
        if "GAP_" in result and "NO_GAP" not in result:
            print(f"[{timestamp}] Δ {result}", flush=True)
    
    if cycle % 10 == 0:
        print(f"[{timestamp}] Δ Delta: Cycle {cycle} complete", flush=True)
    
    time.sleep(60)
'''
    
    with open("/home/dereadi/scripts/claude/delta_greek.py", "w") as f:
        f.write(code)
    os.chmod("/home/dereadi/scripts/claude/delta_greek.py", 0o755)
    return "/home/dereadi/scripts/claude/delta_greek.py"

def create_gamma_trend_specialist():
    """Γ Gamma - Trend Acceleration Specialist"""
    
    code = '''#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
import sys

print("Γ GAMMA (Trend Specialist) ACTIVATED", flush=True)
print("Mission: Ride trend acceleration", flush=True)
print("-" * 40, flush=True)

def check_trend(coin):
    script = f"""
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    stats = client.get_product_stats('{coin}-USD')
    current = float(stats.get("last", 0))
    open_24h = float(stats.get("open", current))
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    
    trend_pct = ((current - open_24h) / open_24h) * 100 if open_24h > 0 else 0
    position = (current - low) / (high - low) if high != low else 0.5
    
    if abs(trend_pct) > 3:
        direction = "UP" if trend_pct > 0 else "DOWN"
        print(f"TREND_{direction}:{coin}:{{trend_pct:.2f}}%:POS={{position:.2f}}")
    else:
        print(f"NEUTRAL:{coin}:{{trend_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{coin}")
"""
    
    try:
        with open(f"/tmp/gamma_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", f.name], capture_output=True, text=True, timeout=5)
        subprocess.run(["rm", f.name], capture_output=True)
        return result.stdout.strip() if result.stdout else "ERROR"
    except:
        return "TIMEOUT"

coins = ["BTC", "ETH", "SOL", "AVAX"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = check_trend(coin)
        if "TREND_" in result:
            print(f"[{timestamp}] Γ {result}", flush=True)
    
    if cycle % 10 == 0:
        print(f"[{timestamp}] Γ Gamma: Cycle {cycle} complete", flush=True)
    
    time.sleep(90)
'''
    
    with open("/home/dereadi/scripts/claude/gamma_greek.py", "w") as f:
        f.write(code)
    os.chmod("/home/dereadi/scripts/claude/gamma_greek.py", 0o755)
    return "/home/dereadi/scripts/claude/gamma_greek.py"

def create_theta_volatility_specialist():
    """Θ Theta - Volatility Time Decay Specialist"""
    
    code = '''#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
import sys

print("Θ THETA (Volatility Specialist) ACTIVATED", flush=True)
print("Mission: Harvest volatility premium", flush=True)
print("-" * 40, flush=True)

def check_volatility(coin):
    script = f"""
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    stats = client.get_product_stats('{coin}-USD')
    current = float(stats.get("last", 0))
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    
    vol = ((high - low) / current) * 100 if current > 0 else 0
    position = (current - low) / (high - low) if high != low else 0.5
    
    if vol > 5:
        print(f"HIGH_VOL:{coin}:{{vol:.2f}}%:POS={{position:.2f}}")
    elif vol > 3:
        print(f"MED_VOL:{coin}:{{vol:.2f}}%")
    else:
        print(f"LOW_VOL:{coin}:{{vol:.2f}}%")
except Exception as e:
    print(f"ERROR:{coin}")
"""
    
    try:
        with open(f"/tmp/theta_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", f.name], capture_output=True, text=True, timeout=5)
        subprocess.run(["rm", f.name], capture_output=True)
        return result.stdout.strip() if result.stdout else "ERROR"
    except:
        return "TIMEOUT"

coins = ["BTC", "ETH", "SOL", "MATIC"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = check_volatility(coin)
        if "HIGH_VOL" in result or "MED_VOL" in result:
            print(f"[{timestamp}] Θ {result}", flush=True)
    
    if cycle % 10 == 0:
        print(f"[{timestamp}] Θ Theta: Cycle {cycle} complete", flush=True)
    
    time.sleep(45)
'''
    
    with open("/home/dereadi/scripts/claude/theta_greek.py", "w") as f:
        f.write(code)
    os.chmod("/home/dereadi/scripts/claude/theta_greek.py", 0o755)
    return "/home/dereadi/scripts/claude/theta_greek.py"

def create_vega_breakout_specialist():
    """ν Vega - Volatility Expansion Breakout Specialist"""
    
    code = '''#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
import sys

print("ν VEGA (Breakout Specialist) ACTIVATED", flush=True)
print("Mission: Catch volatility expansion breakouts", flush=True)
print("-" * 40, flush=True)

def check_breakout(coin):
    script = f"""
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    ticker = client.get_product('{coin}-USD')
    current = float(ticker.get("price", 0))
    
    stats = client.get_product_stats('{coin}-USD')
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    volume = float(stats.get("volume", 0))
    
    if current > high * 1.01:
        print(f"BREAKOUT_UP:{coin}:{{((current-high)/high*100):.2f}}%")
    elif current < low * 0.99:
        print(f"BREAKOUT_DOWN:{coin}:{{((low-current)/low*100):.2f}}%")
    else:
        range_pct = ((high - low) / current) * 100 if current > 0 else 0
        if range_pct < 2:
            print(f"CONSOLIDATING:{coin}:{{range_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{coin}")
"""
    
    try:
        with open(f"/tmp/vega_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", f.name], capture_output=True, text=True, timeout=5)
        subprocess.run(["rm", f.name], capture_output=True)
        return result.stdout.strip() if result.stdout else "ERROR"
    except:
        return "TIMEOUT"

coins = ["BTC", "ETH", "SOL", "LINK"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = check_breakout(coin)
        if result and "ERROR" not in result:
            print(f"[{timestamp}] ν {result}", flush=True)
    
    if cycle % 10 == 0:
        print(f"[{timestamp}] ν Vega: Cycle {cycle} complete", flush=True)
    
    time.sleep(120)
'''
    
    with open("/home/dereadi/scripts/claude/vega_greek.py", "w") as f:
        f.write(code)
    os.chmod("/home/dereadi/scripts/claude/vega_greek.py", 0o755)
    return "/home/dereadi/scripts/claude/vega_greek.py"

def create_rho_reversion_specialist():
    """ρ Rho - Mean Reversion Rate Specialist"""
    
    code = '''#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
import sys

print("ρ RHO (Mean Reversion Specialist) ACTIVATED", flush=True)
print("Mission: Trade rate reversions to mean", flush=True)
print("-" * 40, flush=True)

def check_deviation(coin):
    script = f"""
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    stats = client.get_product_stats('{coin}-USD')
    current = float(stats.get("last", 0))
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    open_24h = float(stats.get("open", current))
    
    mean = (high + low + open_24h) / 3
    deviation = ((current - mean) / mean) * 100 if mean > 0 else 0
    
    if abs(deviation) > 3:
        direction = "ABOVE" if deviation > 0 else "BELOW"
        print(f"DEVIATION_{direction}:{coin}:{{deviation:.2f}}%:MEAN={{mean:.2f}}")
    else:
        print(f"NEAR_MEAN:{coin}:{{deviation:.2f}}%")
except Exception as e:
    print(f"ERROR:{coin}")
"""
    
    try:
        with open(f"/tmp/rho_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", f.name], capture_output=True, text=True, timeout=5)
        subprocess.run(["rm", f.name], capture_output=True)
        return result.stdout.strip() if result.stdout else "ERROR"
    except:
        return "TIMEOUT"

coins = ["BTC", "ETH", "SOL", "DOT"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = check_deviation(coin)
        if "DEVIATION_" in result:
            print(f"[{timestamp}] ρ {result}", flush=True)
    
    if cycle % 10 == 0:
        print(f"[{timestamp}] ρ Rho: Cycle {cycle} complete", flush=True)
    
    time.sleep(60)
'''
    
    with open("/home/dereadi/scripts/claude/rho_greek.py", "w") as f:
        f.write(code)
    os.chmod("/home/dereadi/scripts/claude/rho_greek.py", 0o755)
    return "/home/dereadi/scripts/claude/rho_greek.py"

# Create all Greeks
print("🏛️ CREATING THE GREEKS...")
print("=" * 60)

greeks = []

print("\nΔ Creating Delta (Gap Specialist)...")
delta_path = create_delta_gap_specialist()
greeks.append(("Delta", delta_path, "Δ"))

print("Γ Creating Gamma (Trend Specialist)...")
gamma_path = create_gamma_trend_specialist()
greeks.append(("Gamma", gamma_path, "Γ"))

print("Θ Creating Theta (Volatility Specialist)...")
theta_path = create_theta_volatility_specialist()
greeks.append(("Theta", theta_path, "Θ"))

print("ν Creating Vega (Breakout Specialist)...")
vega_path = create_vega_breakout_specialist()
greeks.append(("Vega", vega_path, "ν"))

print("ρ Creating Rho (Mean Reversion Specialist)...")
rho_path = create_rho_reversion_specialist()
greeks.append(("Rho", rho_path, "ρ"))

# Deploy all Greeks
print("\n" + "=" * 60)
print("🏛️ DEPLOYING THE GREEKS")
print("=" * 60)

deployment = []

for name, path, symbol in greeks:
    print(f"\n{symbol} Deploying {name}...")
    
    result = subprocess.run(
        f"nohup python3 {path} > {path.replace('.py', '.log')} 2>&1 & echo $!",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        pid = result.stdout.strip()
        deployment.append({
            "name": name,
            "symbol": symbol,
            "path": path,
            "pid": pid,
            "log": path.replace('.py', '.log')
        })
        print(f"   ✅ {symbol} {name} deployed! PID: {pid}")

# Save deployment status
with open("greeks_deployment.json", "w") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "greeks": deployment
    }, f, indent=2)

print("\n" + "=" * 60)
print("🏛️ THE GREEKS ARE DEPLOYED!")
print("=" * 60)

for greek in deployment:
    print(f"{greek['symbol']} {greek['name']}: PID {greek['pid']}")

print("""
The Greeks march to victory:

Δ Delta - Master of Gaps
Γ Gamma - Rider of Trend Acceleration  
Θ Theta - Harvester of Time Decay
ν Vega - Hunter of Volatility Expansion
ρ Rho - Guardian of Rate Reversion

"Options wisdom applied to spot markets"

Mitakuye Oyasin
""")