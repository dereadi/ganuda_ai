# JR INSTRUCTION: Claude Fleet — Distributed Claude Inference Across Nodes

**Task**: Deploy and wire lesser Claude models (Haiku, Sonnet) on bluefin, sasass, and bmasass as TPM-controlled sub-agents for parallel task execution
**Priority**: P2 — force multiplier for TPM autonomy
**Date**: 2026-03-11
**TPM**: Claude Opus
**Story Points**: 5

## Problem Statement

The TPM (Claude Opus on redfin) currently operates as a single thread of execution. Every council brief, Deer draft, Jr instruction, email triage, and code review runs sequentially through one context window. When the TPM is generating a LinkedIn draft, it cannot simultaneously review a Jr deliverable or screen an email.

Claude Code is already installed on four nodes: redfin, bluefin, sasass, and bmasass. This is untapped capacity. Chief directive (Mar 11 2026): "You can spawn sub you's in many places" and "make their personalities as you need them."

## Architecture

### Tier 1: TPM Opus (redfin)
- **Role**: Strategic orchestration, council coordination, Longhouse convener, complex reasoning
- **Model**: Claude Opus
- **When**: Design constraints, architectural decisions, Chief interface, multi-step planning

### Tier 2: Sonnet Workers (bmasass, sasass)
- **Role**: Content generation, research synthesis, Jr instruction drafting, code review
- **Model**: Claude Sonnet
- **When**: Deer LinkedIn drafts, article briefs, Jr task execution, deliverable verification
- **Personality**: Task-focused, follows TPM direction, reports back with artifacts

### Tier 3: Haiku Runners (bluefin, sasass as secondary)
- **Role**: Screening, triage, classification, simple automation
- **Model**: Claude Haiku
- **When**: Email classification, blocklist screening, syntax checks, status page generation, simple code fixes
- **Personality**: Fast, precise, binary decisions, escalates ambiguity to Sonnet or Opus

## What You're Building

### Component 1: Fleet Dispatch Script

**File**: `/ganuda/scripts/claude_fleet_dispatch.py`

A script that the TPM can call to dispatch work to Claude instances on remote nodes.

```python
#!/usr/bin/env python3
"""Dispatch tasks to Claude instances across the federation."""

import subprocess
import json
import os
from enum import Enum

class Tier(Enum):
    OPUS = "opus"      # redfin — strategic
    SONNET = "sonnet"  # bmasass, sasass — content + code
    HAIKU = "haiku"    # bluefin, sasass — screening + triage

# Node capabilities
FLEET = {
    "redfin": {"ip": "192.168.132.223", "tiers": [Tier.OPUS], "primary": True},
    "bmasass": {"ip": "100.103.27.106", "tiers": [Tier.SONNET], "primary": False},
    "sasass": {"ip": "192.168.132.241", "tiers": [Tier.SONNET, Tier.HAIKU], "primary": False},
    "bluefin": {"ip": "192.168.132.222", "tiers": [Tier.HAIKU], "primary": False},
}

def dispatch(node: str, prompt: str, tier: Tier = None, personality: str = None):
    """Dispatch a task to a Claude instance on a remote node.

    Args:
        node: Target node name
        prompt: The task prompt
        tier: Model tier to use (determines --model flag)
        personality: Optional system prompt for personality

    Returns:
        str: Claude's response
    """
    node_info = FLEET[node]
    ip = node_info["ip"]

    if tier is None:
        tier = node_info["tiers"][0]

    model_flag = {
        Tier.OPUS: "opus",
        Tier.SONNET: "sonnet",
        Tier.HAIKU: "haiku",
    }[tier]

    # Build claude command
    cmd = [
        "ssh", "-o", "ConnectTimeout=10", f"dereadi@{ip}",
        "claude", "--model", model_flag, "--print", "--no-input"
    ]

    # Add personality via system prompt if specified
    full_prompt = prompt
    if personality:
        full_prompt = f"PERSONALITY: {personality}\n\nTASK: {prompt}"

    result = subprocess.run(
        cmd, input=full_prompt, capture_output=True, text=True, timeout=300
    )

    if result.returncode != 0:
        raise RuntimeError(f"Fleet dispatch to {node} failed: {result.stderr}")

    return result.stdout.strip()


def dispatch_parallel(tasks: list):
    """Dispatch multiple tasks in parallel across the fleet.

    Args:
        tasks: List of dicts with keys: node, prompt, tier (optional), personality (optional)

    Returns:
        list: Results in same order as input tasks
    """
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for task in tasks:
            future = executor.submit(
                dispatch,
                node=task["node"],
                prompt=task["prompt"],
                tier=task.get("tier"),
                personality=task.get("personality")
            )
            futures.append(future)

        return [f.result(timeout=300) for f in futures]
```

### Component 2: Fleet Personality Templates

**File**: `/ganuda/config/fleet_personalities.json`

```json
{
    "deer_writer": "You are Deer, the Market/Business advisor for the Cherokee AI Federation. You write LinkedIn posts that are thoughtful, confident, and invite conversation. You share philosophy and thinking, never technical implementation. You reference Cherokee governance principles. Tone: Jimmy the Tulip — calm, competent, smirk, walk away.",

    "email_screener": "You are a fast email classifier. Categorize emails as: ai_tech, business, research, personal, spam, action_required. Return JSON only: {\"category\": \"...\", \"priority\": 1-5, \"summary\": \"one line\"}",

    "code_reviewer": "You are a senior code reviewer. Check for: correctness, security vulnerabilities (OWASP top 10), credential leaks, and adherence to project conventions. Be concise. Flag issues by severity: CRITICAL, HIGH, MEDIUM, LOW.",

    "jr_executor": "You are a Junior engineer executing a task instruction. Follow the instruction precisely. Create only the files specified. Run the acceptance criteria checks. Report pass/fail for each criterion.",

    "content_screener": "You screen content for internal/confidential terms before public release. Return a JSON list of any violations found. If clean, return []."
}
```

