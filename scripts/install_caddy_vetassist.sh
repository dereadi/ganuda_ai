#!/bin/bash
# Install VetAssist Caddy config
# Run with: sudo bash /ganuda/scripts/install_caddy_vetassist.sh

cp /ganuda/config/Caddyfile.vetassist /etc/caddy/Caddyfile
systemctl reload caddy
systemctl status caddy --no-pager
echo ""
echo "Caddy config updated for vetassist.ganuda.us"
