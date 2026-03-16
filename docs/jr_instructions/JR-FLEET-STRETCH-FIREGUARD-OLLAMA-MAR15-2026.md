# Jr Instruction: Fire Guard Ollama Health Checks for Mac Fleet

**Task**: Add Ollama health checks for sasass, sasass2, and verify bmasass coverage in fire_guard.py
**Priority**: P2
**Story Points**: 2
**Ticket**: Fleet Stretch (83dfa34d)
**Date**: 2026-03-15

## Context

Sub-agent dispatch (sub_agent_dispatch.py) now has 10 node entries spanning redfin, bmasass, sasass, and sasass2. Fire Guard currently monitors bmasass MLX ports (8800, 8801) but has NO coverage for Ollama on sasass or sasass2. These nodes serve code review, research, and resonance models. If Ollama goes down on sasass2, the Jr code review gate is blind.

## Files to Modify

### `/ganuda/scripts/fire_guard.py`

#### Step 1: Add sasass and sasass2 to REMOTE_CHECKS (line ~62-69)

Add entries to the existing REMOTE_CHECKS dict:

```python
REMOTE_CHECKS = {
    "bluefin": [("192.168.132.222", 5432, "PostgreSQL"), ("192.168.132.222", 8090, "VLM")],
    "greenfin": [("192.168.132.224", 8003, "Embedding")],
    "owlfin": [("192.168.132.170", 80, "Caddy")],
    "eaglefin": [("192.168.132.84", 80, "Caddy")],
    "bmasass": [("100.103.27.106", 8800, "Qwen3"), ("100.103.27.106", 8801, "Llama")],
    "sasass": [("192.168.132.241", 11434, "Ollama")],
    "sasass2": [("192.168.132.242", 11434, "Ollama")],
    "redfin_consultation": [("127.0.0.1", 9400, "ConsultationRing")],
}
```

#### Step 2: Add check_ollama_health() function (after check_postgres_db, ~line 316)

```python
def check_ollama_health(host, port=11434, timeout=5):
    """Deep health check for Ollama API — verifies service responds, not just TCP.

    Hits /api/tags to confirm Ollama is alive and can list models.
    Returns (alive: bool, model_count: int, models: list).
    """
    try:
        resp = requests.get(
            f"http://{host}:{port}/api/tags",
            timeout=timeout
        )
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "?") for m in data.get("models", [])]
            return True, len(models), models
        return False, 0, []
    except Exception:
        return False, 0, []
```

**Note**: fire_guard.py already imports `requests` (check first — if not, add it). If `requests` is not available, use `urllib.request` instead:

```python
import urllib.request
import json as json_mod

def check_ollama_health(host, port=11434, timeout=5):
    try:
        req = urllib.request.Request(f"http://{host}:{port}/api/tags")
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json_mod.loads(resp.read())
        models = [m.get("name", "?") for m in data.get("models", [])]
        return True, len(models), models
    except Exception:
        return False, 0, []
```

#### Step 3: Use deep Ollama check in the remote check loop

In the `run_checks()` function where it iterates REMOTE_CHECKS, add a branch for Ollama services (similar to how PostgreSQL uses `check_postgres_db()` instead of raw TCP):

Find the section that calls `check_port()` for each remote service. Add before the generic `check_port()` call:

```python
if service_name == "Ollama":
    alive, model_count, models = check_ollama_health(ip, port)
    if alive:
        results.append(("ok", f"{node} {service_name}: {model_count} models loaded"))
    else:
        results.append(("fail", f"{node} {service_name}: NOT RESPONDING"))
    continue
```

#### Step 4: Add Ollama model count to HTML dashboard

In the `render_html()` function, Ollama entries should show model count when healthy. This is informational — follow the existing pattern for how other services display in the dashboard table.

## Acceptance Criteria

1. `fire_guard.py` runs without errors after changes
2. Health dashboard shows sasass Ollama and sasass2 Ollama status
3. If Ollama is down on either Mac, Fire Guard reports it (not silent)
4. If Ollama is up, dashboard shows model count
5. No false positives — if Mac is asleep/off-network, it should report "fail" not crash

## Do NOT

- Change any existing check behavior
- Add Tailscale IPs for sasass/sasass2 (LAN is fine for these — they're on-prem)
- Add the `requests` import if it doesn't already exist — use urllib fallback
- Touch the emergency brake logic
