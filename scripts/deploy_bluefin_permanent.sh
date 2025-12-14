#!/bin/bash
# Deploy BLUEFIN Jr. instances to permanent location

INSTALL_DIR="/home/dereadi/claude_jr"
mkdir -p $INSTALL_DIR

# Transfer scripts from local /tmp to BLUEFIN permanent location
# These were created earlier
scp /tmp/legal_jr_fixed.py 192.168.132.222:$INSTALL_DIR/ 2>/dev/null || echo "Creating Legal Jr..."
scp /tmp/infra_jr_api.py 192.168.132.222:$INSTALL_DIR/ 2>/dev/null || echo "Creating Infrastructure Jr..."

# If scripts don't exist, recreate them
