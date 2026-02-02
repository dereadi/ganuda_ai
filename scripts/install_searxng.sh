#!/bin/bash
# SearXNG Installation Script for ii-researcher
# Council Vote: 166956a7959c2232
# For Seven Generations - Cherokee AI Federation

set -e

echo "=============================================="
echo "SearXNG Installation"
echo "=============================================="

# Step 1: Create directory
echo "[1/5] Creating SearXNG directory..."
mkdir -p /ganuda/services/searxng
cd /ganuda/services/searxng

# Step 2: Create settings file
echo "[2/5] Creating settings.yml..."
cat > /ganuda/services/searxng/settings.yml << 'EOF'
# SearXNG Configuration for Cherokee AI Federation
use_default_settings: true

general:
  instance_name: "Cherokee Search"
  debug: false
  enable_metrics: false

search:
  safe_search: 0
  autocomplete: ""
  default_lang: "en"
  formats:
    - html
    - json

server:
  secret_key: "cherokee-searxng-7gen-secret-key"
  limiter: false
  image_proxy: false
  port: 8888
  bind_address: "0.0.0.0"

ui:
  static_use_hash: true
  default_theme: simple

outgoing:
  request_timeout: 10.0
  max_request_timeout: 30.0
  pool_connections: 100
  pool_maxsize: 20

engines:
  - name: google
    engine: google
    shortcut: g
    disabled: false

  - name: bing
    engine: bing
    shortcut: b
    disabled: false

  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg
    disabled: false

  - name: wikipedia
    engine: wikipedia
    shortcut: wp
    disabled: false

  - name: github
    engine: github
    shortcut: gh
    disabled: false

  - name: arxiv
    engine: arxiv
    shortcut: arx
    disabled: false
EOF

# Step 3: Create systemd service
echo "[3/5] Creating systemd service..."
cat > /ganuda/scripts/systemd/searxng.service << 'EOF'
[Unit]
Description=SearXNG Meta Search Engine
After=network-online.target

[Service]
Type=simple
User=dereadi
Restart=always
RestartSec=10
ExecStartPre=-/usr/bin/podman stop searxng
ExecStartPre=-/usr/bin/podman rm searxng
ExecStart=/usr/bin/podman run --rm --name searxng \
    -p 8888:8888 \
    -v /ganuda/services/searxng/settings.yml:/etc/searxng/settings.yml:ro \
    -e SEARXNG_BASE_URL=http://localhost:8888/ \
    --cap-drop=ALL \
    --cap-add=CHOWN,SETGID,SETUID \
    docker.io/searxng/searxng:latest
ExecStop=/usr/bin/podman stop searxng
StandardOutput=journal
StandardError=journal
SyslogIdentifier=searxng

[Install]
WantedBy=multi-user.target
EOF

# Step 4: Create SearXNG client for ii-researcher
echo "[4/5] Creating SearXNG client..."
cat > /ganuda/services/ii-researcher/ii_researcher/tool_clients/searxng_client.py << 'EOF'
#!/usr/bin/env python3
"""
SearXNG Search Client for ii-researcher.
Self-hosted meta search - no API keys required.
For Seven Generations - Cherokee AI Federation
"""

import os
import requests
from typing import List, Dict, Any


class SearXNGClient:
    """Search client using self-hosted SearXNG instance."""

    def __init__(self, base_url: str = None, max_results: int = 10):
        self.base_url = base_url or os.environ.get(
            "SEARXNG_URL", "http://localhost:8888"
        )
        self.max_results = max_results

    def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """Search using SearXNG."""
        max_results = max_results or self.max_results

        try:
            response = requests.get(
                f"{self.base_url}/search",
                params={"q": query, "format": "json", "pageno": 1},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "raw_content": item.get("content", "")
                })
            return results

        except Exception as e:
            print(f"SearXNG search error: {e}")
            return []
EOF

# Step 5: Patch search_client.py to add SearXNG support
echo "[5/5] Patching search_client.py..."
SEARCH_CLIENT="/ganuda/services/ii-researcher/ii_researcher/tool_clients/search_client.py"

# Check if already patched
if grep -q "searxng" "$SEARCH_CLIENT"; then
    echo "search_client.py already patched for SearXNG"
else
    # Add import
    sed -i '1a from .searxng_client import SearXNGClient' "$SEARCH_CLIENT"

    # Add method before the final search method
    sed -i '/def search(self, query=None/i\
    def _search_query_by_searxng(self, query, max_results=10):\
        """Searches using self-hosted SearXNG."""\
        client = SearXNGClient()\
        return client.search(query, max_results)\
' "$SEARCH_CLIENT"

    # Add elif for searxng in search method
    sed -i 's/elif self.search_provider == "jina":/elif self.search_provider == "searxng":\
            return self._search_query_by_searxng(query, max_results)\
        elif self.search_provider == "jina":/' "$SEARCH_CLIENT"

    echo "Patched search_client.py"
fi

# Update .env
echo "Updating .env for SearXNG..."
sed -i 's/SEARCH_PROVIDER=tavily/SEARCH_PROVIDER=searxng/' /ganuda/services/ii-researcher/.env
echo "SEARXNG_URL=http://localhost:8888" >> /ganuda/services/ii-researcher/.env

echo ""
echo "=============================================="
echo "Installation complete!"
echo "=============================================="
echo ""
echo "Now run with sudo:"
echo ""
echo "  podman pull docker.io/searxng/searxng:latest"
echo "  sudo ln -sf /ganuda/scripts/systemd/searxng.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable searxng"
echo "  sudo systemctl start searxng"
echo "  sudo systemctl restart ii-researcher"
echo ""
echo "Then verify:"
echo "  curl 'http://localhost:8888/search?q=test&format=json' | head -c 200"
echo "  curl 'http://localhost:8090/search?question=hello'"
echo ""
echo "FOR SEVEN GENERATIONS"
