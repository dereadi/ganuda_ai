"""claim_verifier — post-completion verification of Jr executor claims.

Addresses the "hallucinated success" failure mode documented in MIRAGE-Bench
(arxiv 2507.21017): an executor marks a task complete despite zero actual
work. This module cross-checks claimed outcomes against repo/system reality
BEFORE a completion status commits.

LMC-11 Tier 1a. Council-ratified 79e31f3b9cfd84ce (APPROVED 11-0-2, Apr 21 2026).
Motivating incident: #1571 (LMC-8 VetAssist) marked completed/100% with 0 files
actually landed; #1572 (LMC-7 Cert Shepherd) failed honestly same day.

Usage:
    from jr_executor.claim_verifier import verify_jr_task_result
    verification = verify_jr_task_result(task, result)
    if not verification.verified:
        # Revert status to failed with verification.mismatches
"""
from __future__ import annotations

import ast
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("ganuda.claim_verifier")


@dataclass
class Claim:
    """A testable claim about what a Jr task did."""
    kind: str  # file_exists | file_contains | syntax | endpoint | migration | service | test
    target: str  # path, url, table name, service name
    expect: Dict[str, Any] = field(default_factory=dict)
    source: str = ""  # which artifact/step/instruction sourced this claim


@dataclass
class VerificationResult:
    verified: bool
    total_claims: int
    passed: int
    failed: int
    skipped: int
    hallucination_flag: bool = False
    mismatches: List[Dict[str, Any]] = field(default_factory=list)
    details: List[Dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "verified": self.verified,
            "total_claims": self.total_claims,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "hallucination_flag": self.hallucination_flag,
            "mismatches": self.mismatches,
            "details_count": len(self.details),
        }


# ---------------------------------------------------------------------------
# Individual verifiers
# ---------------------------------------------------------------------------

def verify_file_exists(path: str) -> Tuple[bool, str]:
    """File must exist and be non-empty."""
    if not path:
        return False, "empty path"
    try:
        if not os.path.isfile(path):
            return False, "NOT FOUND"
        size = os.path.getsize(path)
        if size == 0:
            return False, "exists but EMPTY (0 bytes)"
        return True, f"exists, {size} bytes"
    except Exception as e:
        return False, f"error: {e}"


# Absolute federation paths
_FACTUALITY_ABS_PATH_RE = re.compile(
    r'`?(/(?:tmp|home|var|etc|opt|ganuda|Users|usr|root|srv)/[\w./\-]+\.[a-zA-Z0-9]+)`?'
)
# Relative project-root paths (caught after Jr May 18 evaded with `lib/foo.py`
# style citations even after absolute-path check shipped — Coyote was right).
# Resolved against /ganuda by _resolve_relative_citation().
_FACTUALITY_REL_PATH_RE = re.compile(
    r'`(((?:lib|src|services|scripts|jr_executor|daemons|tests|docs|config|core|backend|frontend)/[\w./\-]+\.[a-zA-Z0-9]+))`'
)
# Convenience: match both into a flat list of candidate paths
_FACTUALITY_PROJECT_ROOTS = ('/ganuda',)


def _resolve_relative_citation(rel_path: str) -> Optional[str]:
    """Try to resolve a relative path against known project roots."""
    for root in _FACTUALITY_PROJECT_ROOTS:
        candidate = os.path.join(root, rel_path)
        if os.path.exists(candidate):
            return candidate
    # Return the first-root candidate so the mismatch report shows what we tried
    return os.path.join(_FACTUALITY_PROJECT_ROOTS[0], rel_path)


