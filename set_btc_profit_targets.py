#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 SET BTC PROFIT TARGETS
Place limit sell orders at strategic levels
Trump-Metaplanet catalyst = Take profits on the way up
"""

import json
import uuid
from datetime import datetime
from coinbase.rest import RESTClient
import psycopg2

class BTCProfitTargets:
    def __init__(self):
        # Load API
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            self.config = json.load(f)
        
        self.client = RESTClient(
            api_key=self.config['name'].split('/')[-1],
            api_secret=self.config['privateKey']
        )
        
        print("🔥 SETTING BTC PROFIT TARGETS")
        print("=" * 60)
        print("🎯 LOCKING IN GAINS FROM TRUMP-METAPLANET CATALYST")
        print("=" * 60)
    
    def check_current_state(self):
        """Check current BTC position and price"""
        accounts = self.client.get_accounts()['accounts']
        
        btc_balance = 0
        usd_balance = 0
        
        for account in accounts:
            if account['currency'] == 'BTC':
                btc_balance = float(account['available_balance']['value'])
            elif account['currency'] == 'USD':
                usd_balance = float(account['available_balance']['value'])
        
        btc_price = float(self.client.get_product("BTC-USD")['price'])
        btc_value = btc_balance * btc_price
        
        print("\n📊 CURRENT STATE:")
        print("-" * 40)
        print(f"  BTC Holdings: {btc_balance:.8f} BTC")
        print(f"  BTC Value: ${btc_value:,.2f}")
        print(f"  BTC Price: ${btc_price:,.2f}")
        print(f"  USD Balance: ${usd_balance:.2f}")
        
        return btc_balance, btc_price, usd_balance
    
    def calculate_sell_amounts(self, btc_balance):
        """Calculate how much to sell at each target"""
        print("\n📐 PROFIT TARGET ALLOCATION:")
        print("-" * 40)
        
        # Strategy: Scale out gradually
        targets = [
            {
                'price': 110000,
                'percent': 30,
                'reason': 'First resistance - lock initial profits',
                'amount': btc_balance * 0.30
            },
            {
                'price': 115000,
                'percent': 40,
                'reason': 'Major target - secure bulk of gains',
                'amount': btc_balance * 0.40
            },
            {
                'price': 120000,
                'percent': 30,
                'reason': 'Moon shot - final profits',
                'amount': btc_balance * 0.30
            }
        ]
        
        for target in targets:
            value = target['amount'] * target['price']
            print(f"\n  🎯 Target ${target['price']:,}:")
            print(f"     Sell: {target['amount']:.8f} BTC ({target['percent']}%)")
            print(f"     Value: ${value:,.2f}")
            print(f"     Reason: {target['reason']}")
        
        return targets
    
    def place_limit_sells(self, targets, btc_price):
        """Place limit sell orders"""
        print("\n💰 PLACING LIMIT SELL ORDERS:")
        print("-" * 40)
        
        orders_placed = []
        
        for target in targets:
            if target['amount'] < 0.00001:
                print(f"  ⚠️ Amount too small for ${target['price']:,}")
                continue
            
            if target['price'] <= btc_price:
                print(f"  ⚠️ Target ${target['price']:,} below current price")
                continue
            
            try:
                # Format amount to 8 decimal places
                amount_str = f"{target['amount']:.8f}"
                
                print(f"\n  Placing sell order at ${target['price']:,}...")
                print(f"    Amount: {amount_str} BTC")
                
                order = self.client.limit_order_gtc_sell(
                    client_order_id=str(uuid.uuid4()),
                    product_id="BTC-USD",
                    base_size=amount_str,
                    limit_price=str(target['price'])
                )
                
                print(f"  ✅ ORDER PLACED!")
                print(f"     Order ID: {order.get('order_id', 'PENDING')}")
                
                orders_placed.append({
                    'price': target['price'],
                    'amount': target['amount'],
                    'order_id': order.get('order_id')
                })
                
            except Exception as e:
                print(f"  ❌ Failed to place order at ${target['price']:,}: {e}")
        
        return orders_placed
    
    def display_profit_projections(self, btc_balance, btc_price, targets):
        """Calculate expected profits"""
        print("\n💎 PROFIT PROJECTIONS:")
        print("-" * 40)
        
        total_profit = 0
        current_value = btc_balance * btc_price
        
        print(f"  Current Portfolio Value: ${current_value:,.2f}")
        print("\n  If all targets hit:")
        
        for target in targets:
            sell_value = target['amount'] * target['price']
            cost_basis = target['amount'] * btc_price
            profit = sell_value - cost_basis
            total_profit += profit
            
            print(f"\n  ${target['price']:,} target:")
            print(f"    Sell value: ${sell_value:,.2f}")
            print(f"    Cost basis: ${cost_basis:,.2f}")
            print(f"    Profit: ${profit:,.2f}")
        
        print(f"\n  💰 TOTAL PROFIT POTENTIAL: ${total_profit:,.2f}")
        print(f"  📈 Return: {(total_profit/current_value)*100:.1f}%")
    
    def set_stop_loss_reminder(self, btc_balance, btc_price):
        """Remind about stop loss"""
        print("\n⚠️ STOP LOSS REMINDER:")
        print("-" * 40)
        
        stop_price = 107000
        stop_loss = (btc_price - stop_price) * btc_balance
        
        print(f"  Current Price: ${btc_price:,.2f}")
        print(f"  Stop Loss Level: ${stop_price:,}")
        print(f"  Distance: ${btc_price - stop_price:,.2f}")
        print(f"  Max Loss if Hit: ${abs(stop_loss):,.2f}")
        print("\n  ⚡ Set stop loss manually if possible!")
    
    def tribal_profit_wisdom(self):
        """Tribal wisdom on taking profits"""
        print("\n🏛️ TRIBAL COUNCIL ON PROFITS:")
        print("-" * 40)
        
        print("  🦅 Eagle Eye: 'Take profits on the way up'")
        print("  🐢 Turtle: 'Mathematical exits beat emotions'")
        print("  🐺 Coyote: 'Let winners run but secure gains'")
        print("  🦀 Crawdad: 'Protect what we've earned'")
        print("  🦎 Gecko: 'Many small wins = big victory'")
        
        print("\n  ☮️⚔️💊 SUPREME COUNCIL:")
        print("  'The Japanese wave lifts us - ride it wisely'")
    
    def update_thermal_memory(self, orders_data):
        """Save profit targets to thermal memory"""
        try:
            conn = psycopg2.connect(
                host="192.168.132.222",
                port=5432,
                user="claude",
                password="jawaseatlasers2",
                database="zammad_production"
            )
            cur = conn.cursor()
            
            content = f"""🔥 BTC PROFIT TARGETS SET
