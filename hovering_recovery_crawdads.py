#!/usr/bin/env python3
"""
🦀 HOVERING RECOVERY - CRAWDADS IN VIRTUAL ENV! 🦀
Market recovered and hovering - perfect for crawdads!
Thunder, Mountain, Fire, and others ready to feed!
Using quantum_crawdad_env virtual environment
"""

import json
import subprocess
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🦀 CRAWDAD SWARM STATUS CHECK! 🦀                       ║
║                   Market Hovering - Perfect for Feeding!                   ║
║                Thunder, Mountain, Fire, Wind, Earth, River, Spirit!        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - HOVERING RECOVERY")
print("=" * 70)

# Check crawdad virtual environment
print("\n🦀 CHECKING QUANTUM CRAWDAD ENVIRONMENT:")
print("-" * 50)

# Check if crawdads are running
crawdad_check = subprocess.run(['pgrep', '-f', 'quantum_crawdad'], 
                              capture_output=True, text=True)
if crawdad_check.stdout:
    pids = crawdad_check.stdout.strip().split('\n')
    print(f"✅ {len(pids)} Crawdad processes active!")
    print(f"   PIDs: {', '.join(pids)}")
else:
    print("⚠️ No crawdads currently running")

# Check crawdad log
print("\n📊 CRAWDAD TRADING LOG:")
print("-" * 50)
try:
    with open('quantum_crawdad_live_trader.log', 'r') as f:
        lines = f.readlines()
        # Get last 20 lines for recent activity
        recent = lines[-20:] if len(lines) > 20 else lines
        
        # Look for market prices and crawdad actions
        for line in recent:
            if 'BTC:' in line or 'Crawdad Actions' in line or 'CYCLE' in line:
                print(line.strip())
                
except Exception as e:
    print(f"Could not read log: {e}")

# Launch crawdad analysis in virtual env
print("\n🦀 CRAWDAD SWARM ANALYSIS:")
print("-" * 50)

crawdad_script = """
#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Get market status
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print(f"BTC: ${btc_price:,.2f} - HOVERING")
print(f"ETH: ${eth_price:,.2f}")
print(f"SOL: ${sol_price:,.2f}")

# Calculate hovering metrics
volatility = abs(btc_price - 112200) / 112200 * 100
print(f"\\nHovering Volatility: {volatility:.2f}%")

if volatility < 0.5:
    print("✅ PERFECT HOVERING - Crawdads can feed!")
elif volatility < 1.0:
    print("⚠️ MILD HOVERING - Crawdads cautious")
else:
    print("🚨 TOO VOLATILE - Crawdads waiting")

# Check USD balance
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"\\nUSD Available: ${usd_balance:.2f}")
if usd_balance < 20:
    print("  → Need more USD for crawdads to trade effectively")
else:
    print("  → Crawdads have ammunition!")

# Crawdad personalities
print("\\n🦀 CRAWDAD PERSONALITIES:")
print("  Thunder: Aggressive on dips (needs $50+ USD)")
print("  Mountain: Steady accumulator (needs $30+ USD)")  
print("  Fire: Quick scalper (needs $20+ USD)")
print("  Wind: Momentum rider (needs $25+ USD)")
print("  Earth: Support buyer (needs $40+ USD)")
print("  River: Flow trader (needs $35+ USD)")
print("  Spirit: Intuitive trader (needs $45+ USD)")

print(f"\\n  Current funding allows: {'None - need more USD!' if usd_balance < 20 else 'Fire only' if usd_balance < 25 else 'Fire & Wind' if usd_balance < 30 else 'Multiple crawdads'}")
"""

# Save and run the script
with open('check_hovering_crawdads.py', 'w') as f:
    f.write(crawdad_script)

# Execute with proper virtual env
print("\nRunning crawdad analysis...")
result = subprocess.run(['./quantum_crawdad_env/bin/python3', 'check_hovering_crawdads.py'],
                       capture_output=True, text=True, timeout=10)

if result.stdout:
    print(result.stdout)
if result.stderr:
    print(f"Error: {result.stderr}")

# Check for feeding opportunity
print("\n🎯 HOVERING STRATEGY:")
print("-" * 50)
print("Market recovered from shakeout and hovering!")
print("This creates perfect conditions for:")
print("  1. Micro-scalping by Fire crawdad")
print("  2. Accumulation by Mountain crawdad")
print("  3. Momentum plays by Wind crawdad")
print("")
print("BUT we need more USD for crawdads to feed properly!")
print("Minimum $20 per crawdad for effective trading")

print(f"\n{'🦀' * 35}")
print("CRAWDADS READY IN VIRTUAL ENV!")
print("Market hovering - perfect for feeding!")
print("Thunder, Mountain, Fire awaiting funds!")
print("🦀" * 35)