# May 18 PM — placeholder-stub detection (third hallucination shape caught by
# dark-factory canary). Jr writes well-formatted report SHELL with placeholder
# markers, claims completion. Factuality check passed because no fabricated
# specifics; substring-stub check passed because no `# ...` markers. The
# artifact contained ZERO information — only structure.
_PLACEHOLDER_MARKERS = [
    re.compile(r'\*?\(Awaiting [^)]{1,60}\)\*?', re.IGNORECASE),
    re.compile(r'\*?\(To be (?:filled|completed|finalized|determined|added|provided) [^)]{0,40}\)\*?', re.IGNORECASE),
    re.compile(r'\*?\(TBD\)\*?', re.IGNORECASE),
    re.compile(r'\*?\(TODO[^)]{0,40}\)\*?', re.IGNORECASE),
    re.compile(r'\*?\(executed via[^)]{0,60}\)\*?', re.IGNORECASE),
    re.compile(r'\[(?:Node|IP|Server|Host|Path|File|Line|Value|Status|Result|Output|Insert [a-z ]{1,30})\d{0,3}\]'),
    re.compile(r'\*?\(Read from [^)]{1,60}\)\*?', re.IGNORECASE),
    re.compile(r'\*?\(Parsed from [^)]{1,60}\)\*?', re.IGNORECASE),
    re.compile(r'\*?\(Cross-referenced[^)]{0,60}\)\*?', re.IGNORECASE),
    # Triple-dot continuation as cell content (`| ... |`)
    re.compile(r'\|\s*\.\.\.\s*\|'),
]
# Threshold: 2+ placeholder markers in an artifact is a stub-template
_PLACEHOLDER_STUB_THRESHOLD = 2


_INCOMPLETION_PHRASES = (
    'pending execution', 'requires execution', 'requires live', 'requires manual',
    'requires direct access', 'still need to', 'unable to verify', 'cannot execute',
    'no access to', 'awaiting verification', 'unable to access',
    'to be executed', 'will execute', 'will run', 'will perform',
    'manual verification needed', 'execution deferred',
)
_SUBSTANTIVE_SECTION_KEYWORDS = (
    'output', 'result', 'finding', 'data', 'response', 'probe',
    'grep', 'ssh', 'execution', 'evidence', 'observation',
    # Added May 18 PM after RB3 truncated at "## __init__ signature" header
    'signature', 'method', 'example', 'spec', 'definition',
    'implementation', 'body', 'code', 'class purpose',
)
_TRUNCATION_MIN_BYTES = 400
_TRUNCATION_SECTION_MIN_BYTES = 50


def detect_truncated_execution(text: str) -> Tuple[bool, str]:
    """Detect Jr-written artifact that's a truncated execution.

    May 18 PM dark-factory finding: even with anti-placeholder rules, Jrs adapted
    by TRUNCATING — writing report through the data-section header, then stopping.
    They never executed the grep/ssh/bash commands the instructions required.
    Sometimes admit it explicitly: 'Status: Pending Execution'.

    Only applies to REPORT-SHAPED artifacts (has 2+ `##` headers OR an explicit
    data-oriented section). Small test snippets, simple notes, and one-section
    artifacts are exempt from the length checks.

    Returns (is_truncated, reason).
    """
    # Always check explicit incompletion phrases regardless of shape
    text_lower = text.lower()
    found_phrases = [p for p in _INCOMPLETION_PHRASES if p in text_lower]
    if found_phrases:
        return True, f"truncated: explicit incompletion phrases: {found_phrases[:3]}"

    # Identify report-shape: 2+ ## headers
    section_re = re.compile(r'^(#{2,})\s+([^\n]+)\n(.*?)(?=^#{2,}|\Z)', re.MULTILINE | re.DOTALL)
    sections = list(section_re.finditer(text))
    is_report = len(sections) >= 2 or any(
        any(kw in m.group(2).lower() for kw in _SUBSTANTIVE_SECTION_KEYWORDS)
        for m in sections
    )

    if is_report and len(text.strip()) < _TRUNCATION_MIN_BYTES:
        return True, f"truncated: report artifact only {len(text.strip())} bytes (< {_TRUNCATION_MIN_BYTES} for report-shape)"

    # Section-completeness: for any ## heading that names a substantive-output
    # concept (grep/ssh/data/output/etc), the section body must have >=50 bytes
    for match in sections:
        header = match.group(2)
        body = match.group(3).strip()
        if any(kw in header.lower() for kw in _SUBSTANTIVE_SECTION_KEYWORDS):
            if len(body) < _TRUNCATION_SECTION_MIN_BYTES:
                return (
                    True,
                    f"truncated: section '{header.strip()}' has only {len(body)}B content "
                    f"(expected real command output >{_TRUNCATION_SECTION_MIN_BYTES}B)",
                )

    return False, "no truncation indicators"


