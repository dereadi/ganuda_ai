#!/usr/bin/env python3
"""
Cherokee AI Research Monitor - arxiv Crawler v2
Deploy to: /ganuda/services/research_monitor/arxiv_crawler.py
Schedule: Daily at 6 AM via cron

v2: Adds Council assessment for relevance scoring
"""

import requests
import xml.etree.ElementTree as ET
import time
import json
import re
import psycopg2
from datetime import datetime, timedelta
import os

ARXIV_API = "https://export.arxiv.org/api/query"
GATEWAY_URL = "http://localhost:8080"
API_KEY = "REDACTED_USE_ENV_VAR"

DB_CONFIG = {
    "host": os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'),
    "port": 5432,
    "user": "claude",
    "password": os.environ.get('CHEROKEE_DB_PASS', ''),
    "database": "zammad_production"
}

# Cherokee AI relevant search terms with arxiv category filters
# Format: {"term": str, "categories": list[str]}
# Categories constrain search to relevant arxiv domains (reduces noise 40-60%)
SEARCH_QUERIES = [
    # === Original 12 terms (now with category filters) ===
    {"term": "multi-agent system", "categories": ["cs.MA", "cs.AI"]},
    {"term": "agent orchestration", "categories": ["cs.MA", "cs.AI", "cs.DC"]},
    {"term": "consensus mechanism AI", "categories": ["cs.AI", "cs.DC"]},
    {"term": "memory augmented language model", "categories": ["cs.CL", "cs.AI"]},
    {"term": "mixture of experts", "categories": ["cs.LG", "cs.CL"]},
    {"term": "small language model", "categories": ["cs.CL", "cs.LG"]},
    {"term": "swarm intelligence", "categories": ["cs.MA", "cs.AI", "cs.NE"]},
    {"term": "parallel inference", "categories": ["cs.DC", "cs.LG"]},
    {"term": "AI consciousness", "categories": ["cs.AI", "cs.CY"]},
    {"term": "constitutional AI", "categories": ["cs.AI", "cs.CL"]},
    {"term": "chain of thought", "categories": ["cs.CL", "cs.AI"]},
    {"term": "vLLM optimization", "categories": ["cs.DC", "cs.PF"]},
    # === 12 new terms (cognitive gap expansion Mar 2026) ===
    {"term": "federated learning inference", "categories": ["cs.DC", "cs.LG"]},
    {"term": "energy efficient AI inference", "categories": ["cs.AR", "cs.PF"]},
    {"term": "episodic memory neural network", "categories": ["cs.AI", "cs.NE"]},
    {"term": "AI governance alignment safety", "categories": ["cs.AI", "cs.CY"]},
    {"term": "retrieval augmented generation", "categories": ["cs.CL", "cs.IR"]},
    {"term": "edge distributed inference heterogeneous", "categories": ["cs.DC", "cs.AR"]},
    {"term": "self-organizing autonomous systems", "categories": ["cs.MA", "cs.AI"]},
    {"term": "clinical NLP veteran health", "categories": ["cs.CL"]},
    {"term": "indigenous data sovereignty", "categories": ["cs.CY"]},
    {"term": "tool use function calling LLM", "categories": ["cs.CL", "cs.AI"]},
    {"term": "model quantization efficient LLM", "categories": ["cs.LG", "cs.AR"]},
    {"term": "combinatorial auction matching", "categories": ["cs.GT", "cs.AI"]},
    # === 12 new terms (federation expansion Mar 17 2026) ===
    {"term": "experience replay reinforcement learning agent", "categories": ["cs.AI", "cs.LG"]},
    {"term": "skill library reusable policy", "categories": ["cs.AI", "cs.RO", "cs.LG"]},
    {"term": "tokenization privacy preserving inference", "categories": ["cs.CR", "cs.CL"]},
    {"term": "multi-armed bandit model selection", "categories": ["cs.LG", "cs.AI"]},
    {"term": "graph retrieval augmented generation knowledge", "categories": ["cs.CL", "cs.IR", "cs.AI"]},
    {"term": "thermal memory decay forgetting neural", "categories": ["cs.AI", "cs.NE", "cs.LG"]},
    {"term": "air gapped secure inference deployment", "categories": ["cs.CR", "cs.DC"]},
    {"term": "sovereign AI local inference edge", "categories": ["cs.DC", "cs.CY"]},
    {"term": "council governance multi-agent voting", "categories": ["cs.MA", "cs.AI", "cs.GT"]},
    {"term": "self-improving agent autonomous learning", "categories": ["cs.AI", "cs.LG"]},
    {"term": "speculative decoding parallel generation", "categories": ["cs.CL", "cs.DC"]},
    {"term": "persistent memory context window management", "categories": ["cs.CL", "cs.AI"]},
]


