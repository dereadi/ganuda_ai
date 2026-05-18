"""
Recovery Enzymes — SEV1-Prevention Enzymes
Cherokee AI Federation — The Living Cell Architecture

Three deterministic enzymes for damage recovery, codifying the
disarm-and-verify playbook (KB-JR-SEV1-DISARM-AND-VERIFY-PLAYBOOK-MAY17-2026).

These are PURE PYTHON enzymes (not LLM-backed). They catalyze one
specific reaction each and stop:

  - find_backup(file_path)        : locate sibling .backup_* candidates [read]
  - surgical_restore(...)          : restore damaged section from backup [write]
  - quarantine(file_path, reason)  : move suspect file to dated quarantine [write]

Design rationale per RESEARCH-MINI-MODEL-WORKFORCE-COHERENCE-MAY17-2026:
deterministic recovery operations are TOOLS, not MODEL Rings. A 1M-param
model for file-move would just be `os.rename()` with extra steps and
worse latency. Save the model budget for fuzzy-semantic judgment.

Cross-references:
  - KB-JR-SEV1-DISARM-AND-VERIFY-PLAYBOOK-MAY17-2026.md
  - LONGHOUSE-MICRO-JR-RING-ROLE-TAXONOMY-MAY17-2026.md (revised)
  - RESEARCH-MINI-MODEL-WORKFORCE-COHERENCE-MAY17-2026.md
  - project_duplo_jr_layer_extension_may17_2026 memory
"""

import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("duplo.recovery_enzymes")

# Default quarantine root; callers may override
DEFAULT_QUARANTINE_ROOT = Path("/ganuda")
QUARANTINE_DIR_PREFIX = "jr_stub_quarantine_"


def find_backup(file_path: str) -> List[Dict[str, str]]:
    """
    Locate sibling backup files for a given path.

    Matches two conventions used across the federation:
      - {stem}.backup_<timestamp>{suffix}   (e.g., secrets.env.backup_20260516_222728)
      - {name}.broken-<timestamp>           (e.g., specialist_council.py.broken-20260517-2055)

    Returns a list of dicts ordered newest-first:
      [{"path": "...", "mtime_iso": "...", "shape": "backup|broken"}, ...]

    Read-only. No side effects beyond stat() calls.
    """
    target = Path(file_path)
    parent = target.parent
    if not parent.exists():
        logger.warning(f"find_backup: parent dir does not exist: {parent}")
        return []

    candidates = []

    # Pattern 1: name.backup_<timestamp> (any suffix preserved or stripped)
    backup_glob = f"{target.name}.backup_*"
    for p in parent.glob(backup_glob):
        if p.is_file():
            candidates.append({
                "path": str(p),
                "mtime_iso": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                "shape": "backup",
            })

    # Pattern 2: name.broken-<timestamp> (forensics-preserved corrupted versions)
    broken_glob = f"{target.name}.broken-*"
    for p in parent.glob(broken_glob):
        if p.is_file():
            candidates.append({
                "path": str(p),
                "mtime_iso": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                "shape": "broken",
            })

    # Pattern 3: stem.suffix.backup_<timestamp> variant where suffix matters
    # (already covered by Pattern 1 via target.name)

    candidates.sort(key=lambda c: c["mtime_iso"], reverse=True)

    logger.info(
        f"find_backup({file_path}): found {len(candidates)} candidates "
        f"({sum(1 for c in candidates if c['shape']=='backup')} backup, "
        f"{sum(1 for c in candidates if c['shape']=='broken')} broken)"
    )
    return candidates


