# JR Instruction: CDR-to-Kanban Auto-Port Pipeline

**ID:** JR-CDR-TO-KANBAN-AUTO-PORT-APR11-2026
**Priority:** P2 (structural improvement, not time-critical)
**Created:** 2026-04-11 (Saturday)
**Source:** CDR-IN-PLACE-TTT-INTEGRATION-APR11-2026, kanban hygiene snapshot Apr 11 2026
**Estimated effort:** 8-13 SP
**Status:** queued

---

## Why this exists

On April 11, 2026, TPM ran a kanban hygiene snapshot and discovered a structural gap: **the federation kanban (`triad_federation.kanban_tasks`) had not received a new entry since April 7**, despite the federation having shipped substantial work between April 7 and April 11 (Friday convergence, three Longhouse ratifications, six ii-researcher pulls, Hulsey booking, Kenzie onboarding, CORAL outreach, In-Place TTT primary-source synthesis, three new memory files, and a Council Decision Record).

The gap is structural: **Council Decision Records** (CDRs) at `/ganuda/docs/council/` are written as markdown files with structured "Tracked work items" sections. Conversation-level task tracking happens via `TaskCreate` (the in-conversation tool) but never persists to the federation kanban. The two layers have drifted apart, and the persistent kanban no longer reflects what the federation is actually working on.

Per the cluster-drives-itself principle (Partner directive Apr 11 2026), the federation should not require TPM to manually port CDR work items into the kanban every time. **The cluster should do this automatically.**

---

## What to build

A pipeline that watches `/ganuda/docs/council/` for new CDR markdown files and automatically writes their tracked work items into `triad_federation.kanban_tasks`.

### Components

#### 1. CDR parser (`lib/cdr_parser.py`)

Reads a CDR markdown file. Extracts:
- CDR ID (from frontmatter or `**CDR ID:**` line)
- Convening date
- Author / Council members present
- The "Tracked work items" section, parsing the markdown table(s) inside it
- Each tracked item's: ID (e.g., C1, F1), title, owner, type, status

The CDR table format is documented in `CDR-IN-PLACE-TTT-INTEGRATION-APR11-2026.md` as the reference example. The parser must handle:
- Markdown tables with the headers: `| # | Item | Owner | Type | Status |`
- Two table sections (one for concerns, one for features) with `### Concerns raised` and `### Features proposed` markers
- Status values: `QUEUED`, `DEFERRED`, `RATIFIED`, `THERMALIZED`, `DIRECT ACTION`, `BLOCKING`, `DOCUMENTED`

#### 2. CDR-to-kanban mapper (`lib/cdr_to_kanban.py`)

Converts each parsed tracked item to a `kanban_tasks` row.

**Mapping rules:**
- `title` ← item title (truncated to 500 chars)
- `description` ← item title + owner + type + reference back to the CDR file path
- `status` ← derived from CDR status:
  - `QUEUED`, `RATIFIED` → `'todo'`
  - `DEFERRED` → `'backlog'`
  - `IN PROGRESS`, `ACTIVE` → `'in_progress'`
  - `DIRECT ACTION TONIGHT`, `THERMALIZED`, `DOCUMENTED`, `BLOCKING` → `'done'` with metadata note
- `priority` ← derived from item type:
  - Patent items, Hulsey items, prerequisites for time-locked work → `'P1'`
  - Research / experiments → `'P1'` if active, `'P2'` if deferred
  - Editorial / Substack queue → `'P2'`
  - Standing practices / Charter amendments → `'P2'`
  - Default → `'P2'`
- `board_id` ← `'federation_ops'` for all CDR-derived items
- `node_id` ← `'hub'` (federation-wide work, not node-specific)
- `assignee` ← derived from owner field if it matches a known specialist or Jr (e.g., `'jr'`, `'medicine-woman-jr'`); else `NULL`
- `column_name` ← left empty (mirrors existing convention)
- `tags` ← jsonb array including: `['cdr', cdr_id, item_type]`
- `metadata` ← jsonb with:
  - `source: cdr_id`
  - `cdr_path: path/to/CDR.md`
  - `cdr_item_id: 'C1' | 'F1' | etc.`
  - `created_by: 'cdr-auto-port'`
  - `auto_ported_at: timestamp`

#### 3. CDR file watcher (`daemons/cdr_watcher_daemon.py`)

A daemon that:
- Watches `/ganuda/docs/council/` for new `.md` files (CDR-* prefix)
- On new file: parses, maps, writes to `kanban_tasks` in a single transaction
- Logs the operation to `cdr_auto_port_log` (new table) for audit
- Emits a thermal memory entry tagged `[cdr-auto-port]` summarizing what was ported
- Idempotent: re-running on the same CDR detects existing rows by `metadata.cdr_item_id` and `metadata.source` and SKIPS or UPDATES, never duplicates

