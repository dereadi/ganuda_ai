# JR INSTRUCTION: DC-14 Thread State Bookmark System

**Task**: DC14-THREAD-STATE-001
**Priority**: P2
**Estimated SP**: 5
**Assigned**: Software Engineer Jr.
**Created**: 2026-03-10
**Design Ref**: /ganuda/docs/design/DC-14-WATERSHED-ZERO-TRUST-TRANSIT-MAR10-2026.md

## Objective

Build the thread bookmark system described in DC-14 Watershed Layer, Sub-Check #3: Thread State. Active conversation threads must survive context compaction. Like resuming a daydream — recall the emotional state, the state reconstructs the scene.

This module provides save/load/verify/close/format operations on thread bookmarks stored as a JSON array at `/ganuda/config/thread_bookmarks.json`. Zero trust: every bookmark carries a checksum and every file reference is verified against disk.

## Target File

Create `/ganuda/lib/thread_bookmarks.py` (~130-170 lines)

## Structured Replacement Blocks

### Block 1: Create the module

Create `/ganuda/lib/thread_bookmarks.py` with the following structure:

```python
#!/usr/bin/env python3
"""DC-14 Thread State Bookmark System.

Sub-check #3 of the Watershed Layer (DC-14 Amendment).
Preserves active conversation threads through context compaction.
Zero trust: checksums verified on every load, file_refs checked against disk.

Design ref: /ganuda/docs/design/DC-14-WATERSHED-ZERO-TRUST-TRANSIT-MAR10-2026.md
Council votes: #4e17006b94031187, #39f10191991a0d96
"""
```

### Block 2: Bookmark data structure

Each bookmark is a dict with these fields:

```
thread_id: str          — uuid4, unique per bookmark
topic: str              — e.g. "DC-18 at ADAPT stage"
last_action: str        — what was last done
open_questions: list    — unresolved items (list of strings)
emotional_valence: str  — one of: "momentum", "blocked", "exploring", "complete"
file_refs: list         — absolute file paths touched by this thread
created_at: str         — ISO 8601 timestamp
updated_at: str         — ISO 8601 timestamp
checksum: str           — sha256 of topic + last_action + json(open_questions)
```

### Block 3: Functions to implement

**`_compute_checksum(topic, last_action, open_questions) -> str`**
- Concatenate: `topic + "|" + last_action + "|" + json.dumps(open_questions, sort_keys=True)`
- Return sha256 hex digest of that string (UTF-8 encoded).

**`save_bookmark(topic, last_action, open_questions, valence, file_refs=None) -> dict`**
- Load existing bookmarks from disk.
- If a bookmark with matching `topic` exists, UPDATE it: set last_action, open_questions, valence, file_refs, updated_at, recompute checksum. Keep original thread_id and created_at.
- If no match, CREATE new bookmark with uuid4 thread_id, current ISO timestamps for both created_at and updated_at.
- Validate valence is one of: "momentum", "blocked", "exploring", "complete". Raise ValueError if not.
- Write full bookmark list back to `/ganuda/config/thread_bookmarks.json` with indent=2.
- Return the saved bookmark dict.

**`load_bookmarks() -> list[dict]`**
- Read `/ganuda/config/thread_bookmarks.json`. Return empty list if file doesn't exist or is empty.
- For each bookmark, verify checksum. Add `"verified": True` or `"verified": False` to each bookmark in the returned list.
- Do NOT mutate the file on disk — verified flag is ephemeral (Layer 1 property).

**`verify_bookmark(bookmark) -> bool`**
- Recompute checksum from topic + last_action + open_questions. Compare to stored checksum.
- Check every path in file_refs: does `os.path.exists(path)` return True? If ANY file is missing, return False.
- Return True only if checksum matches AND all file_refs exist.

**`close_bookmark(topic) -> dict or None`**
- Find bookmark by topic. Set emotional_valence to "complete", update updated_at, recompute checksum.
- Write back to disk. Return the closed bookmark, or None if topic not found.

**`get_active_bookmarks() -> list[dict]`**
- Return only bookmarks where emotional_valence != "complete".
- Each bookmark gets a verified flag (call verify_bookmark on each).

**`format_for_context() -> str`**
- Format active bookmarks as a human-readable multi-line string suitable for loading into session context.
- For each active bookmark, show: topic, last_action, open_questions (bulleted), valence, verification status.
- If no active bookmarks, return "No active thread bookmarks."

### Block 4: CLI mode

At the bottom of the module, add `if __name__ == "__main__":` with argparse:

| Flag | Action |
|------|--------|
| `--list` | Print `format_for_context()` output |
| `--save TOPIC ACTION` | Call `save_bookmark(topic=TOPIC, last_action=ACTION, open_questions=[], valence="exploring")` and print the result |
| `--close TOPIC` | Call `close_bookmark(TOPIC)` and print confirmation or "not found" |
| `--verify` | Load all bookmarks, print each with checksum status and file_ref status |

## Acceptance Criteria

- [ ] Module exists at `/ganuda/lib/thread_bookmarks.py`, runs with Python 3.10+ and no external dependencies (stdlib only: json, hashlib, uuid, os, datetime, argparse).
- [ ] `save_bookmark()` creates new bookmarks and updates existing ones by topic match.
- [ ] Checksum is sha256 of `topic|last_action|json(open_questions)`. Recomputed on every save/close.
- [ ] `load_bookmarks()` returns empty list when file doesn't exist (no crash).
- [ ] `verify_bookmark()` returns False if checksum mismatch OR any file_ref path doesn't exist on disk.
- [ ] `close_bookmark()` sets valence to "complete" and recomputes checksum.
- [ ] `get_active_bookmarks()` excludes "complete" bookmarks.
- [ ] `format_for_context()` produces clean human-readable output suitable for pasting into session context.
- [ ] CLI `--list`, `--save`, `--close`, `--verify` all work from command line.
- [ ] Valence is validated: only "momentum", "blocked", "exploring", "complete" accepted.
- [ ] JSON file written with indent=2 for human readability.
- [ ] File I/O failures are caught gracefully (no unhandled exceptions on permission errors or corrupt JSON).
- [ ] Module is 130-170 lines, clean, production-ready.

## Gotchas

- **Do NOT use any external packages.** Stdlib only. This runs on all 5 Linux nodes and both macOS machines without pip install.
- **File path is `/ganuda/config/thread_bookmarks.json`**, not `/tmp/`. This data must survive reboots.
- **verified flag is ephemeral** — added to returned dicts but NEVER written to disk. This is a Layer 1 (working memory) property per DC-14.
- **Checksum is zero-trust verification**, not encryption. If the checksum doesn't match, the bookmark was tampered or corrupted. Log it, flag it, but don't delete it — Turtle reversibility.
- **file_refs should be absolute paths.** Relative paths will fail verify_bookmark since cwd varies across nodes.
- **JSON atomicity**: Write to a temp file then rename, to avoid partial writes corrupting the bookmark file. Use `os.replace()` for atomic swap.
- **Don't import from /ganuda/lib/** — this module must be self-contained. Other modules will import IT.