def surgical_restore(
    damaged_path: str,
    backup_path: str,
    section_start_pattern: Optional[str] = None,
    section_end_pattern: Optional[str] = None,
    preserve_broken: bool = True,
) -> Dict[str, str]:
    """
    Restore damaged file from a backup, optionally splicing only a section.

    If section_start_pattern + section_end_pattern are provided, extracts the
    matching section from the backup and splices it into the damaged file
    (replacing the corresponding section in damaged if found, else inserting).

    If patterns are None, copies the entire backup over the damaged file.

    Behavior:
      - Always preserves the damaged version as {damaged}.broken-<YYYYMMDD-HHMM>
        unless preserve_broken=False
      - Atomic write via temp file + rename
      - Returns dict with action taken, paths, and byte counts

    Write enzyme. Requires write permission on damaged_path's directory.
    """
    damaged = Path(damaged_path)
    backup = Path(backup_path)

    if not damaged.exists():
        raise FileNotFoundError(f"surgical_restore: damaged file missing: {damaged}")
    if not backup.exists():
        raise FileNotFoundError(f"surgical_restore: backup file missing: {backup}")
    if not backup.is_file():
        raise ValueError(f"surgical_restore: backup is not a regular file: {backup}")

    # Preserve damaged version BEFORE any writes
    broken_path = None
    if preserve_broken:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        broken_path = damaged.with_name(f"{damaged.name}.broken-{ts}")
        shutil.copy2(damaged, broken_path)
        logger.info(f"surgical_restore: preserved damaged as {broken_path}")

    backup_bytes = backup.read_bytes()
    damaged_bytes_before = damaged.read_bytes() if damaged.exists() else b""

    # Decide restore mode
    if section_start_pattern is None and section_end_pattern is None:
        # Full copy
        action = "full_copy"
        new_bytes = backup_bytes
    elif section_start_pattern is not None and section_end_pattern is not None:
        # Section splice — only operates on text files
        try:
            backup_text = backup.read_text()
            damaged_text = damaged.read_text()
        except UnicodeDecodeError as e:
            raise ValueError(
                f"surgical_restore: section splice requires text files; "
                f"{damaged} or {backup} is binary"
            ) from e

        start_re = re.compile(section_start_pattern, re.MULTILINE)
        end_re = re.compile(section_end_pattern, re.MULTILINE)

        backup_start = start_re.search(backup_text)
        backup_end = end_re.search(backup_text, pos=backup_start.end() if backup_start else 0)
        if not (backup_start and backup_end):
            raise ValueError(
                f"surgical_restore: section markers not found in backup. "
                f"start='{section_start_pattern}' end='{section_end_pattern}'"
            )
        clean_section = backup_text[backup_start.start():backup_end.end()]

        damaged_start = start_re.search(damaged_text)
        damaged_end = end_re.search(damaged_text, pos=damaged_start.end() if damaged_start else 0)

        if damaged_start and damaged_end:
            action = "section_replace"
            new_text = (
                damaged_text[:damaged_start.start()]
                + clean_section
                + damaged_text[damaged_end.end():]
            )
        else:
            # Section absent in damaged — append clean section at end
            action = "section_insert"
            new_text = damaged_text.rstrip() + "\n\n" + clean_section + "\n"

        new_bytes = new_text.encode("utf-8")
    else:
        raise ValueError(
            "surgical_restore: section_start_pattern and section_end_pattern "
            "must both be set or both None"
        )

    # Atomic write
    tmp_path = damaged.with_name(f".{damaged.name}.tmp-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    tmp_path.write_bytes(new_bytes)
    tmp_path.replace(damaged)

    logger.info(
        f"surgical_restore: {action} on {damaged} from {backup} "
        f"({len(damaged_bytes_before)}B -> {len(new_bytes)}B; broken_preserved={broken_path})"
    )
    return {
        "action": action,
        "damaged_path": str(damaged),
        "backup_path": str(backup),
        "broken_preserved_at": str(broken_path) if broken_path else "",
        "bytes_before": str(len(damaged_bytes_before)),
        "bytes_after": str(len(new_bytes)),
    }


def quarantine(
    file_path: str,
    reason: str = "",
    quarantine_root: Optional[str] = None,
) -> Dict[str, str]:
    """
    Move a suspect file into a dated quarantine directory with metadata.

    Quarantine path:
      {quarantine_root}/{QUARANTINE_DIR_PREFIX}{YYYYMMDD}/{original_name}

    Also writes a metadata sidecar at {quarantined}.quarantine_meta:
      - original_path
      - quarantined_at (ISO timestamp)
      - reason
      - original_mtime_iso
      - original_size_bytes

    Returns dict with the new path and metadata.

    Write enzyme. Move operation (NOT delete) — fully recoverable.
    """
    source = Path(file_path)
    if not source.exists():
        raise FileNotFoundError(f"quarantine: source missing: {source}")
    if not source.is_file():
        raise ValueError(f"quarantine: not a regular file (refusing to recurse dirs): {source}")

    root = Path(quarantine_root) if quarantine_root else DEFAULT_QUARANTINE_ROOT
    today = datetime.now().strftime("%Y%m%d")
    q_dir = root / f"{QUARANTINE_DIR_PREFIX}{today}"
    q_dir.mkdir(parents=True, exist_ok=True)

    # Handle name collision in quarantine (multiple files with same name on same day)
    dest = q_dir / source.name
    if dest.exists():
        suffix = datetime.now().strftime("%H%M%S")
        dest = q_dir / f"{source.stem}.q-{suffix}{source.suffix}"

    original_stat = source.stat()
    original_mtime = datetime.fromtimestamp(original_stat.st_mtime).isoformat()
    original_size = original_stat.st_size

    shutil.move(str(source), str(dest))

    # Sidecar metadata
    meta_path = dest.with_name(dest.name + ".quarantine_meta")
    meta_path.write_text(
        f"original_path: {source}\n"
        f"quarantined_at: {datetime.now().isoformat()}\n"
        f"reason: {reason}\n"
        f"original_mtime_iso: {original_mtime}\n"
        f"original_size_bytes: {original_size}\n"
    )

    logger.info(
        f"quarantine: moved {source} -> {dest} "
        f"({original_size}B, reason={reason or '(none)'})"
    )
    return {
        "original_path": str(source),
        "quarantined_path": str(dest),
        "meta_path": str(meta_path),
        "reason": reason,
        "original_size_bytes": str(original_size),
    }