**Trigger options (Jr to choose):**
- Option 1: inotify file watcher (simplest, requires daemon process)
- Option 2: cron job that runs every 5 minutes (simpler ops, slight delay)
- Option 3: explicit `cdr-port` CLI command that TPM/Partner runs after writing a CDR (most conservative — manual trigger, but no daemon overhead)

**Recommendation:** Option 3 first (CLI command), Option 1 second (daemon). Don't ship Option 2 — cron polling is operationally noisy and we don't need real-time.

#### 4. Validation gate (Council review before activation)

**Hard requirement from the cluster-drives-itself principle:** auto-ported kanban entries must NOT immediately enter active workflows. They should land in `status='backlog'` initially, with a metadata flag `auto_ported: true, council_reviewed: false`. A Council member (or Partner, or TPM in a later session) explicitly promotes them to `todo` after reviewing. This prevents the auto-port from accidentally activating a half-baked CDR item as production work.

**Promotion flow:**
1. CDR written → file appears in `/ganuda/docs/council/`
2. Auto-port pipeline triggers → kanban entries created with `status='backlog'`, `metadata.auto_ported=true`
3. Council member reviews the CDR + the auto-ported entries
4. Promotion: bulk update from `'backlog'` to `'todo'` (or `'in_progress'` for items already in motion), set `metadata.council_reviewed=true`, set `metadata.reviewed_by` and `metadata.reviewed_at`
5. The kanban entries are now active

#### 5. Backlink discipline

Each kanban entry created by the auto-port must include the CDR file path in its description AND in `metadata.cdr_path`. The CDR markdown file should also be updated automatically with a "Kanban entries:" section listing the `task_id` UUIDs created from it (this requires file write permission for the daemon — keep it scoped to `/ganuda/docs/council/CDR-*.md`).

This creates a bidirectional link: from CDR to kanban, and from kanban back to CDR. **No tracked work item should be untraceable to the deliberation that created it.**

---

## Acceptance criteria

- [ ] `lib/cdr_parser.py` exists and can parse `CDR-IN-PLACE-TTT-INTEGRATION-APR11-2026.md` correctly, extracting all 14 concerns and 11 features
- [ ] `lib/cdr_to_kanban.py` correctly maps each parsed item to a `kanban_tasks` row with all required fields populated
- [ ] CLI command `cdr-port <cdr_file_path>` works end-to-end on a test CDR
- [ ] Re-running `cdr-port` on the same CDR is idempotent (no duplicate rows)
- [ ] Auto-ported entries land in `status='backlog'` with `metadata.auto_ported=true` and `metadata.council_reviewed=false`
- [ ] Promotion command `cdr-promote <cdr_id>` exists and bulk-promotes backlog→todo with reviewer attribution
- [ ] Bidirectional backlinks: CDR file lists task_ids; kanban rows reference CDR path
- [ ] Test: auto-port the existing `CDR-IN-PLACE-TTT-INTEGRATION-APR11-2026.md` and verify all 14+11 items land correctly

## Out of scope (do NOT build in this Jr task)

- Web UI for the kanban (the existing kanban surface is enough)
- Cross-CDR dependency tracking (one CDR's items don't yet need to block another CDR's items)
- Auto-decomposition of EPIC-level items (parser leaves them as single rows)
- Auto-priority inference from CDR text (use the simple mapping rules above; don't try to be clever)
- Integration with Charter amendments or thermal memory (separate Jr task if needed)

## Council deliberation note

This Jr instruction was generated as part of the Apr 11 2026 backlog hygiene pass on the federation kanban. The Council ratified the cluster-drives-itself approach (Option C of the kanban hygiene fork), which includes both immediate hand-port of the CDR's tracked items AND building the structural fix that makes hand-porting unnecessary in the future.

**The Council's expectation:** by the time the next CDR is written (likely Hulsey Monday or thereafter), this auto-port pipeline should be operational so the next CDR doesn't require manual porting.

## Related artifacts

- `/ganuda/docs/council/CDR-IN-PLACE-TTT-INTEGRATION-APR11-2026.md` — reference CDR + first test target
- `feedback_backlog_hygiene.md` (auto-memory) — the 14-day rule this pipeline enforces structurally
- `feedback_partner_not_underling.md` (auto-memory) — the cluster-drives-itself principle
- `triad_federation.kanban_tasks` — target table
- Existing kanban tooling at `/ganuda/lib/toolsets/kanban_toolset.py` (read-only ToolSet pattern, may need write extensions)

For Seven Generations.