def build_search_query(term: str, categories: list) -> str:
    """Build arxiv API search query with category filters.

    Uses arxiv cat: syntax to constrain results to relevant domains.
    Example output: all:federated learning+AND+(cat:cs.DC+OR+cat:cs.LG)
    """
    base = f"all:{term}"
    if not categories:
        return base
    cat_filter = "+OR+".join(f"cat:{c}" for c in categories)
    return f"{base}+AND+({cat_filter})"


def search_arxiv(query: str, max_results: int = 5, categories: list = None) -> list:
    """Search arxiv for papers matching query with optional category filters"""
    search_query = build_search_query(query, categories or [])
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    response = requests.get(ARXIV_API, params=params, timeout=30)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    papers = []
    for entry in root.findall("atom:entry", ns):
        arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]
        paper = {
            "external_id": arxiv_id,
            "title": entry.find("atom:title", ns).text.strip().replace("\n", " "),
            "abstract": entry.find("atom:summary", ns).text.strip()[:2000],
            "authors": ", ".join([a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)][:5]),
            "url": entry.find("atom:id", ns).text,
            "published_date": entry.find("atom:published", ns).text[:10],
            "source": "arxiv",
            "matched_query": query
        }
        papers.append(paper)

    return papers


def assess_paper(paper: dict) -> dict:
    """Have Raven (Strategic) assess paper relevance to Cherokee AI"""
    question = f"""Rate this paper's relevance to Cherokee AI (0-100):

TITLE: {paper['title']}

ABSTRACT: {paper['abstract'][:500]}

Cherokee AI: multi-agent consensus system, vLLM inference, thermal memory.

Reply ONLY with a number 0-100 and one sentence. Example: "85 - Directly applicable to our multi-agent architecture."
Do not explain your reasoning process. Just give score and one sentence."""

    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{GATEWAY_URL}/v1/specialist/raven/query",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={"question": question, "max_tokens": 200},
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            answer = result.get("response", "")

            # Clean up thinking tags first
            if "</think>" in answer:
                answer = answer.split("</think>")[-1].strip()

            # Empty response — retry
            if not answer.strip():
                last_error = "Empty response from Raven"
                print(f"    Assessment attempt {attempt + 1}/{max_retries}: empty response, retrying...")
                time.sleep(3)
                continue

            # Parse score from response - try multiple formats
            score = None
            reason = answer

            # Try to find a number at the start or after common patterns
            patterns = [
                r'^(\d{1,3})',  # starts with number
                r'SCORE:\s*(\d{1,3})',  # SCORE: 85
                r'(\d{1,3})\s*[-/]',  # 85 - reason or 85/100
                r'(\d{1,3})\s*$',  # ends with number
            ]

            for pattern in patterns:
                match = re.search(pattern, answer)
                if match:
                    try:
                        score = int(match.group(1))
                        score = min(100, max(0, score))
                        break
                    except:
                        pass

            # If no score parsed, retry
            if score is None:
                last_error = f"Could not parse score from: {answer[:100]}"
                print(f"    Assessment attempt {attempt + 1}/{max_retries}: no score parsed, retrying...")
                time.sleep(3)
                continue

            # Extract reason (everything after the number)
            reason_match = re.search(r'\d{1,3}\s*[-:./]?\s*(.+)', answer)
            if reason_match:
                reason = reason_match.group(1).strip()

            return {
                "score": score,
                "reason": reason[:500],
                "raw_response": answer
            }
        except requests.exceptions.Timeout:
            last_error = f"Timeout on attempt {attempt + 1}"
            print(f"    Assessment attempt {attempt + 1}/{max_retries}: timeout, retrying...")
            time.sleep(5)
        except Exception as e:
            last_error = str(e)
            print(f"    Assessment attempt {attempt + 1}/{max_retries}: {e}")
            time.sleep(3)

    # All retries exhausted — return 0 with error detail
    return {"score": 0, "reason": f"Assessment failed after {max_retries} retries: {last_error}", "raw_response": ""}


def save_paper(paper: dict) -> bool:
    """Save paper to database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO ai_research_papers
            (source, external_id, title, authors, abstract, url, published_date, search_terms_matched)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, external_id) DO UPDATE
            SET search_terms_matched = ai_research_papers.search_terms_matched || %s
            RETURNING paper_id
        """, (
            paper["source"], paper["external_id"], paper["title"], paper["authors"],
            paper["abstract"], paper["url"], paper["published_date"],
            json.dumps([paper["matched_query"]]), json.dumps([paper["matched_query"]])
        ))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"    Save error: {e}")
        return False


