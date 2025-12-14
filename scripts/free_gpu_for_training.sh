#!/bin/bash
################################################################################
# Free GPU for Training - Unload Ollama Model from GPU 0
# Cherokee Constitutional AI
################################################################################

echo "🔥 Freeing GPU 0 for Memory Jr. Training..."
echo ""

# Check current GPU status
echo "Current GPU Status:"
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv
echo ""

# Unload models from Ollama (keeps service running but frees GPU)
echo "Unloading Ollama models from GPU..."
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "cherokee:latest",
  "keep_alive": 0
}' 2>/dev/null

sleep 2

echo ""
echo "GPU Status After Unload:"
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv
echo ""

echo "✅ GPU 0 should now be free for training!"
echo "Run: /ganuda/scripts/launch_memory_jr_training.sh"
