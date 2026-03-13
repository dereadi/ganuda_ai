# [RECURSIVE] sasass2 Triage — Thunderduck Zero (crash loops, credential scrub, thermalize artifacts) - Step 5

**Parent Task**: #1277
**Auto-decomposed**: 2026-03-12T18:01:03.544386
**Original Step Title**: Inventory Live Services

---

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
