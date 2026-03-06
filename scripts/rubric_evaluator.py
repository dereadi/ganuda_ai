#!/usr/bin/env python3
"""Self-Evolving Rubrics: Process Reward Model for Council Votes.
Evaluates council vote quality across confidence, concerns, and consensus.
Run monthly or on-demand: python3 rubric_evaluator.py"""

import json
import sys
from datetime import datetime
from collections import defaultdict

import psycopg2

DB_CONFIG = {
    "host": "192.168.132.222",
    "user": "claude",
    "dbname": "zammad_production"
}

def get_recent_votes(cur, limit=50):
    cur.execute("""
        SELECT vote_id, audit_hash, question, recommendation, confidence,
               concern_count, responses, concerns, consensus, tpm_vote,
               metacognition, voted_at
        FROM council_votes
        WHERE confidence IS NOT NULL
        ORDER BY voted_at DESC
        LIMIT %s
    """, (limit,))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def score_confidence_calibration(votes):
    """Are high-confidence votes actually better outcomes?
    Compare confidence vs TPM approval rate."""
    high_conf = [v for v in votes if v["confidence"] and v["confidence"] >= 0.85]
    low_conf = [v for v in votes if v["confidence"] and v["confidence"] < 0.7]
    high_approved = sum(1 for v in high_conf if v["tpm_vote"] == "approve")
    low_approved = sum(1 for v in low_conf if v["tpm_vote"] == "approve")
    high_rate = high_approved / len(high_conf) if high_conf else 0
    low_rate = low_approved / len(low_conf) if low_conf else 0
    calibration = high_rate - low_rate
    return {
        "calibration_delta": round(calibration, 3),
        "high_conf_approval_rate": round(high_rate, 3),
        "low_conf_approval_rate": round(low_rate, 3),
        "high_conf_count": len(high_conf),
        "low_conf_count": len(low_conf),
        "well_calibrated": calibration > 0.1
    }

def score_concern_quality(votes):
    """Do concerns correlate with actual review needs?"""
    with_concerns = [v for v in votes if v["concern_count"] and v["concern_count"] > 0]
    no_concerns = [v for v in votes if not v["concern_count"] or v["concern_count"] == 0]
    concern_review = sum(1 for v in with_concerns if v["tpm_vote"] in ("reject", "needs_review"))
    no_concern_review = sum(1 for v in no_concerns if v["tpm_vote"] in ("reject", "needs_review"))
    concern_precision = concern_review / len(with_concerns) if with_concerns else 0
    false_positive = 1 - concern_precision
    return {
        "concern_precision": round(concern_precision, 3),
        "false_positive_rate": round(false_positive, 3),
        "total_with_concerns": len(with_concerns),
        "total_without_concerns": len(no_concerns),
        "concerns_are_useful": concern_precision > 0.3
    }

def score_consensus_accuracy(votes):
    """Is consensus text reflective of actual agreement?"""
    proceed_votes = [v for v in votes if v["recommendation"] and "PROCEED" in v["recommendation"]]
    review_votes = [v for v in votes if v["recommendation"] and "REVIEW" in v["recommendation"]]
    proceed_approved = sum(1 for v in proceed_votes if v["tpm_vote"] == "approve")
    review_rejected = sum(1 for v in review_votes if v["tpm_vote"] in ("reject", "needs_review"))
    proceed_acc = proceed_approved / len(proceed_votes) if proceed_votes else 0
    review_acc = review_rejected / len(review_votes) if review_votes else 0
    return {
        "proceed_approval_rate": round(proceed_acc, 3),
        "review_rejection_rate": round(review_acc, 3),
        "proceed_count": len(proceed_votes),
        "review_count": len(review_votes),
        "consensus_reliable": proceed_acc > 0.7
    }

def generate_report(votes):
    report = {
        "generated_at": datetime.now().isoformat(),
        "votes_analyzed": len(votes),
        "date_range": {
            "oldest": str(votes[-1]["voted_at"]) if votes else None,
            "newest": str(votes[0]["voted_at"]) if votes else None
        },
        "confidence_calibration": score_confidence_calibration(votes),
        "concern_quality": score_concern_quality(votes),
        "consensus_accuracy": score_consensus_accuracy(votes),
    }
    overall = sum([
        report["confidence_calibration"]["well_calibrated"],
        report["concern_quality"]["concerns_are_useful"],
        report["consensus_accuracy"]["consensus_reliable"]
    ])
    report["overall_health"] = "HEALTHY" if overall >= 2 else "NEEDS_ATTENTION"
    report["overall_score"] = overall
    return report

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    votes = get_recent_votes(cur, limit=50)
    if not votes:
        print("No votes found.")
        return
    report = generate_report(votes)
    output_path = "/ganuda/reports/rubric-scores.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report written to {output_path}")
    print(f"Overall: {report['overall_health']} ({report['overall_score']}/3)")
    print(f"Confidence calibration: {'PASS' if report['confidence_calibration']['well_calibrated'] else 'FAIL'}")
    print(f"Concern quality: {'PASS' if report['concern_quality']['concerns_are_useful'] else 'FAIL'}")
    print(f"Consensus accuracy: {'PASS' if report['consensus_accuracy']['consensus_reliable'] else 'FAIL'}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()