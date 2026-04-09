#!/usr/bin/env python3
"""
Owl — Debt Reckoning Daemon
Cherokee AI Federation

Looks backward at completed Jr tasks and verifies the work actually
shipped correctly. Catches the 80/20 debt before it becomes 60/40.

Usage:
    python3 owl_debt_reckoning.py                  # Check last 24 hours
    python3 owl_debt_reckoning.py --days 7          # Check last 7 days
    python3 owl_debt_reckoning.py --task-id 905     # Check specific task
    python3 owl_debt_reckoning.py --dry-run          # Analyze only, skip DB store

For Seven Generations
"""

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_CONFIG = {
    "host": os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'),
    "dbname": "zammad_production",
    "user": "claude",
    "password": None,
}

REPORT_PATH = "/ganuda/reports/owl_debt_reckoning.json"
GANUDA_ROOT = Path("/ganuda")

# Patterns that indicate a task created files
FILE_CREATE_PATTERNS = [
    r'Create\s+`([^`]+)`',
    r'Create\s+"([^"]+)"',
    r'Create\s+(\S+\.py)',
    r'files_created.*?(\d+)',
]

# Tables we know Jr tasks create
KNOWN_TABLE_PATTERNS = [
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
]


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db_connection():
    """Open psycopg2 connection."""
    DB_CONFIG["password"] = os.environ.get("CHEROKEE_DB_PASS")
    if not DB_CONFIG["password"]:
        print("[ERROR] CHEROKEE_DB_PASS not set", file=sys.stderr)
        sys.exit(1)
    return psycopg2.connect(**DB_CONFIG)


def fetch_completed_tasks(conn, days=1, task_id=None):
    """Fetch recently completed Jr tasks."""
    if task_id:
        sql = """
            SELECT id, task_id, title, instruction_file, instruction_content,
                   result::text AS result_text, status, completed_at
            FROM jr_work_queue
            WHERE id = %s
        """
        params = (task_id,)
    else:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        sql = """
            SELECT id, task_id, title, instruction_file, instruction_content,
                   result::text AS result_text, status, completed_at
            FROM jr_work_queue
            WHERE status = 'completed'
              AND completed_at >= %s
            ORDER BY completed_at DESC
        """
        params = (since,)

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def table_exists(conn, table_name):
    """Check if a table exists in the database."""
    sql = """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = %s
        )
    """
    with conn.cursor() as cur:
        cur.execute(sql, (table_name,))
        return cur.fetchone()[0]


def table_row_count(conn, table_name):
    """Get row count for a table. Returns -1 on error."""
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cur.fetchone()[0]
    except Exception:
        conn.rollback()
        return -1


# ---------------------------------------------------------------------------
# Verification checks
# ---------------------------------------------------------------------------

def extract_created_files(instruction_content):
    """Extract file paths from instruction content."""
    if not instruction_content:
        return []
    files = []
    for pattern in FILE_CREATE_PATTERNS:
        matches = re.findall(pattern, instruction_content, re.IGNORECASE)
        for m in matches:
            if isinstance(m, str) and "/" in m:
                # Strip backticks and whitespace artifacts from markdown
                cleaned = m.strip("`'\" \t")
                if cleaned.startswith("/"):
                    files.append(cleaned)
    return list(set(files))


def extract_created_tables(instruction_content):
    """Extract table names from CREATE TABLE statements in instructions."""
    if not instruction_content:
        return []
    tables = []
    # SQL reserved words that are NOT real table names
    false_positives = {"statements", "exists", "table", "index", "view", "schema"}
    for pattern in KNOWN_TABLE_PATTERNS:
        matches = re.findall(pattern, instruction_content, re.IGNORECASE)
        for t in matches:
            if t.lower() not in false_positives:
                tables.append(t)
    return list(set(tables))


def check_file_exists(filepath):
    """Check if a file exists and is non-empty."""
    p = Path(filepath)
    if not p.exists():
        return {"exists": False, "size": 0, "issue": "file_missing"}
    size = p.stat().st_size
    if size == 0:
        return {"exists": True, "size": 0, "issue": "empty_file"}
    return {"exists": True, "size": size, "issue": None}


