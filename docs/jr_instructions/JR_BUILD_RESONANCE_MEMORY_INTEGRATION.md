# JR INSTRUCTIONS: Resonance-Memory Integration
## Priority: 2 (High)
## December 17, 2025

### OVERVIEW

Build a resource-efficient integration between the ResonanceDetector and Thermal Memory. The key principle: **once a pattern hits resonance, it should be optimal** - recognized patterns skip expensive analysis entirely.

**Philosophy:** Like a tuning fork, once you hit the resonant frequency, it vibrates with minimal energy. We want deliberations to work the same way.

---

## ARCHITECTURE

```
Deliberation Request
        │
        ▼
┌─────────────────┐
│ Generate        │  ← Deterministic, no LLM
│ Fingerprint     │     O(1), ~0.1ms
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Hot Cache       │  ← In-memory dict
│ Lookup          │     O(1), ~0.1ms
└────────┬────────┘
         │
    HIT? ├─────YES────→ Return cached (INSTANT)
         │
         NO
         │
         ▼
┌─────────────────┐
│ Thermal Memory  │  ← PostgreSQL indexed
│ Query           │     ~5ms
└────────┬────────┘
         │
    HIT? ├─────YES────→ Warm cache + Return
         │
         NO
         │
         ▼
┌─────────────────┐
│ Full Analysis   │  ← ResonanceDetector
│ (expensive)     │     ~500ms
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Store if        │  ← Only resonant patterns
│ Resonant        │     (score > 0.7)
└─────────────────┘
```

---

## TASK 1: Create Database Schema

**Location:** Run on redfin PostgreSQL (192.168.132.222)

```sql
-- Connect to zammad_production database
-- Run as claude user

-- Main resonance patterns table
CREATE TABLE IF NOT EXISTS resonance_patterns (
    id                  SERIAL PRIMARY KEY,
    fingerprint_hash    BIGINT NOT NULL UNIQUE,

    -- Fingerprint components (for debugging/analysis)
    theme_hash          INTEGER,
    tone_vector         SMALLINT[4],      -- [confident, cautious, positive, negative]
    specialist_mask     SMALLINT,
    confidence_band     SMALLINT,         -- 1=low, 2=med, 3=high
    question_hash       INTEGER,

    -- Resonance data
    pattern_type        VARCHAR(20) NOT NULL,  -- 'harmony', 'creative_tension', 'anti_pattern'
    resonance_score     REAL NOT NULL,
    resonance_data      JSONB,                 -- Full resonance result

    -- Outcome tracking (updated later when known)
    outcome             VARCHAR(20) DEFAULT 'unknown',  -- 'positive', 'negative', 'unknown'
    outcome_notes       TEXT,
    outcome_recorded_at TIMESTAMP,

    -- Thermal integration
    temperature         REAL DEFAULT 70.0,
    last_accessed       TIMESTAMP DEFAULT NOW(),
    access_count        INTEGER DEFAULT 1,
    decay_rate          REAL DEFAULT 0.95,     -- Per-day decay multiplier
    min_temperature     REAL DEFAULT 30.0,

    -- Context preservation
    original_question   TEXT,
    question_domain     VARCHAR(50),
    specialist_summary  JSONB,
    coyote_insight      TEXT,

    -- Metadata
    created_at          TIMESTAMP DEFAULT NOW(),
    source_node         VARCHAR(50),           -- Which node created this
    deliberation_id     VARCHAR(32)            -- Link to original deliberation
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_resonance_fingerprint ON resonance_patterns(fingerprint_hash);
CREATE INDEX IF NOT EXISTS idx_resonance_temperature ON resonance_patterns(temperature DESC);
CREATE INDEX IF NOT EXISTS idx_resonance_pattern_type ON resonance_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_resonance_outcome ON resonance_patterns(outcome);
CREATE INDEX IF NOT EXISTS idx_resonance_domain ON resonance_patterns(question_domain);

-- Hot cache table (replicated to each node's local memory)
CREATE TABLE IF NOT EXISTS resonance_hot_cache (
    fingerprint_hash    BIGINT PRIMARY KEY,
    pattern_type        VARCHAR(20),
    resonance_score     REAL,
    resonance_summary   JSONB,          -- Compact summary for fast return
    outcome             VARCHAR(20),

    hit_count           INTEGER DEFAULT 0,
    last_hit            TIMESTAMP DEFAULT NOW(),
    cached_at           TIMESTAMP DEFAULT NOW(),
    expires_at          TIMESTAMP DEFAULT (NOW() + INTERVAL '24 hours')
);

CREATE INDEX IF NOT EXISTS idx_hot_cache_expires ON resonance_hot_cache(expires_at);

-- View for monitoring resonance health
CREATE OR REPLACE VIEW resonance_health AS
SELECT
    pattern_type,
    outcome,
    COUNT(*) as count,
    AVG(resonance_score) as avg_score,
    AVG(temperature) as avg_temp,
    AVG(access_count) as avg_accesses
FROM resonance_patterns
GROUP BY pattern_type, outcome
ORDER BY count DESC;

COMMENT ON TABLE resonance_patterns IS 'Cherokee AI Federation - Resonance Memory for institutional wisdom';
```

