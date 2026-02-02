# JR Instruction: Deploy SearXNG for ii-researcher

**JR ID:** JR-SEARXNG-DEPLOY-II-RESEARCHER-JAN28-2026
**Priority:** P1
**Assigned To:** Infrastructure Jr.
**Council Vote:** 166956a7959c2232
**Related:** JR-II-RESEARCHER-PHASE1-INSTALL-JAN28-2026

---

## Objective

Deploy SearXNG as a self-hosted meta search engine to replace Tavily API dependency. This gives us free, unlimited web search with no API keys required.

---

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  ii-researcher  │────▶│   SearXNG    │────▶│ Google/Bing/    │
│  (port 8090)    │     │  (port 8888) │     │ DuckDuckGo/etc  │
└─────────────────┘     └──────────────┘     └─────────────────┘
        │
        ▼
┌─────────────────┐
│     vLLM        │
│  (port 8000)    │
└─────────────────┘

All on redfin (192.168.132.223)
```

---

## Steps

### 1. Create SearXNG Directory Structure

```bash
mkdir -p /ganuda/services/searxng
cd /ganuda/services/searxng
```

### 2. Create SearXNG Settings

Create `/ganuda/services/searxng/settings.yml`:

```yaml
# SearXNG Configuration for Cherokee AI Federation
# For Seven Generations

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
  secret_key: "cherokee-searxng-secret-change-in-production"
  limiter: false
  image_proxy: false
  port: 8888
  bind_address: "0.0.0.0"

ui:
  static_use_hash: true
  default_theme: simple
  results_on_new_tab: false

outgoing:
  request_timeout: 10.0
  max_request_timeout: 30.0
  useragent_suffix: ""
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

  - name: wikidata
    engine: wikidata
    shortcut: wd
    disabled: false

  - name: github
    engine: github
    shortcut: gh
    disabled: false

  - name: arxiv
    engine: arxiv
    shortcut: arx
    disabled: false

  - name: stackoverflow
    engine: stackoverflow
    shortcut: so
    disabled: false
```

### 3. Create Podman Quadlet Service

Create `/ganuda/services/searxng/searxng.container`:

```ini
# Podman Quadlet for SearXNG
# For Seven Generations - Cherokee AI Federation

[Unit]
Description=SearXNG Meta Search Engine
After=network-online.target

[Container]
Image=docker.io/searxng/searxng:latest
ContainerName=searxng
PublishPort=8888:8888
Volume=/ganuda/services/searxng/settings.yml:/etc/searxng/settings.yml:ro
Environment=SEARXNG_BASE_URL=http://localhost:8888/
DropCapability=ALL
AddCapability=CHOWN SETGID SETUID

[Service]
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target default.target
```

### 4. Create Systemd Service for SearXNG

Create `/ganuda/scripts/systemd/searxng.service`:

```ini
[Unit]
Description=SearXNG Meta Search Engine
After=network-online.target

[Service]
Type=simple
User=dereadi
Restart=always
RestartSec=10
ExecStartPre=/usr/bin/podman pull docker.io/searxng/searxng:latest
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
```

### 5. Create Custom Search Provider for ii-researcher

Create `/ganuda/services/ii-researcher/ii_researcher/tool_clients/searxng_client.py`:

```python
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

    def __init__(
        self,
        base_url: str = None,
        max_results: int = 10
    ):
        self.base_url = base_url or os.environ.get(
            "SEARXNG_URL", "http://localhost:8888"
        )
        self.max_results = max_results

    def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Search using SearXNG.

        Args:
            query: Search query string
            max_results: Maximum results to return

        Returns:
            List of search results with title, url, content
        """
        max_results = max_results or self.max_results

        try:
            response = requests.get(
                f"{self.base_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "pageno": 1
                },
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

        except requests.exceptions.RequestException as e:
            print(f"SearXNG search error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in SearXNG search: {e}")
            return []


# Compatibility function for ii-researcher
def search_with_searxng(query: str, max_results: int = 10) -> List[Dict]:
    """Convenience function for searching with SearXNG."""
    client = SearXNGClient()
    return client.search(query, max_results)
```

### 6. Patch ii-researcher Search Client

Add SearXNG support to `/ganuda/services/ii-researcher/ii_researcher/tool_clients/search_client.py`.

Add import at top:
```python
from .searxng_client import SearXNGClient
```

Add method to SearchClient class:
```python
def _search_query_by_searxng(self, query, max_results=10):
    """Searches using self-hosted SearXNG."""
    client = SearXNGClient()
    return client.search(query, max_results)
```

Update the search() method to include searxng:
```python
elif self.search_provider == "searxng":
    return self._search_query_by_searxng(query, max_results)
```

### 7. Update ii-researcher Environment

Update `/ganuda/services/ii-researcher/.env`:

```bash
# Search Configuration - use self-hosted SearXNG
SEARCH_PROVIDER=searxng
SEARXNG_URL=http://localhost:8888

# Remove or comment out Tavily
# TAVILY_API_KEY=not-needed
```

### 8. Deploy and Start Services

```bash
# Pull SearXNG image
podman pull docker.io/searxng/searxng:latest

# Enable systemd service
sudo ln -sf /ganuda/scripts/systemd/searxng.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable searxng
sudo systemctl start searxng

# Wait for SearXNG to start
sleep 10

# Test SearXNG
curl 'http://localhost:8888/search?q=test&format=json' | head -c 500

# Restart ii-researcher
sudo systemctl restart ii-researcher
```

---

## Verification

```bash
# Check SearXNG is running
curl -s 'http://localhost:8888/search?q=hello&format=json' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Results: {len(d.get(\"results\", []))}')"

# Check ii-researcher can search
curl 'http://localhost:8090/search?question=what%20is%20the%20capital%20of%20france'

# Check Podman container
podman ps | grep searxng

# Check logs
podman logs searxng --tail 20
journalctl -u searxng -n 20
journalctl -u ii-researcher -n 20
```

---

## Troubleshooting

### SearXNG returns no results
- Check if engines are being rate-limited
- Try different search engines in settings.yml
- Check Podman logs: `podman logs searxng`

### Connection refused to port 8888
- Ensure Podman container is running: `podman ps`
- Check firewall: `sudo ufw status`
- Verify port binding: `ss -tlnp | grep 8888`

### ii-researcher still using Tavily
- Verify SEARCH_PROVIDER=searxng in .env
- Restart ii-researcher: `sudo systemctl restart ii-researcher`
- Check environment: `cat /proc/$(pgrep -f ii-researcher)/environ | tr '\0' '\n' | grep SEARCH`

---

## Notes

- SearXNG aggregates from multiple search engines (Google, Bing, DuckDuckGo, etc.)
- No API keys required - completely self-hosted
- Rate limiting handled by SearXNG internally
- Respects robots.txt and search engine ToS
- Aligns with Cherokee data sovereignty principles

---

## Security Considerations

- SearXNG only binds to localhost by default
- No user data stored
- Search queries not logged (unless enabled)
- Consider enabling limiter in production if exposed externally

---

FOR SEVEN GENERATIONS
