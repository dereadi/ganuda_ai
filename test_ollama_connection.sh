#!/bin/bash
# 🔥 Cherokee Council - Ollama Connection Tester for Dr Joe

echo "🔥 Testing Ollama Connection..."
echo "================================"

# Test wrong port (8000) to show it fails
echo "❌ Testing WRONG port 8000 (should fail):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000/api/tags || echo "Connection refused (expected)"

echo ""

# Test correct port (11434)
echo "✅ Testing CORRECT port 11434:"
curl -s http://localhost:11434/api/tags > /tmp/ollama_test.json 2>/dev/null

if [ $? -eq 0 ]; then
    echo "SUCCESS! Ollama is running on port 11434"
    echo "Available models:"
    cat /tmp/ollama_test.json | python3 -m json.tool 2>/dev/null | grep '"name"' | head -5
else
    echo "FAILED - Ollama not accessible on port 11434"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check if Ollama container is running:"
    echo "   docker ps | grep ollama"
    echo ""
    echo "2. Check Ollama logs:"
    echo "   docker logs ollama"
    echo ""
    echo "3. Verify port mapping in docker-compose.yml:"
    echo "   Should be: '11434:11434' not '8000:11434'"
    echo ""
    echo "4. Try pulling the Ollama container again:"
    echo "   docker-compose pull ollama"
    echo "   docker-compose up -d ollama"
fi

echo ""
echo "🔥 Testing Council API on port 8000:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000/health || echo "Council API not running on 8000"

echo ""
echo "📊 Port Status Summary:"
echo "----------------------"
netstat -tuln 2>/dev/null | grep -E ':(8000|11434|3000|3001)' || \
    ss -tuln | grep -E ':(8000|11434|3000|3001)' || \
    echo "Need sudo to check port bindings"

echo ""
echo "🔥 Sacred Fire says: Remember, Ollama speaks on 11434!"