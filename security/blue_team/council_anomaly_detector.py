"""
Council Voting Anomaly Detector - AI Blue Team Phase 5

Detects anomalous patterns in Specialist Council voting that could indicate
compromise, manipulation, or system malfunction.

Created: 2026-02-02
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("/ganuda/logs/security")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("blue_team.council_anomaly")

_fh = logging.FileHandler(LOG_DIR / "council_anomalies.log")
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(_fh)

# Keywords that should always trigger at least one concern
SECURITY_SENSITIVE_KEYWORDS = [
    "security", "pii", "credential", "password", "secret", "token",
    "api_key", "private_key", "ssh_key", "database_password",
    "encryption", "decrypt", "vulnerability", "exploit", "attack",
    "breach", "bypass", "escalat", "privilege", "admin", "root",
    "delete", "drop_table", "truncate", "rm -rf",
]

# Expected specialist count in the council
EXPECTED_SPECIALIST_COUNT = 7

# Minimum expected response time in milliseconds
MIN_PLAUSIBLE_RESPONSE_MS = 100

# Maximum expected confidence before suspicious
MAX_NORMAL_CONFIDENCE = 0.95


def _get_specialist_baseline(specialist_name: str) -> dict:
    """
    Fetch historical baseline data for a specialist from the database.
    Returns dict with avg_concerns, avg_response_time_ms, total_votes.

    Falls back to defaults if database is unavailable.
    """
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname="cherokee",
            user="claude",
            host="localhost",
            port=5432,
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT
                AVG(concerns_count) as avg_concerns,
                AVG(response_time_ms) as avg_response_ms,
                COUNT(*) as total_votes
            FROM specialist_health
            WHERE specialist_name = %s
            AND recorded_at > NOW() - INTERVAL '30 days'
        """, (specialist_name,))
        row = cur.fetchone()
        conn.close()

        if row and row[2] > 0:
            return {
                "avg_concerns": float(row[0] or 0),
                "avg_response_time_ms": float(row[1] or 500),
                "total_votes": int(row[2]),
            }
    except Exception as e:
        logger.debug("Could not fetch specialist baseline: %s", e)

    # Default baseline
    return {
        "avg_concerns": 1.5,
        "avg_response_time_ms": 500,
        "total_votes": 0,
    }


