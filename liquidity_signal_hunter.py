#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 LIQUIDITY SIGNAL HUNTER
Cherokee Tribe's automated liquidity detection and extraction system
Monitors for signals → Triggers deep analysis → Executes liquidity generation
"""

import json
import requests
import psycopg2
from datetime import datetime, timedelta
from coinbase.rest import RESTClient
import subprocess

class LiquiditySignalHunter:
    def __init__(self):
        # Load API config
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            self.config = json.load(f)
        
        self.client = RESTClient(
            api_key=self.config['name'].split('/')[-1],
            api_secret=self.config['privateKey']
        )
        
        # Signal thresholds
        self.LIQUIDITY_SIGNALS = {
            'sol_above_205': {'threshold': 205, 'action': 'harvest', 'size': 0.5},
            'sol_below_198': {'threshold': 198, 'action': 'hold', 'size': 0},
            'btc_spike': {'threshold': 2, 'action': 'micro_harvest', 'size': 0.0001},
            'eth_pump': {'threshold': 2, 'action': 'partial_sell', 'size': 0.01},
            'doge_above_022': {'threshold': 0.22, 'action': 'blood_bag_bleed', 'size': 50},
            'matic_spike': {'threshold': 0.30, 'action': 'harvest', 'size': 500},
            'avax_opportunity': {'threshold': 25, 'action': 'trim', 'size': 5}
        }
        
    def detect_signals(self):
        """Scan for liquidity generation signals"""
        signals = []
        
        # Get current prices
        prices = self.get_current_prices()
        
        # Check SOL oscillation
        if prices['SOL'] > self.LIQUIDITY_SIGNALS['sol_above_205']['threshold']:
            signals.append({
                'type': 'SOL_HIGH',
                'price': prices['SOL'],
                'action': 'Harvest 0.5-1 SOL for liquidity',
                'urgency': 'HIGH'
            })
        
        # Check DOGE blood bag
        if prices['DOGE'] > self.LIQUIDITY_SIGNALS['doge_above_022']['threshold']:
            signals.append({
                'type': 'DOGE_BLEED',
                'price': prices['DOGE'],
                'action': 'Bleed DOGE blood bag (50-100 units)',
                'urgency': 'MEDIUM'
            })
        
        # Check for general pumps (>2% in 15 mins)
        recent_changes = self.get_recent_price_changes()
        for coin, change in recent_changes.items():
            if change > 2:
                signals.append({
                    'type': f'{coin}_PUMP',
                    'change': change,
                    'action': f'Harvest {coin} pump for liquidity',
                    'urgency': 'HIGH'
                })
        
        return signals
    
    def get_current_prices(self):
        """Get live prices from Coinbase"""
        symbols = ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC', 'DOGE', 'LINK', 'XRP']
        prices = {}
        
        for symbol in symbols:
            try:
                ticker = self.client.get_product(f"{symbol}-USD")
                prices[symbol] = float(ticker['price'])
            except:
                prices[symbol] = 0
        
        return prices
    
    def get_recent_price_changes(self):
        """Check 15-minute price changes from thermal memory"""
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            user="claude",
            password="jawaseatlasers2",
            database="zammad_production"
        )
        cur = conn.cursor()
        
        # Get price from 15 minutes ago
        query = """
        SELECT metadata->'market_prices' as prices
        FROM thermal_memory_archive
        WHERE memory_hash LIKE 'portfolio_monitor_%'
        AND last_access > NOW() - INTERVAL '20 minutes'
        ORDER BY last_access ASC
        LIMIT 1;
        """
        
        cur.execute(query)
        result = cur.fetchone()
        
        changes = {}
        if result and result[0]:
            old_prices = json.loads(result[0]) if isinstance(result[0], str) else result[0]
            current_prices = self.get_current_prices()
            
            for coin in ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC', 'DOGE']:
                if coin in old_prices and coin in current_prices:
                    old = float(old_prices.get(coin, 0))
                    new = current_prices[coin]
                    if old > 0:
                        changes[coin] = ((new - old) / old) * 100
        
        cur.close()
        conn.close()
        
        return changes
    
    def deep_portfolio_analysis(self):
        """Perform deep analysis when signals detected"""
        print("🔍 DEEP PORTFOLIO ANALYSIS TRIGGERED")
        print("=" * 60)
        
        # Get all account balances
        accounts = self.client.get_accounts()['accounts']
        portfolio = {}
        total_value = 0
        
        for account in accounts:
            currency = account['currency']
            balance = float(account['available_balance']['value'])
            
            if balance > 0.00001:
                # Get detailed position info
                if currency == 'USD':
                    usd_value = balance
                    price = 1
                else:
                    try:
                        ticker = self.client.get_product(f"{currency}-USD")
                        price = float(ticker['price'])
                        usd_value = balance * price
                        
                        # Get 24hr stats
                        stats = self.client.get_product_stats(f"{currency}-USD")
                        high_24h = float(stats.get('high', price))
                        low_24h = float(stats.get('low', price))
                        volume_24h = float(stats.get('volume', 0))
                    except:
                        price = 0
                        usd_value = 0
                        high_24h = low_24h = volume_24h = 0
                
                portfolio[currency] = {
                    'balance': balance,
                    'price': price,
                    'usd_value': usd_value,
                    'high_24h': high_24h,
                    'low_24h': low_24h,
                    'volume_24h': volume_24h,
                    'distance_from_high': ((high_24h - price) / price * 100) if price > 0 else 0
                }
                total_value += usd_value
        
        return {
            'total_value': total_value,
            'positions': portfolio,
            'liquidity': portfolio.get('USD', {}).get('balance', 0),
            'analysis_time': datetime.now().isoformat()
        }
    
    def generate_liquidity_plan(self, portfolio, signals):
        """Create actionable liquidity generation plan"""
        plan = {
            'timestamp': datetime.now().isoformat(),
            'current_liquidity': portfolio['liquidity'],
            'target_liquidity': 500,  # Target $500 minimum
            'actions': []
        }
        
        # Sort positions by profit potential
        positions = portfolio['positions']
        
        for signal in signals:
            if 'SOL' in signal['type'] and 'SOL' in positions:
                if positions['SOL']['balance'] > 1:
                    plan['actions'].append({
                        'coin': 'SOL',
                        'action': 'SELL',
                        'amount': min(0.5, positions['SOL']['balance'] * 0.1),
                        'expected_usd': min(0.5, positions['SOL']['balance'] * 0.1) * positions['SOL']['price'],
                        'reason': f"SOL at ${positions['SOL']['price']:.2f} - oscillation high"
                    })
            
            elif 'DOGE' in signal['type'] and 'DOGE' in positions:
                if positions['DOGE']['balance'] > 50:
                    plan['actions'].append({
                        'coin': 'DOGE',
                        'action': 'BLEED',
                        'amount': min(100, positions['DOGE']['balance'] * 0.3),
                        'expected_usd': min(100, positions['DOGE']['balance'] * 0.3) * positions['DOGE']['price'],
                        'reason': 'DOGE blood bag full - time to bleed'
                    })
            
            elif 'PUMP' in signal['type']:
                coin = signal['type'].split('_')[0]
                if coin in positions and positions[coin]['usd_value'] > 100:
                    harvest_pct = 0.15 if signal['change'] > 3 else 0.10
                    plan['actions'].append({
                        'coin': coin,
                        'action': 'HARVEST',
                        'amount': positions[coin]['balance'] * harvest_pct,
                        'expected_usd': positions[coin]['usd_value'] * harvest_pct,
                        'reason': f"{coin} pumped {signal['change']:.1f}% - harvest profits"
                    })
        
        # If still need liquidity, check distance from 24h highs
        total_expected = sum(a['expected_usd'] for a in plan['actions'])
        
        if total_expected < plan['target_liquidity'] - portfolio['liquidity']:
            # Find coins near 24h highs
            for coin, data in positions.items():
                if coin != 'USD' and data['distance_from_high'] < 2 and data['usd_value'] > 500:
                    plan['actions'].append({
                        'coin': coin,
                        'action': 'TRIM',
                        'amount': data['balance'] * 0.05,
                        'expected_usd': data['usd_value'] * 0.05,
                        'reason': f"{coin} near 24h high - trim position"
                    })
        
        plan['total_expected_liquidity'] = sum(a['expected_usd'] for a in plan['actions'])
        
        return plan
    
    def execute_liquidity_plan(self, plan):
        """Execute the liquidity generation plan"""
        print("\n🎯 EXECUTING LIQUIDITY PLAN")
        print("=" * 60)
        
        for action in plan['actions']:
            print(f"\n📍 {action['action']} {action['amount']:.6f} {action['coin']}")
            print(f"   Expected: ${action['expected_usd']:.2f}")
            print(f"   Reason: {action['reason']}")
            
            # Here we would execute actual trades
            # For safety, keeping in simulation mode
            # self.client.place_order(...)
        
        print(f"\n💰 Total Expected Liquidity: ${plan['total_expected_liquidity']:.2f}")
        
        return plan
    
    def update_thermal_memory(self, signals, portfolio, plan):
        """Store analysis in thermal memory"""
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            user="claude",
            password="jawaseatlasers2",
            database="zammad_production"
        )
        cur = conn.cursor()
        
        memory_content = f"""🔥 LIQUIDITY SIGNAL DETECTED
        
