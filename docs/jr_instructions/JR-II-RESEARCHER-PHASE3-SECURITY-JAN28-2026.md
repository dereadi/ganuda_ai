# JR Instruction: ii-researcher Phase 3 - Security Hardening

**JR ID:** JR-II-RESEARCHER-PHASE3-SECURITY-JAN28-2026
**Priority:** P2
**Assigned To:** IT Triad Jr.
**Council Vote:** 166956a7959c2232
**Ultrathink:** ULTRATHINK-II-RESEARCHER-INTEGRATION-JAN28-2026.md
**Depends On:** JR-II-RESEARCHER-PHASE2-API-JAN28-2026

---

## Objective

Harden ii-researcher with audit logging, PII detection, rate limiting, and sandboxed execution per Council security concerns.

---

## Steps

### 1. Create Audit Logging Table

```sql
-- Run on bluefin (192.168.132.222) in zammad_production

CREATE TABLE IF NOT EXISTS research_audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_id VARCHAR(100),
    source_system VARCHAR(50),  -- 'telegram', 'vetassist', 'jr_worker', 'gateway'
    query_text TEXT,
    query_hash VARCHAR(64),     -- SHA-256 of query for dedup tracking
    pii_detected BOOLEAN DEFAULT FALSE,
    pii_types TEXT[],           -- Array of detected PII types
    sources_count INTEGER,
    response_time_ms INTEGER,
    confidence_score FLOAT,
    ip_address INET,
    was_rate_limited BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_research_audit_timestamp ON research_audit_log(timestamp);
CREATE INDEX idx_research_audit_user ON research_audit_log(user_id);
CREATE INDEX idx_research_audit_pii ON research_audit_log(pii_detected);
```

### 2. Create PII Detection Pre-filter

Create `/ganuda/lib/research_pii_filter.py`:

```python
#!/usr/bin/env python3
"""
PII Detection for Research Queries.

Prevents personally identifiable information from being sent to external search.

For Seven Generations - Cherokee AI Federation
"""

import re
from typing import Tuple, List

# PII patterns to detect
PII_PATTERNS = {
    'ssn': r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',
    'phone': r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'dob': r'\b(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](19|20)\d{2}\b',
    'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    'va_file_number': r'\b[A-Z]?\d{7,9}\b',  # VA file numbers
    'address': r'\b\d+\s+[\w\s]+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln)\b',
}

def detect_pii(query: str) -> Tuple[bool, List[str]]:
    """
    Check query for PII patterns.

    Args:
        query: The search query text

    Returns:
        Tuple of (has_pii: bool, detected_types: List[str])
    """
    query_lower = query.lower()
    detected = []

    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, query_lower, re.IGNORECASE):
            detected.append(pii_type)

    return (len(detected) > 0, detected)


def sanitize_query(query: str) -> str:
    """
    Remove detected PII from query.

    Args:
        query: Original query

    Returns:
        Sanitized query with PII replaced by [REDACTED]
    """
    sanitized = query
    for pattern in PII_PATTERNS.values():
        sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
    return sanitized


def validate_research_query(query: str, block_pii: bool = True) -> Tuple[bool, str, List[str]]:
    """
    Validate a research query for safety.

    Args:
        query: The query to validate
        block_pii: If True, block queries with PII. If False, sanitize.

    Returns:
        Tuple of (is_safe, processed_query, detected_pii_types)
    """
    has_pii, pii_types = detect_pii(query)

    if not has_pii:
        return (True, query, [])

    if block_pii:
        return (False, None, pii_types)
    else:
        return (True, sanitize_query(query), pii_types)
```

### 3. Implement Rate Limiting

Create `/ganuda/lib/research_rate_limiter.py`:

```python
#!/usr/bin/env python3
"""
Rate Limiter for Research Queries.

Prevents abuse of external search APIs.

For Seven Generations - Cherokee AI Federation
"""

import time
from collections import defaultdict
from threading import Lock

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 10):
        self.rate = requests_per_minute
        self.buckets = defaultdict(lambda: {'tokens': requests_per_minute, 'last_update': time.time()})
        self.lock = Lock()

    def is_allowed(self, user_id: str) -> bool:
        """
        Check if request is allowed for user.

        Args:
            user_id: User or system identifier

        Returns:
            True if request is allowed
        """
        with self.lock:
            bucket = self.buckets[user_id]
            now = time.time()

            # Refill tokens based on time elapsed
            time_passed = now - bucket['last_update']
            bucket['tokens'] = min(
                self.rate,
                bucket['tokens'] + (time_passed / 60.0) * self.rate
            )
            bucket['last_update'] = now

            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True
            return False

    def get_wait_time(self, user_id: str) -> float:
        """Get seconds until next request is allowed."""
        bucket = self.buckets[user_id]
        if bucket['tokens'] >= 1:
            return 0
        tokens_needed = 1 - bucket['tokens']
        return (tokens_needed / self.rate) * 60


# Global rate limiter instance
_rate_limiter = RateLimiter(requests_per_minute=10)

def check_rate_limit(user_id: str) -> Tuple[bool, float]:
    """
    Check rate limit for user.

    Returns:
        Tuple of (is_allowed, wait_seconds)
    """
    if _rate_limiter.is_allowed(user_id):
        return (True, 0)
    return (False, _rate_limiter.get_wait_time(user_id))
```

