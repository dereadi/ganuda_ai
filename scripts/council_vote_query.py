#!/usr/bin/env python3
"""Owl Pass Council Vote Query Tool — Search and display council decisions.

Turtle: "We need to be able to find our own decisions."
Council vote PROCEED. Longhouse open floor request.

Usage:
    python3 council_vote_query.py --hash abc123
    python3 council_vote_query.py --keyword "memory" --days 7
    python3 council_vote_query.py --specialist coyote --min-confidence 0.7
    python3 council_vote_query.py --mode cascaded --days 30
    python3 council_vote_query.py --unfinalized
    python3 council_vote_query.py --concerns --days 14
"""
import argparse
import json
import sys
from datetime import datetime


def get_db_connection():
    """Connect to federation database."""
    import psycopg2
    secrets = {}
    with open("/ganuda/config/secrets.env") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                secrets[k.strip()] = v.strip()

    return psycopg2.connect(
        host="192.168.132.222", port=5432, dbname="zammad_production",
        user="claude", password=secrets.get("CHEROKEE_DB_PASS", "")
    )


def format_vote(row, columns, verbose=False):
    """Format a single vote for display."""
    vote = dict(zip(columns, row))
    lines = []
    lines.append(f"  Vote #{vote['vote_id']} | Hash: {vote.get('audit_hash', 'N/A')}")
    lines.append(f"  Date: {vote.get('voted_at') or vote.get('created_at')}")
    lines.append(f"  Mode: {vote.get('vote_mode', 'parallel')} | Confidence: {vote.get('confidence', 'N/A')}")
    lines.append(f"  TPM: {vote.get('tpm_vote', 'pending')} | Finalized: {vote.get('vote_finalized', False)}")

    question = vote.get('question', '')
    if question:
        q_display = question[:200] + "..." if len(question) > 200 else question
        lines.append(f"  Question: {q_display}")

    recommendation = vote.get('recommendation', '')
    if recommendation:
        r_display = recommendation[:200] + "..." if len(recommendation) > 200 else recommendation
        lines.append(f"  Recommendation: {r_display}")

    if vote.get('concern_count', 0) > 0:
        lines.append(f"  Concerns: {vote['concern_count']}")

    if vote.get('blocked_by'):
        lines.append(f"  Blocked by: {vote['blocked_by']} at stage {vote.get('blocked_at_stage')}")

    if verbose:
        if vote.get('consensus'):
            lines.append(f"  Consensus: {str(vote['consensus'])[:300]}")
        if vote.get('tpm_comment'):
            lines.append(f"  TPM Comment: {vote['tpm_comment']}")
        if vote.get('responses'):
            try:
                responses = vote['responses'] if isinstance(vote['responses'], dict) else json.loads(vote['responses'])
                specialists = list(responses.keys())
                lines.append(f"  Specialists: {', '.join(specialists)}")
            except (json.JSONDecodeError, TypeError):
                pass
        if vote.get('response_time_ms'):
            lines.append(f"  Latency: {vote['response_time_ms']}ms")

    return "\n".join(lines)


