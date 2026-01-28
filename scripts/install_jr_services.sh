#!/bin/bash
# Install Jr worker systemd services

set -e

SYSTEMD_DIR=/etc/systemd/system
SCRIPTS_DIR=/ganuda/scripts/systemd

echo "Installing Jr worker services..."

# Link services
for service in jr-se jr-it-triad jr-research jr-infra; do
    if [ -f "$SCRIPTS_DIR/${service}.service" ]; then
        sudo ln -sf "$SCRIPTS_DIR/${service}.service" "$SYSTEMD_DIR/${service}.service"
        echo "  Linked ${service}.service"
    fi
done

# Reload systemd
sudo systemctl daemon-reload

# Enable services
for service in jr-se jr-it-triad jr-research jr-infra; do
    sudo systemctl enable ${service}.service
    echo "  Enabled ${service}.service"
done

echo "Done. Start services with: sudo systemctl start jr-se jr-it-triad jr-research jr-infra"
