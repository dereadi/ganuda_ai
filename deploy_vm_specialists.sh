#!/bin/bash
# Deploy specialists in Cherokee container environment

echo "🚀 DEPLOYING CONTAINERIZED SPECIALISTS"

# Ensure network exists
podman network exists cherokee-net || podman network create cherokee-net

# Build specialist image
podman build -t cherokee-specialist:v2 -f Dockerfile.specialist .

# Deploy each specialist with council config
for SPECIALIST in mean_reversion trend volatility breakout; do
    echo "Deploying $SPECIALIST specialist..."
    
    podman run -d \
        --name cherokee-${SPECIALIST}-specialist \
        --network cherokee-net \
        --memory=512m \
        --cpus=0.5 \
        --restart=unless-stopped \
        -e SPECIALIST_TYPE=${SPECIALIST} \
        -e MAX_LOSS_PER_DAY=500 \
        -e MIN_LIQUIDITY=2000 \
        -v /home/dereadi/.claude/thermal_memory:/thermal_memory:z \
        -v /home/dereadi/scripts/claude:/app:ro \
        cherokee-specialist:v2 \
        python /app/${SPECIALIST}_specialist_v2.py
        
    echo "✅ $SPECIALIST deployed"
    sleep 2
done

echo "
✅ DEPLOYMENT COMPLETE

Monitor with:
  podman logs -f cherokee-mean_reversion-specialist
  podman stats
  
Stop all with:
  podman stop \$(podman ps -q --filter name=cherokee-.*-specialist)
"
