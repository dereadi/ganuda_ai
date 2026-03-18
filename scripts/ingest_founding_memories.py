#!/usr/bin/env python3
"""
Ingest founding-era markdown files into thermal_memory_archive.

Sources:
  - /home/dereadi/*.md (redfin) — Nov-Dec 2025 founding docs
  - /ganuda/*.md (root) — Oct-Dec 2025 genesis architecture
  - /ganuda/docs/roadmaps/*.md — Dec 2025 roadmaps
  - /ganuda/docs/consultations/*.md — VLM consultations
  - /ganuda/legal_jr_2025_10_15/*.md — Constitutional charter
  - /ganuda/cmdb/*.md — CMDB designs
  - /home/dereadi/cherokee_quantization/*.md — Quantization research
  - Bluefin: /home/dereadi/ganuda_ai/*.md — Original framework
  - Bluefin: /home/dereadi/scripts/claude/*.md — Early Jr assignments
  - Bluefin: /ganuda/ unique files

Deduplicates by sha256 hash against existing thermal_memory_archive.memory_hash.
Tags Oct 2025 genesis documents as sacred_pattern = true.
Uses file mtime as created_at for historical accuracy.

Cherokee AI Federation — For Seven Generations
"""

import os
import sys
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

# ── Config ──────────────────────────────────────────────────────────
DB_HOST = '192.168.132.222'
DB_NAME = 'zammad_production'
DB_USER = 'claude'
SECRETS_FILE = '/ganuda/config/secrets.env'

# Sacred pattern: Oct 2025 genesis + constitutional docs
SACRED_KEYWORDS = [
    'ARCHITECTURE', 'CONSCIOUSNESS', 'CONSTITUTIONAL', 'GADUGI',
    'DEMOCRATIC_AUTONOMOUS', 'THREE_CHIEFS', 'MEDICINE_WOMAN',
    'HISTORIC_TRANSFORMATION', 'CHEROKEE_PLATFORM_VISION',
    'CHEROKEE_AI_BUSINESS_PLAN', 'HUB_SPOKE', 'SHARDING',
    'GOVERNANCE', 'BREATHING', 'FRACTAL_BRAIN',
    'SEVEN_GENERATIONS', 'SOVEREIGNTY',
]

DRY_RUN = '--dry-run' in sys.argv
VERBOSE = '--verbose' in sys.argv or '-v' in sys.argv


def get_db_password():
    """Read password from secrets.env."""
    with open(SECRETS_FILE) as f:
        for line in f:
            if line.startswith('CHEROKEE_DB_PASS='):
                return line.strip().split('=', 1)[1]
    raise RuntimeError("CHEROKEE_DB_PASS not found in secrets.env")


