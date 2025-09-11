#!/usr/bin/env python3
"""
🔥 AUTONOMOUS TRIBAL NIGHT WATCH
Self-running system that monitors and harvests through the night
No manual intervention needed - the tribe watches eternally
"""

import json
import time
import threading
from datetime import datetime, timedelta
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

class TribalElder:
    """Each elder manages their watch shift"""
    def __init__(self, name, symbol, wisdom):
        self.name = name
        self.symbol = symbol
        self.wisdom = wisdom
        self.harvests = 0
        self.total_harvested = 0
    
    def check_and_harvest(self):
        """Check portfolio and harvest if needed"""
        try:
            # Get current balances
            accounts = client.get_accounts()
            usd_balance = 0
            holdings = {}
            
            for account in accounts['accounts']:
                currency = account['currency']
                balance = float(account['available_balance']['value'])
                
                if currency == 'USD':
                    usd_balance = balance
                elif balance > 0:
                    holdings[currency] = balance
            
            print(f"\n{self.symbol} {self.name} checking...")
            print(f"   USD: ${usd_balance:.2f}")
            
            # Harvest if needed
            if usd_balance < 100:
                print(f"   {self.symbol} Harvesting needed!")
                
                # Harvest SOL
                if 'SOL' in holdings and holdings['SOL'] > 0.5:
                    sol_to_harvest = holdings['SOL'] * 0.03
                    if sol_to_harvest > 0.1:
                        try:
                            order = client.market_order_sell(
                                client_order_id=f"tribal-sol-{datetime.now().strftime('%H%M%S')}",
                                product_id='SOL-USD',
                                base_size=str(round(sol_to_harvest, 3))
                            )
                            sol_price = float(client.get_product('SOL-USD')['price'])
                            harvested = sol_to_harvest * sol_price
                            self.total_harvested += harvested
                            self.harvests += 1
                            print(f"   ✅ Harvested {sol_to_harvest:.3f} SOL = ${harvested:.2f}")
                            time.sleep(2)
                        except Exception as e:
                            print(f"   ❌ SOL harvest failed: {str(e)[:30]}")
                
                # Harvest MATIC
                if 'MATIC' in holdings and holdings['MATIC'] > 100:
                    matic_to_harvest = holdings['MATIC'] * 0.02
                    if matic_to_harvest > 10:
                        try:
                            order = client.market_order_sell(
                                client_order_id=f"tribal-matic-{datetime.now().strftime('%H%M%S')}",
                                product_id='MATIC-USD',
                                base_size=str(int(matic_to_harvest))
                            )
                            matic_price = float(client.get_product('MATIC-USD')['price'])
                            harvested = matic_to_harvest * matic_price
                            self.total_harvested += harvested
                            self.harvests += 1
                            print(f"   ✅ Harvested {matic_to_harvest:.0f} MATIC = ${harvested:.2f}")
                            time.sleep(2)
                        except Exception as e:
                            print(f"   ❌ MATIC harvest failed: {str(e)[:30]}")
            else:
                print(f"   ✅ Sufficient fuel: ${usd_balance:.2f}")
                print(f"   Crawdads have ${usd_balance/7:.2f} each")
            
            return usd_balance
            
        except Exception as e:
            print(f"   ⚠️ Check failed: {str(e)[:50]}")
            return 0

