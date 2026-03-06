#!/bin/bash
# Pi Agent — Cherokee AI Federation wrapper
# Usage: pi-fed [--deepseek] "prompt"
# Default: redfin Qwen-72B. Use --deepseek for bmasass reasoning.

export NVM_DIR="/home/dereadi/.nvm"
source "$NVM_DIR/nvm.sh" 2>/dev/null
nvm use 22 >/dev/null 2>&1

PROVIDER="redfin-vllm"
ARGS=()

for arg in "$@"; do
  if [ "$arg" = "--deepseek" ] || [ "$arg" = "--reason" ]; then
    PROVIDER="bmasass-mlx"
  else
    ARGS+=("$arg")
  fi
done

exec pi --provider "$PROVIDER" \
  --append-system-prompt /ganuda/config/pi/federation-system-prompt.md \
  "${ARGS[@]}"
