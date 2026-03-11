#!/usr/bin/env python3
"""DC-14 Thread State Bookmark System.

Sub-check #3 of the Watershed Layer (DC-14 Amendment).
Preserves active conversation threads through context compaction.
Zero trust: checksums verified on every load, file_refs checked against disk.

Design ref: /ganuda/docs/design/DC-14-WATERSHED-ZERO-TRUST-TRANSIT-MAR10-2026.md
Council votes: #4e17006b94031187, #39f10191991a0d96
"""

import argparse
import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone

BOOKMARK_PATH = "/ganuda/config/thread_bookmarks.json"
VALID_VALENCES = ("momentum", "blocked", "exploring", "complete")


def _compute_checksum(topic: str, last_action: str, open_questions: list) -> str:
    """SHA-256 of topic|last_action|json(open_questions). Zero trust integrity."""
    payload = f"{topic}|{last_action}|{json.dumps(open_questions, sort_keys=True)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_bookmarks_raw() -> list:
    """Read bookmark file from disk. Returns empty list on missing/corrupt file."""
    if not os.path.exists(BOOKMARK_PATH):
        return []
    try:
        with open(BOOKMARK_PATH, "r") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _write_bookmarks(bookmarks: list) -> None:
    """Atomic write: temp file then os.replace to avoid partial writes."""
    config_dir = os.path.dirname(BOOKMARK_PATH)
    os.makedirs(config_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=config_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(bookmarks, f, indent=2)
            f.write("\n")
        os.replace(tmp_path, BOOKMARK_PATH)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def verify_bookmark(bookmark: dict) -> bool:
    """Recompute checksum and verify all file_refs exist on disk."""
    expected = _compute_checksum(
        bookmark.get("topic", ""),
        bookmark.get("last_action", ""),
        bookmark.get("open_questions", []),
    )
    if expected != bookmark.get("checksum", ""):
        return False
    for ref in bookmark.get("file_refs", []) or []:
        if not os.path.exists(ref):
            return False
    return True


def save_bookmark(
    topic: str,
    last_action: str,
    open_questions: list,
    valence: str,
    file_refs: list = None,
) -> dict:
    """Create or update a thread bookmark. Returns the saved bookmark."""
    if valence not in VALID_VALENCES:
        raise ValueError(f"Invalid valence '{valence}'. Must be one of: {VALID_VALENCES}")

    bookmarks = _read_bookmarks_raw()
    now = _now_iso()
    checksum = _compute_checksum(topic, last_action, open_questions)

    # Find existing by topic
    for bm in bookmarks:
        if bm.get("topic") == topic:
            bm["last_action"] = last_action
            bm["open_questions"] = open_questions
            bm["emotional_valence"] = valence
            bm["file_refs"] = file_refs or []
            bm["updated_at"] = now
            bm["checksum"] = checksum
            _write_bookmarks(bookmarks)
            return dict(bm)

    # New bookmark
    bookmark = {
        "thread_id": str(uuid.uuid4()),
        "topic": topic,
        "last_action": last_action,
        "open_questions": open_questions,
        "emotional_valence": valence,
        "file_refs": file_refs or [],
        "created_at": now,
        "updated_at": now,
        "checksum": checksum,
    }
    bookmarks.append(bookmark)
    _write_bookmarks(bookmarks)
    return dict(bookmark)


def load_bookmarks() -> list:
    """Load all bookmarks with ephemeral verified flag (never persisted)."""
    bookmarks = _read_bookmarks_raw()
    for bm in bookmarks:
        bm["verified"] = verify_bookmark(bm)
    return bookmarks


def close_bookmark(topic: str) -> dict | None:
    """Set a bookmark to complete. Returns the closed bookmark or None."""
    bookmarks = _read_bookmarks_raw()
    for bm in bookmarks:
        if bm.get("topic") == topic:
            bm["emotional_valence"] = "complete"
            bm["updated_at"] = _now_iso()
            bm["checksum"] = _compute_checksum(
                bm["topic"], bm["last_action"], bm["open_questions"]
            )
            _write_bookmarks(bookmarks)
            return dict(bm)
    return None


def get_active_bookmarks() -> list:
    """Return non-complete bookmarks with verification status."""
    return [bm for bm in load_bookmarks() if bm.get("emotional_valence") != "complete"]


def format_for_context() -> str:
    """Human-readable summary of active threads for session context injection."""
    active = get_active_bookmarks()
    if not active:
        return "No active thread bookmarks."

    lines = [f"Active Thread Bookmarks ({len(active)})", "=" * 40]
    for bm in active:
        status = "VERIFIED" if bm.get("verified") else "UNVERIFIED"
        lines.append(f"\n[{bm['emotional_valence'].upper()}] {bm['topic']}  ({status})")
        lines.append(f"  Last action: {bm['last_action']}")
        if bm.get("open_questions"):
            lines.append("  Open questions:")
            for q in bm["open_questions"]:
                lines.append(f"    - {q}")
        if bm.get("file_refs"):
            lines.append(f"  Files: {', '.join(bm['file_refs'])}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="DC-14 Thread State Bookmarks")
    parser.add_argument("--list", action="store_true", help="Show active bookmarks")
    parser.add_argument("--save", nargs=2, metavar=("TOPIC", "ACTION"), help="Save a bookmark")
    parser.add_argument("--close", metavar="TOPIC", help="Close a bookmark by topic")
    parser.add_argument("--verify", action="store_true", help="Verify all bookmark checksums")
    args = parser.parse_args()

    if args.list:
        print(format_for_context())
    elif args.save:
        bm = save_bookmark(topic=args.save[0], last_action=args.save[1],
                           open_questions=[], valence="exploring")
        print(f"Saved: {bm['topic']} (thread {bm['thread_id'][:8]})")
    elif args.close:
        result = close_bookmark(args.close)
        if result:
            print(f"Closed: {result['topic']}")
        else:
            print(f"Not found: {args.close}")
    elif args.verify:
        bookmarks = load_bookmarks()
        if not bookmarks:
            print("No bookmarks found.")
            return
        for bm in bookmarks:
            status = "OK" if bm["verified"] else "FAILED"
            missing = [r for r in (bm.get("file_refs") or []) if not os.path.exists(r)]
            print(f"[{status}] {bm['topic']} (valence={bm['emotional_valence']})")
            if missing:
                for m in missing:
                    print(f"  Missing file: {m}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
