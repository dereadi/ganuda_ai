# JR INSTRUCTION: sasass2 Triage — Thunderduck Zero

**Task**: Triage sasass2 (192.168.132.242) — fix crash loops, scrub credentials, rotate logs, thermalize founding artifacts
**Priority**: P1 — credential leak + crash-looping daemons
**Date**: 2026-03-11
**TPM**: Claude Opus
**Story Points**: 5
**Council Vote**: #8883 (audit 9567c2be06611b35), APPROVED WITH CONDITIONS (0.887)
**Chief Context**: "It was the first thunderduck." sasass2 has been running autonomously for 18+ days with no human operator — cluster-managed before we even named the concept.

## Problem Statement

sasass2 is BigMac's node (Dr. Joe's hardware at 192.168.132.242). Inventory revealed: 3 crash-looping daemons hemorrhaging error logs (335 MB), a hardcoded DB credential in source code, 900 MB of log bloat (64% of node footprint), and 8 pre-federation artifacts that were never thermalized. The node is alive — hub-spoke sync client and Three Chiefs Triad are actively running — but it's bleeding disk space and leaking a credential.

## What You're Building

### Step 1: URGENT — Stop the Hemorrhage

SSH to sasass2 (192.168.132.242 or Tailscale). The three crash-looping daemons are:

- `executive_jr` — failing on `import requests`
- `memory_jr` — failing on `import requests`
- `meta_jr` — failing on `import requests`

**Option A** (preferred): Install the missing module:
```bash
# Find the Python environment these daemons use
ps aux | grep -E 'executive_jr|memory_jr|meta_jr'
# Install requests in that environment
pip install requests
```

**Option B** (if daemons are orphaned/unnecessary): Disable them:
```bash
# If they're launchd services on macOS
launchctl list | grep -E 'executive|memory|meta'
# Unload them
launchctl unload <plist_path>
```

After fixing, verify they either run clean or are stopped. **Do not leave them crash-looping.**

### Step 2: URGENT — Credential Scrub

File: `/Users/Shared/ganuda/lib/xontrib_cherokee.py`

Contains hardcoded DB password `jawaseatlasers2`. This is a Crawdad violation.

1. Replace the hardcoded password with environment variable lookup:

**File:** `/Users/Shared/ganuda/lib/xontrib_cherokee.py`

```python
import os
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
```

2. If the file has other hardcoded credentials, scrub them all.
3. Verify the password is NOT in git history. If it is, flag for Chief — may need rotation.

### Step 3: Log Rotation

The following logs are bloated:

| Log | Size | Status |
|-----|------|--------|
| Hub-spoke sync client | ~180 MB | Active (still writing) |
| executive_jr errors | ~110 MB | Crash loop output |
| memory_jr errors | ~110 MB | Crash loop output |
| meta_jr errors | ~115 MB | Crash loop output |
| Misc | ~385 MB | Various |

Actions:
1. **Crash loop logs**: Truncate after Step 1 fixes the root cause. `> /path/to/logfile` or `truncate -s 0`
2. **Hub-spoke sync log**: Rotate (copy to `.1`, truncate active). Do NOT delete — this is a live service.
3. **Set up basic log rotation**: Create a cron job or launchd plist that truncates logs over 50 MB weekly.

Target: Reclaim ~800 MB. Node should be under 600 MB after cleanup.

### Step 4: Thermalize Founding Artifacts

These 8 artifacts predate the federation's formal memory system. Each needs to be read, summarized, and stored as a thermal memory with appropriate temperature.

| Artifact | Location (approximate) | Thermal Domain | Suggested Temp |
|----------|----------------------|----------------|----------------|
| Jane Street Track 2 Solver | `scripts/` or `challenges/` | engineering | 65 |
| Two Chiefs CALM Response | `docs/` or root | governance | 80 |
| BIGMAC Ally Spoke Architecture | `docs/` or `config/` | architecture | 75 |
| FedAttn Participant | `lib/` or `scripts/` | research | 78 |
| Grossberg ART Study | `docs/` or `research/` | research | 82 |
| SAG Revenue Architecture | `docs/` or `business/` | business | 70 |
| Triad DB Redesign | `docs/` or `scripts/` | architecture | 68 |
| FARA Browser Scripts | `scripts/` or `fara/` | engineering | 60 |

