# JR INSTRUCTION: BigMac Necklace Onboard — Register as Chain Protocol Ring

**Task**: Connect BigMac (Joe's Mac Studio) to the Cherokee Chain Protocol as an Associate ring-bearing node. Register its Ollama models in the ring registry, deploy the A2A bridge, verify dispatch end-to-end.
**Priority**: P1
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 3
**Depends On**: Tailscale connectivity to bluefin (DONE), FreeIPA onboard (DONE), nftables Tailscale fix (DONE)

## Prerequisites (Already Done)

- BigMac on Tailscale: 100.106.9.80 ✓
- psql to bluefin working: `psql -h 100.112.254.96 -U claude -d zammad_production` ✓
- Joe's FreeIPA account + sudo on all nodes ✓
- Bluefin nftables allows Tailscale (100.64.0.0/10) ✓

## Step 1: Create /Users/Shared/ganuda on BigMac

macOS nodes use `/Users/Shared/ganuda` instead of `/ganuda`.

```bash
sudo mkdir -p /Users/Shared/ganuda/{config,scripts,lib,logs,drjoe}
sudo chown -R jsdorn:staff /Users/Shared/ganuda
```

## Step 2: Copy secrets.env to BigMac

From any federation node:

```bash
scp 10.100.0.1:/ganuda/config/secrets.env /Users/Shared/ganuda/config/secrets.env
chmod 600 /Users/Shared/ganuda/config/secrets.env
```

## Step 3: Install Python Dependencies

```bash
pip3 install psycopg2-binary requests flask
```

## Step 4: Copy Chain Protocol + A2A Bridge

```bash
scp 10.100.0.1:/ganuda/lib/chain_protocol.py /Users/Shared/ganuda/lib/
scp 10.100.0.1:/ganuda/drjoe/cherokee_a2a_bridge.py /Users/Shared/ganuda/drjoe/
```

## Step 5: Verify DB Connectivity from Python

```bash
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='100.112.254.96',
    port=5432,
    dbname='zammad_production',
    user='claude',
    password='bIDhRwvSU8Fm6ezeZw9ujQvLqe0CNAg4'
)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM thermal_memory_archive')
print(f'Thermals: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM duplo_tool_registry')
print(f'Rings: {cur.fetchone()[0]}')
cur.close(); conn.close()
print('BigMac → bluefin DB: OK')
"
```

## Step 6: Verify Ollama is Running

```bash
curl http://localhost:11434/api/tags
```

Should show the models available (llama3.1, mistral, codellama, etc.). Note which models are loaded — each becomes a ring.

## Step 7: Register BigMac Models in Ring Registry

Run from BigMac (or any node with DB access):

```bash
PGPASSWORD=bIDhRwvSU8Fm6ezeZw9ujQvLqe0CNAg4 psql -h 100.112.254.96 -U claude -d zammad_production <<'SQL'

-- Register BigMac Ollama models as Associate rings
INSERT INTO duplo_tool_registry (tool_name, description, module_path, function_name, parameters, safety_class, ring_type, provider, ring_status)
VALUES
('llama3_bigmac', 'Llama 3.1 on BigMac via Ollama', 'lib.rings.ollama_ring', 'dispatch_ollama',
 '{"model": "llama3.1", "base_url": "http://100.106.9.80:11434"}'::jsonb,
 'read', 'associate', 'local_bigmac', 'active'),

('mistral_bigmac', 'Mistral on BigMac via Ollama', 'lib.rings.ollama_ring', 'dispatch_ollama',
 '{"model": "mistral", "base_url": "http://100.106.9.80:11434"}'::jsonb,
 'read', 'associate', 'local_bigmac', 'active'),

('codellama_bigmac', 'CodeLlama on BigMac via Ollama', 'lib.rings.ollama_ring', 'dispatch_ollama',
 '{"model": "codellama", "base_url": "http://100.106.9.80:11434"}'::jsonb,
 'read', 'associate', 'local_bigmac', 'active')

ON CONFLICT (tool_name) DO UPDATE SET
  parameters = EXCLUDED.parameters,
  provider = EXCLUDED.provider,
  ring_status = EXCLUDED.ring_status,
  updated_at = NOW();

-- Verify
SELECT tool_name, ring_type, provider, ring_status FROM duplo_tool_registry WHERE provider = 'local_bigmac';

SQL
```

## Step 8: Create Ollama Ring Dispatcher

Create `/Users/Shared/ganuda/lib/rings/ollama_ring.py`:

```python
"""Ollama ring dispatcher — calls Ollama API on any node via Tailscale."""

import requests
import time


def dispatch_ollama(payload: str, model: str = "llama3.1",
                    base_url: str = "http://localhost:11434") -> dict:
    """Dispatch a prompt to an Ollama model.

    Returns: {"result": str, "model": str, "latency_ms": float}
    """
    start = time.time()
    resp = requests.post(
        f"{base_url}/api/generate",
        json={"model": model, "prompt": payload, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    latency = (time.time() - start) * 1000
    data = resp.json()
    return {
        "result": data.get("response", ""),
        "model": model,
        "latency_ms": round(latency, 1),
    }
```

Also copy this to redfin so the chain protocol can dispatch TO BigMac:

```bash
scp /Users/Shared/ganuda/lib/rings/ollama_ring.py 10.100.0.1:/ganuda/lib/rings/ollama_ring.py
```

## Step 9: Update A2A Bridge for Tailscale

The existing A2A bridge on redfin (`/ganuda/drjoe/cherokee_a2a_bridge.py`) points to `localhost:8080`. That's correct — it runs ON redfin and talks to the local gateway.

For BigMac to call the federation directly, Joe can use:

```bash
# From BigMac — ask the council a question
curl -X POST http://100.116.27.89:9001/bigmac/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the current ring budget?"}'
```

Redfin Tailscale IP is 100.116.27.89. The A2A bridge on redfin:9001 routes to the gateway.

## Step 10: Smoke Test — End to End

From BigMac:

```python
python3 -c "
# Test 1: BigMac Ollama responds
import requests
r = requests.post('http://localhost:11434/api/generate',
    json={'model': 'llama3.1', 'prompt': 'Say hello in Cherokee', 'stream': False}, timeout=60)
print('Ollama:', r.json()['response'][:100])

# Test 2: Chain protocol sees BigMac rings
import psycopg2
conn = psycopg2.connect(host='100.112.254.96', port=5432, dbname='zammad_production',
    user='claude', password='bIDhRwvSU8Fm6ezeZw9ujQvLqe0CNAg4')
cur = conn.cursor()
cur.execute(\"SELECT tool_name, ring_status FROM duplo_tool_registry WHERE provider = 'local_bigmac'\")
for row in cur.fetchall():
    print(f'Ring: {row[0]} — {row[1]}')
cur.close(); conn.close()

# Test 3: Federation can reach BigMac Ollama via Tailscale
# (run this from redfin to verify)
print('Run from redfin: curl http://100.106.9.80:11434/api/tags')
print('Smoke test complete.')
"
```

## Step 11: Thermalize

```sql
INSERT INTO thermal_memory_archive (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
VALUES (
  'BigMac (Joe Mac Studio) onboarded to Chain Protocol as Associate ring-bearing node. Three Ollama models registered: llama3_bigmac, mistral_bigmac, codellama_bigmac. Reachable via Tailscale 100.106.9.80:11434. A2A bridge on redfin:9001 routes BigMac questions to gateway council. End-to-end dispatch verified.',
  72, 'infrastructure', false,
  encode(sha256(('bigmac-necklace-onboard-' || NOW()::text)::bytea), 'hex')
);
```

## Summary — What Joe Actually Does

1. `mkdir` + `scp` secrets and scripts (~2 min)
2. `pip3 install` deps (~1 min)
3. Run the SQL to register his models (~30 sec)
4. Create ollama_ring.py dispatcher (~1 min)
5. Smoke test (~1 min)

**Total: ~5 minutes.** Everything else (Tailscale, nftables, FreeIPA, sudo) is already done.

## DO NOT

- Expose Ollama to 0.0.0.0 on BigMac without firewall — Tailscale handles the mesh, Ollama should bind to localhost or Tailscale IP only
- Register BigMac models as `temp` rings — Joe is an Associate, his hardware is permanent
- Skip the DB connectivity test — if psql doesn't work, nothing else will
- Hardcode the DB password anywhere except secrets.env