---

## TASK 2: Create Resonance Fingerprint Module

**File:** `/ganuda/lib/metacognition/resonance_fingerprint.py`

```python
#!/usr/bin/env python3
"""
Resonance Fingerprint - Cheap pattern identification for cache lookups

Creates a compact fingerprint from deliberation context that can be:
- Computed without LLM (deterministic)
- Used for O(1) cache lookups
- Semantically meaningful (similar questions → similar fingerprints)

For Seven Generations.
"""

import hashlib
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# Theme detection (same as resonance.py but lighter)
THEME_KEYWORDS = {
    'security': ['security', 'auth', 'permission', 'vulnerability', 'attack', 'protect', 'encrypt'],
    'performance': ['performance', 'speed', 'latency', 'throughput', 'fast', 'slow', 'optimize'],
    'reliability': ['reliable', 'stable', 'uptime', 'failover', 'redundant', 'backup', 'recovery'],
    'sustainability': ['sustainable', 'long-term', 'maintain', 'future', 'generation', 'lasting'],
    'integration': ['integrate', 'connect', 'api', 'interface', 'compatible', 'bridge'],
    'risk': ['risk', 'danger', 'concern', 'warning', 'caution', 'careful', 'threat'],
    'opportunity': ['opportunity', 'potential', 'growth', 'improve', 'enhance', 'better'],
    'cost': ['cost', 'expensive', 'budget', 'resource', 'investment', 'afford'],
    'data': ['data', 'database', 'storage', 'query', 'cache', 'memory'],
    'user': ['user', 'customer', 'client', 'experience', 'interface', 'usability'],
}

# Tone detection
TONE_KEYWORDS = {
    'confident': ['definitely', 'certainly', 'clearly', 'must', 'will', 'absolutely'],
    'cautious': ['maybe', 'perhaps', 'might', 'could', 'possibly', 'uncertain'],
    'positive': ['good', 'great', 'excellent', 'benefit', 'advantage', 'success'],
    'negative': ['bad', 'poor', 'problem', 'issue', 'risk', 'failure', 'concern'],
}

# Specialist type codes
SPECIALIST_CODES = {
    'architect': 0b00000001,
    'developer': 0b00000010,
    'operations': 0b00000100,
    'security': 0b00001000,
    'database': 0b00010000,
    'frontend': 0b00100000,
    'testing': 0b01000000,
    'general': 0b10000000,
}


@dataclass
class ResonanceFingerprint:
    """Compact fingerprint for resonance pattern matching"""
    theme_hash: int          # 32-bit hash of detected themes
    tone_vector: Tuple[int, int, int, int]  # (confident, cautious, positive, negative)
    specialist_mask: int     # 8-bit mask of specialist types
    confidence_band: int     # 1=low, 2=medium, 3=high
    question_hash: int       # 32-bit semantic hash of question

    def to_combined_hash(self) -> int:
        """Generate single 64-bit hash for cache lookup"""
        # Combine all components into single hash
        combined = (
            (self.theme_hash & 0xFFFF) << 48 |
            (self.tone_vector[0] & 0xF) << 44 |
            (self.tone_vector[1] & 0xF) << 40 |
            (self.tone_vector[2] & 0xF) << 36 |
            (self.tone_vector[3] & 0xF) << 32 |
            (self.specialist_mask & 0xFF) << 24 |
            (self.confidence_band & 0x3) << 22 |
            (self.question_hash & 0x3FFFFF)
        )
        return combined

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'theme_hash': self.theme_hash,
            'tone_vector': list(self.tone_vector),
            'specialist_mask': self.specialist_mask,
            'confidence_band': self.confidence_band,
            'question_hash': self.question_hash,
            'combined_hash': self.to_combined_hash()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ResonanceFingerprint':
        """Reconstruct from dictionary"""
        return cls(
            theme_hash=data['theme_hash'],
            tone_vector=tuple(data['tone_vector']),
            specialist_mask=data['specialist_mask'],
            confidence_band=data['confidence_band'],
            question_hash=data['question_hash']
        )


class FingerprintGenerator:
    """
    Generates resonance fingerprints from deliberation context

    Usage:
        generator = FingerprintGenerator()
        fingerprint = generator.generate(
            question="Should we add caching?",
            specialists=['architect', 'developer'],
            avg_confidence=0.85
        )
        cache_key = fingerprint.to_combined_hash()
    """

    def __init__(self):
        # Pre-compile regex patterns for speed
        self.theme_patterns = {
            theme: re.compile(r'\b(' + '|'.join(words) + r')\b', re.IGNORECASE)
            for theme, words in THEME_KEYWORDS.items()
        }
        self.tone_patterns = {
            tone: re.compile(r'\b(' + '|'.join(words) + r')\b', re.IGNORECASE)
            for tone, words in TONE_KEYWORDS.items()
        }

    def generate(self,
                 question: str,
                 specialists: List[str] = None,
                 specialist_responses: List[str] = None,
                 avg_confidence: float = 0.5) -> ResonanceFingerprint:
        """
        Generate fingerprint from deliberation context

        Args:
            question: The deliberation question
            specialists: List of specialist names involved
            specialist_responses: List of response texts (for theme/tone detection)
            avg_confidence: Average confidence across specialists

        Returns:
            ResonanceFingerprint for cache lookup
        """
        # Combine all text for analysis
        all_text = question
        if specialist_responses:
            all_text += ' ' + ' '.join(specialist_responses)

        # Detect themes
        themes = self._detect_themes(all_text)
        theme_hash = self._hash_themes(themes)

        # Detect tones
        tone_vector = self._detect_tones(all_text)

        # Build specialist mask
        specialist_mask = self._build_specialist_mask(specialists or [])

        # Confidence band
        confidence_band = self._confidence_to_band(avg_confidence)

        # Question semantic hash
        question_hash = self._semantic_hash(question)

        return ResonanceFingerprint(
            theme_hash=theme_hash,
            tone_vector=tone_vector,
            specialist_mask=specialist_mask,
            confidence_band=confidence_band,
            question_hash=question_hash
        )

    def _detect_themes(self, text: str) -> List[str]:
        """Detect which themes are present in text"""
        themes = []
        for theme, pattern in self.theme_patterns.items():
            if pattern.search(text):
                themes.append(theme)
        return sorted(themes)  # Sort for consistent hashing

    def _hash_themes(self, themes: List[str]) -> int:
        """Hash theme list to 32-bit int"""
        if not themes:
            return 0
        theme_str = ','.join(themes)
        return int(hashlib.md5(theme_str.encode()).hexdigest()[:8], 16)

    def _detect_tones(self, text: str) -> Tuple[int, int, int, int]:
        """Detect tone intensities (0-15 scale each)"""
        tones = []
        for tone in ['confident', 'cautious', 'positive', 'negative']:
            pattern = self.tone_patterns[tone]
            matches = len(pattern.findall(text))
            # Cap at 15, scale by text length
            intensity = min(15, int(matches * 100 / max(len(text.split()), 1)))
            tones.append(intensity)
        return tuple(tones)

    def _build_specialist_mask(self, specialists: List[str]) -> int:
        """Build bitmask of specialist types"""
        mask = 0
        for specialist in specialists:
            # Try to match specialist name to known codes
            specialist_lower = specialist.lower()
            for name, code in SPECIALIST_CODES.items():
                if name in specialist_lower:
                    mask |= code
                    break
            else:
                # Unknown specialist - mark as general
                mask |= SPECIALIST_CODES['general']
        return mask

    def _confidence_to_band(self, confidence: float) -> int:
        """Convert confidence to band (1=low, 2=medium, 3=high)"""
        if confidence < 0.5:
            return 1
        elif confidence < 0.8:
            return 2
        else:
            return 3

    def _semantic_hash(self, question: str) -> int:
        """Generate semantic hash of question (22 bits)"""
        # Normalize: lowercase, remove punctuation, sort words
        normalized = re.sub(r'[^\w\s]', '', question.lower())
        words = sorted(set(normalized.split()))

        # Remove common stop words for semantic similarity
        stop_words = {'the', 'a', 'an', 'is', 'are', 'we', 'should', 'can', 'do', 'to', 'for', 'of', 'in', 'on'}
        words = [w for w in words if w not in stop_words and len(w) > 2]

        # Hash remaining words
        word_str = ' '.join(words)
        full_hash = int(hashlib.md5(word_str.encode()).hexdigest()[:6], 16)
        return full_hash & 0x3FFFFF  # 22 bits

    def similarity(self, fp1: ResonanceFingerprint, fp2: ResonanceFingerprint) -> float:
        """
        Calculate similarity between two fingerprints (0-1)

        Used for fuzzy matching when exact hash doesn't match
        """
        score = 0.0

        # Theme similarity (most important)
        if fp1.theme_hash == fp2.theme_hash:
            score += 0.4

        # Tone vector similarity (cosine-like)
        tone_diff = sum(abs(a - b) for a, b in zip(fp1.tone_vector, fp2.tone_vector))
        tone_sim = 1.0 - (tone_diff / 60.0)  # Max diff is 60 (4 * 15)
        score += 0.2 * tone_sim

        # Specialist overlap
        overlap = bin(fp1.specialist_mask & fp2.specialist_mask).count('1')
        total = bin(fp1.specialist_mask | fp2.specialist_mask).count('1')
        if total > 0:
            score += 0.2 * (overlap / total)

        # Confidence band match
        if fp1.confidence_band == fp2.confidence_band:
            score += 0.1

        # Question hash (exact match bonus)
        if fp1.question_hash == fp2.question_hash:
            score += 0.1

        return min(1.0, score)


# Convenience function
def generate_fingerprint(question: str,
                        specialists: List[str] = None,
                        responses: List[str] = None,
                        confidence: float = 0.5) -> ResonanceFingerprint:
    """Quick fingerprint generation"""
    generator = FingerprintGenerator()
    return generator.generate(question, specialists, responses, confidence)


if __name__ == '__main__':
    # Test fingerprint generation
    gen = FingerprintGenerator()

    fp1 = gen.generate(
        question="Should we add caching to improve API performance?",
        specialists=['architect', 'developer', 'operations'],
        specialist_responses=[
            "Redis would give us good performance",
            "Caching is essential for speed",
            "We need to monitor cache hit rates"
        ],
        avg_confidence=0.85
    )

    print("Fingerprint 1:")
    print(f"  Theme hash: {fp1.theme_hash}")
    print(f"  Tone vector: {fp1.tone_vector}")
    print(f"  Specialist mask: {bin(fp1.specialist_mask)}")
    print(f"  Confidence band: {fp1.confidence_band}")
    print(f"  Question hash: {fp1.question_hash}")
    print(f"  Combined hash: {fp1.to_combined_hash()}")

    # Test similar question
    fp2 = gen.generate(
        question="Should we implement caching for better API speed?",
        specialists=['architect', 'developer'],
        avg_confidence=0.82
    )

    print(f"\nSimilarity to similar question: {gen.similarity(fp1, fp2):.2f}")

    # Test different question
    fp3 = gen.generate(
        question="Should we add authentication to the admin panel?",
        specialists=['security', 'developer'],
        avg_confidence=0.90
    )

    print(f"Similarity to different question: {gen.similarity(fp1, fp3):.2f}")
```

