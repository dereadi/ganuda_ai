#!/usr/bin/env bash
#
# Generate self-signed SSL certificates for PostgreSQL
# Cherokee AI Federation - Security Phase 3
# Generated: 2026-02-02
#
# REQUIRES ADMIN: Run as root or with sudo:
#   sudo bash /ganuda/scripts/generate_pg_ssl_certs.sh
#
set -euo pipefail

PG_CONF_DIR="/etc/postgresql/16/main"
CERT_FILE="${PG_CONF_DIR}/server.crt"
KEY_FILE="${PG_CONF_DIR}/server.key"
DAYS_VALID=3650  # 10 years for internal use

echo "=== PostgreSQL SSL Certificate Generator ==="
echo "Target directory: ${PG_CONF_DIR}"
echo ""

# Check if certs already exist
if [[ -f "${CERT_FILE}" && -f "${KEY_FILE}" ]]; then
    echo "[WARN] Certificates already exist at:"
    echo "  ${CERT_FILE}"
    echo "  ${KEY_FILE}"
    read -rp "Overwrite? (y/N): " CONFIRM
    if [[ "${CONFIRM}" != "y" && "${CONFIRM}" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# Generate private key and self-signed certificate
echo "[1/4] Generating private key and self-signed certificate..."
openssl req -new -x509 -nodes \
    -days ${DAYS_VALID} \
    -keyout "${KEY_FILE}" \
    -out "${CERT_FILE}" \
    -subj "/C=US/ST=NC/L=Cherokee/O=Ganuda Federation/CN=$(hostname -f)" \
    2>/dev/null

echo "[2/4] Setting key permissions to 600 (owner read/write only)..."
chmod 600 "${KEY_FILE}"

echo "[3/4] Setting cert permissions to 644 (world readable)..."
chmod 644 "${CERT_FILE}"

echo "[4/4] Setting ownership to postgres:postgres..."
chown postgres:postgres "${CERT_FILE}" "${KEY_FILE}"

echo ""
echo "=== Certificate Details ==="
openssl x509 -in "${CERT_FILE}" -noout -subject -dates -fingerprint
echo ""
echo "[OK] SSL certificates generated successfully."
echo ""
echo "Next steps:"
echo "  1. Deploy SSL config:  sudo cp /ganuda/config/postgresql-ssl.conf ${PG_CONF_DIR}/conf.d/ssl.conf"
echo "  2. Restart PostgreSQL: sudo systemctl restart postgresql"
echo "  3. Verify SSL:         sudo -u postgres psql -c 'SHOW ssl;'"