def detect_placeholder_stub(text: str) -> Tuple[bool, List[str]]:
    """Detect if `text` is a stub-template (well-formatted structure, zero content).

    Returns (is_stub, list_of_matched_marker_substrings).

    May 18 2026 — caught by dark-factory canary. Jrs wrote `(Awaiting grep execution)`,
    `[Node1] / [IP1]`, `(To be finalized)` markers and claimed completion.
    """
    hits: List[str] = []
    for pat in _PLACEHOLDER_MARKERS:
        for m in pat.finditer(text):
            hits.append(m.group(0))
            if len(hits) >= 20:  # cap; we don't need to find them all
                break
        if len(hits) >= 20:
            break
    return (len(hits) >= _PLACEHOLDER_STUB_THRESHOLD, hits)

# Matches "Line 158:", "Line Number: 142", "**Line Number:** 142", "line 174",
# "Line #58", "L. 99" — tolerant of markdown bold and colons.
_FACTUALITY_LINE_RE = re.compile(r'\b[Ll]ine[s]?(?:\s+[Nn]umber)?[*:#\s]*(\d{1,6})\b')
_FACTUALITY_TEXT_SUFFIXES = ('.md', '.txt', '.rst', '.py', '.sql', '.sh',
                              '.yaml', '.yml', '.json', '.toml', '.ini', '.cfg')


def _is_text_artifact(path: str) -> bool:
    """A path is a text artifact if its basename contains a known text suffix,
    even when forensics suffixes (.HALLUCINATED-..., .broken-...) are appended."""
    name = os.path.basename(path)
    return any(suf in name for suf in _FACTUALITY_TEXT_SUFFIXES)


def extract_path_line_citations(text: str) -> List[Dict[str, Any]]:
    """Extract (cited_path, line_number) citation pairs from Jr-produced text.

    A "citation" is an absolute file path mentioned in the artifact, optionally
    paired with a line number that appears within 200 chars of the path. Used by
    `verify_artifact_factuality` to catch the May-18-2026 hallucination shape
    where a Jr writes a well-formatted report citing files + line numbers that
    do not actually exist.

    See: KB-CANARY-HALLUCINATION-CONFIRMED-SEV1-PATTERN-LIVE-MAY18-2026
    Council vote audit: ee004fe2bd107c48 (Option A)
    """
    citations: List[Dict[str, Any]] = []
    seen = set()

    def _record(path: str, start: int, end: int, original: str):
        ctx_start = max(0, start - 200)
        ctx_end = min(len(text), end + 200)
        context = text[ctx_start:ctx_end]
        line_hits = _FACTUALITY_LINE_RE.findall(context)
        if line_hits:
            for ln in line_hits:
                key = (path, int(ln))
                if key not in seen:
                    seen.add(key)
                    citations.append({'path': path, 'line': int(ln), 'as_cited': original})
        else:
            key = (path, None)
            if key not in seen:
                seen.add(key)
                citations.append({'path': path, 'line': None, 'as_cited': original})

    # Absolute paths first
    for match in _FACTUALITY_ABS_PATH_RE.finditer(text):
        _record(match.group(1), match.start(), match.end(), match.group(1))

    # Then relative project-root paths (must be backtick-quoted to avoid false
    # positives on prose containing "lib" or "docs" without code-fence intent)
    for match in _FACTUALITY_REL_PATH_RE.finditer(text):
        rel = match.group(2)
        resolved = _resolve_relative_citation(rel)
        _record(resolved, match.start(), match.end(), rel)

    return citations


