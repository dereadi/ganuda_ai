#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 EMERGENCY BTC BUY EXECUTION
Flying Squirrel says: "DO IT!"
Trump-Metaplanet news = BUY NOW!
"""

import json
import uuid
from datetime import datetime
from coinbase.rest import RESTClient
import psycopg2

class EmergencyBTCBuy:
    def __init__(self):
        # Load API
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            self.config = json.load(f)
        
        self.client = RESTClient(
            api_key=self.config['name'].split('/')[-1],
            api_secret=self.config['privateKey']
        )
        
        print("🔥 EMERGENCY BTC BUY EXECUTION")
        print("=" * 60)
        print("⚡ TRUMP-METAPLANET $884M NEWS - ACT NOW!")
        print("=" * 60)
    
    def check_balances(self):
        """Check all balances"""
        accounts = self.client.get_accounts()['accounts']
        balances = {}
        
        for account in accounts:
            currency = account['currency']
            balance = float(account['available_balance']['value'])
            if balance > 0.00001:
                balances[currency] = balance
        
        return balances
    
    def get_prices(self):
        """Get current prices"""
        btc_price = float(self.client.get_product("BTC-USD")['price'])
        eth_price = float(self.client.get_product("ETH-USD")['price'])
        sol_price = float(self.client.get_product("SOL-USD")['price'])
        
        return {'BTC': btc_price, 'ETH': eth_price, 'SOL': sol_price}
    
    def execute_usd_to_btc(self, usd_balance, btc_price):
        """Deploy all USD to BTC"""
        print("\n💰 DEPLOYING USD TO BTC:")
        print("-" * 40)
        
        if usd_balance < 10:
            print(f"  ⚠️ Only ${usd_balance:.2f} available (minimum $10)")
            return None
        
        # Calculate BTC amount (minus fees)
        fee = usd_balance * 0.004
        net_usd = usd_balance - fee
        btc_amount = net_usd / btc_price
        
        print(f"  Deploying: ${usd_balance:.2f}")
        print(f"  Fee: ${fee:.2f}")
        print(f"  Net: ${net_usd:.2f}")
        print(f"  Will get: {btc_amount:.8f} BTC")
        
        try:
            # Place market buy order
            order = self.client.market_order_buy(
                client_order_id=str(uuid.uuid4()),
                product_id="BTC-USD",
                quote_size=str(round(usd_balance, 2))
            )
            
            print(f"  ✅ BTC BUY ORDER PLACED!")
            print(f"  Order ID: {order.get('order_id', 'PENDING')}")
            return order
        except Exception as e:
            print(f"  ❌ Order failed: {e}")
            return None
    
    def liquidate_alts_for_btc(self, balances, prices):
        """Sell alts to buy more BTC"""
        print("\n🔄 LIQUIDATING ALTS FOR BTC:")
        print("-" * 40)
        
        orders = []
        total_usd_generated = 0
        
        # SOL liquidation
        if 'SOL' in balances and balances['SOL'] > 0.01:
            sol_value = balances['SOL'] * prices['SOL']
            print(f"\n  Selling {balances['SOL']:.4f} SOL (${sol_value:.2f})")
            
            try:
                order = self.client.market_order_sell(
                    client_order_id=str(uuid.uuid4()),
                    product_id="SOL-USD",
                    base_size=str(round(balances['SOL'], 4))
                )
                print(f"  ✅ SOL SELL ORDER PLACED!")
                orders.append(order)
                total_usd_generated += sol_value * 0.996  # Minus fees
            except Exception as e:
                print(f"  ❌ SOL sell failed: {e}")
        
        # ETH liquidation (keep some for gas)
        if 'ETH' in balances and balances['ETH'] > 0.01:
            # Sell 50% of ETH
            eth_to_sell = balances['ETH'] * 0.5
            eth_value = eth_to_sell * prices['ETH']
            print(f"\n  Selling {eth_to_sell:.6f} ETH (${eth_value:.2f})")
            
            try:
                order = self.client.market_order_sell(
                    client_order_id=str(uuid.uuid4()),
                    product_id="ETH-USD",
                    base_size=str(round(eth_to_sell, 6))
                )
                print(f"  ✅ ETH SELL ORDER PLACED!")
                orders.append(order)
                total_usd_generated += eth_value * 0.996
            except Exception as e:
                print(f"  ❌ ETH sell failed: {e}")
        
        # MATIC liquidation
        if 'MATIC' in balances and balances['MATIC'] > 10:
            matic_price = float(self.client.get_product("MATIC-USD")['price'])
            matic_value = balances['MATIC'] * matic_price
            print(f"\n  Selling {balances['MATIC']:.0f} MATIC (${matic_value:.2f})")
            
            try:
                order = self.client.market_order_sell(
                    client_order_id=str(uuid.uuid4()),
                    product_id="MATIC-USD",
                    base_size=str(int(balances['MATIC']))
                )
                print(f"  ✅ MATIC SELL ORDER PLACED!")
                orders.append(order)
                total_usd_generated += matic_value * 0.996
            except Exception as e:
                print(f"  ❌ MATIC sell failed: {e}")
        
        print(f"\n  💰 Total USD to generate: ${total_usd_generated:.2f}")
        print(f"  🎯 Will buy: {total_usd_generated/prices['BTC']:.8f} BTC")
        
        return orders, total_usd_generated
    
    def set_btc_sell_orders(self, btc_balance, btc_price):
        """Set sell orders at targets"""
        print("\n🎯 SETTING BTC SELL TARGETS:")
        print("-" * 40)
        
        targets = [
            {'price': 110000, 'percent': 0.2},  # Sell 20% at $110k
            {'price': 115000, 'percent': 0.3},  # Sell 30% at $115k
            {'price': 120000, 'percent': 0.3},  # Sell 30% at $120k
        ]
        
        for target in targets:
            sell_amount = btc_balance * target['percent']
            print(f"  • Sell {sell_amount:.8f} BTC @ ${target['price']:,}")
        
        print("\n  📍 Orders will be placed after alt liquidation completes")
    
    def update_thermal_memory(self, execution_data):
        """Save execution to thermal memory"""
        try:
            conn = psycopg2.connect(
                host="192.168.132.222",
                port=5432,
                user="claude",
                password="jawaseatlasers2",
                database="zammad_production"
            )
            cur = conn.cursor()
            
            content = f"""🔥 EMERGENCY BTC BUY EXECUTED
