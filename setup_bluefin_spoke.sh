#!/bin/bash
set -e

echo "🔥 EXECUTIVE JR - SETTING UP BLUEFIN AS INDEPENDENT SPOKE"
echo "============================================================"

# 1. Create directory structure
echo ""
echo "📁 Creating directory structure on BLUEFIN..."
ssh bluefin "mkdir -p /home/dereadi/scripts/sag-spoke"
ssh bluefin "mkdir -p /home/dereadi/scripts/sag-spoke/thermal_db"
ssh bluefin "mkdir -p /home/dereadi/scripts/sag-spoke/logs"

# 2. Check system requirements
echo ""
echo "🔍 Checking BLUEFIN system requirements..."
ssh bluefin "command -v python3" && echo "   ✅ Python3 found" || echo "   ⚠️ Python3 not found"
ssh bluefin "command -v docker" && echo "   ✅ Docker found" || echo "   ⚠️ Docker not found"

# 3. Install required packages if needed
echo ""
echo "📦 Installing required packages..."
ssh bluefin "sudo apt-get update -qq && sudo apt-get install -y -qq \
    python3-pip \
    python3-venv \
    docker.io \
    postgresql-client 2>&1 | grep -v 'Reading\|Building\|Get:' || true"

# 4. Setup Python environment
echo ""
echo "🐍 Setting up Python virtual environment..."
ssh bluefin "cd /home/dereadi/scripts/sag-spoke && \
    python3 -m venv sag_env"

ssh bluefin "cd /home/dereadi/scripts/sag-spoke && \
    source sag_env/bin/activate && \
    pip install --quiet --upgrade pip && \
    pip install --quiet \
        psycopg2-binary \
        pandas \
        numpy \
        scikit-learn \
        scipy \
        requests"

# 5. Verify installation
echo ""
echo "✅ Verifying installation..."
ssh bluefin "cd /home/dereadi/scripts/sag-spoke && \
    source sag_env/bin/activate && \
    python3 -c 'import psycopg2, pandas, sklearn; print(\"   ✅ All Python packages installed\")'"

echo ""
echo "🎯 BLUEFIN ENVIRONMENT SETUP COMPLETE"
echo "============================================================"
echo "   Location: bluefin:/home/dereadi/scripts/sag-spoke/"
echo "   Python env: sag_env (activated)"
echo "   Status: READY FOR DEPLOYMENT"
