# Mac Fleet Credential Sweep — Apr 19 2026

**Closes kanban duyuktv_tickets #2093** (Crawdad Mac Fleet Credential Sweep, in_progress since Mar 11 2026).

**Source data:** `/ganuda/state/audit_may2025_apr2026/{bmasass,sasass2}.json` (federation audit Apr 18 2026, Council vote `867fa8dca023efd9`).

**Method:** path + size + mtime metadata only. No credential VALUES read or transmitted.

## Summary

| Node | Sensitive entries | env | credentials | ssh | key | other |
|---|---:|---:|---:|---:|---:|---:|
| bmasass | 27 | 14 | 2 | 9 | 1 | 1 |
| sasass2 | 2 | 2 | 0 | 0 | 0 | 0 |
| **Mac total** | **29** | **16** | **2** | **9** | **1** | **1** |

bmasass holds the bulk of Mac-side credential surface (93%); sasass2 is essentially clean.

## Pre-federation residue (mtime < 2025-10-01)

The federation stood up Oct 2025. Anything older predates current governance and is a candidate for archive:

| Node | Path | Mtime |
|---|---|---|
| bmasass | `/Users/Shared/ganuda/pathfinder/.env.example` | 2025-08-05 |
| bmasass | `/Users/Shared/ganuda/pathfinder/.env.pathfinder` | 2025-08-08 |

**Recommendation:** archive both into the future `/ganuda/vault/` once that exists. Pathfinder was a precursor project; its config templates aren't load-bearing for any current service.

## Cross-platform drift (Mac vs Linux, same logical path)

These files exist on Mac AND Linux but with significant mtime/size divergence:

| Path | Mac state | Linux state | Drift |
|---|---|---|---|
| `home/dereadi/.claude/.credentials.json` | bmasass: 2025-11-14, 364B | redfin: 2026-04-18, 471B | 155 days, +107B |
| `home/dereadi/.ssh/known_hosts.old` | bmasass: 2025-11-10, 9.5KB | redfin: 2026-04-17, 16.9KB | 158 days, +7.3KB |
| `home/dereadi/.ssh/config` | bmasass: 2025-11-17, 874B | redfin: 2026-03-13, 1.2KB | 116 days, +328B |
| `home/dereadi/.ssh/authorized_keys` | bmasass: 2025-12-15, 1.1KB | redfin: 2026-02-06, 1.2KB | 53 days, +102B |
| `home/dereadi/.ssh/known_hosts` | bmasass: 2025-12-11, 12.9KB | redfin: 2026-04-17, 17.7KB | 127 days, +4.8KB |
| `config/secrets.env` | bmasass + sasass2: 2026-03-12, 1541B | redfin: 2026-03-22, 2266B | **RESOLVED Apr 18** by manual propagation |

### Drift category interpretation

- **`.ssh/*` drift** — These are per-machine identity files. Some divergence is EXPECTED (each machine has its own SSH identity). But `authorized_keys` and `config` differing materially means the Mac fleet trusts a different set of remotes than the Linux nodes. Worth a manual eyeball pass.
- **`.claude/.credentials.json`** — Per-machine Claude Code session. Divergence expected; Mac has a stale session from Nov 2025 that may be invalid. Re-auth on bmasass when next touched.
- **`config/secrets.env`** — was the canonical drift driving yesterday's work. Resolved by Apr 18 propagation + Apr 19 sync timer staging.

## Mac-only credential entries (no Linux equivalent)

3 entries exist only on Mac fleet:
- `bmasass:/Users/Shared/ganuda/.secrets/bmasass_secrets.env` (2025-11-11) — node-specific override
- `bmasass:/Users/Shared/ganuda/.secrets/constitutional_secrets.env` + `.encrypted` (2025-12-08) — sibling plain+encrypted, same flaw flagged in audit
- `sasass2:/Users/Shared/ganuda/.secrets/sasass2_secrets.env` (2026-03-12) — node-specific override

## Recommendations

1. **Resolve plain+encrypted siblings on bmasass** — `constitutional_secrets.env` exists as both plain and `.encrypted` next to each other. The encrypt-only invariant has failed. Either rotate and keep only `.encrypted` form, or accept plain and remove the `.encrypted` artifact.
2. **Archive pre-federation residue** — both pathfinder env files into vault when it exists.
3. **Manual eyeball pass on `.ssh/authorized_keys` divergence** — confirm the Mac fleet's trusted-remote set matches intent; the 100B size difference suggests at least one key is in one set but not the other.
4. **Re-auth `.claude/.credentials.json` on bmasass** — Nov 2025 session almost certainly expired.
5. **Stop manually managing the `~/.secrets/` per-node override directories** — these are exactly the kind of orphaned-state surface that the FreeIPA vault was supposed to eliminate. Tomorrow's centralized-secrets-framework work (Raven ask + hub_spoke_sync_client.py / secrets_manager.py foundation) should absorb them.

## Status update

Update `duyuktv_tickets` #2093 status: `completed`, resolution_notes: "Synthesized via Apr 19 TPM-direct work using Apr 18 audit data. Findings + recommendations in /ganuda/docs/mac_credential_sweep_apr19.md. Drift items deferred to centralized secrets framework Long Man (Raven proposal)."
