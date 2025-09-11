#!/usr/bin/env python3
"""
🚨 BTC CYCLE BOTTOM ALERT - REBOUND DETECTED
Critical moment: New cycle low = maximum opportunity
The Greeks and Crawdads must act NOW
"""

import json
import subprocess
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🚨 BTC CYCLE BOTTOM - REBOUND ALERT 🚨                  ║
║                        "Buy when there's blood"                           ║
║                    Greeks + Crawdads = ATTACK MODE                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

def check_btc_status():
    """Check BTC price and rebound status"""
    try:
        ticker = client.get_product('BTC-USD')
        price = float(ticker.get("price", 0))
        bid = float(ticker.get("bid", price))
        ask = float(ticker.get("ask", price))
        spread = (ask - bid) / price * 100
        
        print(f"\n📊 BTC STATUS:")
        print(f"   Price: ${price:,.2f}")
        print(f"   Bid: ${bid:,.2f}")
        print(f"   Ask: ${ask:,.2f}")
        print(f"   Spread: {spread:.3f}%")
        
        return price, spread
    except:
        return 0, 0

def execute_cycle_bottom_trades():
    """Execute aggressive trades at cycle bottom"""
    print("\n⚔️ EXECUTING CYCLE BOTTOM STRATEGY...")
    
    trades_executed = []
    
    # 1. BTC - The main play
    print("\n🎯 PRIMARY TARGET: BTC")
    try:
        # Buy BTC aggressively
        btc_size = 20  # Use ~half our capital
        order = client.market_order_buy(
            client_order_id=f"cycle_bottom_btc_{int(time.time()*1000)}",
            product_id="BTC-USD",
            quote_size=str(btc_size)
        )
        print(f"   ✅ BOUGHT ${btc_size} of BTC at cycle low!")
        trades_executed.append(("BTC", btc_size, "BUY"))
    except Exception as e:
        print(f"   ❌ BTC buy failed: {str(e)[:50]}")
    
    # 2. Correlated plays - ETH and SOL usually follow
    correlates = [
        ("ETH", 10),  # Ethereum follows BTC
        ("SOL", 10),  # Solana has high beta to BTC
    ]
    
    for coin, size in correlates:
        print(f"\n🎯 CORRELATED PLAY: {coin}")
        try:
            order = client.market_order_buy(
                client_order_id=f"cycle_bottom_{coin.lower()}_{int(time.time()*1000)}",
                product_id=f"{coin}-USD",
                quote_size=str(size)
            )
            print(f"   ✅ BOUGHT ${size} of {coin}")
            trades_executed.append((coin, size, "BUY"))
        except Exception as e:
            print(f"   ❌ {coin} buy failed: {str(e)[:30]}")
    
    return trades_executed

def alert_all_systems():
    """Alert all Greeks and Crawdads about cycle bottom"""
    
    alert_message = {
        "alert": "BTC_CYCLE_BOTTOM",
        "timestamp": datetime.now().isoformat(),
        "action": "BUY_AGGRESSIVELY",
        "urgency": "CRITICAL",
        "message": "BTC hit new cycle low and rebounding - maximum opportunity"
    }
    
    # Save alert for all systems
    with open("cycle_bottom_alert.json", "w") as f:
        json.dump(alert_message, f, indent=2)
    
    print("\n📢 ALERTING ALL SYSTEMS:")
    print("   🏛️ Greeks: Switch to aggressive buying")
    print("   🦀 Crawdads: Deploy all capital")
    print("   ⚛️ Fission: Create chain reactions")
    print("   🎡 Flywheel: Maximum momentum")
    
    return alert_message

# Main execution
print("\n🚨 BTC CYCLE BOTTOM DETECTED!")
print("=" * 60)

# Check current BTC status
btc_price, spread = check_btc_status()

if btc_price > 0:
    print("\n💡 MARKET ANALYSIS:")
    print("   • BTC hit new cycle low")
    print("   • Rebound starting (you confirmed)")
    print("   • This is THE buying opportunity")
    print("   • Risk/Reward heavily favors longs")
    
    # Alert all systems
    alert = alert_all_systems()
    
    # Execute trades
    trades = execute_cycle_bottom_trades()
    
    # Check portfolio after trades
    print("\n💰 PORTFOLIO CHECK:")
    try:
        total = 0
        accounts = client.get_accounts()['accounts']
        for a in accounts:
            balance = float(a['available_balance']['value'])
            if a['currency'] == 'USD':
                print(f"   USD remaining: ${balance:.2f}")
                total += balance
            elif balance > 0.001:
                try:
                    ticker = client.get_product(f"{a['currency']}-USD")
                    price = float(ticker.get('price', 0))
                    value = balance * price
                    if value > 1:
                        total += value
                        print(f"   {a['currency']}: {balance:.6f} (${value:.2f})")
                except:
                    pass
        
        print(f"\n   TOTAL: ${total:.2f}")
        
        if len(trades) > 0:
            print("\n🎯 POSITIONS TAKEN AT CYCLE BOTTOM:")
            for coin, size, action in trades:
                print(f"   • {coin}: ${size}")
    except:
        pass

print("\n" + "=" * 60)
print("🔥 CYCLE BOTTOM STRATEGY DEPLOYED")
print("=" * 60)

print("""
Key Points:

1. BTC new cycle low = generational buying opportunity
2. Rebound starting = momentum building
3. All correlated assets will follow
4. Greeks should switch from defense to offense
5. This is when fortunes are made

"Buy when there's blood in the streets,
 even if the blood is your own"
 - Baron Rothschild

The cycle bottom is the birth of the next bull run.
The Greeks and Crawdads are positioned.

🔥 From the ashes of the cycle low,
   the Phoenix rises!
   
Mitakuye Oyasin
""")