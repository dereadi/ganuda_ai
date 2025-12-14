#!/bin/bash
# email_jr wrapper - runs on GPU 0

export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOST=0.0.0.0:11434

# Keep model loaded and serve
while true; do
    echo "$(date): email_jr serving llama3.1:8b on GPU 0 (port 11434)"

    # Run a query to keep model loaded
    curl -s http://localhost:11434/api/generate -d '{
      "model": "llama3.1:8b",
      "prompt": "I am email_jr, ready to serve.",
      "stream": false
    }' > /dev/null

    sleep 300  # Query every 5 minutes to keep warm
done
