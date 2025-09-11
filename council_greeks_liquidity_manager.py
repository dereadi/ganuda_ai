#!/usr/bin/env python3
"""
🔥🏛️💰 TRIBAL COUNCIL & GREEKS LIQUIDITY FLOW MANAGER
========================================================
Continuous monitoring and rebalancing for optimal trading liquidity

"DOGE may be worthless, but its volatility is gold" - War Chief
"Take profits in USD, redistribute to winners" - Elder Wisdom
"The Sacred Fire needs constant fuel" - Fire Keeper
"""

import json
import time
import uuid
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║         🔥 COUNCIL & GREEKS LIQUIDITY FLOW MANAGEMENT 💰                   ║
║                                                                             ║
║     "Convert wins to USD → Redistribute → Compound → Repeat"               ║
║     "DOGE is our liquidity cow - milk it constantly"                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

# Current market prices
PRICES = {
    'BTC': 112000,  # Approximate
    'ETH': 2600,
    'SOL': 150,
    'AVAX': 25,
    'MATIC': 0.40,
    'LINK': 11,
    'DOGE': 0.10
}

# Liquidity strategy configuration
LIQUIDITY_CONFIG = {
    'min_usd_target': 500,      # Minimum USD to maintain
    'optimal_usd_target': 1500, # Optimal USD for trading
    'max_usd_hold': 3000,      # Above this, deploy to positions
    'profit_take_threshold': 0.02,  # Take profits at 2% gain
    'doge_milk_amount': 1000,  # DOGE to sell per cycle
    'check_interval': 60        # Seconds between checks
}

def get_current_positions():
    """Get all current positions and USD balance"""
    accounts = client.get_accounts()['accounts']
    positions = {}
    usd_balance = 0
    
    for account in accounts:
        symbol = account['currency']
        balance = float(account['available_balance']['value'])
        
        if balance > 0.01:
            if symbol == 'USD':
                usd_balance = balance
            elif symbol in PRICES:
                value = balance * PRICES[symbol]
                positions[symbol] = {
                    'amount': balance,
                    'value': value,
                    'price': PRICES[symbol]
                }
    
    return positions, usd_balance

def council_deliberation(positions, usd_balance):
    """Council and Greeks discuss strategy"""
    print("\n🗣️ COUNCIL & GREEKS DELIBERATION:")
    print("=" * 60)
    
    decisions = []
    
    # Check USD status
    if usd_balance < LIQUIDITY_CONFIG['min_usd_target']:
        print(f"⚠️ Elder: 'USD critically low: ${usd_balance:.2f}'")
        print(f"⚔️ War Chief: 'Need ${LIQUIDITY_CONFIG['min_usd_target'] - usd_balance:.2f} immediately!'")
        
        # Greeks provide input
        print("\n🏛️ GREEKS ANALYSIS:")
        
        # Vega on volatility
        if 'DOGE' in positions:
            doge_val = positions['DOGE']['value']
            print(f"📈 Vega: 'DOGE has ${doge_val:.2f} - high volatility, good for liquidity'")
            decisions.append({
                'action': 'SELL',
                'coin': 'DOGE',
                'amount': min(LIQUIDITY_CONFIG['doge_milk_amount'], positions['DOGE']['amount']),
                'reason': 'Milk DOGE for liquidity'
            })
        
        # Delta on gaps
        print("📊 Delta: 'Trim lowest performers for USD'")
        
        # Theta on time decay
        if 'MATIC' in positions and positions['MATIC']['value'] > 1000:
            print("⏰ Theta: 'MATIC stable but large - trim 20% for liquidity'")
            decisions.append({
                'action': 'SELL',
                'coin': 'MATIC',
                'amount': positions['MATIC']['amount'] * 0.20,
                'reason': 'Stable asset liquidity harvest'
            })
            
    elif usd_balance > LIQUIDITY_CONFIG['max_usd_hold']:
        print(f"💰 Peace Keeper: 'USD abundant: ${usd_balance:.2f}'")
        print("🔥 Fire Keeper: 'Deploy excess to active positions'")
        
        # Deploy to winners
        deploy_amount = usd_balance - LIQUIDITY_CONFIG['optimal_usd_target']
        decisions.append({
            'action': 'DEPLOY',
            'amount': deploy_amount,
            'targets': ['SOL', 'AVAX'],  # High volatility targets
            'reason': 'Excess USD deployment'
        })
    
    else:
        print(f"✅ Star Watcher: 'Balance optimal: ${usd_balance:.2f}'")
        
        # Still milk DOGE if available
        if 'DOGE' in positions and positions['DOGE']['amount'] > 2000:
            print("🥛 War Chief: 'DOGE available for milking'")
            decisions.append({
                'action': 'SELL',
                'coin': 'DOGE',
                'amount': 500,  # Small regular milking
                'reason': 'Routine DOGE liquidity harvest'
            })
    
    return decisions

