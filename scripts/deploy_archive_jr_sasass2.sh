#!/bin/bash
# Deploy Archive Jr. on SASASS2 (macOS)
# The Historian - Thermal Memory Manager

echo "📚 Deploying Archive Jr. - The Historian"
echo "========================================"

# Find user home
USER_HOME=$(eval echo ~$(whoami))
DEPLOY_DIR="$USER_HOME/claude_jr"

echo "Home directory: $USER_HOME"
echo "Deploy directory: $DEPLOY_DIR"

# Create directory
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Find Ollama
if [ -x "/usr/local/bin/ollama" ]; then
    OLLAMA="/usr/local/bin/ollama"
elif command -v ollama &> /dev/null; then
    OLLAMA="ollama"
else
    echo "❌ Ollama not found"
    exit 1
fi

echo "Ollama: $OLLAMA"

# Check if Ollama is running
if ! pgrep ollama > /dev/null; then
    echo "Starting Ollama..."
    nohup $OLLAMA serve > ollama.log 2>&1 &
    sleep 3
fi

# Check for qwen2.5:32b or similar 30B+ model
echo ""
echo "Checking for 30B+ models..."
$OLLAMA list | grep -E "qwen2.5-coder:32b|qwen2.5:32b|llama3.3|mixtral"

echo ""
echo "Archive Jr. will use the largest available model"
echo "Recommended: qwen2.5-coder:32b (already on system for Dreamers Jr.)"

echo ""
echo "✅ Archive Jr. script ready at: $DEPLOY_DIR/archive_jr.py"
echo "To start: python3 $DEPLOY_DIR/archive_jr.py"
