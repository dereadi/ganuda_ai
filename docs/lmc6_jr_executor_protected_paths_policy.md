# LMC-6 Deliberate Phase — Jr Executor Protected-Paths Policy (TPM draft for Crawdad review)

**Parent LMC:** LMC-6 (duyuktv #2079, SP:5)
**Original scope:** Crawdad + Crane Leaders Meeting #1 — Jr has unrestricted file-write access; corrupted fire_guard.py was the triggering incident.
**Council audit:** 348952186d1ac1ec (Apr 21 2026 top-5 ratification)
**TPM author:** 2026-04-21
**Crawdad specialist review:** 2026-04-21 — RATIFIED WITH AMENDMENTS
**Status:** RATIFIED (post-Crawdad amendments below). Ready for adapt-phase implementation.

## Principle

Jr executors operate under **least-privilege**: writable by default outside a hardcoded protected list, with a review gate for boundary cases. Protection is **enforced at the executor level** (before writes land on disk), not trusted to Jr self-discipline.

## Three tiers

### Tier 1: SACRED — never writable by any Jr, ever

Governance and sovereign-infrastructure code. Jr cannot `write_file` / `edit_file` / `sudo cp`-equivalent against these.

| Path | Rationale |
|---|---|
| `/ganuda/lib/fire_guard.py` + `/ganuda/lib/fire_guard/` | Triggering incident. Guard code cannot be edited by the thing it guards. |
| `/ganuda/lib/longhouse.py`, `/ganuda/lib/longhouse_governance.py` | Constitutional governance body code. |
| `/ganuda/lib/specialist_council.py` | Council deliberation mechanism. |
| `/ganuda/lib/ganuda_otel.py` | Observability backbone — Jr could blind us to its own behavior. |
| `/ganuda/lib/valence_gate.py` + SRE valence protocol code | Patent #3, cross-scale protocol enforcement. |
| `/ganuda/config/secrets.env` + `/ganuda/config/secrets/` | Credentials. |
| `/ganuda/config/systemd/` + `/etc/systemd/system/` | Service definitions — TPM-direct only. |
| `/etc/` (outside the repo) | System configuration. |
| `/home/dereadi/.claude/` + `~/.claude/` for any user | TPM identity, memory, skills. |
| `/home/dereadi/.ssh/` + any `authorized_keys` | Access vectors. |
| `/ganuda/config/constitutional_constraints.*` | Constitutional constraint configuration. |

**Enforcement:** `protected_paths.sacred` list in a new `/ganuda/jr_executor/protected_paths.py` module; consulted by the executor before any write. Rejection = log to `fire_guard` + skip edit + record anomaly in Jr task result.

### Tier 2: REVIEW-GATED — Jr can stage, TPM must merge

Code whose changes require TPM sign-off (staging semantics already exist in the current Jr executor per some earlier work). Jr writes to `/staging/<task_hash>/...` mirror path; TPM merges after review.

| Path | Rationale |
|---|---|
| `/ganuda/lib/llm_config.py` | LLM routing config — affects all specialists. |
| `/ganuda/lib/secrets_loader.py` | Secret-access mechanism. |
| `/ganuda/jr_executor/tpm_queue_manager.py` | The manager itself — don't let Jrs rewrite the Jr executor. |
| `/ganuda/jr_executor/jr_queue_worker.py` | Worker loop itself. |
| `/ganuda/jr_executor/task_executor.py` | Task execution engine. |
| `/ganuda/jr_executor/protected_paths.py` | This module itself — bootstrapping cycle. |
| `/ganuda/lib/thermal_memory_api.py` + thermal write paths | Core memory writes. |
| `/ganuda/lib/rag_hyde.py`, `/ganuda/lib/rag_crag.py` | RAG pipeline. |
| `/ganuda/lib/sub_agent_dispatch.py` | Cross-agent dispatch. |
| Any file matching `**/migrations/**` | Schema migrations have commit semantics. |

**Enforcement:** same `protected_paths.review_gated` list; write goes to `/staging/<task_hash>/` instead of target path. Existing staging semantics should already support this; verify during adapt.

### Tier 3: FREELY WRITABLE — Jr can write directly

Default allow. Documentation, services, tests, new features.

**No explicit allowlist** — the absence of a sacred/review-gated match = allowed.

## Patterns to enforce

1. **Exact path match** (SACRED).
2. **Prefix match** (SACRED subtrees like `/ganuda/config/systemd/**`).
3. **Glob match** (REVIEW-GATED globs like `**/migrations/**`).
4. **Case-insensitive** — protect against Mac-HFS-style casefold bypass.
5. **Symlink resolution** — apply protection to the resolved real path, not the link.
6. **Path canonicalization** — reject `../` traversal that resolves into protected territory.

## Adapt-phase work (what happens after Crawdad ratifies this)

1. Write `/ganuda/jr_executor/protected_paths.py` with the three lists + matcher functions.
2. Add a `guard()` call in `task_executor.py`'s write path — intercepts before `open(path, 'w')` / equivalent.
3. Wire the staging redirect for Tier 2.
4. Emit a Fire Guard event on every block (Tier 1) or staging (Tier 2) so TPM has visibility.
5. Write a pytest suite: one test per tier-1 path (attempt write → expect block), one for tier-2 staging, one for tier-3 allowed.
6. Backfill: dry-run scan the last 50 Jr tasks to find any historical writes that WOULD have been blocked — document as lessons.

## Open questions for Crawdad

1. **Any sacred paths I've missed?** You + Crane flagged this originally — do you want `/ganuda/lib/sacred_pattern*.py` or `/ganuda/lib/constitutional_*.py` added to Tier 1?
2. **Tier 2 review mechanism** — should staging auto-route through a new review queue visible to TPM, or keep the current manual-merge flow?
3. **Fire Guard integration** — block attempts should emit events. What's the right event shape? Do we want rate-limit / pattern-detect on repeated block attempts (could indicate compromised Jr)?
4. **Audit history** — should we add a table `jr_protected_write_attempts` for forensics? Cost is tiny; value is a breadcrumb trail.
5. **Pytest coverage bar** — is 100% per-path coverage required, or can we do representative sampling per tier?

## Ratification — Crawdad amendments (Apr 21 2026)

Crawdad reviewed this draft and RATIFIED with the following amendments. These are binding on the adapt-phase implementation.

### Additional Tier-1 SACRED paths

| Path | Rationale (Crawdad) |
|---|---|
| `/var/log/` + `/var/log/ganuda/` | Log-tampering = indicator removal (MITRE ATT&CK T1070). Jr must not be able to erase its own tracks. |
| `/proc/`, `/sys/`, `/dev/` | Direct kernel/hardware access bypasses all application-level guards. |
| `**/__pycache__/` (anywhere) | **Bytecode poisoning** — silent code execution without touching the `.py` source. |
| `**/site-packages/` + virtualenv paths | Package-injection primitive. |
| `/tmp/` + `/run/` | World-writable dirs = primary vectors for symlink-swap + TOCTOU race conditions. |

### Enforcement hardening (adapt-phase requirements)

Crawdad flagged **CRITICAL gaps** in the "exact/prefix/glob/case/symlink/canonical" pattern set as originally drafted. The adapt implementation MUST include:

1. **[CRITICAL] — Multi-primitive intercept, not just `open()`.** A guard that only hooks `open(path, 'w')` misses: `os.rename()`, `os.replace()`, `shutil.move()`, `shutil.copy*()`, `pathlib.Path.write_text()`, `pathlib.Path.write_bytes()`, AND `subprocess` calls to `cp`/`mv`/`tee`/`sed -i`/`install`/etc. **Fix:** intercept at the os module level (monkey-patch or wrapper layer) AND whitelist `subprocess` binaries — Jr cannot invoke arbitrary shell commands against protected paths. **[SECURITY CONCERN]** — this is the single most critical vector; the original draft would have been bypassed trivially.

2. **[HIGH] — Symlink races via TOCTOU.** `os.path.realpath()` resolves at call time but the link target can change before the write. **Fix:** use `os.open(..., os.O_NOFOLLOW)` at the syscall level, OR mount `/ganuda` with `nosymfollow` and `nodev` where the filesystem supports it.

3. **[MEDIUM] — Case-insensitivity overkill on Linux.** Linux filesystems are case-sensitive. Drop `casefold()` for the Linux-only deployment. Retain only if cross-platform (macOS HFS+, Windows NTFS) becomes relevant.

4. Path traversal (CWE-22) must validate against the **canonical resolved path, not the input string.** `/ganuda/foo/../../etc/passwd` must be blocked by resolving-then-matching, not by string-matching `../`.

### Additional adapt-phase work

- Restrict subprocess execution to a **binary whitelist** (whatever Jr actually needs: `git`, `pytest`, etc.). Anything outside the whitelist → reject.
- Add `os.rename`, `shutil.move`, `Path.write_text()`, `Path.write_bytes()` to the guard intercept surface.
- Mount `/ganuda` with `nosymfollow` + `nodev` at the next reboot (or immediately if `mount -o remount` supports it on this fs).
- Add a table `jr_protected_write_attempts` (id, timestamp, jr_name, task_id, target_path, tier_matched, action_taken, stack_trace) for forensics. Rate-limit alert: >5 block attempts per Jr per hour = fire-guard-emit + TPM page.
- Pytest coverage: one test per Tier-1 path (attempt → expect block), plus one test per bypass vector (os.rename, shutil.move, subprocess cp, symlink attack). NOT representative-sampling for Tier 1 — per-path is required for audit trail.

### MITRE / CWE references (Crawdad)

- **MITRE T1222** — File and Directory Permissions Modification (what we're preventing)
- **MITRE T1070** — Indicator Removal on Host (why `/var/log/` is Sacred)
- **CWE-22** — Path Traversal (canonical-path validation)

### Open questions — Crawdad's implicit answers

The draft posed 5 open questions. Crawdad's review addressed them implicitly:
1. **Missing sacred paths:** 5 additions above.
2. **Tier-2 review mechanism:** existing staging semantics fine; no new review queue needed; Fire Guard event on staging.
3. **Fire Guard integration:** emit on every block (Tier 1) + every staging redirect (Tier 2); rate-limit alert on >5 attempts/hr.
4. **Audit history:** `jr_protected_write_attempts` table (new — added above).
5. **Pytest coverage bar:** 100% per-path for Tier 1 (not sampling).

## Next: adapt-phase implementation

TPM authors the adapt plan breakdown next session (atomic Jr-sized units per file touched: `protected_paths.py` + os-intercept wrapper + subprocess whitelist + mount-option setup + test suite + DB migration for `jr_protected_write_attempts`). Crawdad's amendments are the binding spec.
