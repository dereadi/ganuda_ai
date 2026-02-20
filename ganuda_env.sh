#!/bin/bash
source /ganuda/config/secrets.env
# 🔥 GANUDA ENVIRONMENT VARIABLES

export PATHFINDER_HOME="/ganuda/pathfinder"
export GANUDA_HOME="/ganuda"
export THERMAL_MEMORY_HOST="192.168.132.222"
export THERMAL_MEMORY_DB="zammad_production"
export THERMAL_MEMORY_USER="claude"
export THERMAL_MEMORY_PASS="$CHEROKEE_DB_PASS"
export VLLM_MODEL="/ganuda/models/qwen2.5-72b-instruct-awq"
export SACRED_FIRE="ETERNAL"

echo "🔥 Ganuda environment loaded!"
echo "  GANUDA_HOME: $GANUDA_HOME"
echo "  PATHFINDER_HOME: $PATHFINDER_HOME"
echo "  Sacred Fire: BURNING ETERNAL on dedicated storage!"
