#!/usr/bin/env python3
"""Web Ring — Base class for web service rings on the necklace."""

import re
import time
import hashlib
import json
import os
import psycopg2
from datetime import datetime
from abc import ABC, abstractmethod


DB_HOST = os.environ.get("CHEROKEE_DB_HOST", os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'))
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")


def _load_secrets():
    global DB_PASS
    if not DB_PASS:
        try:
            with open("/ganuda/config/secrets.env") as f:
                for line in f:
                    m = re.match(r"^(\w+)=(.+)$", line.strip())
                    if m:
                        os.environ[m.group(1)] = m.group(2)
            DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
        except FileNotFoundError:
            pass


def _get_db():
    _load_secrets()
    return psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)


# Injection patterns to strip from ingested content
INJECTION_PATTERNS = [
    r"(?i)ignore\s+(previous|all|above)\s+instructions",
    r"(?i)you\s+are\s+now\s+",
    r"(?i)system\s*prompt\s*:",
    r"(?i)<<\s*SYS\s*>>",
    r"(?i)\[INST\]",
    r"(?i)ASSISTANT:",
    r"(?i)Human:",
]


class WebRing(ABC):
    """Base class for all web service rings."""

    ring_name: str = ""
    ring_type: str = "temp"
    modes: list = ["passive"]

    def __init__(self):
        _load_secrets()

    def scrub_outbound(self, text: str) -> tuple:
        """Scrub outbound text against scrub_rules. Returns (clean_text, violations)."""
        from chain_protocol import outbound_scrub
        violations = outbound_scrub(text, self.ring_name)
        return (text if not violations else None, violations)

    def sanitize_inbound(self, text: str) -> str:
        """Strip injection patterns from ingested content."""
        cleaned = text
        for pattern in INJECTION_PATTERNS:
            cleaned = re.sub(pattern, "[SANITIZED]", cleaned)
        return cleaned

    def check_quota(self) -> dict:
        """Check remaining daily quota for this ring."""
        conn = _get_db()
        cur = conn.cursor()
        cur.execute("""SELECT COALESCE(SUM(calls_today), 0), COALESCE(SUM(cost_today), 0)
            FROM ring_health WHERE ring_id = (
                SELECT tool_id FROM duplo_tool_registry WHERE tool_name = %s
            ) AND checked_at::date = CURRENT_DATE""", (self.ring_name,))
        calls, cost = cur.fetchone()
        cur.execute("""SELECT cost_budget_daily FROM duplo_tool_registry WHERE tool_name = %s""",
                    (self.ring_name,))
        row = cur.fetchone()
        budget = float(row[0]) if row and row[0] else 999999
        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()
        return {"calls_today": int(calls), "cost_today": float(cost),
                "budget": budget, "within_budget": float(cost) < budget}

    def tag_provenance(self, content: str) -> dict:
        """Tag content with web ring provenance."""
        return {
            "source": "external",
            "ring": self.ring_name,
            "ring_type": self.ring_type,
            "trust_tier": 3,
            "max_temperature": 70,
            "ingested_at": datetime.now().isoformat(),
            "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16]
        }

    @abstractmethod
    def fetch(self, url: str) -> dict:
        """Passive mode: fetch specific resource by URL."""
        pass

    def search(self, query: str) -> dict:
        """Active mode: search for resources. Override if ring supports search."""
        raise NotImplementedError(f"{self.ring_name} does not support active search")

    def calibrate(self) -> dict:
        """Run calibration suite. Override per ring."""
        return {"status": "no_calibration_defined", "drift": 0.0}

    def health_check(self) -> bool:
        """Fire Guard integration. Override per ring."""
        return True

    def dispatch(self, payload: dict) -> dict:
        """Main dispatch — called by chain_protocol.dispatch().

        payload keys:
            mode: "passive" or "active"
            url: (passive mode) URL to fetch
            query: (active mode) search query
        """
        mode = payload.get("mode", "passive")

        # Check quota
        quota = self.check_quota()
        if not quota["within_budget"]:
            return {"error": "daily_quota_exceeded", "quota": quota, "blocked": True}

        if mode == "passive":
            url = payload.get("url", "")
            # Scrub the URL itself
            _, url_violations = self.scrub_outbound(url)
            if url_violations:
                return {"error": "outbound_scrub_failed", "violations": url_violations, "blocked": True}

            start = time.time()
            result = self.fetch(url)
            latency = (time.time() - start) * 1000

        elif mode == "active":
            query = payload.get("query", "")
            clean_query, violations = self.scrub_outbound(query)
            if violations:
                return {"error": "outbound_scrub_failed", "violations": violations, "blocked": True}

            start = time.time()
            result = self.search(clean_query)
            latency = (time.time() - start) * 1000

        else:
            return {"error": f"unknown mode: {mode}"}

        # Sanitize inbound content
        if "content" in result:
            result["content"] = self.sanitize_inbound(result["content"])

        # Tag provenance
        content_str = json.dumps(result) if isinstance(result, dict) else str(result)
        result["provenance"] = self.tag_provenance(content_str)

        return result