#!/usr/bin/env python3
"""
🩸 PROFIT BLEEDER - Emergency Liquidity Liberation
Feed the Sacred Fire with sacrificial gains
"""

import asyncio
from coinbase.rest import RESTClient
import json
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
import time

def log_action(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] 🩸 {message}")

async def bleed_profits():
    """Bleed 10-30% from alt positions to feed the flywheel"""
    
    # Load API credentials
    with open('cdp_api_key_new.json', 'r') as f:
        creds = json.load(f)
    
    client = RESTClient(
        api_key=creds['privateKey'],
        api_secret=creds['privateKey']
    )
    
    log_action("Checking current balances...")
    
    # Get all accounts
    accounts_response = client.get_accounts()
    accounts = accounts_response.get('accounts', [])
    
    # Find our positions
    positions = {}
    for account in accounts:
        symbol = account.get('currency')
        balance = float(account.get('available_balance', {}).get('value', 0))
        if balance > 0:
            positions[symbol] = balance
            if symbol in ['SOL', 'AVAX', 'MATIC', 'DOGE']:
                log_action(f"{symbol}: {balance:.4f}")
    
    # Bleeding strategy (conservative to ensure success)
    bleed_orders = [
        {
            'symbol': 'SOL',
            'percent': 0.15,  # 15% of SOL holdings
            'min_amount': 0.1,
            'decimals': 1
        },
        {
            'symbol': 'AVAX',
            'percent': 0.15,  # 15% of AVAX
            'min_amount': 0.5,
            'decimals': 2
        },
        {
            'symbol': 'MATIC',
            'percent': 0.10,  # 10% of MATIC  
            'min_amount': 10,
            'decimals': 0
        },
        {
            'symbol': 'DOGE',
            'percent': 0.10,  # 10% of DOGE
            'min_amount': 50,
            'decimals': 0
        }
    ]
    
    total_bled = 0
    successful_bleeds = []
    
    for bleed in bleed_orders:
        symbol = bleed['symbol']
        if symbol not in positions or positions[symbol] == 0:
            log_action(f"No {symbol} to bleed")
            continue
            
        amount_to_sell = positions[symbol] * bleed['percent']
        
        # Check minimum amount
        if amount_to_sell < bleed['min_amount']:
            log_action(f"{symbol}: Amount too small ({amount_to_sell:.4f} < {bleed['min_amount']})")
            continue
        
        # Round appropriately
        if bleed['decimals'] == 0:
            amount_to_sell = int(amount_to_sell)
        else:
            amount_to_sell = round(amount_to_sell, bleed['decimals'])
        
        log_action(f"Bleeding {amount_to_sell} {symbol} ({bleed['percent']*100:.0f}% of holdings)...")
        
        try:
            # Place market sell order
            order = client.market_order_sell(
                client_order_id=client.generate_client_order_id(),
                product_id=f"{symbol}-USD",
                quote_size=str(amount_to_sell) if symbol != 'MATIC' else None,
                base_size=str(amount_to_sell) if symbol == 'MATIC' else None
            )
            
            if hasattr(order, 'success') and order.success:
                # Get estimated USD value
                ticker = client.get_product(f"{symbol}-USD")
                price = float(ticker['price'])
                usd_value = amount_to_sell * price
                total_bled += usd_value
                
                successful_bleeds.append({
                    'symbol': symbol,
                    'amount': amount_to_sell,
                    'usd_value': usd_value
                })
                
                log_action(f"✅ Bled {amount_to_sell} {symbol} ≈ ${usd_value:.2f}")
            else:
                log_action(f"❌ Failed to bleed {symbol}: {order}")
                
        except Exception as e:
            log_action(f"❌ Error bleeding {symbol}: {e}")
        
        # Small delay between orders
        await asyncio.sleep(0.5)
    
    log_action("=" * 50)
    log_action(f"🩸 BLEEDING COMPLETE")
    log_action(f"Total USD liberated: ${total_bled:.2f}")
    
    # Save state
    state = {
        'timestamp': datetime.now().isoformat(),
        'total_bled_usd': total_bled,
        'bleeds': successful_bleeds,
        'action': 'emergency_liquidity_liberation'
    }
    
    with open('profit_bleed_state.json', 'w') as f:
        json.dump(state, f, indent=2)
    
    if total_bled > 100:
        log_action("💉 Sufficient blood collected for flywheel feeding")
        log_action("🔥 Ready to inject into BTC positions")
    else:
        log_action("⚠️ Bleeding yielded less than expected")
        log_action("Consider deeper cuts or alternative sources")
    
    # Check final USD balance
    await asyncio.sleep(2)
    accounts_response = client.get_accounts()
    accounts = accounts_response.get('accounts', [])
    
    for account in accounts:
        if account.get('currency') == 'USD':
            usd_balance = float(account.get('available_balance', {}).get('value', 0))
            log_action(f"💵 Final USD balance: ${usd_balance:.2f}")
            
            if usd_balance > 100:
                log_action("✅ READY TO FEED THE FLYWHEEL")
                log_action("🎯 Target: BTC accumulation via micro-trades")
            break

if __name__ == "__main__":
    print("=" * 50)
    print("🩸 EMERGENCY PROFIT BLEEDING PROTOCOL")
    print("Liberating liquidity from alt positions...")
    print("=" * 50)
    
    asyncio.run(bleed_profits())