For each artifact:
1. Read the file content
2. Summarize in 2-3 sentences (what it is, why it matters, when it was created if determinable)
3. Insert into `thermal_memory_archive` on bluefin (192.168.132.222):
```sql
INSERT INTO thermal_memory_archive (original_content, temperature_score, domain_tag, sacred_pattern)
VALUES (%s, %s, %s, false);
```
4. For the Two Chiefs CALM Response and Grossberg ART Study — if content is genuinely foundational, flag for sacred review.

### Step 5: Inventory Live Services

Document what's actively running on sasass2:

1. Hub-spoke sync client — what is it syncing? To where? Is it still needed?
2. Three Chiefs Triad process — 18 days uptime. What does it do? Still relevant?
3. T5-small model (242 MB) — is anything using it? If orphaned, flag for removal.

Write findings to `/Users/Shared/ganuda/docs/SASASS2_SERVICE_INVENTORY.md`.

## Council Conditions (Vote #8883)

1. **Coyote**: Credential rotation must happen BEFORE or SIMULTANEOUSLY with the scrub. Treat the exposed credential as **compromised** after 18+ days of exposure. Flag for TPM/Chief if rotation is needed at the DB level.
2. **Spider**: The three fixed daemons must be added to **Fire Guard watchlist** as part of this task. No triage without governance wiring.
3. **Crawdad**: Log rotation requires a **PII scan pass** before deletion. Thermalize the scan result as an audit record.
4. **Turtle**: Each of the 8 founding artifacts needs a **3-sentence provenance note** before thermalization (what it is, when it was created, why it matters).

## Constraints

- **Crawdad**: Credential scrub is highest priority. No hardcoded passwords in source. PII scan logs before truncation.
- **Coyote**: Treat exposed credential as compromised. Rotation before or with scrub.
- **Spider**: Wire fixed daemons into Fire Guard after triage.
- **Turtle**: Do NOT delete artifacts. Thermalize with provenance notes first, then flag originals for archival decision.
- **DC-7**: These artifacts survived the fire. They're conserved sequences from prior civilizations. Treat them with respect.
- sasass2 is macOS. Commands differ from Linux nodes (launchctl not systemctl, etc.)
- Hub-spoke sync client is LIVE. Do not kill it without understanding what it does first.
- This node may be Dr. Joe's hardware. Be respectful of shared space.

## Target Files

- `/Users/Shared/ganuda/lib/xontrib_cherokee.py` — credential scrub (MODIFY)
- `/Users/Shared/ganuda/docs/SASASS2_SERVICE_INVENTORY.md` — service inventory (CREATE)
- 8 thermal_memory_archive inserts on bluefin (CREATE)
- Cron/launchd log rotation config (CREATE)

## Acceptance Criteria

- No crash-looping daemons (either fixed or disabled)
- No hardcoded credentials in any source file on sasass2
- Log footprint reduced from ~900 MB to under 100 MB
- All 8 artifacts thermalized with appropriate domain tags and temperatures
- Live services documented with status and purpose
- Total node footprint under 600 MB after cleanup

## DO NOT

- Delete any artifact files before thermalizing them
- Kill the hub-spoke sync client without understanding it first
- Ignore the credential leak — this is P0 within the P1
- Leave crash-looping daemons running after triage
- Thermalize artifacts at sacred temperature — flag for review, don't self-promote

## Historical Note

sasass2 was Thunderduck Zero — the first node running autonomously without a human operator, before the concept was even named. The artifacts on this node are founding stories of the federation. DC-7: what survived the fire IS the architecture.
