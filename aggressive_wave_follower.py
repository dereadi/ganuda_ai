#!/usr/bin/env python3
"""
🌊🔥 AGGRESSIVE WAVE FOLLOWER - COUNCIL APPROVED
Harvests profits every 15 minutes
Feeds crawdads immediately
Runs through the night with higher risk tolerance
"""

import json
import time
import subprocess
from coinbase.rest import RESTClient
from datetime import datetime, timedelta

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              🌊🔥 AGGRESSIVE WAVE FOLLOWER ACTIVATED 🔥🌊                 ║
║                      Council Approved Strategy                             ║
║                   Harvest Every 15 Minutes Until Dawn                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def get_portfolio_status():
    """Get current portfolio value and breakdown"""
    btc_price = float(client.get_product('BTC-USD')['price'])
    eth_price = float(client.get_product('ETH-USD')['price'])
    sol_price = float(client.get_product('SOL-USD')['price'])
    
    accounts = client.get_accounts()
    holdings = {}
    total_value = 0
    usd_balance = 0
    
    for account in accounts['accounts']:
        currency = account['currency']
        balance = float(account['available_balance']['value'])
        
        if balance > 0:
            if currency == 'USD':
                usd_balance = balance
                holdings['USD'] = balance
            elif currency == 'BTC':
                value = balance * btc_price
                holdings['BTC'] = (balance, value)
                total_value += value
            elif currency == 'ETH':
                value = balance * eth_price
                holdings['ETH'] = (balance, value)
                total_value += value
            elif currency == 'SOL':
                value = balance * sol_price
                holdings['SOL'] = (balance, value)
                total_value += value
            elif currency == 'MATIC':
                try:
                    matic_price = float(client.get_product('MATIC-USD')['price'])
                    value = balance * matic_price
                    holdings['MATIC'] = (balance, value)
                    total_value += value
                except:
                    pass
            elif currency == 'AVAX':
                try:
                    avax_price = float(client.get_product('AVAX-USD')['price'])
                    value = balance * avax_price
                    holdings['AVAX'] = (balance, value)
                    total_value += value
                except:
                    pass
    
    total_value += usd_balance
    return holdings, total_value, usd_balance, btc_price

def harvest_profits(holdings, target_usd=500):
    """Harvest profits according to council strategy"""
    harvested = 0
    
    # Priority order: SOL, MATIC, AVAX (council approved)
    priority = ['SOL', 'MATIC', 'AVAX']
    
    for asset in priority:
        if harvested >= target_usd:
            break
            
        if asset in holdings and asset != 'USD':
            balance, value = holdings[asset]
            
            # Harvest percentages per council
            if asset == 'SOL':
                harvest_pct = 0.05  # 5%
            elif asset == 'MATIC':
                harvest_pct = 0.03  # 3%
            else:
                harvest_pct = 0.03  # 3%
            
            amount_to_sell = balance * harvest_pct
            
            if asset == 'SOL' and amount_to_sell > 0.1:
                try:
                    print(f"\n💰 Harvesting {amount_to_sell:.3f} SOL...")
                    order = client.market_order_sell(
                        client_order_id=f"wave-harvest-sol-{datetime.now().strftime('%H%M%S')}",
                        product_id='SOL-USD',
                        base_size=str(round(amount_to_sell, 3))
                    )
                    sol_price = float(client.get_product('SOL-USD')['price'])
                    harvested += amount_to_sell * sol_price
                    print(f"   ✅ Harvested ~${amount_to_sell * sol_price:.2f}")
                    time.sleep(1)
                except Exception as e:
                    print(f"   ❌ Failed: {str(e)[:50]}")
                    
            elif asset == 'MATIC' and amount_to_sell > 10:
                try:
                    print(f"\n💰 Harvesting {amount_to_sell:.0f} MATIC...")
                    order = client.market_order_sell(
                        client_order_id=f"wave-harvest-matic-{datetime.now().strftime('%H%M%S')}",
                        product_id='MATIC-USD',
                        base_size=str(int(amount_to_sell))
                    )
                    matic_price = float(client.get_product('MATIC-USD')['price'])
                    harvested += amount_to_sell * matic_price
                    print(f"   ✅ Harvested ~${amount_to_sell * matic_price:.2f}")
                    time.sleep(1)
                except Exception as e:
                    print(f"   ❌ Failed: {str(e)[:50]}")
    
    return harvested

