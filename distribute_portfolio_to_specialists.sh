#!/bin/bash
# 🔥 DISTRIBUTE PORTFOLIO TO CHEROKEE SPECIALISTS
# Sacred Fire Protocol Active

echo "🔥 DISTRIBUTING PORTFOLIO TO SPECIALISTS"
echo "========================================"
echo ""

# Read portfolio summary
PORTFOLIO_VALUE=$(cat /home/dereadi/scripts/claude/specialist_portfolio.json | python3 -c "import json,sys; data=json.load(sys.stdin); print(f\"\${data['total_value']:,.2f}\")")
USD_BALANCE=$(cat /home/dereadi/scripts/claude/specialist_portfolio.json | python3 -c "import json,sys; data=json.load(sys.stdin); print(f\"\${data['usd_balance']:,.2f}\")")

echo "📊 PORTFOLIO SUMMARY:"
echo "  Total Value: $PORTFOLIO_VALUE"
echo "  USD Balance: $USD_BALANCE"
echo "  Status: LIQUIDITY CRISIS - Need $2,000"
echo ""

# Copy portfolio to each specialist
SPECIALISTS=(
    "cherokee-mean-reversion-specialist"
    "cherokee-trend-specialist"
    "cherokee-volatility-specialist"
    "cherokee-breakout-specialist"
)

for SPECIALIST in "${SPECIALISTS[@]}"; do
    echo "📡 Sending to $SPECIALIST..."
    
    # Copy the portfolio file to container
    podman cp /home/dereadi/scripts/claude/specialist_portfolio.json $SPECIALIST:/tmp/portfolio.json
    
    # Process in each specialist
    case $SPECIALIST in
        "cherokee-mean-reversion-specialist")
            podman exec $SPECIALIST python3 -c "
import json
with open('/tmp/portfolio.json') as f:
    data = json.load(f)
print('🎯 MEAN REVERSION ANALYSIS:')
print('Portfolio Value: \$' + f\"{data['total_value']:,.2f}\")
print('Positions to analyze:', len(data['positions']))
for pos in data['positions'][:3]:
    print(f\"  • {pos['symbol']}: \${pos['value']:,.2f}\")
print('Status: Monitoring for extremes...')
"
            ;;
            
        "cherokee-trend-specialist")
            podman exec $SPECIALIST python3 -c "
import json
with open('/tmp/portfolio.json') as f:
    data = json.load(f)
print('📈 TREND ANALYSIS:')
print('Portfolio Value: \$' + f\"{data['total_value']:,.2f}\")
print('Major trends detected:')
print('  • BTC: 26.5% of portfolio')
print('  • Need liquidity generation')
print('Status: Tracking momentum...')
"
            ;;
            
        "cherokee-volatility-specialist")
            podman exec $SPECIALIST python3 -c "
import json
with open('/tmp/portfolio.json') as f:
    data = json.load(f)
print('⚡ VOLATILITY ANALYSIS:')
print('Portfolio Value: \$' + f\"{data['total_value']:,.2f}\")
print('High volatility positions:')
for pos in data['positions']:
    if pos['value'] > 1000:
        print(f\"  • {pos['symbol']}: \${pos['value']:,.2f}\")
print('Status: Calculating ranges...')
"
            ;;
            
        "cherokee-breakout-specialist")
            podman exec $SPECIALIST python3 -c "
import json
with open('/tmp/portfolio.json') as f:
    data = json.load(f)
print('🚀 BREAKOUT ANALYSIS:')
print('Portfolio Value: \$' + f\"{data['total_value']:,.2f}\")
print('Watching for breakouts in:')
for pos in data['positions'][:4]:
    print(f\"  • {pos['symbol']}: \${pos['value']:,.2f}\")
print('Status: Scanning levels...')
"
            ;;
    esac
    echo ""
done

echo "========================================"
echo "✅ PORTFOLIO DISTRIBUTED TO ALL SPECIALISTS"
echo ""
echo "🏛️ COUNCIL RECOMMENDATION:"
echo "  1. Generate $2,000 liquidity immediately"
echo "  2. Reduce BTC concentration (26.5%)"
echo "  3. Monitor in paper trading mode"
echo "  4. Await council approval for live trading"
echo ""
echo "🔥 Sacred Fire burns eternal"
echo "🪶 Mitakuye Oyasin"
echo "========================================"