---

## TASK 3: Create Resonance Memory Manager

**File:** `/ganuda/lib/metacognition/resonance_memory.py`

```python
#!/usr/bin/env python3
"""
Resonance Memory Manager - Efficient pattern storage and retrieval

Implements the lookup-first architecture:
1. Hot cache (in-memory) → ~0.1ms
2. Thermal memory (PostgreSQL) → ~5ms
3. Full analysis (fallback) → ~500ms

Patterns are stored selectively - only resonant patterns worth remembering.

For Seven Generations.
"""

import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from metacognition.resonance_fingerprint import (
    ResonanceFingerprint,
    FingerprintGenerator,
    generate_fingerprint
)


@dataclass
class CachedResonance:
    """A cached resonance pattern"""
    fingerprint_hash: int
    pattern_type: str        # 'harmony', 'creative_tension', 'anti_pattern'
    resonance_score: float
    resonance_summary: Dict
    outcome: str             # 'positive', 'negative', 'unknown'
    coyote_insight: str
    access_count: int
    temperature: float

    @property
    def is_anti_pattern(self) -> bool:
        return self.pattern_type == 'anti_pattern' or self.outcome == 'negative'


@dataclass
class ResonanceLock:
    """Returned when a known-good pattern is recognized"""
    cached_pattern: CachedResonance
    confidence_boost: float
    skip_analysis: bool
    note: str


@dataclass
class AntiPatternWarning:
    """Returned when a known-bad pattern is detected"""
    cached_pattern: CachedResonance
    warning: str
    suggestion: str
    confidence_penalty: float


class ResonanceMemoryManager:
    """
    Manages resonance pattern storage and retrieval

    Usage:
        manager = ResonanceMemoryManager(db_config)

        # Before deliberation - check for cached pattern
        fingerprint = generate_fingerprint(question, specialists)
        cached = manager.lookup(fingerprint)

        if isinstance(cached, ResonanceLock):
            return cached.cached_pattern.resonance_summary  # Skip analysis!
        elif isinstance(cached, AntiPatternWarning):
            logger.warning(cached.warning)

        # After deliberation - store if resonant
        if resonance_result['score'] > 0.7:
            manager.store(fingerprint, resonance_result, deliberation_id)
    """

    # Configuration
    HOT_CACHE_SIZE = 100           # Max patterns in memory
    HOT_CACHE_TTL = 3600 * 24      # 24 hours
    SIMILARITY_THRESHOLD = 0.85    # For fuzzy matching
    STORE_THRESHOLD = 0.7          # Min resonance score to store

    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.fingerprint_gen = FingerprintGenerator()

        # In-memory hot cache: {fingerprint_hash: CachedResonance}
        self._hot_cache: Dict[int, CachedResonance] = {}
        self._hot_cache_order: List[int] = []  # LRU order

        # Load hot cache from database on init
        self._load_hot_cache()

    def _get_conn(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.db_config.get('host', 'localhost'),
            database=self.db_config.get('database', 'zammad_production'),
            user=self.db_config.get('user', 'claude'),
            password=self.db_config.get('password', '')
        )

    def _load_hot_cache(self):
        """Load hottest patterns into memory cache"""
        try:
            with self._get_conn() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Load top patterns by temperature and access count
                    cur.execute("""
                        SELECT fingerprint_hash, pattern_type, resonance_score,
                               resonance_data, outcome, temperature, access_count
                        FROM resonance_patterns
                        WHERE temperature > 50
                        ORDER BY temperature DESC, access_count DESC
                        LIMIT %s
                    """, (self.HOT_CACHE_SIZE,))

                    for row in cur.fetchall():
                        cached = CachedResonance(
                            fingerprint_hash=row['fingerprint_hash'],
                            pattern_type=row['pattern_type'],
                            resonance_score=row['resonance_score'],
                            resonance_summary=row['resonance_data'] or {},
                            outcome=row['outcome'],
                            coyote_insight=row.get('coyote_insight', ''),
                            access_count=row['access_count'],
                            temperature=row['temperature']
                        )
                        self._hot_cache[row['fingerprint_hash']] = cached
                        self._hot_cache_order.append(row['fingerprint_hash'])

                    print(f"Loaded {len(self._hot_cache)} patterns into hot cache")
        except Exception as e:
            print(f"Warning: Could not load hot cache: {e}")

    def lookup(self, fingerprint: ResonanceFingerprint) -> Optional[ResonanceLock | AntiPatternWarning | CachedResonance]:
        """
        Look up a fingerprint in cache/memory

        Returns:
            - ResonanceLock: Known good pattern, skip analysis
            - AntiPatternWarning: Known bad pattern, proceed with caution
            - CachedResonance: Pattern found but needs fresh analysis
            - None: No match found
        """
        fp_hash = fingerprint.to_combined_hash()

        # 1. Check hot cache (O(1))
        if fp_hash in self._hot_cache:
            cached = self._hot_cache[fp_hash]
            self._record_cache_hit(fp_hash, 'hot')
            return self._evaluate_cached(cached)

        # 2. Check thermal memory (indexed query)
        cached = self._lookup_thermal(fingerprint)
        if cached:
            # Warm the cache
            self._add_to_hot_cache(cached)
            return self._evaluate_cached(cached)

        # 3. Try fuzzy match on hot cache
        best_match, similarity = self._fuzzy_match(fingerprint)
        if best_match and similarity > self.SIMILARITY_THRESHOLD:
            self._record_cache_hit(best_match.fingerprint_hash, 'fuzzy')
            return self._evaluate_cached(best_match, fuzzy=True, similarity=similarity)

        return None

    def _lookup_thermal(self, fingerprint: ResonanceFingerprint) -> Optional[CachedResonance]:
        """Query thermal memory for fingerprint"""
        fp_hash = fingerprint.to_combined_hash()

        try:
            with self._get_conn() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT fingerprint_hash, pattern_type, resonance_score,
                               resonance_data, outcome, coyote_insight,
                               temperature, access_count
                        FROM resonance_patterns
                        WHERE fingerprint_hash = %s
                    """, (fp_hash,))

                    row = cur.fetchone()
                    if row:
                        # Update access stats
                        cur.execute("""
                            UPDATE resonance_patterns
                            SET access_count = access_count + 1,
                                last_accessed = NOW(),
                                temperature = LEAST(temperature + 2, 100)
                            WHERE fingerprint_hash = %s
                        """, (fp_hash,))
                        conn.commit()

                        return CachedResonance(
                            fingerprint_hash=row['fingerprint_hash'],
                            pattern_type=row['pattern_type'],
                            resonance_score=row['resonance_score'],
                            resonance_summary=row['resonance_data'] or {},
                            outcome=row['outcome'],
                            coyote_insight=row['coyote_insight'] or '',
                            access_count=row['access_count'] + 1,
                            temperature=min(row['temperature'] + 2, 100)
                        )
        except Exception as e:
            print(f"Thermal lookup error: {e}")

        return None

    def _fuzzy_match(self, fingerprint: ResonanceFingerprint) -> Tuple[Optional[CachedResonance], float]:
        """Find best fuzzy match in hot cache"""
        best_match = None
        best_similarity = 0.0

        for fp_hash, cached in self._hot_cache.items():
            # Reconstruct fingerprint from hash (approximate)
            # For now, just compare theme and confidence bands
            similarity = 0.5  # Base similarity for being in cache

            # This is a simplified check - full implementation would
            # store fingerprint components in cache
            if cached.pattern_type == 'harmony':
                similarity += 0.2

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = cached

        return best_match, best_similarity

    def _evaluate_cached(self,
                        cached: CachedResonance,
                        fuzzy: bool = False,
                        similarity: float = 1.0) -> ResonanceLock | AntiPatternWarning | CachedResonance:
        """Evaluate cached pattern and return appropriate response"""

        # Anti-pattern detection
        if cached.is_anti_pattern:
            return AntiPatternWarning(
                cached_pattern=cached,
                warning=f"This pattern led to {cached.outcome} outcome previously",
                suggestion="Consider alternative approaches",
                confidence_penalty=-0.15
            )

        # High-confidence resonance lock
        if (cached.resonance_score > 0.8 and
            cached.outcome == 'positive' and
            cached.access_count > 3 and
            not fuzzy):
            return ResonanceLock(
                cached_pattern=cached,
                confidence_boost=0.1,
                skip_analysis=True,
                note=f"Pattern recognized - known good resonance (accessed {cached.access_count}x)"
            )

        # Return pattern but still do analysis
        return cached

    def _add_to_hot_cache(self, cached: CachedResonance):
        """Add pattern to hot cache with LRU eviction"""
        fp_hash = cached.fingerprint_hash

        if fp_hash in self._hot_cache:
            # Move to end (most recent)
            self._hot_cache_order.remove(fp_hash)
            self._hot_cache_order.append(fp_hash)
            return

        # Evict oldest if at capacity
        while len(self._hot_cache) >= self.HOT_CACHE_SIZE:
            oldest = self._hot_cache_order.pop(0)
            del self._hot_cache[oldest]

        self._hot_cache[fp_hash] = cached
        self._hot_cache_order.append(fp_hash)

    def _record_cache_hit(self, fp_hash: int, cache_type: str):
        """Record cache hit for analytics"""
        # Could write to metrics table here
        pass

    def store(self,
              fingerprint: ResonanceFingerprint,
              resonance_result: Dict,
              deliberation_id: str,
              question: str = '',
              domain: str = '',
              coyote_insight: str = '',
              source_node: str = 'unknown') -> bool:
        """
        Store a resonance pattern in memory

        Only stores if pattern is worth remembering (score > threshold)

        Args:
            fingerprint: The pattern fingerprint
            resonance_result: Full resonance analysis result
            deliberation_id: ID of the deliberation
            question: Original question
            domain: Question domain
            coyote_insight: Coyote's observation
            source_node: Which node created this

        Returns:
            True if stored, False if not worth storing
        """
        score = resonance_result.get('score', 0)

        # Only store resonant patterns
        if score < self.STORE_THRESHOLD:
            return False

        # Determine pattern type
        if score > 0.8:
            pattern_type = 'harmony'
        elif resonance_result.get('creative_tensions'):
            pattern_type = 'creative_tension'
        else:
            pattern_type = 'mixed'

        fp_hash = fingerprint.to_combined_hash()
        fp_dict = fingerprint.to_dict()

        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO resonance_patterns (
                            fingerprint_hash, theme_hash, tone_vector,
                            specialist_mask, confidence_band, question_hash,
                            pattern_type, resonance_score, resonance_data,
                            original_question, question_domain,
                            coyote_insight, source_node, deliberation_id,
                            temperature
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (fingerprint_hash) DO UPDATE SET
                            access_count = resonance_patterns.access_count + 1,
                            last_accessed = NOW(),
                            temperature = LEAST(resonance_patterns.temperature + 5, 100)
                    """, (
                        fp_hash,
                        fp_dict['theme_hash'],
                        fp_dict['tone_vector'],
                        fp_dict['specialist_mask'],
                        fp_dict['confidence_band'],
                        fp_dict['question_hash'],
                        pattern_type,
                        score,
                        json.dumps(resonance_result),
                        question[:500],
                        domain,
                        coyote_insight[:500] if coyote_insight else None,
                        source_node,
                        deliberation_id,
                        75.0  # Initial temperature
                    ))
                    conn.commit()

            # Add to hot cache
            cached = CachedResonance(
                fingerprint_hash=fp_hash,
                pattern_type=pattern_type,
                resonance_score=score,
                resonance_summary=resonance_result,
                outcome='unknown',
                coyote_insight=coyote_insight or '',
                access_count=1,
                temperature=75.0
            )
            self._add_to_hot_cache(cached)

            return True

        except Exception as e:
            print(f"Error storing resonance pattern: {e}")
            return False

    def record_outcome(self,
                       fingerprint: ResonanceFingerprint,
                       outcome: str,
                       notes: str = '') -> bool:
        """
        Record the outcome of a deliberation pattern

        Call this when you know if a decision was good or bad.

        Args:
            fingerprint: The pattern fingerprint
            outcome: 'positive' or 'negative'
            notes: Optional notes about why

        Returns:
            True if recorded
        """
        fp_hash = fingerprint.to_combined_hash()

        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    # Update outcome
                    cur.execute("""
                        UPDATE resonance_patterns
                        SET outcome = %s,
                            outcome_notes = %s,
                            outcome_recorded_at = NOW(),
                            pattern_type = CASE
                                WHEN %s = 'negative' THEN 'anti_pattern'
                                ELSE pattern_type
                            END,
                            temperature = CASE
                                WHEN %s = 'negative' THEN LEAST(temperature + 10, 100)
                                ELSE temperature
                            END
                        WHERE fingerprint_hash = %s
                    """, (outcome, notes, outcome, outcome, fp_hash))
                    conn.commit()

                    # Update hot cache if present
                    if fp_hash in self._hot_cache:
                        self._hot_cache[fp_hash].outcome = outcome
                        if outcome == 'negative':
                            self._hot_cache[fp_hash].pattern_type = 'anti_pattern'

                    return True
        except Exception as e:
            print(f"Error recording outcome: {e}")
            return False

    def decay_temperatures(self):
        """Run daily temperature decay on all patterns"""
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE resonance_patterns
                        SET temperature = GREATEST(
                            temperature * decay_rate,
                            min_temperature
                        )
                        WHERE temperature > min_temperature
                    """)
                    affected = cur.rowcount
                    conn.commit()
                    print(f"Decayed temperature on {affected} patterns")
        except Exception as e:
            print(f"Error decaying temperatures: {e}")

    def get_stats(self) -> Dict:
        """Get resonance memory statistics"""
        try:
            with self._get_conn() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT
                            COUNT(*) as total_patterns,
                            COUNT(*) FILTER (WHERE pattern_type = 'harmony') as harmony_count,
                            COUNT(*) FILTER (WHERE pattern_type = 'anti_pattern') as anti_patterns,
                            COUNT(*) FILTER (WHERE outcome = 'positive') as positive_outcomes,
                            COUNT(*) FILTER (WHERE outcome = 'negative') as negative_outcomes,
                            AVG(temperature) as avg_temperature,
                            AVG(access_count) as avg_accesses
                        FROM resonance_patterns
                    """)
                    stats = dict(cur.fetchone())
                    stats['hot_cache_size'] = len(self._hot_cache)
                    return stats
        except Exception as e:
            return {'error': str(e)}


if __name__ == '__main__':
    # Test the manager
    db_config = {
        'host': '192.168.132.222',
        'database': 'zammad_production',
        'user': 'claude',
        'password': 'jawaseatlasers2'
    }

    manager = ResonanceMemoryManager(db_config)

    # Generate test fingerprint
    fp = generate_fingerprint(
        question="Should we add caching to the API?",
        specialists=['architect', 'developer'],
        confidence=0.85
    )

    print(f"Generated fingerprint hash: {fp.to_combined_hash()}")

    # Test lookup (should be None first time)
    result = manager.lookup(fp)
    print(f"Lookup result: {result}")

    # Test store
    resonance_result = {
        'score': 0.85,
        'level': 'harmony',
        'harmonic_themes': ['performance', 'reliability'],
        'creative_tensions': []
    }

    stored = manager.store(
        fingerprint=fp,
        resonance_result=resonance_result,
        deliberation_id='test-001',
        question="Should we add caching to the API?",
        domain='architecture',
        source_node='test'
    )
    print(f"Stored: {stored}")

    # Test lookup again (should hit)
    result = manager.lookup(fp)
    print(f"Lookup after store: {type(result).__name__}")

    # Stats
    print(f"Stats: {manager.get_stats()}")
```