def query_votes(args):
    """Build and execute query based on args."""
    conn = get_db_connection()
    cur = conn.cursor()

    base_query = """SELECT vote_id, audit_hash, question, recommendation, confidence,
        concern_count, specialist_count, tpm_vote, vote_finalized, vote_mode,
        blocked_by, blocked_at_stage, response_time_ms, voted_at, created_at,
        consensus, tpm_comment, responses, concerns
        FROM council_votes WHERE 1=1"""

    params = []
    conditions = []

    if args.hash:
        conditions.append("audit_hash ILIKE %s")
        params.append(f"%{args.hash}%")

    if args.keyword:
        conditions.append("(question ILIKE %s OR recommendation ILIKE %s OR consensus::text ILIKE %s)")
        params.extend([f"%{args.keyword}%"] * 3)

    if args.specialist:
        conditions.append("responses::text ILIKE %s")
        params.append(f"%{args.specialist}%")

    if args.days:
        conditions.append("COALESCE(voted_at, created_at) > NOW() - INTERVAL '%s days'")
        params.append(args.days)

    if args.min_confidence is not None:
        conditions.append("confidence >= %s")
        params.append(args.min_confidence)

    if args.max_confidence is not None:
        conditions.append("confidence <= %s")
        params.append(args.max_confidence)

    if args.mode:
        conditions.append("vote_mode = %s")
        params.append(args.mode)

    if args.unfinalized:
        conditions.append("(vote_finalized = FALSE OR vote_finalized IS NULL)")

    if args.concerns:
        conditions.append("concern_count > 0")

    if args.blocked:
        conditions.append("blocked_by IS NOT NULL")

    if args.tpm_vote:
        conditions.append("tpm_vote = %s")
        params.append(args.tpm_vote)

    if conditions:
        base_query += " AND " + " AND ".join(conditions)

    base_query += " ORDER BY COALESCE(voted_at, created_at) DESC"

    limit = args.limit or 20
    base_query += f" LIMIT {limit}"

    cur.execute(base_query, params)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    # Display results
    print(f"=== COUNCIL VOTE QUERY ===")
    print(f"Results: {len(rows)} vote(s) (limit {limit})")
    print()

    for row in rows:
        print(format_vote(row, columns, verbose=args.verbose))
        print()

    # Summary stats if multiple results
    if len(rows) > 1:
        confidences = [dict(zip(columns, r)).get('confidence') for r in rows if dict(zip(columns, r)).get('confidence') is not None]
        concern_counts = [dict(zip(columns, r)).get('concern_count', 0) for r in rows]
        modes = {}
        for r in rows:
            v = dict(zip(columns, r))
            m = v.get('vote_mode', 'parallel')
            modes[m] = modes.get(m, 0) + 1

        print("--- Summary ---")
        if confidences:
            print(f"  Avg confidence: {sum(confidences)/len(confidences):.3f}")
            print(f"  Min/Max: {min(confidences):.3f} / {max(confidences):.3f}")
        print(f"  Total concerns: {sum(concern_counts)}")
        print(f"  Modes: {', '.join(f'{k}={v}' for k,v in modes.items())}")

    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Query council votes — Turtle's Owl Pass tool")
    parser.add_argument("--hash", help="Search by audit hash (partial match)")
    parser.add_argument("--keyword", "-k", help="Search question/recommendation/consensus text")
    parser.add_argument("--specialist", "-s", help="Filter by specialist name in responses")
    parser.add_argument("--days", "-d", type=int, help="Limit to last N days")
    parser.add_argument("--min-confidence", type=float, help="Minimum confidence threshold")
    parser.add_argument("--max-confidence", type=float, help="Maximum confidence threshold")
    parser.add_argument("--mode", "-m", choices=["parallel", "cascaded", "halo", "halo_mcts"], help="Filter by vote mode")
    parser.add_argument("--unfinalized", "-u", action="store_true", help="Show only unfinalized votes")
    parser.add_argument("--concerns", "-c", action="store_true", help="Show only votes with concerns")
    parser.add_argument("--blocked", "-b", action="store_true", help="Show only blocked votes")
    parser.add_argument("--tpm-vote", choices=["pending", "approve", "reject", "auto-finalized"], help="Filter by TPM vote")
    parser.add_argument("--limit", "-l", type=int, default=20, help="Max results (default 20)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full details")

    args = parser.parse_args()

    # If no filters, show recent
    has_filter = any([args.hash, args.keyword, args.specialist, args.days,
                      args.min_confidence is not None, args.max_confidence is not None,
                      args.mode, args.unfinalized, args.concerns, args.blocked, args.tpm_vote])
    if not has_filter:
        print("No filters specified. Showing last 20 votes.")
        print("Use --help for filter options.\n")
        args.limit = 20

    query_votes(args)


if __name__ == "__main__":
    main()