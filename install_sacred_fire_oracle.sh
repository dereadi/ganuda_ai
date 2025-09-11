#!/bin/bash

echo "🔥 INSTALLING SACRED FIRE ORACLE (SFO) FOR OLLAMA"
echo "=================================================="

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "⚠️ Ollama not found. Installing Ollama first..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Create the model from the Modelfile
echo "📦 Creating Sacred Fire Oracle model..."
ollama create sacred-fire-oracle -f /home/dereadi/scripts/claude/sacred_fire_oracle_modelfile

# Test the model
echo "🧪 Testing Sacred Fire Oracle..."
ollama run sacred-fire-oracle "What do you see in the market today?"

echo ""
echo "✅ Sacred Fire Oracle installed!"
echo ""
echo "🔥 Usage:"
echo "   ollama run sacred-fire-oracle"
echo ""
echo "💡 Integration example:"
echo "   curl http://localhost:11434/api/generate -d '{"
echo '     "model": "sacred-fire-oracle",'
echo '     "prompt": "Should I buy BTC at 117,000?"'
echo "   }'"
echo ""
echo "The Sacred Fire burns eternal. Mitakuye Oyasin 🦅"