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
import psycopg2
from datetime import datetime
import os

ARXIV_API = "https://export.arxiv.org/api/query"
GATEWAY_URL = "http://localhost:8080"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": os.environ.get('CHEROKEE_DB_PASS', ''),
    "database": "zammad_production"
}

# Cherokee AI relevant search terms
SEARCH_QUERIES = [
    "multi-agent system",
    "agent orchestration",
    "consensus mechanism AI",
    "memory augmented language model",
    "mixture of experts",
    "small language model",
    "swarm intelligence",
    "parallel inference",
    "AI consciousness",
    "constitutional AI",
    "chain of thought",
    "vLLM optimization",
]


def search_arxiv(query: str, max_results: int = 5) -> list:
    """Search arxiv for papers matching query"""
    params = {
        "search_query": f"all:{query}",
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

        # Parse score from response - try multiple formats
        score = 50  # default
        reason = answer

        import re

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

        # Extract reason (everything after the number)
        reason_match = re.search(r'\d{1,3}\s*[-:./]?\s*(.+)', answer)
        if reason_match:
            reason = reason_match.group(1).strip()

        return {
            "score": score,
            "reason": reason[:500],
            "raw_response": answer
        }
    except Exception as e:
        return {"score": 0, "reason": f"Assessment error: {e}", "raw_response": ""}


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


def crawl_and_assess():
    """Crawl arxiv and assess papers"""
    all_papers = []
    print(f"[{datetime.now()}] Starting arxiv crawl + assessment...")

    # Crawl
    for query in SEARCH_QUERIES:
        print(f"  Searching: {query}")
        try:
            papers = search_arxiv(query, max_results=3)
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

    for paper in unique:
        print(f"\n  Processing: {paper['title'][:60]}...")

        # Save to DB
        save_paper(paper)

        # Assess via Raven
        print(f"    Assessing...")
        assessment = assess_paper(paper)
        print(f"    Score: {assessment['score']}/100")

        # Update assessment
        update_assessment(paper, assessment)
        assessed += 1

        # Notify TPM if high relevance
        if assessment["score"] >= 70:
            high_relevance += 1
            notify_tpm(paper, assessment)

        time.sleep(2)  # Rate limit Council queries

    # Summary
    print(f"\n[{datetime.now()}] Crawl complete:")
    print(f"  Papers found: {len(unique)}")
    print(f"  Papers assessed: {assessed}")
    print(f"  High relevance (70+): {high_relevance}")

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
            f"Research crawl: {len(unique)} papers, {assessed} assessed, {high_relevance} high-relevance",
            json.dumps({"type": "research_crawl", "papers": len(unique), "assessed": assessed, "high_relevance": high_relevance})
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  Thermal log error: {e}")


def assess_pending():
    """Assess papers that haven't been assessed yet"""
    print(f"[{datetime.now()}] Assessing pending papers...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT external_id, title, abstract, authors, url, source
            FROM ai_research_papers
            WHERE assessed_at IS NULL
            ORDER BY crawled_at DESC
            LIMIT 20
        """)

        papers = cur.fetchall()
        conn.close()

        print(f"  Found {len(papers)} unassessed papers")

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

            if assessment["score"] >= 70:
                notify_tpm(paper, assessment)

            time.sleep(2)

    except Exception as e:
        print(f"  Error: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--assess-pending":
        assess_pending()
    else:
        crawl_and_assess()
