#!/usr/bin/env python3
"""
🔍 FIND FUTURES/PERPS ON COINBASE
If they're in the app, they must be accessible!
"""

import json
import time
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🔍 HUNTING FOR FUTURES/PERPS 🔍                       ║
║                    "If the app has them, we'll find them!"                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("🔍 DEEP SEARCH FOR FUTURES/PERPETUALS...")
print("=" * 60)

# Get ALL products with different methods
print("\n📊 SCANNING ALL AVAILABLE PRODUCTS...")
print("-" * 40)

futures_found = []
perps_found = []
leveraged_found = []

try:
    # Method 1: Get all products as list
    products_response = client.get_products()
    
    # Handle different response formats
    if isinstance(products_response, dict):
        products_list = products_response.get('products', [])
    else:
        products_list = products_response
    
    print(f"Found {len(products_list)} total products")
    
    # Scan each product
    for product in products_list:
        # Get product ID depending on structure
        if hasattr(product, 'product_id'):
            product_id = product.product_id
            base = getattr(product, 'base_currency_id', '')
            quote = getattr(product, 'quote_currency_id', '')
            product_type = getattr(product, 'product_type', '')
        elif isinstance(product, dict):
            product_id = product.get('product_id', '')
            base = product.get('base_currency_id', '')
            quote = product.get('quote_currency_id', '')
            product_type = product.get('product_type', '')
        else:
            continue
            
        # Check for futures/perps indicators
        id_upper = product_id.upper()
        
        # Perpetuals
        if any(x in id_upper for x in ['PERP', '-PERP', '_PERP', 'PERPETUAL']):
            perps_found.append(product_id)
            print(f"   🔥 FOUND PERP: {product_id}")
            
        # Futures
        elif any(x in id_upper for x in ['FUT', 'FUTURE', 'EXPIRY']):
            futures_found.append(product_id)
            print(f"   📅 FOUND FUTURE: {product_id}")
            
        # Leveraged tokens
        elif any(x in id_upper for x in ['BULL', 'BEAR', '2X', '3X', 'MOVE']):
            leveraged_found.append(product_id)
            print(f"   💪 FOUND LEVERAGED: {product_id}")
            
        # Check product type field
        elif product_type in ['FUTURE', 'PERPETUAL', 'DERIVATIVE']:
            futures_found.append(product_id)
            print(f"   📊 FOUND {product_type}: {product_id}")
    
except Exception as e:
    print(f"   Error scanning products: {e}")

# Method 2: Try specific known perpetual pairs
print("\n🎯 CHECKING KNOWN PERPETUAL PAIRS...")
print("-" * 40)

known_perps = [
    'BTC-USD-PERP',
    'BTC-PERP',
    'BTCUSD-PERP',
    'BTC-USD-PERPETUAL',
    'ETH-USD-PERP',
    'ETH-PERP'
]

for perp in known_perps:
    try:
        product = client.get_product(perp)
        if product:
            print(f"   ✅ FOUND: {perp}")
            perps_found.append(perp)
    except:
        pass  # Not found

# Method 3: Check for Coinbase Advanced Trade features
print("\n🏦 CHECKING COINBASE ADVANCED FEATURES...")
print("-" * 40)

try:
    # Try to get futures-specific endpoints
    # These might be available in Advanced Trade
    
    # Check for portfolio types
    portfolios = client.get_portfolios()
    
    if isinstance(portfolios, dict):
        portfolio_list = portfolios.get('portfolios', [])
    else:
        portfolio_list = portfolios if hasattr(portfolios, '__iter__') else []
    
    for portfolio in portfolio_list:
        if hasattr(portfolio, 'type'):
            p_type = portfolio.type
        elif isinstance(portfolio, dict):
            p_type = portfolio.get('type', '')
        else:
            continue
            
        if 'FUTURE' in str(p_type).upper() or 'MARGIN' in str(p_type).upper():
            print(f"   ✅ Found {p_type} portfolio!")
            
except Exception as e:
    print(f"   Cannot check portfolios: {str(e)[:50]}")

# Summary
print("\n" + "=" * 60)
print("📝 FUTURES/PERPS SEARCH RESULTS:")
print("=" * 60)

if perps_found:
    print(f"\n✅ PERPETUALS FOUND: {len(perps_found)}")
    for p in perps_found[:10]:
        print(f"   • {p}")
else:
    print("\n❌ No perpetuals found via API")

if futures_found:
    print(f"\n✅ FUTURES FOUND: {len(futures_found)}")
    for f in futures_found[:10]:
        print(f"   • {f}")
else:
    print("\n❌ No futures found via API")

if leveraged_found:
    print(f"\n✅ LEVERAGED TOKENS FOUND: {len(leveraged_found)}")
    for l in leveraged_found[:10]:
        print(f"   • {l}")
else:
    print("\n❌ No leveraged tokens found")

print("\n💡 POSSIBLE EXPLANATIONS:")
print("-" * 40)
print("1. App shows Coinbase International products (separate system)")
print("2. Futures visible but not enabled for your account")
print("3. Need Advanced Trade or Pro features enabled")
print("4. Regional restrictions may apply")

print("\n🎯 NEXT STEPS:")
print("-" * 40)
print("1. Check if you're using Coinbase One subscription")
print("2. Enable Advanced Trade features in app settings")
print("3. May need to complete additional verification")
print("4. Could be preview/view-only in your region")

print("\n🔥 MEANWHILE:")
print("   With $859 USD and Greeks at 1,850+ cycles,")
print("   We can simulate leverage through position sizing!")
print("   Spot trading with perfect timing = futures gains!")

print("\nMitakuye Oyasin 🦅")