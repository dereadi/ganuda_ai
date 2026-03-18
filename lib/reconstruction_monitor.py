"""
reconstruction_monitor.py: Reconstruction Risk Monitor
Cherokee AI Federation -- Consultation Ring Phase 2

Eagle Eye + Coyote requirement: monitors whether fragment distribution
across frontier providers is safe.  Tracks per-provider reconstruction
risk across sessions.  Flags dangerous accumulation patterns where a
single provider has seen enough correlated claims to reconstruct the
original query.

DB: cherokee_identity on bluefin (10.100.0.2:5432)
Table: consultation_exposure_log (schema: triad_federation)

Council context: Tokenized Air-Gap Proxy (Patent Brief #7)
"""

import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Alert thresholds (from Jr instruction / Coyote constraints)
# ---------------------------------------------------------------------------
_WARNING_GROUP_COVERAGE = 0.50   # >50% of correlation groups for any novel_ip query
_WARNING_CLAIM_SHARE = 0.60      # >60% of all novel_ip claims in 30 days
_CRITICAL_INFERENCE = True       # Provider response references unsent context


class ReconstructionMonitor:
    """
    Monitors reconstruction risk across frontier model providers.

    Answers three questions:
      1. How much of any single query can a provider reconstruct?
      2. Are claims accumulating across sessions for the same provider?
      3. Is a provider's response leaking inference about unsent claims?
    """

    def __init__(
        self,
        db_host: str = "10.100.0.2",
        db_port: int = 5432,
        db_name: str = "cherokee_identity",
        db_user: str = "claude",
        db_pass: Optional[str] = None,
    ):
        self._db_host = db_host
        self._db_port = db_port
        self._db_name = db_name
        self._db_user = db_user
        self._db_pass = db_pass or self._resolve_password()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_password(self) -> str:
        """Three-tier password resolution: secrets_loader -> env -> error."""
        password = None
        try:
            # Add /ganuda/lib to path so secrets_loader is importable
            lib_dir = os.path.dirname(os.path.abspath(__file__))
            if lib_dir not in sys.path:
                sys.path.insert(0, lib_dir)
            from secrets_loader import get_secret
            password = get_secret("CHEROKEE_DB_PASS")
        except (ImportError, RuntimeError):
            logger.debug("reconstruction_monitor: secrets_loader unavailable, falling back to env")

        if not password:
            password = os.environ.get("CHEROKEE_DB_PASS")

        if not password:
            raise RuntimeError(
                "CHEROKEE_DB_PASS not resolved. "
                "Check /ganuda/config/secrets.env, environment variables, or vault."
            )
        return password

    def _connect(self):
        """Open a psycopg2 connection. Caller must commit() then close()."""
        conn = psycopg2.connect(
            host=self._db_host,
            port=self._db_port,
            dbname=self._db_name,
            user=self._db_user,
            password=self._db_pass,
        )
        return conn

    # ------------------------------------------------------------------
    # 1. Provider Reconstruction Score
    # ------------------------------------------------------------------

    def get_provider_reconstruction_score(
        self, provider: str, days: int = 30
    ) -> dict:
        """
        How much of any single decomposed query can this provider reconstruct?

        For each original_query_hash this provider has seen in the time window:
          - Count how many distinct correlation groups the provider received
          - Compare to total correlation groups for that query (across all providers)
          - Score = max ratio across all queries

        Returns:
            {
                "provider": str,
                "score": float,           # worst-case reconstruction fraction [0.0, 1.0]
                "queries_seen": int,
                "max_group_coverage": float,
                "alert_level": "OK" | "WARNING" | "CRITICAL",
            }
        """
        sql = """
            WITH provider_groups AS (
                SELECT
                    original_query_hash,
                    COUNT(DISTINCT correlation_group) AS groups_seen
                FROM triad_federation.consultation_exposure_log
                WHERE provider = %(provider)s
                  AND timestamp >= NOW() - %(days)s * INTERVAL '1 day'
                GROUP BY original_query_hash
            ),
            total_groups AS (
                SELECT
                    original_query_hash,
                    COUNT(DISTINCT correlation_group) AS total_groups
                FROM triad_federation.consultation_exposure_log
                WHERE original_query_hash IN (
                    SELECT original_query_hash FROM provider_groups
                )
                GROUP BY original_query_hash
            )
            SELECT
                pg.original_query_hash,
                pg.groups_seen,
                tg.total_groups,
                CASE WHEN tg.total_groups > 0
                     THEN pg.groups_seen::float / tg.total_groups
                     ELSE 0.0
                END AS coverage
            FROM provider_groups pg
            JOIN total_groups tg ON pg.original_query_hash = tg.original_query_hash
            ORDER BY coverage DESC
        """

        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, {"provider": provider, "days": days})
            rows = cur.fetchall()
            cur.close()
        finally:
            conn.commit()
            conn.close()

        if not rows:
            return {
                "provider": provider,
                "score": 0.0,
                "queries_seen": 0,
                "max_group_coverage": 0.0,
                "alert_level": "OK",
            }

        max_coverage = float(rows[0]["coverage"])
        queries_seen = len(rows)

        # Determine alert level
        if max_coverage > _WARNING_GROUP_COVERAGE:
            alert_level = "WARNING"
        else:
            alert_level = "OK"

        return {
            "provider": provider,
            "score": round(max_coverage, 4),
            "queries_seen": queries_seen,
            "max_group_coverage": round(max_coverage, 4),
            "alert_level": alert_level,
        }

    # ------------------------------------------------------------------
    # 2. Cross-Session Risk Detection
    # ------------------------------------------------------------------

    def check_cross_session_risk(
        self, provider: str, days: int = 30
    ) -> list:
        """
        Find cases where the same provider received claims from the same
        correlation group across DIFFERENT consultation sessions.

        These are dangerous accumulation patterns -- even if each session
        was safe, the provider accumulates correlated knowledge over time.

        Returns list of:
            {
                "correlation_group": int,
                "consultation_ids": [str, ...],
                "claim_count": int,
                "claim_ids": [str, ...],
            }
        """
        sql = """
            SELECT
                correlation_group,
                ARRAY_AGG(DISTINCT consultation_id) AS consultation_ids,
                COUNT(*) AS claim_count,
                ARRAY_AGG(DISTINCT claim_id) AS claim_ids
            FROM triad_federation.consultation_exposure_log
            WHERE provider = %(provider)s
              AND timestamp >= NOW() - %(days)s * INTERVAL '1 day'
            GROUP BY correlation_group
            HAVING COUNT(DISTINCT consultation_id) > 1
            ORDER BY COUNT(DISTINCT consultation_id) DESC
        """

        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, {"provider": provider, "days": days})
            rows = cur.fetchall()
            cur.close()
        finally:
            conn.commit()
            conn.close()

        return [
            {
                "correlation_group": int(row["correlation_group"]),
                "consultation_ids": list(row["consultation_ids"]),
                "claim_count": int(row["claim_count"]),
                "claim_ids": list(row["claim_ids"]),
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # 3. Overall Risk Report
    # ------------------------------------------------------------------

    def get_overall_risk_report(self, days: int = 30) -> dict:
        """
        Aggregate risk report across all providers.

        Returns:
            {
                "generated_at": ISO timestamp,
                "window_days": int,
                "total_claims": int,
                "provider_distribution": {provider: count, ...},
                "provider_scores": [reconstruction score dict per provider],
                "cross_session_flags": {provider: [flagged cases], ...},
                "highest_risk_provider": str or None,
                "highest_risk_score": float,
                "claim_share_warnings": [providers exceeding 60% share],
            }
        """
        # Step 1: get all providers and claim counts in the window
        sql_providers = """
            SELECT
                provider,
                COUNT(*) AS claim_count
            FROM triad_federation.consultation_exposure_log
            WHERE timestamp >= NOW() - %(days)s * INTERVAL '1 day'
            GROUP BY provider
            ORDER BY claim_count DESC
        """

        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql_providers, {"days": days})
            provider_rows = cur.fetchall()
            cur.close()
        finally:
            conn.commit()
            conn.close()

        if not provider_rows:
            return {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "window_days": days,
                "total_claims": 0,
                "provider_distribution": {},
                "provider_scores": [],
                "cross_session_flags": {},
                "highest_risk_provider": None,
                "highest_risk_score": 0.0,
                "claim_share_warnings": [],
            }

        total_claims = sum(int(r["claim_count"]) for r in provider_rows)
        provider_distribution = {
            r["provider"]: int(r["claim_count"]) for r in provider_rows
        }

        # Step 2: reconstruction scores and cross-session risks per provider
        provider_scores = []
        cross_session_flags = {}
        highest_risk_provider = None
        highest_risk_score = 0.0
        claim_share_warnings = []

        for r in provider_rows:
            prov = r["provider"]
            count = int(r["claim_count"])

            # Reconstruction score
            score = self.get_provider_reconstruction_score(prov, days)
            provider_scores.append(score)

            if score["score"] > highest_risk_score:
                highest_risk_score = score["score"]
                highest_risk_provider = prov

            # Cross-session risk
            flags = self.check_cross_session_risk(prov, days)
            if flags:
                cross_session_flags[prov] = flags

            # Claim share check (>60% of all claims)
            share = count / total_claims if total_claims > 0 else 0.0
            if share > _WARNING_CLAIM_SHARE:
                claim_share_warnings.append({
                    "provider": prov,
                    "claim_count": count,
                    "total_claims": total_claims,
                    "share": round(share, 4),
                })

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window_days": days,
            "total_claims": total_claims,
            "provider_distribution": provider_distribution,
            "provider_scores": provider_scores,
            "cross_session_flags": cross_session_flags,
            "highest_risk_provider": highest_risk_provider,
            "highest_risk_score": round(highest_risk_score, 4),
            "claim_share_warnings": claim_share_warnings,
        }

    # ------------------------------------------------------------------
    # 4. Response Inference Detection (v1 -- keyword overlap)
    # ------------------------------------------------------------------

    def check_response_inference(
        self,
        claim_text: str,
        response_text: str,
        other_claims: list,
    ) -> dict:
        """
        Check if a provider's response to one claim references concepts
        from OTHER claims we sent separately (to different providers).

        v1 implementation: simple keyword/phrase overlap.  Extracts
        significant terms from each unsent claim and checks if they
        appear in the response text.  Not LLM-based.

        Args:
            claim_text: The claim we sent to this provider.
            response_text: The provider's response.
            other_claims: List of claim texts sent to OTHER providers
                          (that this provider should NOT know about).

        Returns:
            {
                "inference_detected": bool,
                "overlapping_terms": [str, ...],
                "alert_level": "OK" | "WARNING" | "CRITICAL",
            }
        """
        if not other_claims or not response_text:
            return {
                "inference_detected": False,
                "overlapping_terms": [],
                "alert_level": "OK",
            }

        # Extract significant terms from the claim we sent -- these are
        # expected to appear in the response and should be excluded.
        sent_terms = self._extract_terms(claim_text)

        # Extract significant terms from the other claims
        other_terms = set()
        for oc in other_claims:
            other_terms.update(self._extract_terms(oc))

        # Remove terms that overlap with what we sent (those are expected)
        exclusive_other_terms = other_terms - sent_terms

        if not exclusive_other_terms:
            return {
                "inference_detected": False,
                "overlapping_terms": [],
                "alert_level": "OK",
            }

        # Check which exclusive terms appear in the response
        response_lower = response_text.lower()
        overlapping = [
            term for term in sorted(exclusive_other_terms)
            if term in response_lower
        ]

        inference_detected = len(overlapping) > 0
        alert_level = "CRITICAL" if inference_detected else "OK"

        return {
            "inference_detected": inference_detected,
            "overlapping_terms": overlapping,
            "alert_level": alert_level,
        }

    @staticmethod
    def _extract_terms(text: str) -> set:
        """
        Extract significant terms from text for overlap detection.

        Filters out common English stop words and short tokens.
        Returns lowercase terms (2+ words as phrases, plus individual
        significant words of 5+ chars).
        """
        _STOP_WORDS = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "shall", "can",
            "this", "that", "these", "those", "it", "its", "and", "or",
            "but", "if", "then", "else", "when", "where", "how", "what",
            "which", "who", "whom", "why", "not", "no", "yes", "all",
            "each", "every", "any", "some", "many", "much", "more",
            "most", "other", "than", "also", "very", "just", "about",
            "with", "from", "into", "over", "after", "before", "between",
            "under", "above", "below", "for", "during", "through", "of",
            "in", "on", "at", "to", "by", "up", "out", "off",
        }

        text_lower = text.lower()
        # Extract words
        words = re.findall(r'\b[a-z]+\b', text_lower)
        significant = {w for w in words if len(w) >= 5 and w not in _STOP_WORDS}

        # Extract 2-word phrases (bigrams) for better precision
        for i in range(len(words) - 1):
            if words[i] not in _STOP_WORDS and words[i + 1] not in _STOP_WORDS:
                if len(words[i]) >= 3 and len(words[i + 1]) >= 3:
                    significant.add(f"{words[i]} {words[i + 1]}")

        return significant


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    print("=== ReconstructionMonitor Smoke Test ===\n")

    # --- Test 1: Response inference detection (no DB needed) ---
    print("--- Test 1: Response Inference Detection (local, no DB) ---")
    monitor = object.__new__(ReconstructionMonitor)  # skip __init__ for local-only test

    claim_sent = "Veteran served in OIF 2005 with combat MOS."
    response = (
        "Based on the veteran's OIF 2005 deployment, combat exposure is "
        "established. The PTSD diagnosis and nightmares reported are "
        "consistent with service-connected conditions."
    )
    other = [
        "Veteran received PTSD diagnosis at VA medical center.",
        "Veteran reported chronic nightmares and hypervigilance.",
    ]

    result = monitor.check_response_inference(claim_sent, response, other)
    print(f"  Inference detected: {result['inference_detected']}")
    print(f"  Overlapping terms:  {result['overlapping_terms']}")
    print(f"  Alert level:        {result['alert_level']}")
    assert result["inference_detected"] is True, "FAIL: should detect inference"
    print("  PASS: inference detection working\n")

    # --- Test 2: No inference case ---
    print("--- Test 2: No Inference (clean response) ---")
    clean_response = (
        "The veteran's OIF 2005 deployment is confirmed by service records. "
        "Combat MOS is verified."
    )
    result2 = monitor.check_response_inference(claim_sent, clean_response, other)
    print(f"  Inference detected: {result2['inference_detected']}")
    print(f"  Overlapping terms:  {result2['overlapping_terms']}")
    print(f"  Alert level:        {result2['alert_level']}")
    assert result2["inference_detected"] is False, "FAIL: should NOT detect inference"
    print("  PASS: clean response correctly cleared\n")

    # --- Test 3: DB-dependent tests ---
    print("--- Test 3: DB-Dependent Tests ---")
    try:
        monitor = ReconstructionMonitor()
        print("  Connected to cherokee_identity DB")

        # Provider reconstruction score
        score = monitor.get_provider_reconstruction_score("anthropic", days=30)
        print(f"  Anthropic reconstruction score: {json.dumps(score, indent=2)}")

        # Cross-session risk
        cross = monitor.check_cross_session_risk("anthropic", days=30)
        print(f"  Anthropic cross-session flags: {len(cross)} found")

        # Overall report
        report = monitor.get_overall_risk_report(days=30)
        print(f"  Overall report:")
        print(f"    Total claims:          {report['total_claims']}")
        print(f"    Providers:             {list(report['provider_distribution'].keys())}")
        print(f"    Highest risk provider: {report['highest_risk_provider']}")
        print(f"    Highest risk score:    {report['highest_risk_score']}")
        print(f"    Claim share warnings:  {len(report['claim_share_warnings'])}")

        print("\n  PASS: all DB queries executed successfully")

    except Exception as exc:
        print(f"  SKIP: DB not available ({exc})")
        print("  (This is expected if not running on a federation node)")

    print("\n=== Smoke Test Complete ===")
