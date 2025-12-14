#!/bin/bash

echo "========================================================================="
echo "🔥 STOPPING OLLAMA SERVICE FOR PHASE 2 REDUX LORA TRAINING"
echo "========================================================================="
echo ""
echo "This will temporarily stop the Cherokee Jrs (Ollama service) to free"
echo "GPU memory for Phase 2 behavioral training."
echo ""
echo "The Jrs will automatically restart when the ollama service is started again."
echo ""
echo "========================================================================="
echo ""

# Stop ollama service
echo "🛑 Stopping ollama.service..."
sudo systemctl stop ollama.service

# Wait for processes to terminate
sleep 5

# Verify GPUs are free
echo ""
echo "📊 Checking GPU memory..."
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader

GPU_PROCS=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | wc -l)

if [ "$GPU_PROCS" -eq 0 ]; then
    echo "✅ GPUs are now free for training!"
    echo ""
    echo "🔥 Launching Phase 2 Redux LoRA training on GPU 0..."

    source /home/dereadi/cherokee_venv/bin/activate && \
    TOKENIZERS_PARALLELISM=false CUDA_VISIBLE_DEVICES=0 \
    nohup python3 /ganuda/scripts/train_phase2_redux_lora.py \
    > /ganuda/cherokee_resonance_training/logs/phase2_redux_lora_training.log 2>&1 &

    TRAINING_PID=$!
    echo "✅ Phase 2 Redux LoRA training started (PID: $TRAINING_PID)"
    echo ""
    echo "📋 Monitor training progress:"
    echo "   tail -f /ganuda/cherokee_resonance_training/logs/phase2_redux_lora_training.log"
    echo ""
    echo "📊 Monitor GPU usage:"
    echo "   nvidia-smi dmon"
    echo ""
    echo "🔄 When training completes (1-2 days), restart Ollama:"
    echo "   sudo systemctl start ollama.service"
    echo ""
else
    echo "❌ GPU processes still running:"
    nvidia-smi --query-compute-apps=pid,name,used_memory --format=csv
    echo ""
    echo "Wait a few more seconds and try again"
fi

echo "========================================================================="
