# JR INSTRUCTION: Gemini Ring — BigMac Associate Ring via Google API

**Task**: Register Google Gemini as an Associate ring on BigMac, callable from the chain protocol. Wrap Gemini API (not CLI) so the federation can dispatch prompts to Gemini through BigMac.
**Priority**: P2
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 2
**Depends On**: BigMac necklace onboard (DONE), Gemini CLI on BigMac (Joe has OAuth creds)

## Context

Joe has Google Gemini CLI on BigMac with OAuth personal auth (`/Users/joedorn/.gemini/`). Rather than wrapping the interactive CLI, we create an API ring dispatcher that calls Gemini's REST API. This gives the federation access to Gemini 2.5 Pro/Flash alongside our local Ollama models and Qwen on redfin.

## Step 1: Get Gemini API Key

Joe needs to generate a Gemini API key:

1. Go to https://aistudio.google.com/apikey
2. Create an API key (free tier: 15 RPM on Gemini 2.5 Flash, 2 RPM on Pro)
3. Add to BigMac secrets:

```bash
echo 'GEMINI_API_KEY=<key-here>' >> /Users/Shared/ganuda/config/secrets.env
```

## Step 2: Create Gemini Ring Dispatcher on BigMac

Create `/Users/Shared/ganuda/lib/rings/gemini_ring.py`:

```python
"""Gemini ring dispatcher — calls Google Gemini API.

Associate ring on BigMac. Registered in duplo_tool_registry.
Models: gemini-2.5-flash (fast/free), gemini-2.5-pro (heavy/free-tier limited)
"""

import requests
import time
import os

# Load from secrets.env
SECRETS_PATH = "/Users/Shared/ganuda/config/secrets.env"


def _get_api_key() -> str:
    """Load Gemini API key from secrets.env."""
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    try:
        with open(SECRETS_PATH) as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.strip().split("=", 1)[1]
    except FileNotFoundError:
        pass
    raise RuntimeError("GEMINI_API_KEY not found in env or secrets.env")


def dispatch_gemini(payload: str, model: str = "gemini-2.5-flash",
                    max_tokens: int = 1024) -> dict:
    """Dispatch a prompt to Google Gemini API.

    Returns: {"result": str, "model": str, "latency_ms": float, "usage": dict}
    """
    api_key = _get_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    start = time.time()
    resp = requests.post(
        url,
        params={"key": api_key},
        json={
            "contents": [{"parts": [{"text": payload}]}],
            "generationConfig": {"maxOutputTokens": max_tokens},
        },
        timeout=120,
    )
    resp.raise_for_status()
    latency = (time.time() - start) * 1000
    data = resp.json()

    # Extract text from Gemini response
    text = ""
    usage = {}
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        text = str(data)
    try:
        usage = data.get("usageMetadata", {})
    except Exception:
        pass

    return {
        "result": text,
        "model": model,
        "latency_ms": round(latency, 1),
        "usage": usage,
    }
```

## Step 3: Create Gemini Ring HTTP Bridge on BigMac

The chain protocol on redfin needs to reach this ring over the network. Create a lightweight Flask bridge at `/Users/Shared/ganuda/services/gemini_bridge.py`:

```python
"""Gemini Ring Bridge — HTTP wrapper for chain protocol dispatch.

Runs on BigMac port 9100. Federation calls this to dispatch to Gemini.
Usage: python3 gemini_bridge.py
"""

from flask import Flask, request, jsonify
import sys
sys.path.insert(0, "/Users/Shared/ganuda/lib/rings")
from gemini_ring import dispatch_gemini

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "gemini-ring-bridge"})


@app.route("/dispatch", methods=["POST"])
def dispatch():
    data = request.json
    if not data or "payload" not in data:
        return jsonify({"error": "missing payload"}), 400

    try:
        result = dispatch_gemini(
            payload=data["payload"],
            model=data.get("model", "gemini-2.5-flash"),
            max_tokens=data.get("max_tokens", 1024),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9100)
```

## Step 4: Register Gemini Rings in Chain Protocol