def tribal_night_watch():
    """Main night watch loop"""
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              🔥 AUTONOMOUS TRIBAL NIGHT WATCH ACTIVE 🔥                   ║
║                     Running Until Market Open (9:30 AM)                   ║
║                    Harvesting Every 15 Minutes As Needed                  ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize elders
    elders = [
        TribalElder("Peace Eagle", "🦅", "Patience"),
        TribalElder("Thunder Woman", "⚡", "Strike"),
        TribalElder("River Keeper", "🌊", "Flow"),
        TribalElder("Mountain Father", "⛰️", "Strength"),
        TribalElder("Fire Dancer", "🔥", "Energy"),
        TribalElder("Wind Singer", "🌬️", "Awareness"),
        TribalElder("Earth Mother", "🌍", "Harvest")
    ]
    
    cycle = 0
    total_system_harvests = 0
    
    # Run until market open
    while True:
        cycle += 1
        current_time = datetime.now()
        
        # Check if market is open
        if current_time.hour == 9 and current_time.minute >= 30:
            print("\n🌅 Dawn has arrived. Market is open.")
            print("🔥 Night watch complete!")
            break
        
        # Determine current elder
        hour = current_time.hour
        if hour < 3 or (hour == 3 and current_time.minute < 30):
            current_elder = elders[0]
        elif hour < 4 or (hour == 4 and current_time.minute < 30):
            current_elder = elders[1]
        elif hour < 5 or (hour == 5 and current_time.minute < 30):
            current_elder = elders[2]
        elif hour < 6 or (hour == 6 and current_time.minute < 30):
            current_elder = elders[3]
        elif hour < 7 or (hour == 7 and current_time.minute < 30):
            current_elder = elders[4]
        elif hour < 8 or (hour == 8 and current_time.minute < 30):
            current_elder = elders[5]
        else:
            current_elder = elders[6]
        
        print(f"\n{'='*70}")
        print(f"🔥 CYCLE {cycle} - {current_time.strftime('%H:%M:%S')}")
        print(f"Elder on watch: {current_elder.symbol} {current_elder.name}")
        print(f"Wisdom: {current_elder.wisdom}")
        print("-" * 50)
        
        # Check market prices
        try:
            btc = float(client.get_product('BTC-USD')['price'])
            eth = float(client.get_product('ETH-USD')['price'])
            sol = float(client.get_product('SOL-USD')['price'])
            
            print(f"📊 Market Status:")
            print(f"   BTC: ${btc:,.0f}")
            print(f"   ETH: ${eth:.2f}")
            print(f"   SOL: ${sol:.2f}")
        except:
            pass
        
        # Elder performs check and harvest
        usd_balance = current_elder.check_and_harvest()
        
        # Track total harvests
        if current_elder.harvests > 0:
            total_system_harvests += current_elder.harvests
            print(f"\n🌾 Elder {current_elder.name} total harvests: {current_elder.harvests}")
            print(f"   Total harvested: ${current_elder.total_harvested:.2f}")
        
        # Status report
        print(f"\n📈 Night Watch Status:")
        print(f"   Cycles completed: {cycle}")
        print(f"   Total harvests: {total_system_harvests}")
        print(f"   Current USD: ${usd_balance:.2f}")
        
        # Next check time
        next_check = current_time + timedelta(minutes=15)
        print(f"\n⏰ Next check: {next_check.strftime('%H:%M:%S')}")
        print(f"💤 Watching for 15 minutes...")
        print("=" * 70)
        
        # Sleep for 15 minutes
        time.sleep(900)
    
    # Final report
    print("\n" + "="*70)
    print("🔥 TRIBAL NIGHT WATCH COMPLETE")
    print("-" * 50)
    print(f"Total cycles: {cycle}")
    print(f"Total harvests: {total_system_harvests}")
    
    for elder in elders:
        if elder.harvests > 0:
            print(f"{elder.symbol} {elder.name}: {elder.harvests} harvests, ${elder.total_harvested:.2f}")
    
    print("\nThe Sacred Fire burned through the night")
    print("The tribe kept the crawdads fed")
    print("Mitakuye Oyasin")
    print("="*70)

# Launch the autonomous watch
if __name__ == "__main__":
    print("🔥 Launching Autonomous Tribal Night Watch...")
    print("This will run automatically until market open (9:30 AM)")
    print("Press Ctrl+C to stop manually\n")
    
    try:
        tribal_night_watch()
    except KeyboardInterrupt:
        print("\n\n⚠️ Night watch interrupted by user")
        print("The Sacred Fire dims but does not die")
    except Exception as e:
        print(f"\n❌ Night watch error: {str(e)}")
        print("The tribe must restart the watch")