def check_python_syntax(filepath):
    """Check Python file for syntax errors."""
    try:
        with open(filepath, "r") as f:
            source = f.read()
        ast.parse(source)
        return {"valid": True, "error": None}
    except SyntaxError as e:
        return {"valid": False, "error": f"SyntaxError line {e.lineno}: {e.msg}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def check_python_imports(filepath):
    """Check if Python file has duplicate function definitions or obvious issues."""
    issues = []
    try:
        with open(filepath, "r") as f:
            source = f.read()

        tree = ast.parse(source)
        func_names = []
        class_names = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_names.append(node.name)
            elif isinstance(node, ast.ClassDef):
                class_names.append(node.name)

        # Check for duplicate function definitions (sign of appended files)
        seen = set()
        for name in func_names:
            if name in seen:
                issues.append(f"duplicate_function:{name}")
            seen.add(name)

        # Check for multiple if __name__ blocks (sign of concatenated files)
        main_count = source.count('if __name__')
        if main_count > 1:
            issues.append(f"multiple_main_blocks:{main_count}")

    except Exception as e:
        issues.append(f"parse_error:{e}")

    return issues


def check_result_json(result_text):
    """Parse the Jr result JSON for success indicators."""
    if not result_text:
        return {"parsed": False, "success": None, "steps_succeeded": 0, "steps_failed": 0}
    try:
        result = json.loads(result_text)
        return {
            "parsed": True,
            "success": result.get("success"),
            "steps_succeeded": sum(1 for s in result.get("steps_executed", []) if s.get("success")),
            "steps_failed": sum(1 for s in result.get("steps_executed", []) if not s.get("success")),
            "files_created": result.get("files_created", 0),
        }
    except (json.JSONDecodeError, TypeError):
        return {"parsed": False, "success": None, "steps_succeeded": 0, "steps_failed": 0}


# ---------------------------------------------------------------------------
# Reckoning engine
# ---------------------------------------------------------------------------

def reckon_task(conn, task):
    """Run all verification checks on a single task. Returns a reckoning dict."""
    task_id = task["id"]
    title = task["title"]
    instruction = task.get("instruction_content") or ""

    # If instruction_content is empty, try reading the instruction file
    if not instruction and task.get("instruction_file"):
        try:
            with open(task["instruction_file"], "r") as f:
                instruction = f.read()
        except Exception:
            pass

    reckoning = {
        "task_id": task_id,
        "title": title,
        "status": task["status"],
        "completed_at": str(task.get("completed_at", "")),
        "checks": [],
        "score": "VERIFIED",
        "issues": [],
    }

    # 1. Check result JSON
    result_info = check_result_json(task.get("result_text"))
    reckoning["result_info"] = result_info

    if result_info["parsed"] and result_info["steps_failed"] > 0:
        pct_failed = result_info["steps_failed"] / (result_info["steps_succeeded"] + result_info["steps_failed"])
        if pct_failed > 0.5:
            reckoning["score"] = "BROKEN"
            reckoning["issues"].append(f"{result_info['steps_failed']} of {result_info['steps_succeeded'] + result_info['steps_failed']} steps failed")
        elif pct_failed > 0:
            reckoning["score"] = "DEGRADED"
            reckoning["issues"].append(f"{result_info['steps_failed']} step(s) failed")

    # 2. Check created files
    created_files = extract_created_files(instruction)
    for filepath in created_files:
        file_check = check_file_exists(filepath)
        reckoning["checks"].append({"type": "file_exists", "path": filepath, "result": file_check})

        if file_check["issue"] == "file_missing":
            reckoning["score"] = "BROKEN"
            reckoning["issues"].append(f"File missing: {filepath}")
        elif file_check["issue"] == "empty_file":
            reckoning["score"] = "DEGRADED" if reckoning["score"] != "BROKEN" else "BROKEN"
            reckoning["issues"].append(f"Empty file: {filepath}")

        # Python syntax check
        if filepath.endswith(".py") and file_check["exists"]:
            syntax = check_python_syntax(filepath)
            reckoning["checks"].append({"type": "python_syntax", "path": filepath, "result": syntax})
            if not syntax["valid"]:
                reckoning["score"] = "BROKEN"
                reckoning["issues"].append(f"Syntax error: {filepath}: {syntax['error']}")

            # Duplicate function check
            code_issues = check_python_imports(filepath)
            if code_issues:
                reckoning["checks"].append({"type": "code_quality", "path": filepath, "result": code_issues})
                for issue in code_issues:
                    if "duplicate_function" in issue or "multiple_main_blocks" in issue:
                        reckoning["score"] = "BROKEN"
                        reckoning["issues"].append(f"Code quality: {filepath}: {issue}")

    # 3. Check created tables
    created_tables = extract_created_tables(instruction)
    for table_name in created_tables:
        exists = table_exists(conn, table_name)
        row_count = table_row_count(conn, table_name) if exists else 0
        reckoning["checks"].append({
            "type": "table_exists",
            "table": table_name,
            "result": {"exists": exists, "row_count": row_count},
        })
        if not exists:
            reckoning["score"] = "BROKEN"
            reckoning["issues"].append(f"Table missing: {table_name}")

    return reckoning


# ---------------------------------------------------------------------------
# Report & store
# ---------------------------------------------------------------------------

def store_reckoning(conn, report):
    """Store debt reckoning report in thermal_memory_archive."""
    summary_lines = [
        f"OWL DEBT RECKONING — {report['generated_at'][:10]}",
        f"Tasks checked: {report['summary']['total_checked']}",
        f"VERIFIED: {report['summary']['verified']}",
        f"DEGRADED: {report['summary']['degraded']}",
        f"BROKEN: {report['summary']['broken']}",
        "",
    ]

    for r in report["reckonings"]:
        status_icon = {"VERIFIED": "+", "DEGRADED": "~", "BROKEN": "!"}
        icon = status_icon.get(r["score"], "?")
        summary_lines.append(f"[{icon}] #{r['task_id']} {r['title']}: {r['score']}")
        for issue in r["issues"]:
            summary_lines.append(f"    - {issue}")

    content = "\n".join(summary_lines)
    mem_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    tags = ["owl", "debt_reckoning", "verification", "retrospective"]
    metadata = json.dumps({
        "source": "owl_debt_reckoning",
        "total_checked": report["summary"]["total_checked"],
        "verified": report["summary"]["verified"],
        "degraded": report["summary"]["degraded"],
        "broken": report["summary"]["broken"],
        "checked_at": report["generated_at"],
    })

    sql = """
        INSERT INTO thermal_memory_archive
            (original_content, memory_type, tags, temperature_score,
             memory_hash, metadata, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (memory_hash) DO NOTHING
    """
    temp_score = 50
    if report["summary"]["broken"] > 0:
        temp_score = 80
    elif report["summary"]["degraded"] > 0:
        temp_score = 65

    with conn.cursor() as cur:
        cur.execute(sql, (
            content,
            "debt_audit",
            tags,
            temp_score,
            mem_hash,
            metadata,
            datetime.now(timezone.utc),
        ))
    conn.commit()
    return content


def main():
    parser = argparse.ArgumentParser(description="Owl — Debt Reckoning Daemon")
    parser.add_argument("--days", type=int, default=1, help="Look back N days (default: 1)")
    parser.add_argument("--task-id", type=int, help="Check a specific task by ID")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, skip DB store")
    args = parser.parse_args()

    print("=" * 60)
    print("OWL — Debt Reckoning")
    print("Seeing what others miss in the dark")
    print("=" * 60)
    print()

    conn = get_db_connection()
    print("[OK] Database connected")

    tasks = fetch_completed_tasks(conn, days=args.days, task_id=args.task_id)
    print(f"[INFO] Found {len(tasks)} completed task(s) to check")
    print()

    if not tasks:
        print("[DONE] Nothing to reckon")
        conn.commit()  # explicit commit before close
        conn.close()
        return

    reckonings = []
    for task in tasks:
        print(f"--- Checking #{task['id']}: {task['title']} ---")
        r = reckon_task(conn, task)
        reckonings.append(r)

        print(f"  Score: {r['score']}")
        if r["issues"]:
            for issue in r["issues"]:
                print(f"  Issue: {issue}")
        if r["checks"]:
            print(f"  Checks run: {len(r['checks'])}")
        print()

    # --- Observability Report (BSM Leg 3) ---
    # Timer: weekly_observability_report runs at Wed 04:50, owl runs at Wed 05:00
    # Read the pre-generated report if it exists, otherwise note absence
    obs_report_path = "/ganuda/logs/weekly_observability_report.md"
    obs_report_content = None
    try:
        if os.path.exists(obs_report_path):
            with open(obs_report_path, "r") as f:
                obs_report_content = f.read()
            # Only include if it was generated today (fresh report)
            report_mtime = datetime.fromtimestamp(
                os.path.getmtime(obs_report_path), tz=timezone.utc
            )
            age_hours = (datetime.now(timezone.utc) - report_mtime).total_seconds() / 3600
            if age_hours > 24:
                print(f"[WARN] Observability report is {age_hours:.0f}h old — may be stale")
            else:
                print(f"[OK] Observability report loaded ({len(obs_report_content)} chars, {age_hours:.1f}h old)")
        else:
            print(f"[WARN] No observability report at {obs_report_path} — timer may not have run")
    except Exception as e:
        print(f"[WARN] Failed to read observability report: {e}")

    # Build report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lookback_days": args.days,
        "summary": {
            "total_checked": len(reckonings),
            "verified": sum(1 for r in reckonings if r["score"] == "VERIFIED"),
            "degraded": sum(1 for r in reckonings if r["score"] == "DEGRADED"),
            "broken": sum(1 for r in reckonings if r["score"] == "BROKEN"),
        },
        "reckonings": reckonings,
        "observability_report_available": obs_report_content is not None,
    }

    # Save JSON report
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Store in thermal memory
    if not args.dry_run:
        summary_text = store_reckoning(conn, report)
        print("[OK] Reckoning stored in thermal memory")
    else:
        print("[DRY RUN] Skipping thermal memory store")

    conn.commit()  # explicit commit before close
    conn.close()

    # Print final summary
    print()
    print("=" * 60)
    print("DEBT RECKONING COMPLETE")
    print(f"  Total checked:  {report['summary']['total_checked']}")
    print(f"  VERIFIED:       {report['summary']['verified']}")
    print(f"  DEGRADED:       {report['summary']['degraded']}")
    print(f"  BROKEN:         {report['summary']['broken']}")
    print(f"  Report:         {REPORT_PATH}")
    print("=" * 60)

    # --- BSM Leg 3: Observability Report Section ---
    if obs_report_content:
        print()
        print("=" * 60)
        print("OBSERVABILITY REPORT (BSM Leg 3)")
        print("=" * 60)
        print(obs_report_content)
        print("=" * 60)

    # Exit non-zero if anything is broken
    if report["summary"]["broken"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()