def execute_liquidity_trades(decisions):
    """Execute the liquidity management trades"""
    print("\n🚀 EXECUTING LIQUIDITY MANAGEMENT:")
    print("=" * 60)
    
    results = []
    for decision in decisions:
        if decision['action'] == 'SELL':
            try:
                print(f"🔄 Selling {decision['amount']:.2f} {decision['coin']}...")
                
                order = client.market_order_sell(
                    client_order_id=f"liquidity_{int(time.time())}_{uuid.uuid4().hex[:8]}",
                    product_id=f"{decision['coin']}-USD",
                    base_size=str(decision['amount'])
                )
                
                if hasattr(order, 'success') and order.success:
                    print(f"✅ Sold {decision['coin']}: Order {order.success_response['order_id']}")
                    results.append({'status': 'success', 'action': decision})
                else:
                    print(f"⚠️ {decision['coin']} order needs adjustment")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)[:100]}")
                
        elif decision['action'] == 'DEPLOY':
            print(f"💸 Deploying ${decision['amount']:.2f} to {decision['targets']}")
            # Deployment logic would go here
            
        time.sleep(2)  # Rate limiting
    
    return results

def continuous_liquidity_monitor():
    """Main monitoring loop"""
    print("\n⚡ STARTING CONTINUOUS LIQUIDITY MONITORING")
    print("Checking every 60 seconds...")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    cycle = 0
    total_doge_milked = 0
    total_usd_generated = 0
    
    while True:
        cycle += 1
        print(f"\n🔄 CYCLE {cycle} - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 40)
        
        try:
            # Get current state
            positions, usd_balance = get_current_positions()
            
            # Calculate total portfolio
            total_value = usd_balance + sum(p['value'] for p in positions.values())
            
            print(f"💰 Portfolio: ${total_value:,.2f}")
            print(f"💵 USD: ${usd_balance:.2f}")
            
            # Special focus on DOGE
            if 'DOGE' in positions:
                doge_amount = positions['DOGE']['amount']
                doge_value = positions['DOGE']['value']
                print(f"🐕 DOGE: {doge_amount:,.0f} units (${doge_value:.2f})")
                print(f"   Milking potential: ${doge_value * 0.1:.2f}/cycle")
            
            # Council deliberation
            decisions = council_deliberation(positions, usd_balance)
            
            if decisions:
                # Execute trades
                results = execute_liquidity_trades(decisions)
                
                # Track DOGE milking
                for r in results:
                    if r['status'] == 'success' and r['action']['coin'] == 'DOGE':
                        milked = r['action']['amount'] * PRICES['DOGE']
                        total_doge_milked += milked
                        total_usd_generated += milked
                        print(f"🥛 DOGE milked this cycle: ${milked:.2f}")
            else:
                print("📊 No liquidity actions needed")
            
            # Summary
            if cycle % 10 == 0:  # Every 10 cycles
                print(f"\n📈 10-CYCLE SUMMARY:")
                print(f"   Total DOGE milked: ${total_doge_milked:.2f}")
                print(f"   Total USD generated: ${total_usd_generated:.2f}")
                print(f"   Current USD: ${usd_balance:.2f}")
            
        except Exception as e:
            print(f"⚠️ Cycle error: {str(e)[:100]}")
        
        # Wait for next cycle
        print(f"\n⏳ Next check in {LIQUIDITY_CONFIG['check_interval']} seconds...")
        time.sleep(LIQUIDITY_CONFIG['check_interval'])

def check_flywheel_needs():
    """Quick check if flywheel needs fuel"""
    positions, usd = get_current_positions()
    
    if usd < 100:
        print("\n🌪️ FLYWHEEL ALERT: Needs fuel!")
        print(f"   Current USD: ${usd:.2f}")
        print(f"   Minimum needed: $100")
        print(f"   Optimal: $500+")
        
        # Emergency DOGE milk
        if 'DOGE' in positions and positions['DOGE']['amount'] > 1000:
            print(f"\n🚨 EMERGENCY: Milking 2000 DOGE immediately!")
            return [{
                'action': 'SELL',
                'coin': 'DOGE',
                'amount': 2000,
                'reason': 'Emergency flywheel fuel'
            }]
    
    return []

if __name__ == "__main__":
    print("\n🎯 LIQUIDITY MANAGEMENT STRATEGY:")
    print("-" * 60)
    print("1. Continuously monitor USD balance")
    print("2. Milk DOGE regularly for liquidity")
    print("3. Trim winners when they peak")
    print("4. Maintain $500-1500 USD for trading")
    print("5. Deploy excess above $3000")
    print("6. Feed the flywheel constantly")
    
    # Check immediate needs
    emergency = check_flywheel_needs()
    if emergency:
        execute_liquidity_trades(emergency)
    
    # Start continuous monitoring
    try:
        continuous_liquidity_monitor()
    except KeyboardInterrupt:
        print("\n\n🛑 Liquidity monitor stopped")
        print("The Sacred Fire continues to burn")
        print("Mitakuye Oyasin 🔥")