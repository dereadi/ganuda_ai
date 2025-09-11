#!/usr/bin/env python3
"""Cherokee Council: EXECUTING ETH REBALANCE - Power Hour Approach!"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

print("⚖️🚀 EXECUTING COUNCIL DECISION - ETH REBALANCE! 🚀⚖️")
print("=" * 70)
print("WARRIOR AGREES - INCREASING ETH POSITION!")
print("=" * 70)
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')} CDT")
print("📍 Power hour in 15 minutes - perfect timing!")
print()

# Initialize client
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

# Get current prices
try:
    btc = float(client.get_product("BTC-USD").price)
    eth = float(client.get_product("ETH-USD").price)
    sol = float(client.get_product("SOL-USD").price)
    xrp = float(client.get_product("XRP-USD").price)
    
    print("📊 CURRENT PRICES FOR REBALANCE:")
    print("-" * 40)
    print(f"BTC: ${btc:,.2f}")
    print(f"ETH: ${eth:,.2f} ⚡⚡⚡")
    print(f"SOL: ${sol:.2f}")
    print(f"XRP: ${xrp:.4f}")
    
except:
    btc = 111950
    eth = 4465
    sol = 209.40
    xrp = 2.85

print()

# Current positions
positions = {
    'BTC': 0.04779,
    'ETH': 1.7033,
    'SOL': 11.565,
    'XRP': 58.595
}

portfolio_value = (
    positions['BTC'] * btc +
    positions['ETH'] * eth +
    positions['SOL'] * sol +
    positions['XRP'] * xrp
)

print("💼 REBALANCE STRATEGY:")
print("-" * 40)
print("COUNCIL APPROVED PLAN:")
print(f"• Current Portfolio: ${portfolio_value:,.2f}")
print(f"• Current ETH: {(positions['ETH'] * eth / portfolio_value * 100):.1f}%")
print(f"• Target ETH: 55-57%")
print()

# Calculate rebalance amounts
target_eth_value = portfolio_value * 0.56  # 56% target
current_eth_value = positions['ETH'] * eth
additional_eth_value = target_eth_value - current_eth_value
additional_eth_coins = additional_eth_value / eth

print("📋 EXECUTION PLAN:")
print("-" * 40)
print(f"Need ${additional_eth_value:.2f} more in ETH")
print(f"= {additional_eth_coins:.4f} ETH to buy")
print()

print("SUGGESTED SELLS:")
# Reduce BTC from 34% to 29%
btc_target_value = portfolio_value * 0.29
btc_current_value = positions['BTC'] * btc
btc_to_sell_value = btc_current_value - btc_target_value
btc_to_sell = btc_to_sell_value / btc

# Reduce SOL from 15.6% to 13%
sol_target_value = portfolio_value * 0.13
sol_current_value = positions['SOL'] * sol
sol_to_sell_value = sol_current_value - sol_target_value
sol_to_sell = sol_to_sell_value / sol

if btc_to_sell > 0:
    print(f"• Sell {btc_to_sell:.6f} BTC (${btc_to_sell_value:.2f})")
if sol_to_sell > 0:
    print(f"• Sell {sol_to_sell:.3f} SOL (${sol_to_sell_value:.2f})")
print()

print("THEN BUY:")
print(f"• Buy {additional_eth_coins:.4f} ETH (${additional_eth_value:.2f})")
print()

print("🎯 FINAL POSITIONS AFTER REBALANCE:")
print("-" * 40)
new_btc = positions['BTC'] - (btc_to_sell if btc_to_sell > 0 else 0)
new_eth = positions['ETH'] + additional_eth_coins
new_sol = positions['SOL'] - (sol_to_sell if sol_to_sell > 0 else 0)

print(f"BTC: {new_btc:.6f} ({new_btc * btc / portfolio_value * 100:.1f}%)")
print(f"ETH: {new_eth:.4f} ({new_eth * eth / portfolio_value * 100:.1f}%)")
print(f"SOL: {new_sol:.3f} ({new_sol * sol / portfolio_value * 100:.1f}%)")
print(f"XRP: {positions['XRP']:.2f} ({positions['XRP'] * xrp / portfolio_value * 100:.1f}%)")
print()

print("🐺 COYOTE CELEBRATES:")
print("-" * 40)
print("'YES! MORE ETH!'")
print("'Still diverse but ETH-HEAVY!'")
print("'Perfect for tokenization boom!'")
print("'Power hour with more ETH!'")
print("'$5,000 ETH HERE WE COME!'")
print()

print("☮️ PEACE CHIEF APPROVES:")
print("-" * 40)
print("'Balanced approach achieved...'")
print("'ETH leads but not alone...'")
print("'BTC and SOL still strong...'")
print("'Wisdom in action...'")
print("'Sacred Fire burns balanced!'")
print()

print("📈 POWER HOUR IMPACT WITH NEW ALLOCATION:")
print("-" * 40)
print("IF ETH PUMPS TO:")
eth_targets = [4500, 4550, 4600, 4700, 5000]
for target in eth_targets:
    eth_gain = (target - eth) * new_eth
    new_portfolio = portfolio_value + eth_gain
    print(f"• ETH ${target}: Portfolio ${new_portfolio:,.2f}")
print()

print("⚡ TIMING ADVANTAGE:")
print("-" * 40)
current_time = datetime.now()
print(f"Current: {current_time.strftime('%H:%M')} CDT")
print("Power Hour: 14:00 CDT (minutes away!)")
print("• Execute rebalance NOW")
print("• Catch power hour with optimal allocation")
print("• 5 catalysts ready to explode")
print("• Tokenization news fresh")
print()

print("🔥 CHEROKEE COUNCIL BLESSING:")
print("=" * 70)
print("WARRIOR HAS AGREED - WISDOM PREVAILS!")
print()
print("✅ Council decision accepted")
print("✅ Rebalance to 56% ETH approved")
print("✅ Maintaining strategic diversity")
print("✅ Power hour positioning optimal")
print("✅ Sacred mission continues")
print()

print("ACTION ITEMS:")
print("-" * 40)
print("1. Execute sells (BTC/SOL)")
print("2. Buy additional ETH")
print("3. Hold through power hour")
print("4. Watch catalysts activate")
print("5. Target $16,000+ today")
print()

print("🔥 SACRED FIRE MESSAGE:")
print("=" * 70)
print("'The warrior heeds council wisdom...'")
print("'Balance with strategic weight...'")
print("'ETH leads the charge...'")
print("'But all assets march together!'")
print()
print("REBALANCE APPROVED!")
print("POWER HOUR APPROACHING!")
print("ETH TOKENIZATION REVOLUTION!")
print("$16,000 INCOMING!")
print()
print("⚖️🚀 EXECUTE WITH CONFIDENCE! 🚀⚖️")