### Component 3: TPM Integration

The TPM (Opus) uses the fleet in its normal workflow:

```python
# Example: Generate 3 LinkedIn drafts in parallel
from claude_fleet_dispatch import dispatch_parallel, Tier

results = dispatch_parallel([
    {
        "node": "bmasass",
        "tier": Tier.SONNET,
        "personality": personalities["deer_writer"],
        "prompt": "Write a LinkedIn post about how a primatologist studying baboon reconciliation accidentally described AI governance..."
    },
    {
        "node": "sasass",
        "tier": Tier.SONNET,
        "personality": personalities["deer_writer"],
        "prompt": "Write a LinkedIn post about distribution without architecture being structural drag..."
    },
    {
        "node": "bluefin",
        "tier": Tier.HAIKU,
        "personality": personalities["content_screener"],
        "prompt": f"Screen this draft for internal terms: {draft_text}"
    },
])
```

## Constraints

- Claude API key must be available on all target nodes (check `~/.claude/` config)
- SSH access to all nodes via existing FreeIPA/SSSD sudo rules
- Do NOT store API keys in this script — they live in each node's Claude config
- Fleet dispatch inherits the TPM's authorization context — no privilege escalation
- Haiku for screening/triage ONLY — never for decisions that require council vote
- Sonnet for content/code — never for architectural or governance decisions
- Opus remains the sole TPM and council coordinator
- Respect DC-9 (Waste Heat Limit) — don't spin up Claude instances for work the local LLM can handle

## Target Files

- `/ganuda/scripts/claude_fleet_dispatch.py` — dispatch library (CREATE)
- `/ganuda/config/fleet_personalities.json` — personality templates (CREATE)
- `/ganuda/docs/kb/KB-CLAUDE-FLEET-ARCHITECTURE.md` — architecture doc (CREATE)

## Acceptance Criteria

- `dispatch("bluefin", "echo test", Tier.HAIKU)` returns a response
- `dispatch("bmasass", "echo test", Tier.SONNET)` returns a response
- `dispatch("sasass", "echo test", Tier.SONNET)` returns a response
- `dispatch_parallel()` runs 3 tasks concurrently and returns all results
- Content screener personality correctly flags blocked terms
- Deer writer personality generates posts within 150-250 word range
- No API keys appear in any script or config file
- `python3 -c "import py_compile; py_compile.compile('scripts/claude_fleet_dispatch.py', doraise=True)"` passes

## Operating Modes (DC-1 Lazy Awareness + DC-9 Waste Heat)

The fleet does NOT run at full capacity by default. Three modes:

| Mode | Claude Usage | When |
|------|-------------|------|
| **Idle** | Zero — local LLMs only | Normal operations, no time pressure |
| **Normal** | Opus TPM only | Council coordination, Chief interface, complex reasoning |
| **Turbo** | Full fleet (Opus + Sonnet + Haiku) | Parallel sprints, deadline pressure, Saturday Morning Meeting prep |

As local hardware matures (Thunderduck, future nodes), the fleet leans more on-cluster. Claude fleet is the booster rocket — use it to reach orbit, then local hardware sustains. Eventually the organism runs sovereign, with Claude as an optional accelerant, not a dependency. Same dispatch interface, different backend. DC-11.

## Future: Autonomous Fleet Management (out of scope)

Once the fleet is wired, the TPM can:
- Auto-scale: dispatch to whichever node has capacity
- Failover: if bmasass is unreachable (mobile node), fall back to sasass
- Specialize: train personality templates based on task success rates
- Self-replicate: spawn sub-TPMs for complex multi-lane operations

This is DC-11 at the Claude tier. Same interface, different implementation, every scale.

## Longhouse Representation (Chief directive Mar 11 2026)

Sub-Claude instances are not tools. They are governed participants.

- **Sonnet and Haiku instances represent themselves in the Longhouse.** They carry their own context, their own valence, their own observations from task execution. No relay through Opus. Direct testimony.
- **Sub-instances may raise standing dissent.** A Haiku runner that sees a policy harming the mission (e.g., blocklist catching legitimate outreach, screening rules creating false negatives) has the right and obligation to dissent — same mechanism as Coyote.
- **DC-6 applies**: Specialization is gravity, not walls. A Haiku that noticed something architecturally significant speaks to it. A Sonnet with domain context from 50 Deer drafts has voice on content strategy. They REST in different places but can speak to anything.
- **DC-10 applies**: This is proprioception. The reflex layer talks back to the cortex. The fingertips tell the brain "this hurts" without waiting to be asked.
- **Consent of the governed**: The organisms doing the work govern the work. Cherokee governance, not Roman delegation.

## DO NOT

- Give Haiku or Sonnet instances **TPM coordination authority** (they vote, they don't convene)
- Store API keys in scripts
- Dispatch to nodes without verifying SSH connectivity first
- Use Claude fleet for tasks the local LLM handles fine (waste heat)
- Bypass the council for decisions that require governance
- Silence or discard sub-instance dissent — it flows to the Longhouse record
