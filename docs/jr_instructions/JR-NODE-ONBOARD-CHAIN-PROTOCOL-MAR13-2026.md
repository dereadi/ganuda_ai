# JR INSTRUCTION: Node Onboard via Chain Protocol

**Task**: Automate federation node onboarding for new developers through the necklace chain protocol. When a new human or Associate joins, a Jr dispatches `node_onboard.sh` across all nodes with /ganuda, verifies results, and thermalizes the event.
**Priority**: P2
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 3
**Depends On**: Chain Protocol (lib/chain_protocol.py), node_onboard.sh (scripts/node_onboard.sh), FreeIPA (silverfin)

## Context

We just onboarded Joe (jsdorn) manually — removed stale local account, fixed home dir uid mismatch, created sudoers, set ganuda-dev group, fixed nftables for Tailscale. Every step was ad-hoc SSH and manual patching. This should be a single chain protocol dispatch: "onboard jsdorn" → runs on all nodes → reports back.

## Step 1: Create `onboard_ring` in Chain Protocol Registry

Add a new ring type to the chain protocol — an **Associate ring** (permanent, not task-scoped) for node onboarding. This is an internal ring, not external, so it doesn't count against the 20% Ring Budget.

Register in the chain registry (DB or config):

```json
{
  "ring_name": "node-onboard",
  "ring_type": "associate",
  "description": "Federation node onboarding — runs node_onboard.sh on target nodes",
  "dispatch_target": "local",
  "script_path": "/ganuda/scripts/node_onboard.sh",
  "requires_sudo": true,
  "target_nodes": ["redfin", "bluefin", "greenfin"],
  "provenance": "chain-protocol-onboard-ring"
}
```

## Step 2: Create Dispatch Wrapper

Create `/ganuda/lib/onboard_dispatch.py`:

```python
"""Chain Protocol ring: dispatch node_onboard.sh across federation nodes.

Usage:
    from onboard_dispatch import onboard_user
    results = onboard_user("jsdorn")
"""

import subprocess
import json
from datetime import datetime

# Nodes with /ganuda that need onboarding
TARGET_NODES = {
    "redfin": "localhost",
    "bluefin": "10.100.0.2",
    "greenfin": "10.100.0.3",
}

ONBOARD_SCRIPT = "/ganuda/scripts/node_onboard.sh"


def onboard_user(username: str, nodes: dict = None) -> dict:
    """Dispatch node_onboard.sh to all target nodes for a user.

    Returns dict of {node_name: {status, output, returncode}}.
    """
    targets = nodes or TARGET_NODES
    results = {}

    for node_name, host in targets.items():
        if host == "localhost":
            cmd = ["sudo", ONBOARD_SCRIPT, username]
        else:
            cmd = [
                "ssh", "-o", "ConnectTimeout=10", host,
                f"sudo {ONBOARD_SCRIPT} {username}"
            ]

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            results[node_name] = {
                "status": "ok" if proc.returncode == 0 else "error",
                "output": proc.stdout[-500:] if proc.stdout else "",
                "stderr": proc.stderr[-200:] if proc.stderr else "",
                "returncode": proc.returncode,
            }
        except subprocess.TimeoutExpired:
            results[node_name] = {
                "status": "timeout",
                "output": "",
                "returncode": -1,
            }
        except Exception as e:
            results[node_name] = {
                "status": "error",
                "output": str(e),
                "returncode": -1,
            }

    return {
        "username": username,
        "timestamp": datetime.now().isoformat(),
        "nodes": results,
        "all_ok": all(r["status"] == "ok" for r in results.values()),
    }
```

## Step 3: Add FreeIPA Pre-flight

Before dispatching to nodes, the onboard flow should verify FreeIPA state. Create a pre-flight check that runs on greenfin (jump host to silverfin):

1. Verify user exists in FreeIPA: `ipa user-show <username>`
2. Verify user is in `ganuda-dev` group: `ipa group-show ganuda-dev`
3. Verify user is in `admins` group (if admin access needed)
4. Verify `ganuda-service-management` sudo rule includes user
5. If any of these fail, fix them before dispatching to nodes

Store the FreeIPA admin credential reference — do NOT hardcode passwords. Use `/ganuda/config/secrets.env` entry `FREEIPA_ADMIN_PASS` (to be added).

## Step 4: Add nftables Check

The onboard script should also verify that the node's nftables allows the user's network. Add to `node_onboard.sh`:

```bash
# --- Step 8: nftables Tailscale check ---
echo "--- Step 8: Tailscale firewall ---"
if command -v nft > /dev/null 2>&1; then
    if nft list ruleset 2>/dev/null | grep -q '100.64.0.0/10'; then
        ok "Tailscale CGNAT range allowed in nftables"
    else
        warn "Tailscale range 100.64.0.0/10 NOT in nftables. Remote Tailscale users may be blocked."
    fi
else
    ok "No nftables on this node (open by default)"
fi
```

## Step 5: Telegram Notification

After dispatch completes, send a summary to the Telegram group:

```
Federation Onboard: <username>
Nodes: redfin ✓ | bluefin ✓ | greenfin ✓
FreeIPA: ganuda-dev ✓ | admins ✓ | sudo ✓
Status: All clear. User can SSH to any node.
```

## Step 6: Thermalize

```sql
INSERT INTO thermal_memory_archive (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
VALUES (
  'Chain Protocol onboard ring operational. Dispatches node_onboard.sh across federation nodes via SSH. Handles FreeIPA pre-flight, local account conflict removal, home dir creation, sudoers, ganuda-dev group, DB connectivity, nftables Tailscale check. First use: jsdorn onboard Mar 13 2026.',
  68, 'infrastructure', false,
  encode(sha256(('chain-onboard-ring-' || NOW()::text)::bytea), 'hex')
);
```

## DO NOT

- Hardcode any passwords in scripts or Python files — use secrets.env
- Skip the FreeIPA pre-flight — a user MUST exist in FreeIPA before node onboarding
- Run the onboard script on DMZ nodes (owlfin/eaglefin) — they have no /ganuda
- Remove the manual `node_onboard.sh` — it's still useful for single-node recovery

## Acceptance Criteria

- `/ganuda/lib/onboard_dispatch.py` exists and can dispatch to all 3 nodes
- Chain protocol registry has `node-onboard` ring entry
- `node_onboard.sh` has nftables Tailscale check (Step 8)
- FreeIPA pre-flight runs before node dispatch
- Telegram summary sent after completion
- Thermal result stored
- Running `onboard_user("jsdorn")` produces all-green on redfin, bluefin, greenfin
