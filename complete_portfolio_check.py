#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 COMPLETE PORTFOLIO CHECK WITH DOGE
Flying Squirrel Tewa demands full accounting
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient
import psycopg2

class CompletePortfolioCheck:
    def __init__(self):
        # Load API config
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            self.config = json.load(f)
        
        self.client = RESTClient(
            api_key=self.config['name'].split('/')[-1],
            api_secret=self.config['privateKey']
        )
        
        print("🔥 COMPLETE PORTFOLIO ANALYSIS")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
    
    def get_all_balances(self):
        """Get all account balances including DOGE"""
        accounts = self.client.get_accounts()['accounts']
        balances = {}
        
        for account in accounts:
            currency = account['currency']
            balance = float(account['available_balance']['value'])
            if balance > 0.00001:  # Filter dust
                balances[currency] = balance
        
        return balances
    
    def get_current_prices(self):
        """Get current prices for all holdings"""
        # Key coins we care about
        symbols = ['BTC', 'ETH', 'SOL', 'DOGE', 'MATIC', 'AVAX', 'LINK', 'XRP', 'ADA', 'DOT']
        prices = {}
        
        for symbol in symbols:
            try:
                ticker = self.client.get_product(f"{symbol}-USD")
                prices[symbol] = float(ticker['price'])
            except:
                continue
        
        return prices
    
    def calculate_portfolio_value(self, balances, prices):
        """Calculate total portfolio value with breakdown"""
        portfolio = []
        total_value = 0
        
        # Add USD first
        usd_balance = balances.get('USD', 0)
        total_value += usd_balance
        
        # Calculate crypto values
        for coin, amount in balances.items():
            if coin == 'USD':
                continue
            
            if coin in prices:
                price = prices[coin]
                value = amount * price
                total_value += value
                
                portfolio.append({
                    'coin': coin,
                    'amount': amount,
                    'price': price,
                    'value': value,
                    'percentage': 0  # Will calculate after total
                })
        
        # Sort by value
        portfolio.sort(key=lambda x: x['value'], reverse=True)
        
        # Calculate percentages
        for item in portfolio:
            item['percentage'] = (item['value'] / total_value) * 100
        
        return portfolio, total_value, usd_balance
    
    def check_doge_blood_bag(self, doge_amount, doge_price):
        """Check DOGE blood bag status"""
        print("\n🩸 DOGE BLOOD BAG STATUS:")
        print("-" * 40)
        
        if doge_amount > 0:
            value = doge_amount * doge_price
            print(f"  Holdings: {doge_amount:.2f} DOGE")
            print(f"  Current Price: ${doge_price:.6f}")
            print(f"  Position Value: ${value:.2f}")
            
            # Blood bag zones
            feed_zone = 0.20
            bleed_zone = 0.22
            
            if doge_price < feed_zone:
                print(f"  🟢 FEED ZONE! Price below ${feed_zone}")
                print(f"  📍 Action: ACCUMULATE MORE")
            elif doge_price > bleed_zone:
                print(f"  🔴 BLEED ZONE! Price above ${bleed_zone}")
                print(f"  📍 Action: HARVEST PROFITS")
                bleed_amount = min(50, doge_amount * 0.3)
                potential_harvest = bleed_amount * doge_price
                fee = potential_harvest * 0.004
                net_harvest = potential_harvest - fee
                print(f"  💰 Potential harvest: {bleed_amount:.0f} DOGE = ${net_harvest:.2f} (after fees)")
            else:
                print(f"  🟡 NEUTRAL ZONE (${doge_price:.4f})")
                print(f"  📍 Wait for ${feed_zone} to feed or ${bleed_zone} to bleed")
                distance_to_bleed = bleed_zone - doge_price
                print(f"  📊 Distance to bleed: ${distance_to_bleed:.4f} ({(distance_to_bleed/doge_price)*100:.1f}% move needed)")
        else:
            print("  ❌ No DOGE position found!")
    
    def analyze_fee_impact(self, portfolio):
        """Analyze fee impact on each position"""
        print("\n💸 FEE-AWARE HARVEST ANALYSIS:")
        print("-" * 40)
        
        fee_rate = 0.004  # 0.4% each way
        round_trip = 0.008  # 0.8% total
        
        for item in portfolio:
            if item['value'] < 10:  # Skip dust
                continue
                
            # Calculate harvest potential
            harvest_10_percent = item['value'] * 0.10
            fee_to_sell = harvest_10_percent * fee_rate
            net_harvest = harvest_10_percent - fee_to_sell
            
            # Calculate price needed for 2% profit after fees
            breakeven_price = item['price'] * (1 + round_trip)
            profit_price = item['price'] * 1.02
            
            print(f"\n  {item['coin']}:")
            print(f"    Position: {item['amount']:.4f} @ ${item['price']:,.2f} = ${item['value']:.2f}")
            print(f"    10% Harvest: ${harvest_10_percent:.2f} - ${fee_to_sell:.2f} fee = ${net_harvest:.2f} net")
            print(f"    Breakeven: ${breakeven_price:,.2f} (+{round_trip*100:.1f}%)")
            print(f"    2% Profit Target: ${profit_price:,.2f}")
    
    def display_results(self):
        """Main execution and display"""
        # Get all data
        balances = self.get_all_balances()
        prices = self.get_current_prices()
        portfolio, total_value, usd_balance = self.calculate_portfolio_value(balances, prices)
        
        # Display overview
        print("\n📊 PORTFOLIO OVERVIEW:")
        print("-" * 40)
        print(f"  Total Value: ${total_value:,.2f}")
        print(f"  USD Balance: ${usd_balance:,.2f} ({(usd_balance/total_value)*100:.2f}%)")
        print(f"  Crypto Value: ${total_value - usd_balance:,.2f} ({((total_value-usd_balance)/total_value)*100:.2f}%)")
        
        # Starting reference
        starting_capital = 10000
        total_gain = total_value - starting_capital
        gain_percent = (total_gain / starting_capital) * 100
        print(f"\n  📈 Performance:")
        print(f"     Starting: $10,000")
        print(f"     Current: ${total_value:,.2f}")
        print(f"     Gain: ${total_gain:,.2f} ({gain_percent:.1f}%)")
        
        # Display positions
        print("\n🪙 POSITIONS BY VALUE:")
        print("-" * 40)
        
        for i, item in enumerate(portfolio, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🪙"
            print(f"  {emoji} {item['coin']}: ${item['value']:,.2f} ({item['percentage']:.1f}%)")
            print(f"      Amount: {item['amount']:.4f} @ ${item['price']:,.2f}")
        
        # Check DOGE specifically
        doge_balance = balances.get('DOGE', 0)
        doge_price = prices.get('DOGE', 0)
        self.check_doge_blood_bag(doge_balance, doge_price)
        
        # Fee analysis
        self.analyze_fee_impact(portfolio)
        
        # Liquidity status
        print("\n🚨 LIQUIDITY STATUS:")
        print("-" * 40)
        if usd_balance < 50:
            print(f"  ⚠️ CRITICAL: Only ${usd_balance:.2f} USD available!")
            print(f"  📍 Need to generate ${500 - usd_balance:.2f} more for safety")
        elif usd_balance < 500:
            print(f"  🟡 LOW: ${usd_balance:.2f} USD available")
            print(f"  📍 Consider generating ${500 - usd_balance:.2f} more")
        else:
            print(f"  ✅ HEALTHY: ${usd_balance:.2f} USD available")
        
        # Save to thermal memory
        self.save_to_thermal_memory(portfolio, total_value, usd_balance)
        
        print("\n" + "=" * 70)
        print("🔥 Cherokee Trading Council Portfolio Check Complete")
        print("🐿️ Flying Squirrel Tewa sees all from above")
        print("=" * 70)
    
    def save_to_thermal_memory(self, portfolio, total_value, usd_balance):
        """Save portfolio status to thermal memory"""
        try:
            conn = psycopg2.connect(
                host="192.168.132.222",
                port=5432,
                user="claude",
                password="jawaseatlasers2",
                database="zammad_production"
            )
            cur = conn.cursor()
            
            # Create portfolio summary
            portfolio_json = {
                'timestamp': datetime.now().isoformat(),
                'total_value': total_value,
                'usd_balance': usd_balance,
                'positions': [
                    {
                        'coin': p['coin'],
                        'value': p['value'],
                        'percentage': p['percentage']
                    } for p in portfolio[:10]  # Top 10 positions
                ]
            }
            
            content = f"""🔥 COMPLETE PORTFOLIO CHECK
Time: {datetime.now()}
Total Value: ${total_value:,.2f}
USD Balance: ${usd_balance:,.2f}
Top Positions: {', '.join([f"{p['coin']} (${p['value']:.0f})" for p in portfolio[:5]])}
DOGE Status: Checked and analyzed
Flying Squirrel Tewa: Aerial view complete"""
            
            query = """
            INSERT INTO thermal_memory_archive (
                memory_hash,
                temperature_score,
                current_stage,
                access_count,
                last_access,
                original_content,
                metadata,
                sacred_pattern
            ) VALUES (
                %s, 95, 'WHITE_HOT', 0, NOW(), %s, %s::jsonb, true
            ) ON CONFLICT (memory_hash) DO UPDATE 
            SET temperature_score = 95,
                last_access = NOW(),
                access_count = thermal_memory_archive.access_count + 1;
            """
            
            memory_hash = f"portfolio_complete_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            cur.execute(query, (memory_hash, content, json.dumps(portfolio_json)))
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"\n✅ Saved to thermal memory: {memory_hash}")
        except Exception as e:
            print(f"\n⚠️ Could not save to thermal memory: {e}")

if __name__ == "__main__":
    checker = CompletePortfolioCheck()
    checker.display_results()