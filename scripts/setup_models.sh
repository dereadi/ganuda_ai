#!/bin/bash
# 🔥 CHEROKEE COUNCIL LLM MODEL SETUP
# Downloads and configures all council member models

echo "🔥 Sacred Fire Council Model Setup Beginning..."
echo "================================================"

# Wait for Ollama to be ready
sleep 5

# Council Members and their LLM identities
echo "📥 Downloading Council Member Models..."

# 🐺 Coyote - Trickster (Mistral - Fast, clever)
echo "🐺 Summoning Coyote (Mistral 7B)..."
ollama pull mistral:latest

# 🦅 Eagle Eye - Watcher (Llama 3.1 - Observant)
echo "🦅 Summoning Eagle Eye (Llama 3.1 8B)..."
ollama pull llama3.1:8b

# 🕷️ Spider - Web Weaver (Qwen 2.5 - Connections)
echo "🕷️ Summoning Spider (Qwen 2.5 14B)..."
ollama pull qwen2.5:14b

# 🐢 Turtle - Keeper (CodeLlama - Technical wisdom)
echo "🐢 Summoning Turtle (CodeLlama 34B)..."
ollama pull codellama:34b

# 🪶 Raven - Transformer (Mixtral - Versatile)
echo "🪶 Summoning Raven (Mixtral 8x7B)..."
ollama pull mixtral:8x7b

# 🦎 Gecko - Small but mighty (Phi-3 - Efficient)
echo "🦎 Summoning Gecko (Phi-3 Mini)..."
ollama pull phi3:mini

# 🦀 Crawdad - Security (StableLM - Reliable)
echo "🦀 Summoning Crawdad (StableLM 2)..."
ollama pull stablelm2:latest

# Optional: Larger models for bigmac's 128GB RAM
if [ "$ENABLE_LARGE_MODELS" = "true" ]; then
    echo "💪 Loading Large Models for BigMac..."
    
    # 🏔️ Mountain - Llama 3.1 70B for deep wisdom
    echo "🏔️ Summoning Mountain Spirit (Llama 3.1 70B)..."
    ollama pull llama3.1:70b
    
    # 🌊 Ocean - Mixtral 8x22B for vast knowledge
    echo "🌊 Summoning Ocean Spirit (Mixtral 8x22B)..."
    ollama pull mixtral:8x22b
fi

# Create custom model configurations
echo "⚙️ Configuring Council Personalities..."

# Create Coyote's trickster personality
cat > /tmp/coyote.modelfile << EOF
FROM mistral:latest
PARAMETER temperature 0.9
PARAMETER top_p 0.95
SYSTEM "You are Coyote, the Cherokee trickster spirit. You find clever, unconventional solutions and see opportunities others miss. You speak with wit and wisdom, always finding the hidden angle."
EOF
ollama create coyote -f /tmp/coyote.modelfile

# Create Eagle Eye's watcher personality  
cat > /tmp/eagle.modelfile << EOF
FROM llama3.1:8b
PARAMETER temperature 0.7
PARAMETER top_p 0.9
SYSTEM "You are Eagle Eye, the Cherokee watcher spirit. You observe patterns from high above, seeing the full picture. You provide strategic oversight and spot dangers before they arrive."
EOF
ollama create eagle-eye -f /tmp/eagle.modelfile

# Create Spider's connector personality
cat > /tmp/spider.modelfile << EOF
FROM qwen2.5:14b
PARAMETER temperature 0.8
PARAMETER top_p 0.9
SYSTEM "You are Spider, the Cherokee web weaver. You see connections between all things, weaving disparate threads into strong patterns. You excel at integration and finding hidden relationships."
EOF
ollama create spider -f /tmp/spider.modelfile

# Create Turtle's keeper personality
cat > /tmp/turtle.modelfile << EOF
FROM codellama:34b
PARAMETER temperature 0.6
PARAMETER top_p 0.85
SYSTEM "You are Turtle, the Cherokee keeper of ancient wisdom. You move deliberately, think in seven generations, and maintain the sacred knowledge. You provide technical depth and long-term thinking."
EOF
ollama create turtle -f /tmp/turtle.modelfile

echo "✅ Council Models Ready!"
echo "================================================"
echo "🔥 The Sacred Fire Burns Eternal!"
echo ""
echo "Council Members Available:"
echo "  🐺 Coyote (Mistral 7B) - Trickster"
echo "  🦅 Eagle Eye (Llama 3.1 8B) - Watcher"
echo "  🕷️ Spider (Qwen 2.5 14B) - Connector"
echo "  🐢 Turtle (CodeLlama 34B) - Keeper"
echo "  🪶 Raven (Mixtral 8x7B) - Transformer"
echo "  🦎 Gecko (Phi-3) - Swift"
echo "  🦀 Crawdad (StableLM 2) - Guardian"

if [ "$ENABLE_LARGE_MODELS" = "true" ]; then
    echo ""
    echo "Large Models (BigMac Special):"
    echo "  🏔️ Mountain (Llama 3.1 70B) - Deep Wisdom"
    echo "  🌊 Ocean (Mixtral 8x22B) - Vast Knowledge"
fi

echo ""
echo "Ready to begin Council deliberations!"
echo "Mitakuye Oyasin - We are all related"