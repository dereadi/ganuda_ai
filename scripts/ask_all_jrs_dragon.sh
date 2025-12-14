#!/bin/bash

# Ask all 5 working Jr.s about Dragon Hatchling
QUESTION="Please read this Dragon Hatchling assessment and provide your thoughts: $(cat /tmp/dragon_hatchling_assessment_phase2.md)"

echo "🐉 Asking 5 Jr.s about Dragon Hatchling (Brain-inspired AI)..."
echo ""

# Email Jr. (REDFIN port 8000)
echo "📧 Email Jr. (REDFIN)..."
curl -X POST http://localhost:8000/api/email_jr/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"$QUESTION\"}" \
  --max-time 60 2>/dev/null > /tmp/dragon_email_jr.json &

# Trading Jr. (REDFIN port 8000)
echo "📈 Trading Jr. (REDFIN)..."
curl -X POST http://localhost:8000/api/trading_jr/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"$QUESTION\"}" \
  --max-time 60 2>/dev/null > /tmp/dragon_trading_jr.json &

# Infrastructure Jr. (BLUEFIN port 8002)
echo "🏗️ Infrastructure Jr. (BLUEFIN)..."
curl -X POST http://192.168.132.222:8002/api/infrastructure_jr/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"$QUESTION\"}" \
  --max-time 60 2>/dev/null > /tmp/dragon_infra_jr.json &

# Legal Jr. (BLUEFIN port 8001)
echo "⚖️ Legal Jr. (BLUEFIN)..."
curl -X POST http://192.168.132.222:8001/api/legal_jr/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"$QUESTION\"}" \
  --max-time 60 2>/dev/null > /tmp/dragon_legal_jr.json &

# Archive Jr. (SASASS2 port 8005)
echo "📚 Archive Jr. (SASASS2)..."
curl -X POST http://192.168.132.242:8005/api/archive_jr/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"$QUESTION\"}" \
  --max-time 60 2>/dev/null > /tmp/dragon_archive_jr.json &

echo ""
echo "⏳ Waiting for all Jr.s to respond (max 60 seconds)..."
wait

echo ""
echo "✅ All responses received!"
echo ""

# Show response counts
for jr in email trading infra legal archive; do
  file="/tmp/dragon_${jr}_jr.json"
  if [ -f "$file" ]; then
    chars=$(cat "$file" | jq -r '.answer // .error' 2>/dev/null | wc -c)
    echo "$jr Jr.: $chars chars"
  fi
done
