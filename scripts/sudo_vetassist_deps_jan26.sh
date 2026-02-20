#!/bin/bash
# Fix VetAssist Backend Dependencies
# Run as: sudo bash /ganuda/scripts/sudo_vetassist_deps_jan26.sh

echo "=== Installing VetAssist Backend Dependencies ==="

cd /ganuda/vetassist/backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating venv..."
    python3 -m venv venv
fi

# Activate and install
echo "Activating venv and installing requirements..."
. venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify key imports
echo ""
echo "=== Verifying imports ==="
python -c "from slowapi import Limiter; print('slowapi: OK')"
python -c "from fastapi import FastAPI; print('fastapi: OK')"
python -c "from passlib.context import CryptContext; print('passlib: OK')"
python -c "from jose import jwt; print('python-jose: OK')"

echo ""
echo "=== Testing app import ==="
cd /ganuda/vetassist/backend
python -c "from app.main import app; print('app.main: OK')" 2>&1 || echo "App import failed - circular import issue still present"

echo ""
echo "Done. If app import failed, run the circular import fix task."
