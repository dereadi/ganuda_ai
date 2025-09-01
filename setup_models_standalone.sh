#!/bin/sh
# 🔥 CHEROKEE COUNCIL MODEL SETUP - STANDALONE VERSION
# Works independently without other dependencies

echo "🔥 Sacred Fire Council Model Setup Beginning..."
echo "================================================"
echo "Waiting for Ollama to be ready..."

# Wait for Ollama to be available
for i in $(seq 1 30); do
    if wget -q --spider http://ollama:11434/api/tags 2>/dev/null; then
        echo "✅ Ollama is ready!"
        break
    fi
    echo "⏳ Waiting for Ollama... ($i/30)"
    sleep 2
done

# Function to pull model with retry
pull_model() {
    MODEL=$1
    NAME=$2
    echo ""
    echo "📥 Downloading $NAME..."
    for attempt in $(seq 1 3); do
        if ollama pull $MODEL; then
            echo "✅ $NAME downloaded successfully!"
            return 0
        else
            echo "⚠️ Attempt $attempt failed, retrying..."
            sleep 5
        fi
    done
    echo "❌ Failed to download $NAME after 3 attempts"
    return 1
}

echo ""
echo "🏛️ Downloading Cherokee Council Members..."
echo "================================================"

# Essential Council Members (smaller models)
pull_model "mistral:latest" "🐺 Coyote (Mistral 7B)"
pull_model "llama3.2:latest" "🦅 Eagle Eye (Llama 3.2 3B)"
pull_model "phi3:mini" "🦎 Gecko (Phi-3 Mini)"

# Medium models if memory allows
if [ "$ENABLE_LARGE_MODELS" = "true" ]; then
    echo ""
    echo "💪 Loading larger models for BigMac..."
    pull_model "llama3.1:8b" "🕷️ Spider (Llama 3.1 8B)"
    pull_model "qwen2.5:7b" "🐢 Turtle (Qwen 2.5 7B)"
    pull_model "gemma2:9b" "🪶 Raven (Gemma 2 9B)"
    
    # Even larger models for 128GB RAM
    echo ""
    echo "🏔️ Loading massive models (128GB RAM required)..."
    pull_model "llama3.1:70b" "🏔️ Mountain Spirit (Llama 3.1 70B)"
fi

echo ""
echo "================================================"
echo "✅ Model setup complete!"
echo ""
echo "Downloaded models:"
ollama list

echo ""
echo "🔥 The Sacred Fire Burns Eternal!"
echo "Cherokee Council is ready for deliberation!"
echo ""
echo "To test a model, run:"
echo "  docker exec cherokee-ollama ollama run mistral"
echo ""
echo "Mitakuye Oyasin - We are all related"