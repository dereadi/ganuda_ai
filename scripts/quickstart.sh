#!/bin/bash
# Ganuda Quickstart Script
# Works with Docker or Podman
# Usage: ./scripts/quickstart.sh

set -e

echo "🏔️  Ganuda Gateway Quickstart"
echo "=============================="
echo ""

# Detect container runtime
if command -v podman &> /dev/null; then
    RUNTIME="podman"
    COMPOSE="podman-compose"
elif command -v docker &> /dev/null; then
    RUNTIME="docker"
    COMPOSE="docker-compose"
else
    echo "❌ Neither Docker nor Podman found. Please install one first."
    exit 1
fi

echo "✓ Using: $RUNTIME"

# Check compose
if ! command -v $COMPOSE &> /dev/null; then
    echo "❌ $COMPOSE not found. Please install it."
    exit 1
fi

# Create config if not exists
if [ ! -f "config/ganuda.yaml" ]; then
    echo "📄 Creating config/ganuda.yaml from example..."
    cp config/ganuda.yaml.example config/ganuda.yaml
    echo "   ⚠️  Edit config/ganuda.yaml to set your inference backend"
fi

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "📄 Creating .env from example..."
    cp .env.example .env
    
    # Generate random password
    RANDOM_PASS=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/your-secure-password-here/$RANDOM_PASS/" .env
    else
        sed -i "s/your-secure-password-here/$RANDOM_PASS/" .env
    fi
    echo "   ✓ Generated random database password"
fi

echo ""
echo "🚀 Starting Ganuda Gateway..."
$COMPOSE up -d

echo ""
echo "⏳ Waiting for services..."
sleep 10

# Check health
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        echo ""
        echo "✅ Ganuda Gateway is running!"
        echo ""
        echo "   API Endpoint: http://localhost:8080"
        echo "   Health Check: http://localhost:8080/health"
        echo ""
        echo "   Example API call:"
        echo '   curl http://localhost:8080/v1/chat/completions \'
        echo '     -H "Content-Type: application/json" \'
        echo '     -H "Authorization: Bearer gnd-admin-default-key" \'
        echo '     -d '"'"'{"model":"default","messages":[{"role":"user","content":"Hello!"}]}'"'"
        echo ""
        exit 0
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "   Waiting... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

echo "⚠️  Gateway may still be starting. Check logs:"
echo "   $COMPOSE logs -f gateway"