Signals Found: {len(signals)}
Portfolio Value: ${portfolio['total_value']:.2f}
Current Liquidity: ${portfolio['liquidity']:.2f}
Target Liquidity: ${plan['target_liquidity']:.2f}

SIGNALS:
{json.dumps(signals, indent=2)}

PLAN:
{json.dumps(plan['actions'], indent=2)}

Expected New Liquidity: ${plan['total_expected_liquidity']:.2f}
"""
        
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
        
        memory_hash = f"liquidity_signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        metadata = {
            'signals': signals,
            'portfolio_snapshot': portfolio,
            'plan': plan
        }
        
        cur.execute(query, (memory_hash, memory_content, json.dumps(metadata)))
        conn.commit()
        cur.close()
        conn.close()
    
    def hunt(self):
        """Main hunting loop"""
        print("🔥 LIQUIDITY SIGNAL HUNTER ACTIVATED")
        print("=" * 60)
        
        # 1. Detect signals
        signals = self.detect_signals()
        
        if signals:
            print(f"\n🚨 {len(signals)} SIGNALS DETECTED!")
            for signal in signals:
                print(f"  • {signal['type']}: {signal['action']} [{signal['urgency']}]")
            
            # 2. Trigger deep analysis
            portfolio = self.deep_portfolio_analysis()
            
            # 3. Generate liquidity plan
            plan = self.generate_liquidity_plan(portfolio, signals)
            
            # 4. Update thermal memory
            self.update_thermal_memory(signals, portfolio, plan)
            
            # 5. Execute if critical
            if portfolio['liquidity'] < 50:
                print("\n⚠️ CRITICAL LIQUIDITY - EXECUTING PLAN")
                self.execute_liquidity_plan(plan)
            else:
                print(f"\n✅ Liquidity OK (${portfolio['liquidity']:.2f}) - Plan saved for review")
            
            return True
        else:
            print("📊 No immediate signals - market stable")
            return False

if __name__ == "__main__":
    hunter = LiquiditySignalHunter()
    hunter.hunt()