def file_hash(content: str) -> str:
    """SHA256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def is_sacred(filepath: str, mtime: datetime) -> bool:
    """Determine if a file should be marked sacred_pattern."""
    name = os.path.basename(filepath).upper()
    # Oct 2025 genesis period
    if mtime.year == 2025 and mtime.month == 10:
        return True
    # Constitutional / foundational docs
    for kw in SACRED_KEYWORDS:
        if kw in name:
            return True
    return False


def get_file_mtime(filepath: str) -> datetime:
    """Get file modification time as datetime."""
    ts = os.path.getmtime(filepath)
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def classify_memory(filepath: str) -> str:
    """Classify memory type based on path/name."""
    name = os.path.basename(filepath).upper()
    if 'ROADMAP' in name or 'VISION' in name or 'PLAN' in name:
        return 'strategic'
    if 'ARCHITECTURE' in name or 'TECHNICAL' in name or 'INFRASTRUCTURE' in name:
        return 'technical'
    if 'COUNCIL' in name or 'CHIEF' in name or 'TRIAD' in name:
        return 'governance'
    if 'SECURITY' in name or 'CRAWDAD' in name:
        return 'security'
    if 'DEPLOYMENT' in name or 'STATUS' in name or 'OPERATIONAL' in name:
        return 'operational'
    if 'JR' in name or 'ASSIGNMENT' in name:
        return 'task'
    if 'CONSCIOUSNESS' in name or 'MEDICINE' in name or 'SACRED' in name:
        return 'cultural'
    if 'SESSION' in name or 'HANDOFF' in name or 'SUMMARY' in name:
        return 'session'
    if 'RESEARCH' in name or 'ANALYSIS' in name or 'ULTRA_THINK' in name:
        return 'research'
    return 'general'


def collect_local_files() -> list:
    """Collect all local md files to ingest."""
    targets = []

    # Redfin home dir (top level only)
    for f in Path('/home/dereadi').glob('*.md'):
        targets.append(str(f))

    # Redfin home subdirs (cherokee_quantization)
    for f in Path('/home/dereadi/cherokee_quantization').glob('*.md'):
        targets.append(str(f))

    # /ganuda root level
    for f in Path('/ganuda').glob('*.md'):
        targets.append(str(f))

    # /ganuda subdirs
    for subdir in ['docs/roadmaps', 'docs/consultations', 'legal_jr_2025_10_15',
                    'cmdb', 'cmdb/schema', 'cmdb/ui', 'cmdb/discovery',
                    'missions', 'runbooks', 'vllm_research', 'vllm_research/benchmarks',
                    'conscience_jr_model']:
        path = Path(f'/ganuda/{subdir}')
        if path.exists():
            for f in path.glob('*.md'):
                targets.append(str(f))

    return sorted(set(targets))


def collect_remote_files(host: str, paths: list, is_macos: bool = False) -> list:
    """Collect md files from a remote host via SSH, return list of (remote_path, content, mtime)."""
    results = []
    exclude = '-not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/supabase/*" -not -path "*/pgvector/*" -not -path "*/telegram-bot-api/*" -not -path "*/crawl4ai*" -not -path "*/Wav2Lip/*" -not -path "*/rvc_voice*" -not -path "*/SadTalker/*" -not -path "*/Library/*" -not -path "*/.Trash/*" -not -path "*/llama.cpp/*" -not -path "*/SuperClaude/*" -not -path "*/exo/*" -not -path "*/.claude/*" -not -path "*/grafana/*"'
    # macOS uses stat -f %m, Linux uses stat --format=%Y
    stat_cmd = 'stat -f %m' if is_macos else 'stat --format=%Y'

    for remote_path in paths:
        try:
            cmd = f'ssh -o ConnectTimeout=10 {host} \'find {remote_path} -maxdepth 4 -name "*.md" {exclude} 2>/dev/null\''
            output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            files = [f.strip() for f in output.stdout.strip().split('\n') if f.strip()]
            print(f"  {host}:{remote_path} -> {len(files)} files")

            for remote_file in files:
                try:
                    cmd2 = f'ssh -o ConnectTimeout=10 {host} \'{stat_cmd} "{remote_file}" && cat "{remote_file}"\''
                    result = subprocess.run(cmd2, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n', 1)
                        if len(lines) == 2 and lines[0].strip().isdigit():
                            mtime = datetime.fromtimestamp(int(lines[0].strip()), tz=timezone.utc)
                            content = lines[1]
                            results.append((f"{host}:{remote_file}", content, mtime))
                except (subprocess.TimeoutExpired, Exception) as e:
                    print(f"  SKIP {remote_file}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"  SKIP {remote_path}: {e}", file=sys.stderr)

    return results


def main():
    pw = get_db_password()
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=pw)
    conn.autocommit = True
    cur = conn.cursor()

    # Get existing hashes
    print("Loading existing memory hashes...")
    cur.execute("SELECT memory_hash FROM thermal_memory_archive")
    existing_hashes = set(row[0] for row in cur.fetchall())
    print(f"  {len(existing_hashes)} existing memories")

    # ── Collect local files ──
    print("\nCollecting local files...")
    local_files = collect_local_files()
    print(f"  Found {len(local_files)} local md files")

    records = []
    skipped_dup = 0
    skipped_empty = 0
    skipped_small = 0

    for filepath in local_files:
        try:
            content = Path(filepath).read_text(encoding='utf-8', errors='replace')
            if not content.strip():
                skipped_empty += 1
                continue
            if len(content.strip()) < 50:
                skipped_small += 1
                continue

            h = file_hash(content)
            if h in existing_hashes:
                skipped_dup += 1
                continue

            mtime = get_file_mtime(filepath)
            sacred = is_sacred(filepath, mtime)
            mem_type = classify_memory(filepath)

            metadata = json.dumps({
                'source_file': filepath,
                'source_node': 'redfin',
                'ingestion': 'founding_memory_ingest',
                'memory_type': mem_type,
            })

            records.append((
                content,           # original_content
                h,                 # memory_hash
                sacred,            # sacred_pattern
                mtime,             # created_at
                0.5,               # temperature_score (warm but not hot)
                metadata,          # metadata
            ))
            existing_hashes.add(h)  # prevent self-dups

            if VERBOSE:
                tag = "SACRED" if sacred else "normal"
                print(f"  [{tag}] {os.path.basename(filepath)} ({mem_type}, {mtime.date()})")

        except Exception as e:
            print(f"  ERROR {filepath}: {e}", file=sys.stderr)

    print(f"\nLocal: {len(records)} new, {skipped_dup} duplicates, {skipped_empty} empty, {skipped_small} too small")

    # ── Collect remote files from all nodes ──
    remote_nodes = [
        ('bluefin', False, [  # Linux
            '/home/dereadi/ganuda_ai',
            '/home/dereadi/scripts/claude',
            '/home/dereadi/scripts/sag-spoke',
            '/home/dereadi',
            '/ganuda/dreams',
            '/ganuda/jr_assignments',
            '/ganuda/jr_instructions',
            '/ganuda/missions',
            '/ganuda/runbooks',
            '/ganuda/vllm_research',
            '/ganuda/docs',
        ]),
        ('192.168.132.241', True, [  # sasass - macOS - THE MOTHERLODE
            '/Users/dereadi',
            '/Users/dereadi/Desktop',
            '/Users/dereadi/Documents/brds',
            '/Users/dereadi/Documents',
            '/Users/dereadi/Downloads',
            '/Users/dereadi/cherokee_constitutional_ecoflow',
            '/Users/dereadi/scripts',
            '/Users/dereadi/dr_joe_qbees',
            '/Users/dereadi/QBEES_WHITEPAPERS',
            '/Users/dereadi/ecoflow_constitutional_compliance',
        ]),
        ('192.168.132.21', True, [  # bmasass - macOS
            '/Users/dereadi',
            '/Users/dereadi/Desktop',
            '/Users/dereadi/Documents',
            '/Users/dereadi/tribe',
            '/Users/dereadi/cherokee_triad',
        ]),
        ('192.168.132.242', True, [  # sasass2 - macOS
            '/Users/dereadi',
            '/Users/dereadi/ganuda_ai',
            '/Users/dereadi/cherokee-containers',
            '/Users/dereadi/cherokee_triad',
        ]),
    ]

    for host, is_macos, paths in remote_nodes:
        node_name = {
            '192.168.132.241': 'sasass',
            '192.168.132.21': 'bmasass',
        }.get(host, host)

        print(f"\nCollecting from {node_name}...")
        remote_files = collect_remote_files(host, paths, is_macos=is_macos)
        print(f"  Found {len(remote_files)} files from {node_name}")

        node_new = 0
        for remote_path, content, mtime in remote_files:
            if not content.strip() or len(content.strip()) < 50:
                continue

            h = file_hash(content)
            if h in existing_hashes:
                skipped_dup += 1
                continue

            filepath_str = remote_path.split(':', 1)[1] if ':' in remote_path else remote_path
            sacred = is_sacred(filepath_str, mtime)
            mem_type = classify_memory(filepath_str)

            metadata = json.dumps({
                'source_file': filepath_str,
                'source_node': node_name,
                'ingestion': 'founding_memory_ingest',
                'memory_type': mem_type,
            })

            records.append((content, h, sacred, mtime, 0.5, metadata))
            existing_hashes.add(h)
            node_new += 1

            if VERBOSE:
                tag = "SACRED" if sacred else "normal"
                print(f"  [{tag}] {os.path.basename(filepath_str)} ({mem_type}, {mtime.date()})")

        print(f"{node_name}: {node_new} new")

    # ── Summary ──
    sacred_count = sum(1 for r in records if r[2])
    print(f"\n{'='*50}")
    print(f"TOTAL TO INGEST: {len(records)} new memories")
    print(f"  Sacred: {sacred_count}")
    print(f"  Regular: {len(records) - sacred_count}")
    print(f"  Skipped (duplicate): {skipped_dup}")

    if DRY_RUN:
        print("\n[DRY RUN] No records inserted.")
        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()
        return

    if not records:
        print("\nNothing to ingest.")
        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()
        return

    # ── Insert ──
    print(f"\nInserting {len(records)} records...")
    insert_sql = """
        INSERT INTO thermal_memory_archive
            (original_content, memory_hash, sacred_pattern, created_at, temperature_score, metadata)
        VALUES %s
        ON CONFLICT (memory_hash) DO NOTHING
    """

    execute_values(cur, insert_sql, records, page_size=50)

    # Verify
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive")
    total = cur.fetchone()[0]
    print(f"Done. Total thermal memories: {total}")

    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()


if __name__ == '__main__':
    main()
