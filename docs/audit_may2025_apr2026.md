# Federation Audit: May 2025 → April 2026

**Council vote:** `867fa8dca023efd9` (APPROVED 8-0-5, high-stakes)
**Scan date:** 2026-04-18
**Scope:** 5 nodes, both primary filesystems, mtime ≥ 2025-05-01
**Executed by:** TPM (direct, per Easy Button Principle, due to cluster collapse urgency)

## Headline numbers

| Node | Files since May 2025 | Sensitive (raw) | Sensitive (filtered) |
|---|---:|---:|---:|
| redfin | 1,030,641 | 96 | 68 |
| bluefin | 7,027 | 1 | 1 |
| greenfin | 4,882 | 7 | 5 |
| sasass2 | 612 | 2 | 2 |
| bmasass | 33,486 | 27 | 21 |
| **TOTAL** | **1,076,648** | **133** | **97** |

Redfin holds 95% of post-May-2025 activity. Most of its bulk is `/ganuda/data` (ML datasets, sky_events timeseries, Tribe Build recording) and `/ganuda/tmp` (scratch). The work-identifying signal lives in `home/`, `experiments/`, `research/`, `pathfinder/`, `docs/`.

## The prior iteration's lair

**`/ganuda/home/dereadi/old_dereadi_data/`** on redfin is the primary archaeological site. Explicit "old" naming, mtime Jul–Nov 2025 (pre-federation). Contains:

- `old_dereadi_data/scripts/claude/` — prior-era Claude scripts (discord-vc-llm, robin_stocks, .etrade_credentials.sh, ganuda_ai_v2/desktop_assistant)
- `old_dereadi_data/Ganuda_ai/infra/.env.template` (Oct 2025) — pre-federation infra config
- `old_dereadi_data/.ssh/` — prior SSH identity (id_ed25519, authorized_keys empty)
- `old_dereadi_data/.gmail_credentials/` — earlier Gmail cred
- `old_dereadi_data/.claude/.credentials.json` — prior Claude session
- `old_dereadi_data/.config/kdeconnect/` — device trust certs July 2025

These are the **prior Council's property**. Per Council mandate, they need to be securely reclaimed: consolidate, rotate any still-live credentials, archive the rest under encrypted vault.

## Real secrets needing attention

### Currently active (don't disturb until consolidated)
- `/ganuda/config/secrets.env` — **replicated across all 5 nodes** at identical 2026-03-12 mtime. This is the federation's main synced secrets file. Confirms a working sync mechanism.
- `/ganuda/vetassist/backend/.env` + `keys/va_ccg_private.pem` (2026-01-20, 2026-02-09)
- `/ganuda/services/ii-researcher/.env` (2026-02-09)
- `/ganuda/services/moltbook_proxy/.env` (2026-03-25)
- `/ganuda/services/moltbook-mcp/providers/credentials.js` (2026-02-05)
- `/ganuda/services/power_monitor/anker-solix-api/.env` (redfin + greenfin, 2026-02-11)
- `/ganuda/home/dereadi/.gmail_credentials/credentials.json` (2026-02-11, plus .corrupted + .encrypted + .backup variants — drift)
- `/ganuda/home/dereadi/.claude/.credentials.json` (2026-04-18)
- `/ganuda/home/dereadi/.ansible/.../vault/private.pem` + public.pem (freeipa vault, 2026-02-06)

### Pre-federation / early-federation (candidates for reclaim-then-retire)
- `/ganuda/pathfinder/.env.pathfinder` (2025-08-08) — pathfinder precursor project
- `/ganuda/home/dereadi/trade_executor.env` (2025-11-12) + backup
- `/ganuda/home/dereadi/.secrets/constitutional_secrets.env` + `.encrypted` (2025-11-11) — Cherokee Constitutional AI era, both plain AND encrypted exist side-by-side
- `/ganuda/home/dereadi/.secrets/redfin_secrets.env` + `.encrypted` (2025-11-11) — same pattern
- `/ganuda/home/dereadi/.secrets/test.env` (2025-11-11) — likely retire
- `/ganuda/home/dereadi/.ssh/ganuda_github` (2025-11-10) — GitHub deploy key

