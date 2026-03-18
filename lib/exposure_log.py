"""
exposure_log.py: Outbound Claim Exposure Logger
Cherokee AI Federation — Consultation Ring Privacy Layer

Logs every claim sent to frontier models (OpenAI, Anthropic, etc.) via the
consultation ring. Enables reconstruction-risk analysis: if a provider has seen
enough correlated claims, they may be able to reconstruct the original query.

PRIVACY RULE: Original query text is NEVER stored. Only the md5 hash.

DB: triad_federation on bluefin (10.100.0.2:5432)
Table: consultation_exposure_log
"""

import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


@dataclass
class ExposureClaim:
    claim_id: str
    claim_text: str
    correlation_group: int
    sensitivity_score: float
    provider: str
    ip_classification: str


class ExposureLog:
    def __init__(
        self,
        db_host: str = "10.100.0.2",
        db_port: int = 5432,
        db_name: str = "triad_federation",
        db_user: str = "claude",
        db_pass: Optional[str] = None,
    ):
        """
        Initialize with DB connection params.
        If db_pass is not provided, loads from secrets_loader (CHEROKEE_DB_PASS key)
        with a fallback to the CHEROKEE_DB_PASS environment variable.
        """
        self._db_host = db_host
        self._db_port = db_port
        self._db_name = db_name
        self._db_user = db_user
        self._db_pass = db_pass or self._resolve_password()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_password(self) -> str:
        """Three-tier password resolution: secrets_loader → env → error."""
        password = None
        try:
            from secrets_loader import get_secret
            password = get_secret("CHEROKEE_DB_PASS")
        except ImportError:
            logger.debug("exposure_log: secrets_loader not available, falling back to env")

        if not password:
            password = os.environ.get("CHEROKEE_DB_PASS")

        if not password:
            raise RuntimeError(
                "CHEROKEE_DB_PASS not resolved. "
                "Check /ganuda/config/secrets.env, environment variables, or vault."
            )
        return password

    def _connect(self):
        """
        Open a new psycopg2 connection with autocommit=True.
        Caller is responsible for closing it.
        """
        conn = psycopg2.connect(
            host=self._db_host,
            port=self._db_port,
            dbname=self._db_name,
            user=self._db_user,
            password=self._db_pass,
        )
        conn.autocommit = True
        return conn

    @staticmethod
    def _hash_query(original_query: str) -> str:
        """Return md5 hex digest of the original query. Never store the raw text."""
        return hashlib.md5(original_query.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_claims(
        self,
        consultation_id: str,
        original_query: str,
        claims: List[ExposureClaim],
    ) -> int:
        """
        Log a batch of claims for one consultation.

        Stores the md5 hash of original_query, NEVER the original text.
        Uses executemany for efficiency; autocommit means each statement
        commits immediately — no silent rollbacks.

        Returns the number of rows inserted.
        """
        if not claims:
            logger.debug("exposure_log.log_claims: empty claims list, nothing to log")
            return 0

        query_hash = self._hash_query(original_query)
        now = datetime.now(timezone.utc)

        rows = [
            (
                consultation_id,
                claim.claim_id,
                claim.claim_text,
                claim.correlation_group,
                claim.sensitivity_score,
                claim.provider,
                claim.ip_classification,
                now,
                query_hash,
            )
            for claim in claims
        ]

        sql = """
            INSERT INTO consultation_exposure_log
                (consultation_id, claim_id, claim_text, correlation_group,
                 sensitivity_score, provider, ip_classification,
                 timestamp, original_query_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.executemany(sql, rows)
            inserted = cur.rowcount
            cur.close()
        finally:
            conn.commit()  # explicit commit before close
            conn.close()

        logger.debug(
            "exposure_log.log_claims: consultation=%s provider=%s claims=%d",
            consultation_id,
            claims[0].provider if claims else "?",
            inserted,
        )
        return inserted

    def get_provider_exposure(self, provider: str, days: int = 30) -> dict:
        """
        What has this provider seen over the last N days?

        Returns:
            {
                "provider": str,
                "days": int,
                "claim_count": int,
                "unique_query_hashes": int,
                "earliest": ISO timestamp or None,
                "latest": ISO timestamp or None,
            }
        """
        sql = """
            SELECT
                COUNT(*)                        AS claim_count,
                COUNT(DISTINCT original_query_hash) AS unique_query_hashes,
                MIN(timestamp)                  AS earliest,
                MAX(timestamp)                  AS latest
            FROM consultation_exposure_log
            WHERE provider = %s
              AND timestamp >= NOW() - INTERVAL '%s days'
        """

        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, (provider, days))
            row = cur.fetchone()
            cur.close()
        finally:
            conn.commit()  # explicit commit before close
            conn.close()

        return {
            "provider": provider,
            "days": days,
            "claim_count": int(row["claim_count"]) if row else 0,
            "unique_query_hashes": int(row["unique_query_hashes"]) if row else 0,
            "earliest": row["earliest"].isoformat() if row and row["earliest"] else None,
            "latest": row["latest"].isoformat() if row and row["latest"] else None,
        }

    def get_query_exposure(self, original_query: str) -> dict:
        """
        How much of this query's claims have been exposed and to whom?

        Accepts the original query text locally (to hash it) but never
        passes the raw text to the DB.

        Returns:
            {
                "query_hash": str,
                "total_claims": int,
                "providers": [{"provider": str, "claim_count": int}, ...],
                "ip_classifications": [{"ip_classification": str, "claim_count": int}, ...],
                "correlation_groups_seen": int,
            }
        """
        query_hash = self._hash_query(original_query)

        sql_summary = """
            SELECT
                COUNT(*)                              AS total_claims,
                COUNT(DISTINCT correlation_group)     AS correlation_groups_seen
            FROM consultation_exposure_log
            WHERE original_query_hash = %s
        """

        sql_by_provider = """
            SELECT provider, COUNT(*) AS claim_count
            FROM consultation_exposure_log
            WHERE original_query_hash = %s
            GROUP BY provider
            ORDER BY claim_count DESC
        """

        sql_by_class = """
            SELECT ip_classification, COUNT(*) AS claim_count
            FROM consultation_exposure_log
            WHERE original_query_hash = %s
            GROUP BY ip_classification
            ORDER BY claim_count DESC
        """

        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cur.execute(sql_summary, (query_hash,))
            summary = cur.fetchone()

            cur.execute(sql_by_provider, (query_hash,))
            providers = [dict(r) for r in cur.fetchall()]

            cur.execute(sql_by_class, (query_hash,))
            classifications = [dict(r) for r in cur.fetchall()]

            cur.close()
        finally:
            conn.commit()  # explicit commit before close
            conn.close()

        return {
            "query_hash": query_hash,
            "total_claims": int(summary["total_claims"]) if summary else 0,
            "correlation_groups_seen": int(summary["correlation_groups_seen"]) if summary else 0,
            "providers": providers,
            "ip_classifications": classifications,
        }

    def get_total_exposure_surface(self) -> dict:
        """
        Overall exposure surface across all consultations.

        Returns:
            {
                "total_claims": int,
                "unique_consultations": int,
                "unique_query_hashes": int,
                "by_provider": [{"provider": str, "claim_count": int}, ...],
                "by_classification": [{"ip_classification": str, "claim_count": int}, ...],
                "by_date": [{"date": "YYYY-MM-DD", "claim_count": int}, ...],
            }
        """
        sql_totals = """
            SELECT
                COUNT(*)                              AS total_claims,
                COUNT(DISTINCT consultation_id)       AS unique_consultations,
                COUNT(DISTINCT original_query_hash)   AS unique_query_hashes
            FROM consultation_exposure_log
        """

        sql_by_provider = """
            SELECT provider, COUNT(*) AS claim_count
            FROM consultation_exposure_log
            GROUP BY provider
            ORDER BY claim_count DESC
        """

        sql_by_class = """
            SELECT ip_classification, COUNT(*) AS claim_count
            FROM consultation_exposure_log
            GROUP BY ip_classification
            ORDER BY claim_count DESC
        """

        sql_by_date = """
            SELECT
                DATE(timestamp AT TIME ZONE 'UTC') AS date,
                COUNT(*) AS claim_count
            FROM consultation_exposure_log
            GROUP BY DATE(timestamp AT TIME ZONE 'UTC')
            ORDER BY date DESC
            LIMIT 90
        """

        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cur.execute(sql_totals)
            totals = cur.fetchone()

            cur.execute(sql_by_provider)
            by_provider = [dict(r) for r in cur.fetchall()]

            cur.execute(sql_by_class)
            by_classification = [dict(r) for r in cur.fetchall()]

            cur.execute(sql_by_date)
            by_date = [
                {"date": str(r["date"]), "claim_count": int(r["claim_count"])}
                for r in cur.fetchall()
            ]

            cur.close()
        finally:
            conn.commit()  # explicit commit before close
            conn.close()

        return {
            "total_claims": int(totals["total_claims"]) if totals else 0,
            "unique_consultations": int(totals["unique_consultations"]) if totals else 0,
            "unique_query_hashes": int(totals["unique_query_hashes"]) if totals else 0,
            "by_provider": by_provider,
            "by_classification": by_classification,
            "by_date": by_date,
        }

    def get_reconstruction_risk(self, provider: str, query_hash: str) -> float:
        """
        What fraction of correlation groups for this query has this provider seen?

        Risk = (distinct correlation groups seen by provider) / (total distinct correlation groups)

        Returns a float in [0.0, 1.0].
        Returns 0.0 if the query hash has never been logged (no data = no risk).
        """
        sql_provider_groups = """
            SELECT COUNT(DISTINCT correlation_group) AS seen
            FROM consultation_exposure_log
            WHERE provider = %s
              AND original_query_hash = %s
        """

        sql_total_groups = """
            SELECT COUNT(DISTINCT correlation_group) AS total
            FROM consultation_exposure_log
            WHERE original_query_hash = %s
        """

        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cur.execute(sql_provider_groups, (provider, query_hash))
            provider_row = cur.fetchone()

            cur.execute(sql_total_groups, (query_hash,))
            total_row = cur.fetchone()

            cur.close()
        finally:
            conn.commit()  # explicit commit before close
            conn.close()

        total = int(total_row["total"]) if total_row else 0
        if total == 0:
            return 0.0

        seen = int(provider_row["seen"]) if provider_row else 0
        return round(seen / total, 4)
