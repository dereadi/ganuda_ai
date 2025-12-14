#!/bin/bash
# trading_jr wrapper - runs on GPU 1

export CUDA_VISIBLE_DEVICES=1
export OLLAMA_HOST=0.0.0.0:11435

# Keep model loaded and serve
while true; do
    echo "$(date): trading_jr serving qwen2.5:14b on GPU 1 (port 11435)"

    # Run a query to keep model loaded
    curl -s http://localhost:11435/api/generate -d '{
      "model": "qwen2.5:14b",
      "prompt": "I am trading_jr, ready to serve.",
      "stream": false
    }' > /dev/null

    sleep 300  # Query every 5 minutes to keep warm
done