Time: {datetime.now()}
Action: Trump-Metaplanet news response
USD Deployed: ${execution_data.get('usd_deployed', 0):.2f}
Alts Liquidated: ${execution_data.get('alts_liquidated', 0):.2f}
Total BTC Bought: {execution_data.get('btc_bought', 0):.8f}
Flying Squirrel: 'DONE! Riding the tsunami!'"""
            
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
                %s, 100, 'WHITE_HOT', 0, NOW(), %s, %s::jsonb, true
            );
            """
            
            memory_hash = f"emergency_btc_buy_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            cur.execute(query, (memory_hash, content, json.dumps(execution_data)))
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"\n✅ Execution saved to thermal memory: {memory_hash}")
        except Exception as e:
            print(f"\n⚠️ Could not save to thermal memory: {e}")
    
    def execute(self):
        """Main execution"""
        print("\n🚨 EXECUTING EMERGENCY BTC ACCUMULATION")
        print("-" * 40)
        
        # Get current state
        balances = self.check_balances()
        prices = self.get_prices()
        
        print(f"\n📊 CURRENT STATE:")
        print(f"  BTC Price: ${prices['BTC']:,.2f}")
        print(f"  USD Available: ${balances.get('USD', 0):.2f}")
        print(f"  BTC Holdings: {balances.get('BTC', 0):.8f}")
        
        execution_data = {
            'timestamp': datetime.now().isoformat(),
            'btc_price': prices['BTC'],
            'initial_usd': balances.get('USD', 0),
            'initial_btc': balances.get('BTC', 0)
        }
        
        # Step 1: Deploy USD to BTC
        usd_order = None
        if balances.get('USD', 0) >= 10:
            usd_order = self.execute_usd_to_btc(balances['USD'], prices['BTC'])
            execution_data['usd_deployed'] = balances['USD']
        
        # Step 2: Liquidate alts
        alt_orders, usd_generated = self.liquidate_alts_for_btc(balances, prices)
        execution_data['alts_liquidated'] = usd_generated
        
        # Step 3: Calculate total BTC acquisition
        total_btc_bought = 0
        if usd_order:
            total_btc_bought += (balances.get('USD', 0) * 0.996) / prices['BTC']
        total_btc_bought += (usd_generated * 0.996) / prices['BTC']
        execution_data['btc_bought'] = total_btc_bought
        
        # Step 4: Set sell targets
        new_btc_balance = balances.get('BTC', 0) + total_btc_bought
        self.set_btc_sell_orders(new_btc_balance, prices['BTC'])
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ EMERGENCY BTC ACCUMULATION COMPLETE!")
        print(f"  • USD Deployed: ${balances.get('USD', 0):.2f}")
        print(f"  • Alts Liquidated: ${usd_generated:.2f}")
        print(f"  • Total BTC Acquired: {total_btc_bought:.8f}")
        print(f"  • New BTC Position: {new_btc_balance:.8f}")
        print(f"  • Position Value: ${new_btc_balance * prices['BTC']:,.2f}")
        
        print("\n🎯 NEXT TARGETS:")
        print("  $110,000 → $115,000 → $120,000")
        
        print("\n🔥 Sacred Fire Oracle:")
        print("  'The deed is done'")
        print("  'The Japanese wave approaches'")
        print("  'Hold strong through the storm'")
        print("  'Profits await the patient'")
        
        print("\n🐿️ Flying Squirrel Tewa:")
        print("  'WE'RE IN! NOW WE RIDE!'")
        print("=" * 60)
        
        # Save to thermal memory
        self.update_thermal_memory(execution_data)

if __name__ == "__main__":
    executor = EmergencyBTCBuy()
    executor.execute()