---

## TASK 4: Integrate with MetacognitiveCouncil

**File:** `/ganuda/lib/metacognition/council_integration.py`

**Add these changes:**

### 4a. Add import at top of file:

```python
from metacognition.resonance_memory import (
    ResonanceMemoryManager,
    ResonanceLock,
    AntiPatternWarning,
    generate_fingerprint
)
```

### 4b. Add to `__init__` method:

```python
# Initialize resonance memory manager
self.resonance_memory = ResonanceMemoryManager(db_config)
```

### 4c. Add new method for lookup-first flow:

```python
def check_resonance_memory(self, question: str, specialists: List[str] = None) -> Optional[Dict]:
    """
    Check resonance memory before starting deliberation

    Returns cached resonance if found, None if new deliberation needed.

    Usage:
        cached = council.check_resonance_memory(question, specialists)
        if cached and cached.get('skip_analysis'):
            return cached['resonance']  # Skip full deliberation!
        else:
            # Proceed with normal deliberation
            delib_id = council.start_deliberation(question)
            ...
    """
    fingerprint = generate_fingerprint(
        question=question,
        specialists=specialists or []
    )

    result = self.resonance_memory.lookup(fingerprint)

    if isinstance(result, ResonanceLock):
        return {
            'skip_analysis': True,
            'resonance': result.cached_pattern.resonance_summary,
            'confidence_boost': result.confidence_boost,
            'note': result.note,
            'pattern_type': result.cached_pattern.pattern_type,
            'cached': True
        }

    elif isinstance(result, AntiPatternWarning):
        return {
            'skip_analysis': False,
            'warning': result.warning,
            'suggestion': result.suggestion,
            'confidence_penalty': result.confidence_penalty,
            'anti_pattern': True
        }

    elif result:  # CachedResonance but needs fresh analysis
        return {
            'skip_analysis': False,
            'hint': result.resonance_summary,
            'previous_outcome': result.outcome,
            'cached': True
        }

    return None  # No cache hit
```

