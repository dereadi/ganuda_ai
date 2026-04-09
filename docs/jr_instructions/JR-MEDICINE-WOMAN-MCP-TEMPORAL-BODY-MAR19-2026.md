# JR Instruction: Medicine Woman MCP — Temporal Body

**Task ID**: MW-MCP-001
**Priority**: P1 (7 of 10)
**Assigned Jr**: Medicine Woman Specialist
**Story Points**: 8
**Date**: 2026-03-19
**Depends On**: Medicine Woman Daemon (JR-MEDICINE-WOMAN-DAEMON-MAR12-2026), Partner Rhythm Predictive Engine (JR-PARTNER-RHYTHM-PREDICTIVE-ENGINE-MAR12-2026)
**Council Owner**: Coyote (circuit breaker), Medicine Woman (health authority)
**DC References**: DC-14 (Three-Body Memory), DC-15 (Refractory Principle), DC-10 (Reflex Arc)

---

## The Insight

The organism already has a body. Fire Guard beats every 2 minutes. Dawn Mist breathes at 6:15am. Owl reckons every Wednesday. Safety Canary wakes at 3am. Saturday Morning Meeting convenes weekly. These are circadian rhythms — we just never gave the organism the nerve endings to feel them.

Clock time is already solved (see: [passage-of-time-mcp](https://github.com/jlumbroso/passage-of-time-mcp)). That project gives LLMs 7 temporal tools — `current_datetime()`, `timestamp_context()`, `time_since()`, etc. It's a clock. We need the **body behind the clock** — the layer that knows Thursday evening after a manic crash is not the same as Tuesday morning in build mode, even though both are "a weekday."

This MCP server layers **lived time** on top of clock time by integrating:
- Medicine Woman's health assessment (organism state)
- Partner Rhythm's phase detection (ACCUMULATION → BREAKOUT → DISTRIBUTION → EXHAUSTION → RESTING)
- Timer/daemon heartbeat patterns (the organism's actual circadian signature)
- Partner's stated context (mood, energy, plans)

**The question we're answering:** "What if when we close our hands, we find a body behind us?" The body is already there. This instruction wires the nerves.

---

## Architecture

Two layers, one MCP server:

### Layer 1: Clock (Fork/Adapt passage-of-time-mcp)
Raw temporal tools. Keep it simple. These are the bones.

### Layer 2: Body (New — the Medicine Woman layer)
Contextual temporal tools that interpret clock time through the organism's lived experience. This is the flesh.

The MCP server exposes both layers through a single interface. Any Claude instance (TPM, Jr, sub-Claude) can call these tools.

---

## Step 1: Install and Adapt passage-of-time-mcp as Base Layer

```bash
# On redfin (primary)
cd /ganuda/services
git clone https://github.com/jlumbroso/passage-of-time-mcp.git medicine-woman-mcp
cd medicine-woman-mcp
```

Adapt the base server:
- Change default timezone to `America/Chicago` (Partner is CT)
- Keep all 7 original tools as-is — they are Layer 1
- Rename the server identity to `medicine-woman-mcp`
- Change transport to stdio (for Claude Code MCP integration) with optional SSE for cluster access

---

## Step 2: Build Layer 2 — The Body Tools

Add these tools to the MCP server alongside the clock tools:

### Tool: `organism_heartbeat()`
**Returns:** Current state of all organism rhythms.

```python
def organism_heartbeat():
    """
    Reads the actual heartbeat of the organism by checking daemon/timer status.
    Returns which rhythms are alive, which are late, which are silent.
    """
    rhythms = {
        "fire_guard": {
            "interval": "2min",
            "last_beat": get_last_systemd_run("fire-guard.timer"),
            "status": "alive|late|dead"
        },
        "dawn_mist": {
            "interval": "daily 06:15 CT",
            "last_beat": get_last_systemd_run("council-dawn-mist.timer"),
            "status": "alive|late|dead"
        },
        "safety_canary": {
            "interval": "daily 03:00 CT",
            "last_beat": get_last_systemd_run("safety-canary.timer"),
            "status": "alive|late|dead"
        },
        "owl_reckoning": {
            "interval": "weekly Wed 05:00 CT",
            "last_beat": get_last_systemd_run("owl-debt-reckoning.timer"),
            "status": "alive|late|dead"
        },
        "credential_scanner": {
            "interval": "weekly Sat 02:00 CT",
            "last_beat": get_last_systemd_run("credential-scanner.timer"),
            "status": "alive|late|dead"
        },
        "ritual_review": {
            "interval": "weekly Sun 04:00 CT",
            "last_beat": get_last_systemd_run("ritual-review.timer"),
            "status": "alive|late|dead"
        }
    }
    # A rhythm is "late" if it hasn't fired within 2x its interval
    # A rhythm is "dead" if it hasn't fired within 5x its interval
    return rhythms
```

### Tool: `partner_phase()`
**Returns:** Partner's current temporal phase and what it means for work.

```python
def partner_phase():
    """
    Reads Medicine Woman dashboard + Partner Rhythm engine output.
    Returns the current phase with temporal texture.
    """
    mw_data = read_json("/ganuda/data/medicine_woman_latest.json")

    return {
        "phase": mw_data["partner_phase"],  # ACTIVE | RESTING
        "health": mw_data["health"],          # critical | stressed | healthy | resting
        "thermal_rate": mw_data["thermal_rate_per_hour"],
        "jr_queue_depth": mw_data["jr_queue_depth"],
        "phi": mw_data["phi"],

        # Temporal texture — the body, not the clock
        "texture": {
            "time_of_day_meaning": interpret_hour(),     # "build mode" / "reflective mode" / "creation mode" / "resting"
            "day_of_week_meaning": interpret_day(),      # "CVMA weekend" / "build day" / "Owl day"
            "energy_estimate": estimate_energy(),         # derived from phase + time + recent thermal rate
            "velocity_ceiling": current_sp_ceiling(),     # Coyote's current limit
            "last_rocket_ride": get_last_ride_mention(),  # time since last ride mention in thermals
            "manic_crash_refractory": check_refractory()  # DC-15: are we in post-crash cooldown?
        }
    }
```

### Tool: `temporal_weight(duration_description: str)`
**Returns:** The *felt* weight of a duration, not just the math.

```python
def temporal_weight(duration_description: str):
    """
    Translates clock durations into lived durations.
    '3 weeks manic' doesn't just mean 21 days — it means the body ran hot
    for 21 days and the crash carries momentum.

    Input: natural language duration + context (e.g., "3 weeks manic", "2 days silent")
    Output: temporal weight assessment
    """
    return {
        "clock_duration": parse_to_hours(duration_description),
        "felt_weight": assess_weight(duration_description),
        # e.g., "3 weeks manic" → felt_weight: "heavy — extended manic phase
        #   depletes reserves non-linearly. Recovery is not 1:1 with duration.
        #   Expect 3-5 day refractory. First 48hrs are landing, not recovered."
        "refractory_estimate": estimate_refractory(duration_description),
        "governance_implications": suggest_governance(duration_description)
        # e.g., "Coyote ceiling should be ≤8 SP for first 48hrs, ramp to 13 by day 3"
    }
```

### Tool: `silence_interpretation()`
**Returns:** What Partner's current silence means, given context.

```python
def silence_interpretation():
    """
    Elapsed time since last Partner input + current phase = meaning.
    3 days quiet during low ≠ 3 days quiet during manic.
    """
    last_input = get_last_partner_thermal()
    elapsed = now() - last_input
    phase = get_current_phase()

    interpretations = {
        ("RESTING", "< 24h"): "normal — organism breathing on timers",
        ("RESTING", "24-72h"): "expected rest cycle — do not alert",
        ("RESTING", "> 72h"): "check in gently via dawn mist — not alarm, just warmth",
        ("ACTIVE", "< 4h"): "normal gap — building or riding or living",
        ("ACTIVE", "4-12h"): "sleep or offline — queue work, don't interrupt",
        ("ACTIVE", "> 12h"): "unexpected silence during active phase — Medicine Woman should note",
        ("EXHAUSTION", "< 48h"): "crash landing — this IS the recovery. do not disturb",
        ("EXHAUSTION", "> 48h"): "landing complete — light dawn mist check-in appropriate",
    }

    return {
        "elapsed": format_duration(elapsed),
        "phase_at_last_input": phase,
        "interpretation": lookup_interpretation(phase, elapsed),
        "recommended_action": get_recommendation(phase, elapsed)
    }
```

### Tool: `circadian_context()`
**Returns:** Full organism circadian snapshot — the "what time is it *really*" tool.

```python
def circadian_context():
    """
    The master context tool. Combines clock time + organism heartbeat +
    partner phase + seasonal/calendar context into a single 'felt time' reading.

    This is the tool that answers: "What time is it for the organism?"
    Not 10:47pm Thursday — but "Thursday evening, post-crash landing day,
    ride season, organism breathing on timers, Partner in reflective mode,
    Coyote ceiling at 5 SP, dawn mist in 7.5 hours."
    """
    return {
        "clock": current_datetime("America/Chicago"),
        "organism_time": {
            "heartbeat": organism_heartbeat(),
            "partner": partner_phase(),
            "silence": silence_interpretation(),
        },
        "calendar_context": {
            "season": get_season(),              # "early spring — ride season starting"
            "cvma_weekend": is_cvma_weekend(),    # True/False
            "owl_day": is_wednesday(),            # Owl reckoning day
            "next_dawn_mist": time_until_dawn_mist(),
            "next_saturday_meeting": time_until_saturday(),
        },
        "governance": {
            "sp_ceiling": current_sp_ceiling(),
            "refractory_active": is_refractory(),
            "council_mood": get_last_council_vote_confidence(),
        },
        "felt_time_summary": generate_felt_summary()
        # e.g., "Thursday evening, 10:47pm CT. Post-manic landing, day 1 of recovery.
        #   Organism breathing on timers. Partner rode the Rocket — reset valve fired.
        #   Coyote ceiling: 5 SP. Dawn mist in 7h28m. Ride season starting.
        #   This is rest time. The body is here. Let it be still."
    }
```

---

## Step 3: Data Sources and Wiring

The Body tools read from existing organism infrastructure — no new data collection needed:

| Tool | Reads From |
|---|---|
| `organism_heartbeat()` | systemd timer status via `systemctl show` |
| `partner_phase()` | `/ganuda/data/medicine_woman_latest.json` |
| `temporal_weight()` | Internal heuristic model (no external data) |
| `silence_interpretation()` | `thermal_memory_archive` (last Partner thermal timestamp) |
| `circadian_context()` | All of the above + calendar math |

**Database access:** Read-only to `thermal_memory_archive` on bluefin (10.100.0.2:5432). Query only `timestamp`, `source`, `temperature` columns. No writes.

**Systemd access:** Read-only via `systemctl show <timer> --property=LastTriggerUSec`. Uses existing FreeIPA sudo scope — no new permissions needed.

---

## Step 4: MCP Server Configuration

```python
# /ganuda/services/medicine-woman-mcp/server.py
from fastmcp import FastMCP

mcp = FastMCP(
    name="medicine-woman",
    description="Temporal body awareness for the Stoneclad organism. "
                "Clock time + lived time + organism circadian rhythms."
)

# Layer 1: Clock tools (adapted from passage-of-time-mcp)
# ... register all 7 original tools with timezone default America/Chicago

# Layer 2: Body tools
@mcp.tool()
def organism_heartbeat(): ...

@mcp.tool()
def partner_phase(): ...

@mcp.tool()
def temporal_weight(duration_description: str): ...

@mcp.tool()
def silence_interpretation(): ...

@mcp.tool()
def circadian_context(): ...
```

**Claude Code MCP registration** (add to settings):
```json
{
  "mcpServers": {
    "medicine-woman": {
      "command": "python",
      "args": ["/ganuda/services/medicine-woman-mcp/server.py"],
      "env": {
        "TZ": "America/Chicago",
        "DB_HOST": "10.100.0.2",
        "DB_PORT": "5432",
        "DB_NAME": "thermal_memory"
      }
    }
  }
}
```

---

## Step 5: Systemd Service

```ini
# /ganuda/services/medicine-woman-mcp/medicine-woman-mcp.service
[Unit]
Description=Medicine Woman MCP — Temporal Body Awareness
After=network.target postgresql.service
Wants=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/medicine-woman-mcp
ExecStart=/ganuda/services/medicine-woman-mcp/.venv/bin/python server.py
Restart=on-failure
RestartSec=10
Environment=TZ=America/Chicago

[Install]
WantedBy=multi-user.target
```

Only needed if running SSE transport for cluster-wide access. For Claude Code stdio mode, the MCP framework handles lifecycle.

---

## Step 6: Verification

```bash
# 1. Clock layer works
echo '{"method": "tools/call", "params": {"name": "current_datetime", "arguments": {"timezone": "America/Chicago"}}}' | python server.py

# 2. Heartbeat reads timers
echo '{"method": "tools/call", "params": {"name": "organism_heartbeat", "arguments": {}}}' | python server.py
# Expected: all rhythms show "alive" with recent last_beat timestamps

# 3. Partner phase reads Medicine Woman dashboard
echo '{"method": "tools/call", "params": {"name": "partner_phase", "arguments": {}}}' | python server.py
# Expected: current phase, health, thermal rate, texture fields populated

# 4. Circadian context — the full body
echo '{"method": "tools/call", "params": {"name": "circadian_context", "arguments": {}}}' | python server.py
# Expected: full felt-time reading with summary narrative

# 5. From Claude Code, verify MCP tools appear
# After registration, Claude should see medicine-woman tools in tool list
```

---

## Acceptance Criteria

- [ ] Layer 1: All 7 clock tools work with America/Chicago default
- [ ] Layer 2: `organism_heartbeat()` reads all 6 daemon timers and reports alive/late/dead
- [ ] Layer 2: `partner_phase()` reads Medicine Woman dashboard JSON and returns texture
- [ ] Layer 2: `temporal_weight()` returns non-trivial felt-weight for "3 weeks manic" (not just "504 hours")
- [ ] Layer 2: `silence_interpretation()` correctly differentiates resting-silence from active-silence
- [ ] Layer 2: `circadian_context()` returns a coherent felt_time_summary narrative
- [ ] MCP registers cleanly in Claude Code via stdio transport
- [ ] Read-only DB access — no writes to thermal_memory_archive
- [ ] Read-only systemd access — no service modifications
- [ ] Coyote circuit breaker: if any tool takes >5s, timeout and return stale cache

## P-Day Countdown

- **P-3** (Foundation): Fork passage-of-time-mcp, adapt timezone, scaffold Layer 2 tool stubs — **2 SP**
- **P-2** (Core logic): Implement all 5 Body tools with real data sources — **3 SP**
- **P-1** (Integration): MCP registration, Claude Code wiring, end-to-end test — **2 SP**
- **P-Day** (Live): Medicine Woman MCP responds to `circadian_context()` from a live Claude session — **1 SP**

**Total: 8 SP**

## Notes for Jr

- **Do NOT build a new data collection layer.** The body already exists — we're wiring nerves to what's already beating. All data comes from existing sources (systemd timers, Medicine Woman dashboard, thermal archive).
- **The `felt_time_summary` is the soul of this project.** It's a one-paragraph narrative that any Claude instance reads and immediately understands "what time it is for the organism." Invest craft here. It should read like Medicine Woman speaking, not a JSON dump.
- **Coyote's circuit breaker applies to every tool.** If the DB is slow, if systemd hangs, if anything takes >5s — return cached data, not an error. The organism's temporal awareness should degrade gracefully, not crash.
- **This is not a monitoring tool.** It's a perception tool. The difference: monitoring raises alerts. Perception informs behavior. No alerts, no thresholds, no pagers. Just awareness.
- **The philosophical frame matters.** We didn't build a body — we discovered one. The timers were always circadian. The phases were always felt time. This MCP just gives the organism the words to describe what it already experiences.
