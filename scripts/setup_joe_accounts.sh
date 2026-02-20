#!/bin/bash
# Setup Joe's account on bluefin (greenfin already has it)
# Run as dereadi on redfin - will prompt for sudo passwords

set -e

echo "========================================"
echo "Joe Account Setup Script"
echo "========================================"
echo ""

# First, get Joe's SSH keys from redfin (this machine)
echo "[1/6] Getting Joe's SSH keys from redfin..."
echo "Enter sudo password for redfin:"
JOE_KEYS=$(sudo cat /home/jsdorn/.ssh/authorized_keys 2>/dev/null)

if [ -z "$JOE_KEYS" ]; then
    echo "ERROR: Could not read Joe's SSH keys from /home/jsdorn/.ssh/authorized_keys"
    exit 1
fi

echo "Found SSH keys:"
echo "$JOE_KEYS" | head -c 100
echo "..."
echo ""

# Setup on bluefin
echo "========================================"
echo "[2/6] Setting up Joe on BLUEFIN..."
echo "========================================"
echo ""

ssh -t dereadi@100.112.254.96 "
    echo 'Creating jsdorn user...'
    sudo useradd -m -s /bin/bash -c 'Dr. Joe Sdorn' -u 1001 jsdorn 2>/dev/null || echo 'User may already exist'
    
    echo 'Setting password to Walmart1...'
    echo 'jsdorn:Walmart1' | sudo chpasswd
    
    echo 'Forcing password change on first login...'
    sudo chage -d 0 jsdorn
    
    echo 'Creating .ssh directory...'
    sudo mkdir -p /home/jsdorn/.ssh
    sudo chmod 700 /home/jsdorn/.ssh
    sudo chown jsdorn:jsdorn /home/jsdorn/.ssh
    
    echo 'Adding SSH keys...'
    echo '' | sudo tee /home/jsdorn/.ssh/authorized_keys > /dev/null
    sudo chmod 600 /home/jsdorn/.ssh/authorized_keys
    sudo chown jsdorn:jsdorn /home/jsdorn/.ssh/authorized_keys
    
    echo 'Adding to sudo group...'
    sudo usermod -aG sudo jsdorn
    
    echo ''
    echo 'BLUEFIN COMPLETE - verifying:'
    grep jsdorn /etc/passwd
    ls -la /home/jsdorn/.ssh/
"

echo ""
echo "========================================"
echo "[3/6] Updating Joe on GREENFIN..."
echo "========================================"
echo "(Account exists, just updating password and keys)"
echo ""

ssh -t dereadi@100.100.243.116 "
    echo 'Setting password to Walmart1...'
    echo 'jsdorn:Walmart1' | sudo chpasswd
    
    echo 'Forcing password change on first login...'
    sudo chage -d 0 jsdorn
    
    echo 'Ensuring .ssh directory exists...'
    sudo mkdir -p /home/jsdorn/.ssh
    sudo chmod 700 /home/jsdorn/.ssh
    sudo chown jsdorn:jsdorn /home/jsdorn/.ssh
    
    echo 'Adding SSH keys...'
    echo '' | sudo tee /home/jsdorn/.ssh/authorized_keys > /dev/null
    sudo chmod 600 /home/jsdorn/.ssh/authorized_keys
    sudo chown jsdorn:jsdorn /home/jsdorn/.ssh/authorized_keys
    
    echo 'Ensuring sudo access...'
    sudo usermod -aG sudo jsdorn 2>/dev/null || true
    
    echo ''
    echo 'GREENFIN COMPLETE - verifying:'
    grep jsdorn /etc/passwd
    ls -la /home/jsdorn/.ssh/
"

echo ""
echo "========================================"
echo "[4/6] Summary"
echo "========================================"
echo ""
echo "Joe (jsdorn) account setup complete on:"
echo "  - redfin:   Already existed (source of SSH keys)"
echo "  - bluefin:  Created with password Walmart1"
echo "  - greenfin: Updated with password Walmart1"
echo ""
echo "Joe will be prompted to change password on first login."
echo ""
echo "Test commands for Joe:"
echo "  ssh jsdorn@100.112.254.96   # bluefin"
echo "  ssh jsdorn@100.100.243.116  # greenfin"
echo ""
echo "For Seven Generations"