```sql
PGPASSWORD=<from-secrets.env> psql -h 100.112.254.96 -U claude -d zammad_production <<'SQL'

INSERT INTO duplo_tool_registry (tool_name, description, module_path, function_name, parameters, safety_class, ring_type, provider, ring_status)
VALUES
('gemini_flash_bigmac', 'Gemini 2.5 Flash on BigMac via Google API', 'lib.rings.gemini_ring', 'dispatch_gemini',
 '{"model": "gemini-2.5-flash", "base_url": "http://100.106.9.80:9100"}'::jsonb,
 'read', 'associate', 'google_bigmac', 'active'),

('gemini_pro_bigmac', 'Gemini 2.5 Pro on BigMac via Google API', 'lib.rings.gemini_ring', 'dispatch_gemini',
 '{"model": "gemini-2.5-pro", "base_url": "http://100.106.9.80:9100"}'::jsonb,
 'read', 'associate', 'google_bigmac', 'active')

ON CONFLICT (tool_name) DO UPDATE SET
  parameters = EXCLUDED.parameters,
  provider = EXCLUDED.provider,
  ring_status = EXCLUDED.ring_status,
  updated_at = NOW();

SELECT tool_name, ring_type, provider, ring_status FROM duplo_tool_registry WHERE provider = 'google_bigmac';

SQL
```

## Step 5: Add Quick Script for Joe

Create `/Users/Shared/ganuda/scripts/ask_gemini.sh`:

```bash
#!/bin/bash
# ask_gemini.sh — Ask Gemini directly from BigMac
# Usage: ask_gemini.sh "your question" [model]
# Models: gemini-2.5-flash (default, fast), gemini-2.5-pro (heavy)

MODEL="${2:-gemini-2.5-flash}"

if [ -z "$1" ]; then
    echo "Usage: ask_gemini.sh \"your question\" [gemini-2.5-flash|gemini-2.5-pro]"
    exit 1
fi

source /Users/Shared/ganuda/config/secrets.env

curl -s --max-time 60 \
  "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${GEMINI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"contents\": [{\"parts\": [{\"text\": \"$1\"}]}]}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['candidates'][0]['content']['parts'][0]['text'])
except:
    print(sys.stdin.read())
" 2>/dev/null
```

## Step 6: Start Bridge as launchd Service (Optional)

For persistent ring availability, create a launchd plist so the bridge starts on boot:

```bash
cat > /Library/LaunchDaemons/us.ganuda.gemini-bridge.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>us.ganuda.gemini-bridge</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/Shared/ganuda/services/gemini_bridge.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/Shared/ganuda/logs/gemini-bridge.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/Shared/ganuda/logs/gemini-bridge.log</string>
</dict>
</plist>
PLIST
sudo launchctl load /Library/LaunchDaemons/us.ganuda.gemini-bridge.plist
```

## Step 7: Smoke Test

```bash
# Direct API test
bash /Users/Shared/ganuda/scripts/ask_gemini.sh "Say hello in Cherokee"

# Bridge test (after starting gemini_bridge.py)
curl -s http://localhost:9100/dispatch \
  -H "Content-Type: application/json" \
  -d '{"payload": "Say hello in Cherokee", "model": "gemini-2.5-flash"}'

# Federation test (from redfin)
curl -s http://100.106.9.80:9100/dispatch \
  -H "Content-Type: application/json" \
  -d '{"payload": "Say hello in Cherokee"}'
```

## Step 8: Thermalize

```sql
INSERT INTO thermal_memory_archive (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
VALUES (
  'Gemini ring operational on BigMac via Google API. Two Associate rings: gemini_flash_bigmac (2.5 Flash, fast/free), gemini_pro_bigmac (2.5 Pro, rate-limited). HTTP bridge on port 9100 reachable via Tailscale. Federation can now dispatch to Google Gemini through BigMac alongside local Ollama models.',
  70, 'infrastructure', false,
  encode(sha256(('gemini-ring-bigmac-' || NOW()::text)::bytea), 'hex')
);
```

## Ring Budget Impact

Two external API rings (Google Gemini). Currently we have 14 active rings — adding 2 brings us to 16. The 20% external ring budget applies to external API calls, not local rings. These are the first true external API rings on the necklace.

## DO NOT

- Hardcode the Gemini API key anywhere — use secrets.env only
- Use Joe's OAuth creds for the ring — those are personal/interactive. API key is for programmatic access
- Expose the bridge on 0.0.0.0 without verifying BigMac's firewall — Tailscale mesh is the trust boundary
- Register as `temp` rings — Joe's BigMac is permanent Associate hardware