def update_assessment(paper: dict, assessment: dict):
    """Update paper with assessment"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            UPDATE ai_research_papers
            SET relevance_score = %s,
                council_assessment = %s,
                assessed_at = NOW()
            WHERE source = %s AND external_id = %s
        """, (
            assessment["score"],
            assessment["reason"],
            paper["source"],
            paper["external_id"]
        ))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"    Assessment update error: {e}")


def notify_tpm(paper: dict, assessment: dict):
    """Notify TPM of high-relevance paper"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO tpm_notifications
            (priority, category, title, message, source_system, related_hash)
            VALUES (%s, 'research', %s, %s, 'arxiv_crawler', %s)
        """, (
            'P2' if assessment["score"] >= 80 else 'P3',
            f"High-relevance paper: {paper['title'][:60]}...",
            f"""Relevance Score: {assessment['score']}/100

Title: {paper['title']}

Authors: {paper['authors']}

Assessment: {assessment['reason']}

URL: {paper['url']}""",
            paper["external_id"]
        ))

        conn.commit()
        cur.close()
        conn.close()
        print(f"    TPM notified (score: {assessment['score']})")
    except Exception as e:
        print(f"    TPM notification error: {e}")


def compute_noise_ratios():
    """Compute noise ratio per search term over the last 30 days.

    noise_ratio = (papers with score < 20) / (total papers for term)
    Returns dict of {term: {"total": N, "low_score": N, "noise_ratio": float}}
    """
    noise_stats = {}
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        for entry in SEARCH_QUERIES:
            term = entry["term"]
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN relevance_score IS NOT NULL AND relevance_score < 20 THEN 1 ELSE 0 END) as low_score
                FROM ai_research_papers
                WHERE search_terms_matched::text LIKE %s
                AND crawled_at >= %s
            """, (f'%{term}%', cutoff))

            row = cur.fetchone()
            total = row[0] or 0
            low_score = row[1] or 0
            ratio = (low_score / total) if total > 0 else 0.0

            noise_stats[term] = {
                "total": total,
                "low_score": low_score,
                "noise_ratio": round(ratio, 3)
            }

            if ratio > 0.8 and total >= 5:
                print(f"  [NOISE WARNING] '{term}': {ratio:.0%} noise ratio ({low_score}/{total} papers scored <20)")

        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()
    except Exception as e:
        print(f"  Noise ratio computation error: {e}")

    return noise_stats


def check_auto_disable():
    """Auto-disable search terms that produce zero relevant papers (score >= 70) after 30 days.

    Logs disabled terms but does NOT modify the SEARCH_QUERIES list at runtime.
    Instead, logs recommendations for manual review.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        for entry in SEARCH_QUERIES:
            term = entry["term"]
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN relevance_score >= 70 THEN 1 ELSE 0 END) as relevant
                FROM ai_research_papers
                WHERE search_terms_matched::text LIKE %s
                AND crawled_at >= %s
            """, (f'%{term}%', cutoff))

            row = cur.fetchone()
            total = row[0] or 0
            relevant = row[1] or 0

            if total >= 10 and relevant == 0:
                print(f"  [AUTO-DISABLE CANDIDATE] '{term}': {total} papers, 0 relevant (score>=70) in 30 days")

        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()
    except Exception as e:
        print(f"  Auto-disable check error: {e}")


def alert_unassessed_backlog():
    """Alert if unassessed papers exceed 50 (dawn mist integration)."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT COUNT(*) FROM ai_research_papers
            WHERE assessed_at IS NULL OR relevance_score = 0
        """)
        count = cur.fetchone()[0]

        if count > 50:
            print(f"  [DAWN MIST ALERT] Raven assessment backlog: {count} unassessed papers (threshold: 50)")
            # Send TPM notification
            cur.execute("""
                INSERT INTO tpm_notifications
                (priority, category, title, message, source_system, related_hash)
                VALUES ('P2', 'research', %s, %s, 'arxiv_crawler', %s)
            """, (
                f"Raven assessment backlog: {count} papers",
                f"Assessment backlog has grown to {count} papers (threshold: 50). "
                f"Run with --assess-pending to process backlog, or investigate Raven gateway timeouts.",
                f"backlog-alert-{datetime.now().strftime('%Y%m%d')}"
            ))
            conn.commit()

        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"  Backlog check error: {e}")
        return -1


def crawl_and_assess():
    """Crawl arxiv and assess papers"""
    all_papers = []
    print(f"[{datetime.now()}] Starting arxiv crawl + assessment (24 search terms)...")

    # Crawl
    for entry in SEARCH_QUERIES:
        term = entry["term"]
        categories = entry["categories"]
        print(f"  Searching: {term} (categories: {', '.join(categories)})")
        try:
            papers = search_arxiv(term, max_results=3, categories=categories)
            all_papers.extend(papers)
            print(f"    Found {len(papers)} papers")
        except Exception as e:
            print(f"    Error: {e}")
        time.sleep(3)  # Rate limiting

    # Deduplicate
    seen = set()
    unique = []
    for p in all_papers:
        if p["external_id"] not in seen:
            seen.add(p["external_id"])
            unique.append(p)

    print(f"\n  Total unique papers: {len(unique)}")

    # Save and assess each paper
    assessed = 0
    high_relevance = 0
    failed_assessments = 0

    for paper in unique:
        print(f"\n  Processing: {paper['title'][:60]}...")

        # Save to DB
        save_paper(paper)

        # Assess via Raven
        print(f"    Assessing...")
        assessment = assess_paper(paper)
        print(f"    Score: {assessment['score']}/100")

        # Track failed assessments
        if assessment["score"] == 0:
            failed_assessments += 1

        # Update assessment
        update_assessment(paper, assessment)
        assessed += 1

        # Notify TPM if high relevance
        if assessment["score"] >= 70:
            high_relevance += 1
            notify_tpm(paper, assessment)

        time.sleep(2)  # Rate limit Council queries

    # Noise ratio tracking
    print(f"\n  Computing noise ratios (30-day window)...")
    noise_stats = compute_noise_ratios()

    # Auto-disable check
    print(f"\n  Checking for low-value terms...")
    check_auto_disable()

    # Backlog alert
    backlog_count = alert_unassessed_backlog()

    # Summary
    print(f"\n[{datetime.now()}] Crawl complete:")
    print(f"  Search terms: {len(SEARCH_QUERIES)}")
    print(f"  Papers found: {len(unique)}")
    print(f"  Papers assessed: {assessed}")
    print(f"  Failed assessments: {failed_assessments}")
    print(f"  High relevance (70+): {high_relevance}")
    if backlog_count >= 0:
        print(f"  Unassessed backlog: {backlog_count}")

    # Log noise stats for high-noise terms
    high_noise_terms = [t for t, s in noise_stats.items() if s["noise_ratio"] > 0.8 and s["total"] >= 5]
    if high_noise_terms:
        print(f"  High-noise terms (>80%): {', '.join(high_noise_terms)}")

    # Log to thermal memory
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, 75.0, %s)
            ON CONFLICT (memory_hash) DO UPDATE SET
                temperature_score = 75.0,
                original_content = EXCLUDED.original_content
        """, (
            f"research-{datetime.now().strftime('%Y%m%d')}",
            f"Research crawl: {len(unique)} papers, {assessed} assessed, {high_relevance} high-relevance, {failed_assessments} failed",
            json.dumps({
                "type": "research_crawl",
                "search_terms": len(SEARCH_QUERIES),
                "papers": len(unique),
                "assessed": assessed,
                "high_relevance": high_relevance,
                "failed_assessments": failed_assessments,
                "noise_stats": noise_stats
            })
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  Thermal log error: {e}")


def assess_pending():
    """Assess papers that haven't been assessed yet or previously failed (score=0).

    Processes both unassessed papers and papers where assessment failed
    (score=0 with error reasons), which addresses the 227-paper backlog.
    """
    print(f"[{datetime.now()}] Assessing pending papers (includes score=0 retries)...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Fetch unassessed AND previously-failed (score=0) papers
        cur.execute("""
            SELECT external_id, title, abstract, authors, url, source
            FROM ai_research_papers
            WHERE assessed_at IS NULL
               OR (relevance_score = 0 AND council_assessment LIKE 'Assessment%%')
            ORDER BY crawled_at DESC
            LIMIT 30
        """)

        papers = cur.fetchall()
        conn.commit()  # explicit commit before close
        conn.close()

        print(f"  Found {len(papers)} papers to assess/retry")

        assessed = 0
        still_failed = 0

        for row in papers:
            paper = {
                "external_id": row[0],
                "title": row[1],
                "abstract": row[2],
                "authors": row[3],
                "url": row[4],
                "source": row[5]
            }

            print(f"\n  Assessing: {paper['title'][:50]}...")
            assessment = assess_paper(paper)
            print(f"    Score: {assessment['score']}/100")

            update_assessment(paper, assessment)
            assessed += 1

            if assessment["score"] == 0:
                still_failed += 1

            if assessment["score"] >= 70:
                notify_tpm(paper, assessment)

            time.sleep(2)

        print(f"\n  Assessed: {assessed}, Still failed: {still_failed}")

    except Exception as e:
        print(f"  Error: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--assess-pending":
        assess_pending()
    else:
        crawl_and_assess()