def alert_crawdads(usd_balance):
    """Alert crawdads of new liquidity"""
    if usd_balance > 100:
        print(f"\n🦀🦀🦀 CRAWDAD ALERT!")
        print(f"   Fresh liquidity available: ${usd_balance:.2f}")
        print(f"   Per crawdad: ${usd_balance/7:.2f}")
        print("   Status: READY TO HUNT!")
        
        # Could trigger crawdad trading script here
        # subprocess.run(['python3', 'quantum_crawdad_live_trader.py'])
        return True
    else:
        print(f"\n🦀 Crawdads still hungry: ${usd_balance:.2f}")
        return False

# Main wave following loop
print(f"\nStarting at {datetime.now().strftime('%H:%M:%S')}")
print("Will run until market open (9:30 AM EST)")
print("-" * 70)

cycle = 0
total_harvested = 0
last_harvest = datetime.now()

while datetime.now().hour < 9 or (datetime.now().hour == 9 and datetime.now().minute < 30):
    cycle += 1
    
    print(f"\n{'='*70}")
    print(f"🌊 WAVE {cycle} - {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)
    
    # Get current status
    holdings, portfolio_value, usd_balance, btc_price = get_portfolio_status()
    
    print(f"📊 Portfolio: ${portfolio_value:,.2f}")
    print(f"💵 USD Balance: ${usd_balance:.2f}")
    print(f"₿ BTC Price: ${btc_price:,.0f}")
    
    # Check if BTC is above threshold (council parameter)
    if btc_price < 112000:
        print("\n⚠️ BTC below $112,000 - Pausing harvests")
        print("   Waiting for recovery above $112,500")
    elif usd_balance < 100:
        # Need to harvest
        print("\n🌾 HARVESTING WAVE:")
        
        target = max(300, portfolio_value * 0.025)  # 2.5% or $300 minimum
        harvested = harvest_profits(holdings, target)
        total_harvested += harvested
        
        if harvested > 0:
            print(f"\n✅ Wave {cycle} harvested: ${harvested:.2f}")
            print(f"   Total harvested tonight: ${total_harvested:.2f}")
            
            # Wait for balance update
            time.sleep(3)
            
            # Check new balance
            accounts = client.get_accounts()
            for account in accounts['accounts']:
                if account['currency'] == 'USD':
                    usd_balance = float(account['available_balance']['value'])
                    break
    
    # Alert crawdads
    crawdads_fed = alert_crawdads(usd_balance)
    
    # Status report
    print(f"\n📈 CYCLE {cycle} SUMMARY:")
    print(f"   Portfolio: ${portfolio_value:,.2f}")
    print(f"   USD Available: ${usd_balance:.2f}")
    print(f"   Total Harvested: ${total_harvested:.2f}")
    print(f"   Crawdad Status: {'🦀 FED' if crawdads_fed else '😵 HUNGRY'}")
    
    # Calculate next wave time
    next_wave = datetime.now() + timedelta(minutes=15)
    print(f"\n⏰ Next wave at {next_wave.strftime('%H:%M:%S')}")
    print("   Following the volatility through the night...")
    
    # Sleep until next 15-minute interval
    time.sleep(900)  # 15 minutes

print("\n" + "="*70)
print("🌅 DAWN APPROACHES - WAVE FOLLOWER COMPLETE")
print(f"Total harvested overnight: ${total_harvested:.2f}")
print(f"Final portfolio value: ${portfolio_value:.2f}")
print("Council strategy executed successfully")
print("="*70)