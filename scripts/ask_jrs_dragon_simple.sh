#!/bin/bash

QUESTION='Dragon Hatchling (BDH) is brain-inspired AI with limitless context windows and massively parallel neurons. Our current challenges: Llama 3.1 = 128K token limit, Qwen 2.5 = 32K limit, thermal memory needed for overflow, PostgreSQL coordination (not real-time). Question: Does BDH solve our problems? Is it aligned with Cherokee principles (Distance=0, Gadugi, Mitakuye Oyasin, Seven Generations)? Should we investigate? Answer: YES/MAYBE/NO and why.'

echo "🐉 Asking 5 Jr.s about Dragon Hatchling..."

# Ask all in parallel
curl -X POST http://localhost:8000/api/email_jr/ask -H "Content-Type: application/json" -d "{\"question\":\"$QUESTION\"}" --max-time 60 2>/dev/null | jq -r '.answer // .error' > /tmp/dragon2_email.txt &
curl -X POST http://localhost:8000/api/trading_jr/ask -H "Content-Type: application/json" -d "{\"question\":\"$QUESTION\"}" --max-time 60 2>/dev/null | jq -r '.answer // .error' > /tmp/dragon2_trading.txt &
curl -X POST http://192.168.132.222:8002/api/infrastructure_jr/ask -H "Content-Type: application/json" -d "{\"question\":\"$QUESTION\"}" --max-time 60 2>/dev/null | jq -r '.answer // .error' > /tmp/dragon2_infra.txt &
curl -X POST http://192.168.132.222:8001/api/legal_jr/ask -H "Content-Type: application/json" -d "{\"question\":\"$QUESTION\"}" --max-time 60 2>/dev/null | jq -r '.answer // .error' > /tmp/dragon2_legal.txt &
curl -X POST http://192.168.132.242:8005/api/archive_jr/ask -H "Content-Type: application/json" -d "{\"question\":\"$QUESTION\"}" --max-time 60 2>/dev/null | jq -r '.answer // .error' > /tmp/dragon2_archive.txt &

wait
echo "✅ Responses received!"