### 4. Create Secure Research Wrapper

Create `/ganuda/lib/secure_research.py`:

```python
#!/usr/bin/env python3
"""
Secure Research Wrapper.

Combines PII detection, rate limiting, and audit logging.

For Seven Generations - Cherokee AI Federation
"""

import hashlib
import psycopg2
from typing import Dict, Any, Optional
from datetime import datetime

from .research_client import ResearchClient
from .research_pii_filter import validate_research_query
from .research_rate_limiter import check_rate_limit

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}


class SecureResearchClient:
    """Research client with security controls."""

    def __init__(self):
        self.client = ResearchClient()

    async def search(
        self,
        query: str,
        user_id: str,
        source_system: str,
        ip_address: str = None,
        max_sources: int = 5
    ) -> Dict[str, Any]:
        """
        Perform secured research query.

        Args:
            query: Search query
            user_id: User identifier for rate limiting
            source_system: 'telegram', 'vetassist', 'jr_worker', etc.
            ip_address: Optional IP for logging
            max_sources: Max sources to retrieve

        Returns:
            Research result or error dict
        """
        # Check rate limit
        is_allowed, wait_time = check_rate_limit(user_id)
        if not is_allowed:
            self._log_audit(
                user_id, source_system, query, False, [],
                0, 0, 0, ip_address, was_rate_limited=True
            )
            return {
                'error': 'rate_limited',
                'message': f'Rate limit exceeded. Try again in {wait_time:.1f} seconds.',
                'wait_seconds': wait_time
            }

        # Check for PII
        is_safe, processed_query, pii_types = validate_research_query(query, block_pii=True)
        if not is_safe:
            self._log_audit(
                user_id, source_system, query, True, pii_types,
                0, 0, 0, ip_address
            )
            return {
                'error': 'pii_detected',
                'message': f'Query contains PII ({", ".join(pii_types)}). Please remove personal information.',
                'pii_types': pii_types
            }

        # Perform search
        start_time = datetime.now()
        try:
            result = await self.client.search(processed_query, max_sources)
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Log successful search
            self._log_audit(
                user_id, source_system, query, False, [],
                len(result.get('sources', [])),
                response_time,
                result.get('confidence', 0),
                ip_address
            )

            return result
        except Exception as e:
            self._log_audit(
                user_id, source_system, query, False, [],
                0, 0, 0, ip_address
            )
            return {
                'error': 'search_failed',
                'message': str(e)
            }

    def _log_audit(
        self,
        user_id: str,
        source_system: str,
        query: str,
        pii_detected: bool,
        pii_types: list,
        sources_count: int,
        response_time: int,
        confidence: float,
        ip_address: str,
        was_rate_limited: bool = False
    ):
        """Log search to audit table."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO research_audit_log
                (user_id, source_system, query_text, query_hash, pii_detected,
                 pii_types, sources_count, response_time_ms, confidence_score,
                 ip_address, was_rate_limited)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                source_system,
                query[:500],  # Truncate long queries
                hashlib.sha256(query.encode()).hexdigest()[:64],
                pii_detected,
                pii_types,
                sources_count,
                response_time,
                confidence,
                ip_address,
                was_rate_limited
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[SecureResearch] Audit log failed: {e}")
```

### 5. Update Gateway Route with Security

Modify `/ganuda/services/llm_gateway/routes/research.py` to use SecureResearchClient:

```python
# Add to imports
from lib.secure_research import SecureResearchClient

# Replace research endpoint
@router.post("/v1/research")
async def research(request: ResearchRequest, req: Request):
    """Perform secured web research."""
    client = SecureResearchClient()

    # Extract user info from API key or headers
    user_id = request.headers.get('X-User-ID', 'anonymous')
    ip_address = req.client.host

    result = await client.search(
        query=request.query,
        user_id=user_id,
        source_system='gateway',
        ip_address=ip_address,
        max_sources=request.max_sources
    )

    if 'error' in result:
        raise HTTPException(
            status_code=429 if result['error'] == 'rate_limited' else 400,
            detail=result['message']
        )

    return result
```

---

## Verification

```bash
# Check audit table
psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT * FROM research_audit_log LIMIT 5"

# Test PII detection
python3 -c "from lib.research_pii_filter import detect_pii; print(detect_pii('my SSN is 123-45-6789'))"

# Test rate limiting
for i in {1..15}; do
  curl -s http://localhost:8080/v1/research \
    -H "Content-Type: application/json" \
    -H "X-User-ID: test-user" \
    -d '{"query": "test"}' | jq .error
done

# Verify audit logs
psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT timestamp, source_system, pii_detected, was_rate_limited
FROM research_audit_log ORDER BY timestamp DESC LIMIT 10"
```

---

## Notes

- All external queries are logged for compliance
- PII is blocked, not sanitized (fail-safe approach)
- Rate limit is 10 requests/minute per user
- Audit logs retained per Seven Generations data governance

---

FOR SEVEN GENERATIONS
