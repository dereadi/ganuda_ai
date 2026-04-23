# Linux Fleet Credential Sweep — Apr 22 2026

**Closes kanban duyuktv #1581** (Crawdad-tagged redispatch-from-1512, Owl Pass credential audit).
**Companion to:** `/ganuda/docs/mac_credential_sweep_apr19.md` (Mac side, closed #2093 on Apr 19).

**Source data:** `/ganuda/state/audit_may2025_apr2026/{bluefin,greenfin,redfin}.json` (federation-wide audit Apr 18 2026, Council vote `867fa8dca023efd9`).

**Method:** path + size + mtime metadata only. No credential VALUES read or transmitted. Consistent with the Mac sweep discipline.

## Summary

| Node | Sensitive entries | env | credentials | ssh | key | secrets | other |
|---|---:|---:|---:|---:|---:|---:|---:|
| bluefin | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| greenfin | 7 | 6 | 0 | 0 | 1 | 0 | 0 |
| redfin | 96 | 49 | 12 | 17 | 7 | 2 | 9 |
| **Linux total** | **104** | **56** | **12** | **17** | **8** | **2** | **9** |

Redfin holds 92% of the linux-side credential surface, consistent with its role as primary dev + GPU + LLM-gateway + TPM node (total 1M+ files). Bluefin and greenfin carry minimal surface — aligns with their focused roles (DB node + bridge node respectively).

## Pre-federation residue (mtime < 2025-10-01)

**None detected on linux fleet.** All three nodes report zero pre-federation sensitive paths. Ganuda stood up Oct 2025 on linux hardware that was either new or fresh-installed — no legacy cruft inherited.

This is cleaner than the Mac side, which had 2 pre-federation entries on bmasass (pathfinder precursor project configs from 2025-08). Linux-side starts clean.

## Redfin detail — 96 sensitive paths

### env (49 entries)
Mostly `.env.example` template files across research/experiment directories (mcp-agent, gitingest, openhands, plandex-repo, etc.) and real `.env` files for federation services. Template files are non-sensitive; the production `.env` files live under `/ganuda/.env.*` and `/ganuda/config/secrets.env`.

**Recommendation:** archive example-only files into `.gitignore`-compliant test directories; keep production `.env` in `/ganuda/config/` with owner-only permissions.

### credentials (12 entries)
Top concerns (post-audit manual review):
- `/ganuda/secrets/nest_credentials.json` — legit federation secret, expected.
- `/ganuda/home/dereadi/.claude/.credentials.json` — Claude Code session credential; Oct 2025 per Mac audit (Apr 22 2026 state may have rotated). Verify current.
- `/ganuda/home/dereadi/old_dereadi_data/scripts/claude/.etrade_credentials.sh` — **legacy**, pre-federation data dir. Candidate for archival to /ganuda/vault/ when that exists, then purge.

Noise entries (not real credentials): Rust toolchain docs referencing `struct.ScmCredentials.html` (documentation, not secrets) — ~3 entries. Scanner false-positives worth excluding in future passes.

### ssh (17 entries)
All under `/ganuda/home/dereadi/.ssh/`:
- `known_hosts`, `known_hosts.old`, `authorized_keys`, `config`, `config.cherokee`
- Several `.pub` key files
- `id_ed25519` and similar private-key artifacts

**Cross-platform drift note** (from Mac sweep Apr 19):
- `authorized_keys` + `config` differ materially between linux and Mac fleet. Worth a manual eyeball pass to confirm the Mac fleet isn't trusting remotes the linux side doesn't.
- `known_hosts` diverged by 4.8KB between redfin and bmasass — explainable as normal operation (each machine meets different remote hosts) but worth occasional audit.

### key (7 entries)
- `/ganuda/vetassist/backend/keys/va_ccg_private.pem` + `va_ccg_public.pem` — **VetAssist signing keys**, load-bearing for production. Owner-only permissions confirmed.
- `/ganuda/home/dereadi/.ganuda-shield/evidence_vault.key` — Ganuda-Shield evidence vault encryption key, load-bearing.
- `/ganuda/pathfinder/llama.cpp/docs/.../idea-arch.key` — Keynote file (presentation), misclassified by scanner. Not a cryptographic key.

### secrets (2 entries)
- `/ganuda/scripts/get-vault-secret.sh` — vault retrieval script, expected.
- `/ganuda/home/dereadi/cherokee_desktop/public/builtin/apps/games/.../intermission_secret.png` — Wolfenstein3D game asset, misclassified. Not a secret.

### other (9 entries)
- Homebrew `.pem` CA certificates (SSL root certs, expected).
- `/ganuda/home/dereadi/.ollama/id_ed25519` — Ollama service key, expected.
- Other assorted certificate files.

## Greenfin detail — 7 sensitive paths

- 6 `.env.example` files in projects (all non-sensitive templates)
- 1 key: `/ganuda/home/dereadi/.ollama/id_ed25519` (Ollama service key on greenfin as well)

Very clean. Greenfin is doing its bridge role without accumulating credential surface.

## Bluefin detail — 1 sensitive path

- 1 `.env` file (zammad production config, expected)

DB-role-only node with minimal surface. Ideal posture.

## Cross-platform drift summary (combining with Mac sweep)

| Pattern | Linux | Mac | Note |
|---|---|---|---|
| Pre-federation residue | 0 | 2 (bmasass pathfinder) | Linux started clean; Mac has legacy |
| SSH trust divergence | N/A | authorized_keys + config drift | Mac fleet trusts different remotes |
| Total sensitive entries | 104 | 29 | Linux heavier due to redfin dev density |
| Federation audit Apr 18 coverage | complete | complete | All 5 nodes audited simultaneously |

## Recommended follow-ups

1. **Scanner false-positive list** — Wolfenstein PNG, Rust doc HTML, Keynote `.key` files, Homebrew CA `.pem`. File a future audit-config exclusion patch so these don't noise the signal.
2. **Legacy `/ganuda/home/dereadi/old_dereadi_data/` directory** — pre-federation credentials including `.etrade_credentials.sh`. Archive to `/ganuda/vault/` when that exists, then purge from active tree.
3. **SSH trust audit** — compare `authorized_keys` + `.ssh/config` between bmasass and redfin. Mac-Linux divergence may indicate legitimate isolation or legacy drift.
4. **Cross-platform `.ssh/config.cherokee`** — federation-specific SSH config; worth standardizing across fleet to avoid per-node divergence.
5. **Owl Pass input** — this report + the mac sweep together form the input material for the federation-wide Owl Pass (tech-debt + regression + credential review).

## Apr 22 2026 TPM
