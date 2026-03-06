# Jr Instruction: Council Curiosity — Autonomous Research Discovery

**Task ID:** CURIOSITY-DAEMON
**Kanban:** NEW (create: priority 1, SFP 60, story points 8)
**Priority:** 1
**Assigned:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Create a script that lets the Council autonomously identify knowledge gaps and queue research tasks. The script gathers the federation's current state (failures, low-confidence votes, open work, known research backlog), asks the Council what to investigate, executes the research via arxiv and GitHub, summarizes findings through the gateway, and stores results in thermal memory.

The federation's soul matters — research should serve the cluster's mission, not just chase papers.

---

## Step 1: Create the council curiosity script

Create `/ganuda/scripts/council_curiosity.py`

```python
#!/usr/bin/env python3
"""
Council Curiosity — Autonomous Research Discovery

Gathers federation state (failures, low-confidence votes, open work,
research backlog), asks the Council what to investigate, executes
research via arxiv/GitHub, summarizes findings, stores in thermal memory.

Usage:
    python3 council_curiosity.py             # Full run
    python3 council_curiosity.py --dry-run   # Council query only, skip research

For Seven Generations
"""

import argparse
import hashlib
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import quote_plus

import psycopg2
import psycopg2.extras
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GATEWAY_URL = "http://192.168.132.223:8080/v1/chat/completions"
COUNCIL_MODEL = "cherokee-council"
SUMMARIZE_MODEL = "/ganuda/models/qwen2.5-72b-instruct-awq"
ARXIV_API = "https://export.arxiv.org/api/query"
GITHUB_API = "https://api.github.com/search/repositories"

DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
    "password": None,  # filled from env at runtime
}

# Research backlog papers the council already knows about
RESEARCH_BACKLOG = [
    {"arxiv_id": "2512.12818", "title": "Hindsight Memory"},
    {"arxiv_id": "2511.11617", "title": "AnchorTP"},
    {"arxiv_id": "2510.01499", "title": "Beyond Majority Voting"},
]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db_connection():
    """Open a psycopg2 connection using env-based password."""
    DB_CONFIG["password"] = os.environ.get("CHEROKEE_DB_PASS")
    if not DB_CONFIG["password"]:
        print("[ERROR] CHEROKEE_DB_PASS not set in environment", file=sys.stderr)
        sys.exit(1)
    return psycopg2.connect(**DB_CONFIG)


def gather_failed_tasks(conn):
    """Last 10 failed jr_work_queue tasks."""
    sql = """
        SELECT task_id, title, error_message, updated_at
        FROM jr_work_queue
        WHERE status = 'failed'
        ORDER BY updated_at DESC
        LIMIT 10
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()


def gather_low_confidence_votes(conn):
    """Last 5 council votes with confidence < 0.85 from thermal memory."""
    sql = """
        SELECT id, original_content, created_at
        FROM thermal_memory_archive
        WHERE original_content ILIKE '%%confidence%%'
          AND original_content ILIKE '%%council vote%%'
        ORDER BY id DESC
        LIMIT 5
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()


def gather_open_kanban(conn):
    """Top 10 open kanban items by sacred_fire_priority."""
    sql = """
        SELECT id, title, sacred_fire_priority, story_points, status
        FROM duyuktv_tickets
        WHERE status = 'open'
        ORDER BY sacred_fire_priority DESC
        LIMIT 10
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()


def gather_research_backlog(conn):
    """Look up the 3 known research backlog papers in thermal memory."""
    results = []
    for paper in RESEARCH_BACKLOG:
        sql = """
            SELECT id, original_content, tags
            FROM thermal_memory_archive
            WHERE original_content ILIKE %s
            ORDER BY id DESC
            LIMIT 1
        """
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (f"%{paper['arxiv_id']}%",))
            row = cur.fetchone()
            results.append({
                "arxiv_id": paper["arxiv_id"],
                "title": paper["title"],
                "in_memory": row is not None,
                "snippet": (row["original_content"][:300] if row else "Not found in thermal memory"),
            })
    return results


# ---------------------------------------------------------------------------
# Council query
# ---------------------------------------------------------------------------

def ask_council(context_text):
    """Ask the Council what the federation should research next."""
    prompt = f"""You are the Cherokee AI Federation Council. Below is the current state of our federation — recent failures, low-confidence votes, open work items, and known research papers in our backlog.

Based on this context, identify the 3 most valuable things we should research RIGHT NOW. These should directly help our cluster solve real problems, not just be interesting papers.

For each item, provide:
1. A specific search query for arxiv or GitHub (prefix with "arxiv:" or "github:" to indicate which)
2. Why this matters to our federation (1-2 sentences)
3. Which specialist cares most (one of: Chief, Raven, Deer, Turtle, Coyote, Bear, Eagle)

Respond ONLY as a JSON array of objects with keys: "query", "source", "rationale", "specialist"
where "source" is either "arxiv" or "github".

--- FEDERATION STATE ---
{context_text}
--- END STATE ---"""

    payload = {
        "model": COUNCIL_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.3,
    }

    print("[COUNCIL] Asking the Council what to research...")
    resp = requests.post(GATEWAY_URL, json=payload, timeout=120)
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]

    # Extract JSON from response (handle markdown fences)
    if "```" in content:
        start = content.index("```") + 3
        if content[start:].startswith("json"):
            start += 4
        end = content.index("```", start)
        content = content[start:end].strip()

    try:
        items = json.loads(content)
    except json.JSONDecodeError:
        print(f"[ERROR] Council response was not valid JSON:\n{content}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(items, list) or len(items) == 0:
        print(f"[ERROR] Council returned empty or non-list:\n{content}", file=sys.stderr)
        sys.exit(1)

    return items[:3]  # cap at 3


# ---------------------------------------------------------------------------
# Research execution
# ---------------------------------------------------------------------------

def search_arxiv(query):
    """Search arxiv and return up to 3 results."""
    url = f"{ARXIV_API}?search_query=all:{quote_plus(query)}&max_results=3"
    print(f"  [ARXIV] Searching: {query}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(resp.text)
    results = []
    for entry in root.findall("atom:entry", ns):
        title_el = entry.find("atom:title", ns)
        summary_el = entry.find("atom:summary", ns)
        link_el = entry.find("atom:id", ns)
        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        results.append({
            "title": title_el.text.strip() if title_el is not None else "Unknown",
            "summary": summary_el.text.strip() if summary_el is not None else "",
            "authors": authors[:5],
            "link": link_el.text.strip() if link_el is not None else "",
        })
    return results


def search_github(query):
    """Search GitHub repos and return up to 3 results."""
    url = f"{GITHUB_API}?q={quote_plus(query)}&sort=stars&per_page=3"
    print(f"  [GITHUB] Searching: {query}")
    headers = {"Accept": "application/vnd.github.v3+json"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    results = []
    for repo in data.get("items", [])[:3]:
        results.append({
            "name": repo.get("full_name", ""),
            "description": repo.get("description", "") or "",
            "stars": repo.get("stargazers_count", 0),
            "url": repo.get("html_url", ""),
        })
    return results


def summarize_result(result_text):
    """Ask the gateway to summarize a research result for the council."""
    prompt = f"""Summarize this for the Cherokee AI Federation council. How could this help our cluster? Be specific and brief (2-3 sentences max).

{result_text}"""

    payload = {
        "model": SUMMARIZE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.2,
    }

    try:
        resp = requests.post(GATEWAY_URL, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"(Summarization failed: {e})"


def execute_research(council_items):
    """Execute research for each council-recommended item."""
    all_findings = []

    for i, item in enumerate(council_items):
        source = item.get("source", "arxiv")
        query = item.get("query", "")
        rationale = item.get("rationale", "")
        specialist = item.get("specialist", "Raven")

        print(f"\n[RESEARCH {i+1}/3] source={source} specialist={specialist}")
        print(f"  Query: {query}")
        print(f"  Rationale: {rationale}")

        if source == "github":
            raw_results = search_github(query)
            for r in raw_results:
                text_for_summary = f"GitHub repo: {r['name']} ({r['stars']} stars)\n{r['description']}\n{r['url']}"
                summary = summarize_result(text_for_summary)
                all_findings.append({
                    "source": "github",
                    "query": query,
                    "specialist": specialist,
                    "rationale": rationale,
                    "title": r["name"],
                    "url": r["url"],
                    "raw": r,
                    "summary": summary,
                })
        else:
            # Default to arxiv
            raw_results = search_arxiv(query)
            # Be kind to arxiv rate limits
            time.sleep(3)
            for r in raw_results:
                text_for_summary = f"Paper: {r['title']}\nAuthors: {', '.join(r['authors'])}\n\n{r['summary'][:600]}"
                summary = summarize_result(text_for_summary)
                all_findings.append({
                    "source": "arxiv",
                    "query": query,
                    "specialist": specialist,
                    "rationale": rationale,
                    "title": r["title"],
                    "url": r["link"],
                    "raw": r,
                    "summary": summary,
                })

    return all_findings


# ---------------------------------------------------------------------------
# Store results
# ---------------------------------------------------------------------------

def store_findings(conn, findings):
    """Store each finding in thermal_memory_archive."""
    stored = 0
    sql = """
        INSERT INTO thermal_memory_archive
            (original_content, memory_type, tags, temperature_score,
             memory_hash, metadata, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (memory_hash) DO NOTHING
    """

    for f in findings:
        content = (
            f"COUNCIL CURIOSITY FINDING\n"
            f"Source: {f['source']} | Query: {f['query']}\n"
            f"Title: {f['title']}\n"
            f"URL: {f['url']}\n"
            f"Specialist: {f['specialist']}\n"
            f"Rationale: {f['rationale']}\n\n"
            f"Summary: {f['summary']}"
        )
        mem_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        tags = [f['specialist'].lower(), "research", "council_curiosity", f['source']]
        metadata = json.dumps({
            "source": "council_curiosity",
            "query": f["query"],
            "council_rationale": f["rationale"],
            "result_title": f["title"],
            "result_url": f["url"],
            "searched_at": datetime.now(timezone.utc).isoformat(),
        })

        with conn.cursor() as cur:
            cur.execute(sql, (
                content,
                "research",
                tags,
                50,
                mem_hash,
                metadata,
                datetime.now(timezone.utc),
            ))
        stored += 1

    conn.commit()
    print(f"\n[STORE] {stored} findings written to thermal_memory_archive")
    return stored


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(council_items, findings):
    """Print a human-readable report to stdout."""
    print("\n" + "=" * 72)
    print("  COUNCIL CURIOSITY REPORT")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 72)

    print(f"\nCouncil recommended {len(council_items)} research directions:\n")
    for i, item in enumerate(council_items):
        print(f"  {i+1}. [{item.get('source','?').upper()}] {item.get('query','')}")
        print(f"     Specialist: {item.get('specialist','?')}")
        print(f"     Why: {item.get('rationale','')}")
        print()

    if findings:
        print(f"Research yielded {len(findings)} findings:\n")
        for i, f in enumerate(findings):
            print(f"  [{i+1}] {f['title']}")
            print(f"      {f['url']}")
            print(f"      {f['summary'][:200]}")
            print()
    else:
        print("(Dry run — no research executed)\n")

    print("=" * 72)
    print("  For Seven Generations")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Council Curiosity — autonomous research discovery"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ask the council but skip actual research and storage",
    )
    args = parser.parse_args()

    print("[INIT] Council Curiosity starting...")

    # 1. Gather context
    conn = get_db_connection()
    try:
        failed_tasks = gather_failed_tasks(conn)
        low_conf_votes = gather_low_confidence_votes(conn)
        open_kanban = gather_open_kanban(conn)
        backlog = gather_research_backlog(conn)
    finally:
        conn.close()

    # Build context string for the council
    context_parts = []

    context_parts.append("## Recent Failed Tasks")
    if failed_tasks:
        for t in failed_tasks:
            context_parts.append(
                f"- [{t['task_id']}] {t.get('title', 'untitled')}: "
                f"{(t.get('error_message') or 'no error message')[:200]}"
            )
    else:
        context_parts.append("- None recently")

    context_parts.append("\n## Low-Confidence Council Votes (< 0.85)")
    if low_conf_votes:
        for v in low_conf_votes:
            context_parts.append(f"- Memory #{v['id']}: {v['original_content'][:300]}")
    else:
        context_parts.append("- None found")

    context_parts.append("\n## Open Kanban Items (top 10 by priority)")
    if open_kanban:
        for k in open_kanban:
            context_parts.append(
                f"- #{k['id']} {k.get('title', 'untitled')} "
                f"(SFP={k.get('sacred_fire_priority', '?')}, "
                f"SP={k.get('story_points', '?')})"
            )
    else:
        context_parts.append("- None open")

    context_parts.append("\n## Research Backlog Papers")
    for b in backlog:
        status = "IN MEMORY" if b["in_memory"] else "NOT YET STUDIED"
        context_parts.append(f"- {b['title']} (arxiv:{b['arxiv_id']}) — {status}")
        if b["in_memory"]:
            context_parts.append(f"  Snippet: {b['snippet'][:200]}")

    context_text = "\n".join(context_parts)
    print(f"[CONTEXT] Gathered {len(failed_tasks)} failures, "
          f"{len(low_conf_votes)} low-conf votes, "
          f"{len(open_kanban)} open kanban items, "
          f"{len(backlog)} backlog papers")

    # 2. Ask the council
    council_items = ask_council(context_text)
    print(f"[COUNCIL] Received {len(council_items)} research directions")

    # 3. Execute research (unless dry-run)
    findings = []
    if args.dry_run:
        print("[DRY-RUN] Skipping research execution and storage")
    else:
        findings = execute_research(council_items)

        # 4. Store results
        conn = get_db_connection()
        try:
            store_findings(conn, findings)
        finally:
            conn.close()

    # 5. Report
    print_report(council_items, findings)


if __name__ == "__main__":
    main()
```
