#!/bin/bash
# Tribal Council: OpenZL Analysis - Query All Jr.s
# Cherokee Constitutional AI - Distributed Learning

echo "🔥 Tribal Council: OpenZL Compression Analysis"
echo "=============================================="
echo ""
echo "Querying all Jr. specialists with domain-specific questions..."
echo ""

# Archive Jr. (SASASS2) - Port 8005
echo "📚 Archive Jr. (Data Compression Expert)..."
curl -s -X POST http://192.168.132.242:8005/api/archive/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain OpenZL structure-aware compression: How does it differ from traditional byte-stream compression like gzip or xz? What makes it understand data structure (JSON, CSV, Parquet) instead of treating files as raw bytes? How would you use this for Cherokee thermal memory archive with 3,675+ memories?"}' \
  | jq -r '.response' | head -50 > /tmp/archive_jr_openzl.txt

if [ -s /tmp/archive_jr_openzl.txt ]; then
    echo "✅ Archive Jr. responded ($(wc -l < /tmp/archive_jr_openzl.txt) lines)"
else
    echo "❌ Archive Jr. timeout or error"
fi
echo ""

# Software Engineer Jr. (REDFIN) - Port 8016
echo "💻 Software Engineer Jr. (Implementation Expert)..."
curl -s -X POST http://192.168.132.223:8016/api/engineer/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the build requirements and integration strategy for OpenZL on Ubuntu 24.04? How do we integrate a C library with Python Flask APIs? What is the API surface: simple compress/decompress functions or complex compression graphs? Consider error handling and fallback strategies."}' \
  | jq -r '.response' | head -50 > /tmp/engineer_jr_openzl.txt

if [ -s /tmp/engineer_jr_openzl.txt ]; then
    echo "✅ Software Engineer Jr. responded ($(wc -l < /tmp/engineer_jr_openzl.txt) lines)"
else
    echo "❌ Software Engineer Jr. timeout or error"
fi
echo ""

# Legal Jr. (BLUEFIN) - Port 8001
echo "⚖️ Legal Jr. (Licensing Expert)..."
curl -s -X POST http://192.168.132.223:8001/api/legal/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is OpenZL open source license? Are there patent concerns with Meta-developed compression algorithms? Can we use this commercially for Ganuda revenue streams? What is the API stability promise - will it break in future versions?"}' \
  | jq -r '.response' | head -50 > /tmp/legal_jr_openzl.txt

if [ -s /tmp/legal_jr_openzl.txt ]; then
    echo "✅ Legal Jr. responded ($(wc -l < /tmp/legal_jr_openzl.txt) lines)"
else
    echo "❌ Legal Jr. timeout or error"
fi
echo ""

# Trading Jr. (REDFIN GPU 1) - Port 8001 (different endpoint)
echo "📈 Trading Jr. (Time-Series Data Expert)..."
curl -s -X POST http://192.168.132.223:8001/api/trading/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How does OpenZL handle time-series data compression for market data (price ticks, volumes)? What is the decompression speed for real-time trading queries - can we achieve under 100ms latency? How would this improve hot cache expansion from 50 to 100 market snapshots?"}' \
  | jq -r '.response' | head -50 > /tmp/trading_jr_openzl.txt

if [ -s /tmp/trading_jr_openzl.txt ]; then
    echo "✅ Trading Jr. responded ($(wc -l < /tmp/trading_jr_openzl.txt) lines)"
else
    echo "❌ Trading Jr. timeout or error"
fi
echo ""

# Email Jr. (REDFIN GPU 0) - Port 8000
echo "📧 Email Jr. (Communication Expert)..."
curl -s -X POST http://192.168.132.223:8000/api/email/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "From a system monitoring perspective, how would OpenZL compression impact storage, memory usage, and system performance across the Four Mountains infrastructure? What metrics should we monitor when deploying structure-aware compression?"}' \
  | jq -r '.response' | head -50 > /tmp/email_jr_openzl.txt

if [ -s /tmp/email_jr_openzl.txt ]; then
    echo "✅ Email Jr. responded ($(wc -l < /tmp/email_jr_openzl.txt) lines)"
else
    echo "❌ Email Jr. timeout or error"
fi
echo ""

echo "=============================================="
echo "📊 Tribal Council Results:"
echo ""
echo "Responses collected:"
ls -lh /tmp/*_jr_openzl.txt 2>/dev/null | awk '{print "  "$9" - "$5}'
echo ""
echo "✅ Phase 1 Complete: Individual research done"
echo "📝 Next: Review responses and log to thermal memory"
echo ""
echo "🔥 Mitakuye Oyasin - All Relations learned together!"