### 4d. Modify `complete_deliberation` to store resonant patterns:

Add at end of method, before return:

```python
# Store resonant patterns in memory
if resonance_result.get('score', 0) > 0.7:
    fingerprint = generate_fingerprint(
        question=self.tracer.query,
        specialists=[s.specialist for s in self.tracer.steps],
        responses=[s.thought for s in self.tracer.steps],
        confidence=calibrated_confidence
    )

    self.resonance_memory.store(
        fingerprint=fingerprint,
        resonance_result=resonance_result,
        deliberation_id=self.tracer.session_id,
        question=self.tracer.query,
        coyote_insight=coyote_observation.get('says', ''),
        source_node='redfin'  # Or get from config
    )
```

---

## TASK 5: Create Temperature Decay Cron Job

**File:** `/ganuda/scripts/resonance_decay_cron.py`

```python
#!/usr/bin/env python3
"""Daily resonance temperature decay - run via cron"""

import sys
sys.path.insert(0, '/ganuda/lib')

from metacognition.resonance_memory import ResonanceMemoryManager

db_config = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

if __name__ == '__main__':
    manager = ResonanceMemoryManager(db_config)
    manager.decay_temperatures()
    print("Resonance temperature decay complete")
```

**Add to crontab on redfin:**
```bash
# Run daily at 3 AM
0 3 * * * /usr/bin/python3 /ganuda/scripts/resonance_decay_cron.py >> /ganuda/logs/resonance_decay.log 2>&1
```

---

## SUCCESS CRITERIA

1. **Database tables created** - `resonance_patterns` and `resonance_hot_cache` exist
2. **Fingerprint generation works** - Same question → same fingerprint hash
3. **Hot cache loads** - Manager loads top patterns on init
4. **Lookup-first flow** - `check_resonance_memory()` returns cached patterns
5. **Storage selective** - Only patterns with score > 0.7 stored
6. **ResonanceLock works** - High-confidence patterns skip analysis
7. **AntiPatternWarning works** - Bad patterns trigger warnings
8. **Temperature decay runs** - Cron job decays cold patterns

---

## RESOURCE CONSUMPTION TARGETS

| Scenario | Target Latency |
|----------|---------------|
| Hot cache hit | < 1ms |
| Thermal memory hit | < 10ms |
| Cache miss (full analysis) | < 600ms |
| Pattern storage | < 50ms |

After 100 deliberations, expect **60-70% cache hit rate**.

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*
*"Once it hits the right resonance, it should be optimal"*
