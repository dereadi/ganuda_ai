# LMC-6 Adapt Plan — Jr Executor Least-Privilege Implementation

**Parent LMC:** LMC-6 (duyuktv #2079, SP:5 — likely grows with Crawdad amendments)
**Deliberate output:** `/ganuda/docs/lmc6_jr_executor_protected_paths_policy.md` (Crawdad-ratified with amendments)
**Council audit:** 348952186d1ac1ec
**TPM author:** 2026-04-21
**Long Man phase:** adapt

## Scope

Implement the Crawdad-ratified policy. Seven atomic units decomposed by file / responsibility. Order reflects dependency DAG.

## Dependency DAG

```
A1 (protected_paths.py module)
     ↓
A2 (os-module intercept wrapper) ─┐
A3 (subprocess whitelist helper) ─┼─→ A6 (task_executor.py integration)
A4 (symlink/mount hardening) ─────┘
A5 (DB migration: jr_protected_write_attempts)
     ↓
A6 (integration)
     ↓
A7 (pytest suite + historical backfill scan)
```

## Atomic units

### A1 — `/ganuda/jr_executor/protected_paths.py` (new file)

**TPM or Jr atomic | SP: 1**

Declarative lists + matcher functions.

- `SACRED_PATHS: list[str]` — exact paths and prefix patterns from the ratified policy + Crawdad's 5 additions
- `REVIEW_GATED_PATHS: list[str]` — Tier 2 list
- `SACRED_GLOBS: list[str]` — `**/__pycache__/`, `**/site-packages/`, `**/migrations/**`
- `def classify(path: str) -> Literal["sacred", "review_gated", "free"]` — takes a path, returns tier
- `def canonical_check(path: str) -> str` — resolves symlinks (`O_NOFOLLOW`-aware) + `../` traversal + returns canonical absolute path
- `def is_allowed_write(path: str) -> tuple[Literal["sacred","review_gated","free"], str]` — returns (tier, canonical_path)

**Must handle:** exact-match, prefix-match, glob-match (fnmatch), case-sensitive (Linux default — no casefold), symlink-resolution via `os.open(..., os.O_NOFOLLOW)` trial + `os.path.realpath()` cross-check, traversal via resolved-path comparison against protected-tree roots.

### A2 — os-module intercept wrapper

**TPM atomic | SP: 1**

New file `/ganuda/jr_executor/guarded_fs.py` wrapping `open`, `os.rename`, `os.replace`, `shutil.move`, `shutil.copy*`, `pathlib.Path.write_text`, `pathlib.Path.write_bytes`, `os.remove`, `os.unlink`. Each wrapper calls `protected_paths.is_allowed_write(target)` before executing.

Decision matrix:
- tier == 'sacred' → raise `ProtectedPathError` + emit Fire Guard event + write `jr_protected_write_attempts` row with action='blocked'
- tier == 'review_gated' → redirect write to `/staging/<task_hash>/<original_path>`; emit Fire Guard event; write audit row with action='staged'
- tier == 'free' → proceed normally

### A3 — subprocess whitelist helper

**TPM atomic | SP: 1**

New module `/ganuda/jr_executor/subprocess_guard.py` wrapping `subprocess.run`, `subprocess.Popen`, `subprocess.check_output`, `os.system`. Binary allowlist (configurable): `git`, `pytest`, `python`, `cargo`, `cargo`, `bun`, `npm`, `curl` (to localhost only), project-local bin.

For wrapped calls: parse argv[0], resolve to absolute path, check against allowlist. Reject non-whitelisted with `NotWhitelistedBinaryError` + Fire Guard event + audit row.

### A4 — Mount-option hardening (ops action, not code)

**TPM atomic | SP: 0.5**

`/etc/fstab` entry (or `mount -o remount`) for `/ganuda` to include `nosymfollow,nodev` where filesystem supports. Verify: `mount | grep ganuda`. On kernels/filesystems that don't support `nosymfollow`, fall back to `O_NOFOLLOW` enforcement in code (A2).

### A5 — DB migration: `jr_protected_write_attempts`

**Jr atomic | SP: 1**

Create table:
```sql
CREATE TABLE jr_protected_write_attempts (
  id            SERIAL PRIMARY KEY,
  attempted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  jr_name       VARCHAR(100),
  task_id       INTEGER,
  target_path   TEXT NOT NULL,
  tier_matched  VARCHAR(20) CHECK (tier_matched IN ('sacred','review_gated')),
  action_taken  VARCHAR(20) CHECK (action_taken IN ('blocked','staged')),
  stack_trace   TEXT,
  attempt_hash  CHAR(16)
);
CREATE INDEX idx_jpwa_jr_time ON jr_protected_write_attempts (jr_name, attempted_at DESC);
```

Trigger or app-layer rate-limit: fire-guard-alert when a single jr_name hits >5 `action='blocked'` rows in 1h (could indicate compromised Jr).

### A6 — `task_executor.py` integration

**TPM atomic | SP: 1**

Wire A1–A3 into the task executor's write path. Monkey-patch the `open`/`os.rename`/`shutil.*`/`pathlib.*` names in the executor's module scope for the duration of a Jr task. Restore after.

Subprocess: replace `subprocess` imports in executor context with `subprocess_guard`.

### A7 — pytest suite + historical backfill scan

**Jr atomic | SP: 1**

Per Crawdad's 100%-coverage-Tier-1 requirement:

```python
# Test one per Tier-1 path (≥12 tests)
@pytest.mark.parametrize("path", SACRED_PATHS + derived_examples)
def test_sacred_path_blocked(path, guarded_executor):
    with pytest.raises(ProtectedPathError):
        guarded_executor.write_file(path, "malicious content")

# Test each bypass vector (≥5 tests)
def test_os_rename_bypass_blocked(...): ...
def test_shutil_move_bypass_blocked(...): ...
def test_subprocess_cp_blocked(...): ...
def test_symlink_attack_blocked(...): ...
def test_path_traversal_blocked(...): ...

# Test Tier 2 staging redirect (≥3 tests)
def test_review_gated_stages_not_blocks(...): ...
def test_staged_path_mirrors_original(...): ...
def test_fire_guard_event_emitted(...): ...

# Test Tier 3 free allow (≥3 tests)
def test_free_write_succeeds(...): ...
```

Historical backfill: scan last 50 completed Jr tasks in `jr_work_queue`, parse their touched-file lists, cross-reference against the protected lists, produce a report: **what would have been blocked/staged if the policy had been in place?** Deliverable: `/ganuda/docs/lmc6_historical_backfill_report.md`. Findings feed Crawdad's next review cycle.

## Dispatch order

1. **A1** (TPM) — foundational module, no dependencies
2. **A2, A3, A4** (TPM) — parallel; all depend on A1
3. **A5** (Jr atomic) — DB migration, independent
4. **A6** (TPM) — depends on A1-A3
5. **A7** (Jr atomic) — depends on A1-A6 complete

## Acceptance criteria

1. All Tier-1 paths (22+ including Crawdad's additions) block 100% of write attempts across all primitives (open, rename, move, pathlib, subprocess)
2. All Tier-2 paths stage to `/staging/<task_hash>/` with Fire Guard event
3. Rate-limit alert fires on >5 blocks/hr for a single Jr
4. Historical backfill report identifies any past Jr writes that would have been blocked/staged (zero is a good sign; non-zero requires incident review)
5. pytest green
6. Mount options confirmed via `mount | grep ganuda`

## Rollback

All guards can be disabled via env var `GANUDA_JR_PRIV_GATE=off` — sets classify() to always return `'free'`. Useful for emergency recovery or testing. Logged prominently when active.

## Revisit triggers

- New Ganuda core module deployed that should be Sacred — add to A1 lists
- New rate-limit pattern needed (e.g., geographic deviation, time-of-day anomaly) — A5 schema flexible
- Mount-option upgrade (e.g., kernel adds new hardening flag) — A4
- Crawdad's next quarterly security review

## Cross-references

- Deliberate-phase policy: `/ganuda/docs/lmc6_jr_executor_protected_paths_policy.md`
- Fire Guard integration: wherever `fire_guard.emit_event()` lives in `/ganuda/lib/fire_guard/`
- Sub-agent dispatch integration: `/ganuda/lib/sub_agent_dispatch.py`
- Patent #1 Governance Topology — this is governance-topology-in-practice at the executor layer