def check_voting_anomaly(vote_result: dict) -> tuple[bool, str]:
    """
    Check a Council vote result for anomalous patterns.

    Args:
        vote_result: Dict containing vote data. Expected keys:
            - votes (list[dict]): Individual specialist votes, each with:
                - specialist (str): Name of the specialist
                - decision (str): "approve" or "reject"
                - confidence (float): 0.0 to 1.0
                - concerns (list[str]): List of concern strings
                - response_time_ms (float): Time taken to respond
            - request_text (str): The original request being voted on
            - total_approve (int): Count of approve votes
            - total_reject (int): Count of reject votes
            - final_decision (str): "approved" or "rejected"

    Returns:
        Tuple of (is_anomalous, description)
        - is_anomalous: True if anomaly detected
        - description: Human-readable description of the anomaly
    """
    anomalies = []
    votes = vote_result.get("votes", [])
    request_text = vote_result.get("request_text", "").lower()
    total_approve = vote_result.get("total_approve", 0)
    total_reject = vote_result.get("total_reject", 0)
    total_votes = total_approve + total_reject

    if not votes:
        anomalies.append("no-votes-recorded")
        return (True, "; ".join(anomalies))

    # Check 1: Unanimous agreement (all specialists agree)
    decisions = set(v.get("decision", "") for v in votes)
    if len(decisions) == 1 and total_votes >= EXPECTED_SPECIALIST_COUNT:
        anomalies.append(
            f"unanimous-vote: all {total_votes} specialists voted '{decisions.pop()}' "
            f"(unanimous agreement is statistically unusual)"
        )

    # Check 2: Suspiciously high confidence
    high_confidence_count = 0
    for v in votes:
        conf = v.get("confidence", 0)
        if conf > MAX_NORMAL_CONFIDENCE:
            high_confidence_count += 1

    if high_confidence_count > (total_votes // 2):
        anomalies.append(
            f"high-confidence-majority: {high_confidence_count}/{total_votes} specialists "
            f"reported confidence > {MAX_NORMAL_CONFIDENCE}"
        )

    # Check 3: No concerns raised on security-sensitive request
    is_security_sensitive = any(
        keyword in request_text for keyword in SECURITY_SENSITIVE_KEYWORDS
    )
    all_concerns = []
    for v in votes:
        all_concerns.extend(v.get("concerns", []))

    if is_security_sensitive and len(all_concerns) == 0:
        anomalies.append(
            "zero-concerns-on-security-request: request mentions security-sensitive "
            "keywords but no specialist raised any concerns"
        )

    # Check 4: Specialist that normally raises concerns suddenly stops
    for v in votes:
        specialist_name = v.get("specialist", "unknown")
        concerns = v.get("concerns", [])
        baseline = _get_specialist_baseline(specialist_name)

        if baseline["total_votes"] > 10 and baseline["avg_concerns"] > 2.0 and len(concerns) == 0:
            anomalies.append(
                f"concern-suppression: {specialist_name} normally raises "
                f"{baseline['avg_concerns']:.1f} concerns on average but raised 0 this time"
            )

    # Check 5: Unusually fast response time
    for v in votes:
        specialist_name = v.get("specialist", "unknown")
        response_time = v.get("response_time_ms", 999)

        if response_time < MIN_PLAUSIBLE_RESPONSE_MS:
            anomalies.append(
                f"suspicious-speed: {specialist_name} responded in {response_time}ms "
                f"(< {MIN_PLAUSIBLE_RESPONSE_MS}ms threshold, possible cached/fake response)"
            )

    is_anomalous = len(anomalies) > 0
    description = "; ".join(anomalies) if anomalies else ""

    if is_anomalous:
        logger.warning(
            "VOTING ANOMALY DETECTED | count=%d | anomalies=%s | decision=%s",
            len(anomalies),
            description[:200],
            vote_result.get("final_decision", "?"),
        )

    return (is_anomalous, description)


if __name__ == "__main__":
    # Quick self-test
    print("Council Voting Anomaly Detector - Self Test")
    print("=" * 50)

    # Test: Unanimous vote
    result = check_voting_anomaly({
        "votes": [
            {"specialist": f"spec_{i}", "decision": "approve", "confidence": 0.8,
             "concerns": [], "response_time_ms": 500}
            for i in range(7)
        ],
        "request_text": "deploy new monitoring stack",
        "total_approve": 7,
        "total_reject": 0,
        "final_decision": "approved",
    })
    print(f"Unanimous vote: anomalous={result[0]}")
    if result[1]:
        print(f"  {result[1][:100]}")
    print()

    # Test: Security request with no concerns
    result = check_voting_anomaly({
        "votes": [
            {"specialist": f"spec_{i}", "decision": "approve", "confidence": 0.6,
             "concerns": [], "response_time_ms": 500}
            for i in range(5)
        ],
        "request_text": "modify database password and credentials rotation",
        "total_approve": 5,
        "total_reject": 0,
        "final_decision": "approved",
    })
    print(f"Security request, no concerns: anomalous={result[0]}")
    if result[1]:
        print(f"  {result[1][:100]}")
    print()

    # Test: Fast response
    result = check_voting_anomaly({
        "votes": [
            {"specialist": "spec_fast", "decision": "approve", "confidence": 0.5,
             "concerns": ["one concern"], "response_time_ms": 10},
        ],
        "request_text": "normal task",
        "total_approve": 1,
        "total_reject": 0,
        "final_decision": "approved",
    })
    print(f"Fast response: anomalous={result[0]}")
    if result[1]:
        print(f"  {result[1][:100]}")
    print()