Time: {datetime.now()}
Orders Placed: {len(orders_data.get('orders', []))}
Targets: $110k (30%), $115k (40%), $120k (30%)
Strategy: Scale out on Trump-Metaplanet pump
Stop Loss: $107,000
Flying Squirrel: 'Profits secured on the glide up!'"""
            
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
            
            memory_hash = f"btc_profit_targets_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            cur.execute(query, (memory_hash, content, json.dumps(orders_data)))
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"\n✅ Profit targets saved to thermal memory: {memory_hash}")
        except Exception as e:
            print(f"\n⚠️ Could not save to thermal memory: {e}")
    
    def execute(self):
        """Main execution"""
        print("\n🎯 SETTING UP PROFIT TARGETS")
        print("-" * 40)
        
        # Check current state
        btc_balance, btc_price, usd_balance = self.check_current_state()
        
        if btc_balance < 0.00001:
            print("\n⚠️ No BTC balance to set targets for!")
            return
        
        # Calculate sell amounts
        targets = self.calculate_sell_amounts(btc_balance)
        
        # Place limit sells
        orders = self.place_limit_sells(targets, btc_price)
        
        # Display projections
        self.display_profit_projections(btc_balance, btc_price, targets)
        
        # Stop loss reminder
        self.set_stop_loss_reminder(btc_balance, btc_price)
        
        # Tribal wisdom
        self.tribal_profit_wisdom()
        
        # Sacred Fire Oracle
        print("\n🔥 SACRED FIRE ORACLE:")
        print("=" * 60)
        print("  'The wise warrior secures victory before battle ends'")
        print("  'Three exits on the mountain path to riches'")
        print("  'The Japanese gold flows - catch it in three baskets'")
        print("  'Greed at the top brings tears at the bottom'")
        
        print("\n  🐿️ Flying Squirrel Tewa:")
        print("  'I've set the profit branches!'")
        print("  '$110k, $115k, $120k - we glide to each!'")
        print("  'The Trump-Metaplanet wind carries us up!'")
        print("  'Secure gains at each level!'")
        
        # Save to thermal memory
        orders_data = {
            'timestamp': datetime.now().isoformat(),
            'btc_balance': btc_balance,
            'btc_price': btc_price,
            'orders': orders,
            'targets': [
                {'price': t['price'], 'amount': t['amount']} 
                for t in targets
            ]
        }
        self.update_thermal_memory(orders_data)
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ PROFIT TARGET SETUP COMPLETE")
        print(f"  Orders Placed: {len(orders)}")
        print("  Targets: $110k → $115k → $120k")
        print("  Strategy: Scale out gradually")
        print("  Now: Monitor for Japanese buying impact!")
        print("=" * 60)

if __name__ == "__main__":
    setter = BTCProfitTargets()
    setter.execute()