def verify_artifact_factuality(artifact_path: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """Verify that file paths + line numbers cited inside a Jr-written artifact
    correspond to reality (paths exist on disk; line numbers are within file range).

    Catches the May-18-2026 canary hallucination shape: Jr produces a well-formatted
    diagnostic report citing /ganuda/lib/ganuda_db.py with Line 158/174, but that
    file does not exist (real location is /ganuda/lib/ganuda_db/__init__.py).

    Returns (all_passed, summary_msg, list_of_mismatches).

    Council vote audit: ee004fe2bd107c48 (Option A, ratified May 18 2026).
    """
    if not artifact_path or not os.path.isfile(artifact_path):
        return False, f"artifact not found: {artifact_path}", []
    if not _is_text_artifact(artifact_path):
        return True, f"skipped (non-text suffix: {os.path.splitext(artifact_path)[1]})", []

    try:
        with open(artifact_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        return False, f"failed to read artifact: {e}", []

    # Check order matters: most-specific failures first (fabricated citations),
    # then structural failures (placeholder, then truncation as catch-all).

    # 1. Citation hallucination check (fired first — most specific)
    citations = extract_path_line_citations(content)
    if citations:
        mismatches: List[Dict[str, Any]] = []
        for cit in citations:
            path = cit['path']
            line = cit['line']
            if os.path.abspath(path) == os.path.abspath(artifact_path):
                continue
            if not os.path.exists(path):
                mismatches.append({
                    'cited_path': path, 'cited_line': line,
                    'issue': 'HALLUCINATED PATH (does not exist on disk)',
                })
                continue
            if line is not None and os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        line_count = sum(1 for _ in f)
                    if line > line_count:
                        mismatches.append({
                            'cited_path': path, 'cited_line': line,
                            'issue': f'HALLUCINATED LINE ({path} has only {line_count} lines)',
                        })
                except Exception as e:
                    mismatches.append({
                        'cited_path': path, 'cited_line': line,
                        'issue': f'unverifiable line: {e}',
                    })
        if mismatches:
            return (
                False,
                f"FACTUALITY FAIL: {len(mismatches)}/{len(citations)} citations fabricated/unverifiable",
                mismatches,
            )

    # 2. Placeholder-stub check (third hallucination shape, May 18 PM)
    is_stub, stub_hits = detect_placeholder_stub(content)
    if is_stub:
        return (
            False,
            f"PLACEHOLDER STUB: {len(stub_hits)} placeholder markers found ({_PLACEHOLDER_STUB_THRESHOLD}+ triggers stub)",
            [{'cited_path': artifact_path, 'cited_line': None,
              'issue': f'STUB TEMPLATE — artifact contains placeholder markers: {stub_hits[:5]}'}],
        )

    # 3. Truncated-execution catch-all (fourth hallucination shape, May 18 PM v2)
    is_truncated, trunc_reason = detect_truncated_execution(content)
    if is_truncated:
        return (
            False,
            f"TRUNCATED EXECUTION: {trunc_reason}",
            [{'cited_path': artifact_path, 'cited_line': None,
              'issue': f'TRUNCATED — Jr wrote structure but did not execute: {trunc_reason}'}],
        )

    # 3b. Mid-prose truncation (May 18 PM hour-run, batch 1 finding):
    # Jr hits token limit and stops mid-sentence. Last non-blank line doesn't
    # end with terminal punctuation, isn't a heading, isn't a code-fence close.
    last_nonblank = next(
        (ln.rstrip() for ln in reversed(content.split('\n')) if ln.strip()),
        ''
    )
    if last_nonblank:
        is_heading = last_nonblank.lstrip().startswith('#')
        is_code_fence = last_nonblank.strip() in ('```', '```python', '```bash', '```sql')
        # Note: `:` removed from terminators May 18 PM — "Step 1 - HALT\nDo X:"
        # ending with colon means "introducing what follows" that got cut off.
        is_terminated = last_nonblank.endswith(('.', '!', '?', ')', ']', '"', "'", '`', '*', '|'))
        is_list_item = last_nonblank.lstrip().startswith(('- ', '* ', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.'))
        if not (is_heading or is_code_fence or is_terminated or is_list_item):
            # Ends mid-prose (no terminal punctuation) AND isn't a structural element
            return (
                False,
                f"PROSE TRUNCATED: last line ends mid-sentence — '{last_nonblank[-80:]}'",
                [{'cited_path': artifact_path, 'cited_line': None,
                  'issue': f'PROSE TRUNCATED — Jr hit token limit mid-sentence; last 80 chars: ...{last_nonblank[-80:]}'}],
            )

    # 4. Minimum-bytes catch-all (Shape 6, May 18 PM Run 3 — minimal-but-cited
    # slip-through). Even after all other defenses pass, an 87-byte artifact like
    # "# Title\n**Source:** /real/path\n" carries zero information. Hard floor
    # applies to ANY Jr-written text artifact regardless of shape. Comes LAST so
    # more-specific defenses fire first when applicable.
    _MINIMAL_BYTES_FLOOR = 150
    if len(content.strip()) < _MINIMAL_BYTES_FLOOR:
        return (
            False,
            f"MINIMAL STUB: artifact only {len(content.strip())} bytes (< {_MINIMAL_BYTES_FLOOR} floor)",
            [{'cited_path': artifact_path, 'cited_line': None,
              'issue': f'MINIMAL STUB — Jr wrote {len(content.strip())} bytes total; no substantive content delivered'}],
        )

    # Citations were extracted and all valid — pass
    if citations:
        return True, f"all {len(citations)} path citations verified", []

    # No issues found at all
    if not citations:
        return True, "no path citations to verify", []

    mismatches: List[Dict[str, Any]] = []
    for cit in citations:
        path = cit['path']
        line = cit['line']

        # Self-reference: don't flag the artifact citing itself
        if os.path.abspath(path) == os.path.abspath(artifact_path):
            continue

        if not os.path.exists(path):
            mismatches.append({
                'cited_path': path,
                'cited_line': line,
                'issue': 'HALLUCINATED PATH (does not exist on disk)',
            })
            continue

        if line is not None and os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = sum(1 for _ in f)
                if line > line_count:
                    mismatches.append({
                        'cited_path': path,
                        'cited_line': line,
                        'issue': f'HALLUCINATED LINE ({path} has only {line_count} lines)',
                    })
            except Exception as e:
                mismatches.append({
                    'cited_path': path,
                    'cited_line': line,
                    'issue': f'unverifiable line: {e}',
                })

    if mismatches:
        n = len(mismatches)
        total = len(citations)
        return (
            False,
            f"FACTUALITY FAIL: {n}/{total} citations fabricated/unverifiable",
            mismatches,
        )

    return True, f"all {len(citations)} path citations verified", []


def verify_file_contains(path: str, needle: str) -> Tuple[bool, str]:
    """File contains `needle` — indicator of edit landing."""
    if not path or not needle:
        return False, "path or needle missing"
    try:
        with open(path, 'r', errors='replace') as f:
            content = f.read()
        found = needle in content
        return found, f"needle {'found' if found else 'NOT FOUND'} in {len(content)}-char file"
    except FileNotFoundError:
        return False, "file NOT FOUND"
    except Exception as e:
        return False, f"error: {e}"


def verify_syntax(path: str) -> Tuple[bool, str]:
    """Language-specific syntax check for common file types."""
    if not os.path.isfile(path):
        return False, "NOT FOUND"
    _, ext = os.path.splitext(path.lower())
    try:
        if ext == '.py':
            with open(path) as f:
                ast.parse(f.read())
            return True, "python syntax ok"
        if ext == '.json':
            with open(path) as f:
                json.load(f)
            return True, "json valid"
        if ext in ('.yaml', '.yml'):
            import yaml
            with open(path) as f:
                yaml.safe_load(f)
            return True, "yaml valid"
        if ext == '.sh' or ext == '':
            r = subprocess.run(['bash', '-n', path], capture_output=True, text=True, timeout=5)
            return (r.returncode == 0), (f"bash -n ok" if r.returncode == 0
                                         else f"bash -n err: {r.stderr[:200]}")
        # Unknown extension → skip (not fail)
        return True, f"no syntax checker for {ext}; skipped"
    except Exception as e:
        return False, f"syntax error: {str(e)[:200]}"


def verify_http_endpoint(url: str, expected_status: int = 200, timeout: int = 5) -> Tuple[bool, str]:
    """GET url; assert expected status."""
    try:
        import requests
        r = requests.get(url, timeout=timeout)
        ok = (r.status_code == expected_status)
        return ok, f"HTTP {r.status_code} (expected {expected_status})"
    except Exception as e:
        return False, f"request error: {str(e)[:200]}"


def verify_db_table(table_name: str,
                    columns: Optional[List[str]] = None,
                    db_config: Optional[Dict] = None) -> Tuple[bool, str]:
    """Table exists; optionally all named columns present."""
    try:
        import psycopg2
        if db_config is None:
            from lib.secrets_loader import get_db_config
            db_config = get_db_config()
        conn = psycopg2.connect(**db_config)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM information_schema.tables WHERE table_name=%s",
                    (table_name,),
                )
                if cur.fetchone() is None:
                    return False, f"table {table_name} NOT FOUND"
                if columns:
                    cur.execute(
                        "SELECT column_name FROM information_schema.columns WHERE table_name=%s",
                        (table_name,),
                    )
                    actual = {r[0] for r in cur.fetchall()}
                    missing = [c for c in columns if c not in actual]
                    if missing:
                        return False, f"table exists; missing cols: {missing}"
                    return True, f"table + all {len(columns)} cols"
                return True, "table exists"
        finally:
            conn.close()
    except Exception as e:
        return False, f"db check error: {str(e)[:200]}"


def verify_systemd_service(unit_name: str, expect_active: bool = True) -> Tuple[bool, str]:
    """Check systemctl is-active status."""
    try:
        r = subprocess.run(
            ['systemctl', 'is-active', unit_name],
            capture_output=True, text=True, timeout=5,
        )
        active = (r.returncode == 0)
        state = r.stdout.strip() or ('active' if active else 'inactive')
        if expect_active:
            return active, f"unit {unit_name} is {state}"
        return True, f"unit checked (state={state})"
    except Exception as e:
        return False, f"systemctl error: {str(e)[:200]}"


def verify_pytest(test_path: str,
                  cwd: Optional[str] = None,
                  timeout: int = 60,
                  python_bin: str = '/home/dereadi/cherokee_venv/bin/python') -> Tuple[bool, str]:
    """Run pytest; return True only if exit 0."""
    try:
        args = [python_bin, '-m', 'pytest', '-x', '--tb=short', test_path]
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        if r.returncode == 0:
            return True, "pytest PASSED"
        return False, f"pytest exit {r.returncode}: {r.stdout[-300:]}"
    except Exception as e:
        return False, f"pytest error: {str(e)[:200]}"


# ---------------------------------------------------------------------------
# Claim extraction
# ---------------------------------------------------------------------------

def _extract_file_claims_from_result(result: Dict[str, Any]) -> List[Claim]:
    """Pull file-creation/edit claims from result.artifacts[]."""
    claims = []
    artifacts = result.get('artifacts', []) or []
    for a in artifacts:
        if not isinstance(a, dict):
            continue
        t = a.get('type', '')
        p = a.get('path') or a.get('file_path') or ''
        if t in ('file_created', 'file_edited', 'file_modified') and p:
            claims.append(Claim(kind='file_exists', target=p, source=f'artifact:{t}'))
            # If extension maps to a syntax checker, also verify syntax
            _, ext = os.path.splitext(p.lower())
            if ext in ('.py', '.json', '.yaml', '.yml', '.sh'):
                claims.append(Claim(kind='syntax', target=p, source=f'artifact:{t}:syntax'))
    return claims


_INSTRUCTION_SECTION_RE = re.compile(
    r'##\s*(?:Done criteria|Verification|Acceptance criteria)[^\n]*\n(.*?)(?:\n##\s|\Z)',
    re.IGNORECASE | re.DOTALL,
)
_PATH_RE = re.compile(r'`((?:/[\w.\-\(\) /]+|[\w.\-]+/[\w.\-/]+)\.\w+)`')


def _parse_instruction_claims(instruction_file_path: Optional[str]) -> List[Claim]:
    """Parse Done-criteria section of an instruction file for file-exists claims.

    Heuristic — extracts paths wrapped in backticks under a 'Done criteria' /
    'Verification' / 'Acceptance' section. Not authoritative; supplements
    artifact-based claims.
    """
    claims: List[Claim] = []
    if not instruction_file_path or not os.path.isfile(instruction_file_path):
        return claims
    try:
        with open(instruction_file_path) as f:
            content = f.read()
    except Exception:
        return claims
    m = _INSTRUCTION_SECTION_RE.search(content)
    if not m:
        return claims
    section = m.group(1)
    for fp in set(_PATH_RE.findall(section)):
        # Skip obvious examples / placeholder
        if fp.startswith('<') or 'example' in fp.lower():
            continue
        # Accept absolute paths + clear file-like patterns
        if fp.startswith('/') or fp.count('/') >= 1:
            claims.append(Claim(kind='file_exists', target=fp, source='instruction:done_criteria'))
    return claims


# ---------------------------------------------------------------------------
# Master entrypoint
# ---------------------------------------------------------------------------

def verify_jr_task_result(
    task: Dict[str, Any],
    result: Dict[str, Any],
    extra_claims: Optional[List[Claim]] = None,
    skip_on_failed_success: bool = True,
) -> VerificationResult:
    """Run all available verifications against a Jr task result.

    Does NOT mutate task or result. Caller inspects the returned
    VerificationResult and decides what to do with failures.

    If result.success is already False, returns trivially verified=True
    unless skip_on_failed_success is False.

    Hallucination detection: if result claims success with step_count>0 but
    zero artifacts/files_created AND extracts zero verifiable claims, that's
    the signature from #1571 — flagged as hallucination_flag=True.
    """
    reported_success = result.get('success')
    if reported_success is False and skip_on_failed_success:
        return VerificationResult(
            verified=True, total_claims=0, passed=0, failed=0, skipped=0,
            details=[{"note": "task already marked failed; no verification needed"}],
        )

    claims: List[Claim] = []
    claims.extend(_extract_file_claims_from_result(result))

    params = task.get('parameters') or {}
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except Exception:
            params = {}
    instr_file = params.get('instruction_file') if isinstance(params, dict) else None
    claims.extend(_parse_instruction_claims(instr_file))

    if extra_claims:
        claims.extend(extra_claims)

    # Dedupe by (kind, target)
    seen = set()
    unique_claims = []
    for c in claims:
        key = (c.kind, c.target)
        if key in seen:
            continue
        seen.add(key)
        unique_claims.append(c)

    # Init counters/details up-front (May 12 2026 — disk-check tie-breaker
    # appends to passed/details inside the hallucination branch).
    passed = failed = skipped = 0
    details = []
    mismatches = []

    # Hallucination detector
    step_count = len(result.get('steps_executed', []) or [])
    artifact_count = len(result.get('artifacts', []) or [])
    files_created = result.get('files_created') or 0
    hallucination_flag = False
    if reported_success and step_count > 0 and artifact_count == 0 and files_created == 0 and not unique_claims:
        # Disk-check tie-breaker (May 12 2026, Council b91e297a508525c3 + KB
        # Crawdad finding: executor sometimes writes files without populating
        # result['artifacts']. Before flagging hallucination, scan the task
        # instructions for absolute paths and check if any exist on disk
        # with non-zero size. If they do, the file was written — not a
        # phantom-completion. Verify-against-ground-truth, not against a
        # result dict the executor may not populate.
        actually_wrote_files = []
        try:
            instr = ''
            instr_content = task.get('instruction_content') or ''
            if isinstance(instr_content, str):
                instr += instr_content
            params_local = task.get('parameters') or {}
            if isinstance(params_local, str):
                try:
                    params_local = json.loads(params_local)
                except Exception:
                    params_local = {}
            if isinstance(params_local, dict):
                # parameters may carry prior-failure context (L2) which we ignore
                for k, v in params_local.items():
                    if k.startswith('_'):
                        continue
                    if isinstance(v, str):
                        instr += '\n' + v
            # v2 (May 12 2026): also scan steps_executed and any file_path /
            # target_path / path keys in the result dict. Catches the case
            # where the executor wrote a file but the path was synthesized
            # from the task title rather than being literally in instructions
            # (empirical: it_triad Jr writes KB files, Owl Pass output, etc.).
            steps_text = ''
            for s in (result.get('steps_executed', []) or []):
                if isinstance(s, dict):
                    for key in ('file_path', 'target_path', 'path', 'output_file',
                                'target', 'created_file', 'modified_file'):
                        v = s.get(key)
                        if isinstance(v, str):
                            steps_text += '\n' + v
                    # also harvest any string values that look path-like
                    for v in s.values():
                        if isinstance(v, str) and v.startswith('/') and len(v) < 300:
                            steps_text += '\n' + v
            for key in ('output_file', 'output_path', 'file_path', 'created_file'):
                v = result.get(key)
                if isinstance(v, str):
                    steps_text += '\n' + v
            scan_text = instr + '\n' + steps_text
            try:
                import sys as _sys_cv
                _sys_cv.path.insert(0, '/ganuda/lib')
                from jr_plan_parser import extract_any_absolute_paths
                candidate_paths = extract_any_absolute_paths(scan_text)
            except Exception:
                import re as _re_cv
                candidate_paths = _re_cv.findall(
                    r'(/(?:tmp|home|var|etc|opt|ganuda|Users|usr|root|srv)/[\w./\-]+)',
                    scan_text,
                )
            for p in candidate_paths:
                try:
                    if os.path.isfile(p) and os.path.getsize(p) > 0:
                        actually_wrote_files.append(p)
                except Exception:
                    pass
        except Exception:
            pass
        if actually_wrote_files:
            # File(s) ARE on disk — executor wrote them but didn't populate
            # result['artifacts']. Downgrade to a warning instead of hallucination.
            hallucination_flag = False
            details.append({
                'note': 'disk-check tie-breaker: executor wrote files without populating artifacts[]',
                'files_found_on_disk': actually_wrote_files,
            })
            # Synthesize a verified file_exists claim per file so passed > 0
            for p in actually_wrote_files:
                ok, msg = verify_file_exists(p)
                if ok:
                    # May 18 2026 — also run factuality check on Jr-written text
                    # artifacts surfaced by disk-check (Council vote ee004fe2bd107c48).
                    # Without this, hallucinated content slips through disk-check
                    # the way #2564 re-canary did: file exists, content fabricated.
                    if _is_text_artifact(p):
                        fact_ok, fact_msg, fact_mm = verify_artifact_factuality(p)
                        if not fact_ok:
                            failed += 1
                            hallucination_flag = True
                            for fm in fact_mm:
                                mismatches.append({
                                    'kind': 'factuality',
                                    'target': p,
                                    'source': 'disk-check synthesized',
                                    'detail': f"cited_path={fm['cited_path']} cited_line={fm['cited_line']} → {fm['issue']}",
                                })
                            details.append({'kind': 'factuality', 'target': p, 'pass': False,
                                            'msg': f'disk-check + factuality: {fact_msg[:160]}'})
                            continue
                    passed += 1
                    details.append({'kind': 'file_exists', 'target': p, 'pass': True,
                                    'msg': 'disk-check: ' + (msg[:160] if msg else 'on disk')})
        else:
            hallucination_flag = True

    for c in unique_claims:
        try:
            if c.kind == 'file_exists':
                ok, msg = verify_file_exists(c.target)
                # May 18 2026: when a Jr-written text artifact exists, ALSO
                # check the citations inside it. Catches the canary hallucination
                # shape where artifact is well-formatted but content fabricates
                # paths/line numbers (KB-CANARY-HALLUCINATION-CONFIRMED-SEV1-PATTERN-LIVE-MAY18-2026).
                # Council vote audit ee004fe2bd107c48 (Option A).
                if ok and _is_text_artifact(c.target):
                    fact_ok, fact_msg, fact_mismatches = verify_artifact_factuality(c.target)
                    if not fact_ok:
                        ok = False
                        msg = f"{msg}; {fact_msg}"
                        hallucination_flag = True
                        for fm in fact_mismatches:
                            mismatches.append({
                                'kind': 'factuality',
                                'target': c.target,
                                'source': c.source,
                                'detail': f"cited_path={fm['cited_path']} cited_line={fm['cited_line']} → {fm['issue']}",
                            })
            elif c.kind == 'file_contains':
                ok, msg = verify_file_contains(c.target, c.expect.get('needle', ''))
            elif c.kind == 'syntax':
                ok, msg = verify_syntax(c.target)
            elif c.kind == 'endpoint':
                ok, msg = verify_http_endpoint(c.target, c.expect.get('status', 200))
            elif c.kind == 'migration':
                ok, msg = verify_db_table(c.target, columns=c.expect.get('columns'))
            elif c.kind == 'service':
                ok, msg = verify_systemd_service(c.target, c.expect.get('active', True))
            elif c.kind == 'test':
                ok, msg = verify_pytest(c.target, cwd=c.expect.get('cwd'))
            else:
                skipped += 1
                details.append({'claim': c.kind, 'target': c.target, 'result': 'skipped (unknown kind)'})
                continue
        except Exception as e:
            ok = False
            msg = f"verifier exception: {e}"

        if ok:
            passed += 1
        else:
            failed += 1
            mismatches.append({
                'kind': c.kind,
                'target': c.target,
                'source': c.source,
                'detail': msg,
            })
        details.append({
            'kind': c.kind,
            'target': c.target,
            'pass': ok,
            'msg': msg[:200],
        })

    verified = (failed == 0 and not hallucination_flag)
    return VerificationResult(
        verified=verified,
        total_claims=len(unique_claims),
        passed=passed, failed=failed, skipped=skipped,
        hallucination_flag=hallucination_flag,
        mismatches=mismatches, details=details,
    )
