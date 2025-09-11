#!/usr/bin/env python3
"""
ETH POSITION CHECK - TESTING DOWN
==================================
"""

from datetime import datetime

print("⚠️ ETH TESTING DOWN - POSITION CHECK")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Your ETH position
eth_amount = 0.44080584
current_price = 4355.99  # From last check
test_price = 4320  # Testing down level
position_value = eth_amount * test_price

print("📊 YOUR ETH POSITION:")
print("-" * 40)
print(f"Holdings: {eth_amount:.8f} ETH")
print(f"Last price: ${current_price:.2f}")
print(f"Testing: ${test_price:.2f} 📉")
print(f"Position value: ${position_value:.2f}")
print()

# Support levels
print("🛡️ KEY SUPPORT LEVELS:")
print("-" * 40)
print("• $4,300 - Immediate support (testing now)")
print("• $4,250 - Strong support (50-day MA)")
print("• $4,200 - Critical support (must hold)")
print("• $4,150 - Panic zone")
print()

# What's happening
print("📈 MARKET CONTEXT:")
print("-" * 40)
print("• BTC flat at $108k = Money rotating")
print("• ETH testing support while BTC consolidates")
print("• $320B monthly volume still bullish")
print("• ETH/BTC ratio improving overall")
print()

# Action plan
print("🎯 ACTION PLAN:")
print("-" * 40)
if test_price > 4250:
    print("✅ HOLD - Normal pullback")
    print("• This is healthy consolidation")
    print("• Strong support at $4,250")
    print("• Consider adding if drops to $4,200")
else:
    print("⚠️ WATCH CLOSELY")
    print("• Breaking below $4,250 is concerning")
    print("• May test $4,200 critical support")
    print("• Have stop loss at $4,150")

print()

# Liquidity check for buying opportunity
print("💰 LIQUIDITY FOR DIP BUYING:")
print("-" * 40)
cash_available = 500
eth_buy_amounts = [
    {"price": 4300, "amount": 100, "eth_get": 100/4300},
    {"price": 4250, "amount": 150, "eth_get": 150/4250},
    {"price": 4200, "amount": 200, "eth_get": 200/4200},
]

print(f"Cash available: ${cash_available}")
print()
print("Potential buys:")
for buy in eth_buy_amounts:
    print(f"• At ${buy['price']}: Buy ${buy['amount']} = {buy['eth_get']:.5f} ETH")

print()

# Overall portfolio impact
print("📊 PORTFOLIO IMPACT:")
print("-" * 40)
portfolio_total = 12774
eth_drop = (current_price - test_price) * eth_amount
new_portfolio = portfolio_total - eth_drop

print(f"Current portfolio: ${portfolio_total:.2f}")
print(f"ETH impact: -${eth_drop:.2f}")
print(f"New total: ${new_portfolio:.2f}")
print(f"Still up: {((new_portfolio - 10229) / 10229 * 100):.1f}% overall")
print()

print("=" * 60)
print("🔥 VERDICT: NORMAL PULLBACK - HOLD STRONG!")
print("Have $500 ready to buy the dip if needed!")
print("=" * 60)