### Old-era (from `old_dereadi_data`, archive-candidate)
Listed above in "prior iteration's lair" section.

### False positives scrubbed
Rust docs (`.rustup/toolchains/**/*env*.html`), vllm-source build configs, `.env.example` templates, homebrew-bundled CA certs, `llama.cpp/docs/**/idea-arch.key` (Keynote file, not a private key — 488KB gives it away).

## Top directories by node (where the post-May-2025 work lives)

### redfin (the workhorse)
```
  505,131  data          — datasets (sky_events timeseries, resumes, transcripts, tribe_meeting_dec17)
  297,066  tmp           — scratch; skip per Partner policy
  121,339  home          — user scratch incl. old_dereadi_data
   36,755  services      — active services
   36,392  src           — source checkouts (vllm-source, etc.)
    6,076  experiments   — jane-street, rl_reward_research, qwen context tests
    3,422  pathfinder    — pre-federation project, Aug-Sep 2025
    2,953  docs
    1,874  research
    1,689  llama.cpp
```

### bmasass
```
   11,859  home
   10,542  cherokee_desktop  — Cherokee Desktop app (includes 3kh0-lite-main embedded web games)
    3,349  pathfinder
    1,829  research
      969  data
      683  experiments
      581  fara              — FARA agent code
      435  cherokee_resonance_training
      396  document_jr_context
      388  docs
```

### sasass2 (sparse, mostly experiments)
```
      512  experiments
       16  models
       15  logs
       10  ansible
```

### bluefin (lightweight, services-focused)
```
    3,791  data
    2,130  home
      644  experiments
       69  prometheus
       68  models
       41  services / docs
       39  homeassistant
       26  vetassist
```

### greenfin (research node)
```
    2,263  bitnet          — BitNet research
    1,207  services
      600  experiments
      373  vetassist
       88  models
       44  calm_research   — unclear purpose, pre-federation?
```

## Directories Partner should eyeball personally

1. **`/ganuda/home/dereadi/old_dereadi_data/`** — prior Council era, needs triage
2. **`/ganuda/pathfinder/`** — pre-federation project (Aug 2025 start, still files modified through Feb 2026)
3. **`/ganuda/research/`** — 1874 files on redfin, 1829 on bmasass
4. **`/ganuda/cherokee_resonance_training/`** — 435 files on bmasass; unclear if referenced elsewhere
5. **`/ganuda/document_jr_context/`** — 396 files on bmasass
6. **`/ganuda/bitnet/`** — 2263 files on greenfin
7. **`/ganuda/calm_research/`** — 44 files on greenfin, unknown project
8. **`/ganuda/experiments/rl_reward_research/`** — Reagent, ART, agent-lightning experiments (Jan 2026)
9. **`/ganuda/experiments/jane-street/`** — unclear context
10. **`/Users/Shared/ganuda/.secrets/`** on bmasass — per-node secret stash with encrypted + plain variants

## Cluster-health observations surfaced incidentally

- Both Linux nodes (bluefin, greenfin) show "System restart required" at SSH login — pending kernel updates not applied
- Redfin's `/ganuda/config/secrets.env` was last synced 2026-03-12 (~5 weeks ago) — sync may be stale
- Gmail credentials drift: `.json` + `.json.corrupted` + `.json.backup` + `.json.encrypted` all coexist — consolidation needed
- `.secrets/constitutional_secrets.env` exists BOTH as plain and `.encrypted` side-by-side on redfin and bmasass — the encrypted-only invariant failed

## Recommendations for second Council review

1. **Immediate:** Consolidate and rotate any still-live credentials in `old_dereadi_data` before they can be accidentally referenced
2. **Short-term:** Run a second scan focused only on `old_dereadi_data` with content-enabled inventory (Council-approved, since it's our own property) to classify each file as keep/archive/retire
3. **Medium-term:** Establish a `/ganuda/vault/` encrypted archive for pre-federation artifacts; migrate `old_dereadi_data` there
4. **Cluster-revival priority:** Bluefin and greenfin both need their kernel updates + restart sequencing coordinated

## Raw outputs
- `/ganuda/state/audit_may2025_apr2026/{redfin,bluefin,greenfin,sasass2,bmasass}.json`
