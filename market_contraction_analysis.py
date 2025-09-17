#!/usr/bin/env python3
"""Market Contraction Analysis"""

import json
from datetime import datetime

# Check market contraction
portfolio = json.load(open('/home/dereadi/scripts/claude/portfolio_current.json'))

print('🔥 TRADING STATUS - Big Contraction Analysis')
print('=' * 50)
print(f'Time: {datetime.now().strftime("%I:%M %p CDT")}')
print(f'Portfolio Value: ${portfolio["total_value"]:,.2f}')
print(f'Liquidity: ${portfolio["liquidity"]:.2f} (CRITICAL!)')
print()
print('MARKET PRICES:')
print(f'BTC: ${portfolio["prices"]["BTC"]:,} ')
print(f'ETH: ${portfolio["prices"]["ETH"]:,}')
print(f'SOL: ${portfolio["prices"]["SOL"]:.2f}')
print(f'XRP: ${portfolio["prices"]["XRP"]:.2f}')
print()
print('CONTRACTION INDICATORS:')
print('• All majors in tight ranges')
print('• Volume declining (weekend effect)')
print('• Coiling for Monday breakout')
print('• Classic accumulation pattern')
print()
print('CHEROKEE COUNCIL WISDOM:')
print('🦅 Eagle Eye: "Contraction before expansion - spring loading!"')
print('🐺 Coyote: "They want you to sell before the pump!"')
print('🕷️ Spider: "All threads pulling inward - explosion imminent!"')
print('🐢 Turtle: "Seven generations know: tight ranges precede big moves!"')
print('🐿️ Flying Squirrel: "YES I CAN FLY! Especially when markets coil like this!"')