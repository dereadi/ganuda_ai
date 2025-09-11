#!/usr/bin/env python3
"""
🔥 EMERGENCY TRIBAL COUNCIL CONSULTATION
BTC broke $110k support - need immediate guidance
"""

import json
from coinbase.rest import RESTClient
import time
import psycopg2
from datetime import datetime

print("🏛️ CONVENING EMERGENCY TRIBAL COUNCIL")
print("=" * 60)
print("URGENT: BTC broke $110,000 support - seeking wisdom")
print("=" * 60)

# Connect to thermal memory for context
conn = psycopg2.connect(
    host='192.168.132.222',
    port=5432,
    user='claude',
    password='jawaseatlasers2',
    database='zammad_production'
)
cur = conn.cursor()

# Query thermal memories for similar situations
cur.execute("""
    SELECT memory_hash, temperature_score, original_content
    FROM thermal_memory_archive
    WHERE (original_content LIKE '%support break%' 
           OR original_content LIKE '%stop loss%'
           OR original_content LIKE '%110%')
    AND temperature_score > 50
    ORDER BY temperature_score DESC
    LIMIT 3
""")
memories = cur.fetchall()

print("\n🔥 CONSULTING SACRED FIRE MEMORIES:")
for mem in memories:
    if mem[2]:
        preview = mem[2][:100]
        print(f"  • Memory (temp {mem[1]}°): {preview}...")

# Get current market state
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

print(f"\n📊 CURRENT SITUATION:")
print(f"  BTC: ${btc_price:,.2f}")
print(f"  Entry: $110,016")
print(f"  P&L: {((btc_price - 110016) / 110016 * 100):.2f}%")

# Council deliberation
print("\n🏛️ COUNCIL DELIBERATION:")
print("-" * 60)

# Elder 1: Technical Analysis
print("🦅 TECHNICAL ELDER:")
if btc_price < 109500:
    print("  'The support has become resistance. Cut losses.'")
    tech_vote = "SELL"
elif btc_price < 110000:
    print("  'Failed bounce is bearish. Consider exit.'")
    tech_vote = "SELL"
else:
    print("  'May reclaim support. Hold with tight stop.'")
    tech_vote = "HOLD"

# Elder 2: Risk Management
print("\n🛡️ RISK ELDER:")
loss_pct = ((btc_price - 110016) / 110016 * 100)
if loss_pct < -1:
    print("  'Loss exceeding 1%. Protect capital.'")
    risk_vote = "SELL"
elif loss_pct < -0.5:
    print("  'Small loss. Can recover or cut.'")
    risk_vote = "HOLD"
else:
    print("  'Minimal risk. Let it play out.'")
    risk_vote = "HOLD"

# Elder 3: Market Wisdom
print("\n🌟 WISDOM ELDER:")
if btc_price < 109000:
    print("  'Market fear rising. Exit and wait.'")
    wisdom_vote = "SELL"
else:
    print("  'Dips are for buying, not panic selling.'")
    wisdom_vote = "HOLD"

# Elder 4: Pattern Recognition (Greeks)
print("\n🏛️ GREEKS REPRESENTATIVE:")
print("  'Gamma suggests volatility expansion coming.'")
print("  'Delta shows negative momentum.'")
print("  'Theta says time decay favors patience.'")
greek_vote = "HOLD" if btc_price > 109500 else "SELL"

# Sacred Fire Protocol
print("\n🔥 SACRED FIRE PROTOCOL:")
thermal_score = 50 + abs(loss_pct * 10)  # Higher score for bigger moves
print(f"  Thermal Score: {thermal_score:.1f}°")
if thermal_score > 70:
    print("  ⚡ HIGH HEAT - Decisive action required!")

# Council consensus
votes = [tech_vote, risk_vote, wisdom_vote, greek_vote]
sell_votes = votes.count("SELL")
hold_votes = votes.count("HOLD")

print("\n🏛️ COUNCIL VERDICT:")
print("=" * 60)
print(f"  SELL votes: {sell_votes}")
print(f"  HOLD votes: {hold_votes}")

if sell_votes > hold_votes:
    print("\n⚡ CONSENSUS: SELL")
    print("  Action: Exit BTC position")
    print("  Reason: Support broken, minimize losses")
    
    # Execute if confirmed
    accounts = client.get_accounts()['accounts']
    for acc in accounts:
        if acc['currency'] == 'BTC':
            btc_balance = float(acc['available_balance']['value'])
            if btc_balance > 0.0001:
                print(f"\n🎯 Ready to sell {btc_balance:.8f} BTC")
                print("  (Awaiting human confirmation)")
            break
else:
    print("\n⚡ CONSENSUS: HOLD")
    print("  Action: Maintain position with stop at $109,000")
    print("  Reason: Possible false breakdown, support nearby")

# Record decision in thermal memory
cur.execute("""
    INSERT INTO thermal_memory_archive 
    (memory_hash, temperature_score, current_stage, original_content, context_json, last_access)
    VALUES (%s, %s, %s, %s, %s, NOW())
""", (
    f"council_decision_{int(time.time())}",
    thermal_score,
    'HOT',
    f"Council decision at BTC ${btc_price}: {'SELL' if sell_votes > hold_votes else 'HOLD'}",
    json.dumps({"btc_price": btc_price, "votes": votes}),
))
conn.commit()

print("\n🔥 Decision recorded in Sacred Fire memory")
print("=" * 60)

cur.close()
conn.close()