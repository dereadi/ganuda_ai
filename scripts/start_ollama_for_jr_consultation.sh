#!/bin/bash
echo "🔄 Starting Ollama service for Cherokee Jr consultation..."
sudo systemctl start ollama.service
sleep 8
echo "✅ Checking Ollama status..."
systemctl status ollama.service --no-pager | head -5
echo ""
echo "📊 Waiting for Jrs to load models..."
sleep 10
echo "✅ Cherokee Jrs should be ready for consultation!"
echo ""
echo "Run this command when ready:"
echo "  curl -s http://localhost:11434/api/tags | python3 -m json.tool"
