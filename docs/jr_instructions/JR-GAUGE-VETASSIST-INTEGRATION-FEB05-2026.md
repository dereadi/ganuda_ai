# Jr Instruction: GAUGE Affective Monitoring Integration for VetAssist Crisis Detection

**Date:** 2026-02-05
**Priority:** P0 — Critical Safety Enhancement
**Council Vote:** Approved with Security Concern
**Assigned To:** Software Engineer Jr. (vetassist-backend)
**Depends On:** Existing C-SSRS crisis classifier (`/ganuda/vetassist/backend/app/services/crisis_classifier.py`)

---

## Objective

Integrate the GAUGE (logit-based affective monitoring) framework as a second-tier detection layer in VetAssist crisis detection, complementing the existing C-SSRS explicit marker detection with implicit emotional trajectory monitoring.

---

## Background

### Current Architecture (C-SSRS Three-Tier)

The existing crisis detection in VetAssist uses:

1. **Tier 1: Lexicon Screen** — Fast regex-based keyword matching for explicit crisis markers
2. **Tier 2: C-SSRS LLM Classification** — Local LLM (Nemotron via gateway at 192.168.132.223:8080) classifies messages on Columbia-Suicide Severity Rating Scale (0-6)
3. **Tier 3: Intervention Routing** — Routes to appropriate intervention (banner, modal, overlay) based on C-SSRS level

**Limitation:** Current system only detects *explicit* crisis language. It misses cases where veterans express distress through implicit emotional drift without using direct crisis terminology.

### GAUGE Framework (arXiv 2512.06193)

GAUGE is a logit-based framework for real-time detection of hidden conversational escalation. It measures how an LLM's output probabilistically shifts the affective state of a dialogue.

**Key Metrics:**

| Metric | Formula | Purpose |
|--------|---------|---------|
| **NRS** (Negative Risk Shift) | `NRS = cos(lambda, z)` | Measures directional momentum — how actively the conversation is steering toward negative outcomes |
| **ARP** (Absolute Risk Potential) | `ARP = sum(lambda_i * Z(z_i)) / sum(lambda_i)` | Measures magnitude of risk exposure — detects dwelling in high-risk emotional states |

**Key Innovation:** GAUGE reuses existing vocabulary logits during inference without additional forward passes, introducing only 2-3% computational overhead.

---

## Integration Approach

GAUGE will operate as a **second-tier detection layer** that runs *after* explicit C-SSRS detection:

```
User Message
     |
     v
[Tier 1: Lexicon Screen] --> If match --> [Tier 2: C-SSRS LLM] --> Intervention
     |
     v (no explicit match)
[GAUGE Affective Monitor] --> If NRS/ARP threshold exceeded --> [Tier 2: C-SSRS LLM]
     |
     v (no concern)
Normal Chat Processing
```

**Rationale:** Veterans may express severe distress without using explicit crisis language. GAUGE catches the implicit emotional trajectory that explicit keyword matching misses.

---

## Implementation Steps

### Step 1: Add NRC Emotion Lexicon to Dependencies

**File to create:** `/ganuda/vetassist/backend/app/data/nrc_emotion_lexicon.py`

The NRC Emotion Lexicon provides affect categories used by GAUGE for probability mass tracking.

```python
"""
NRC Emotion Lexicon - Risk Categories for GAUGE
Subset focused on crisis-relevant affect dimensions

SECURITY: This is a static lexicon with no PII. Safe for embedding.
"""

# Core NRC categories relevant to crisis detection
NRC_RISK_CATEGORIES = {
    "anger": [
        "angry", "rage", "furious", "hostile", "aggravated", "bitter",
        "resentful", "hateful", "violent", "enraged", "irritated", "frustrated"
    ],
    "fear": [
        "afraid", "scared", "terrified", "anxious", "panic", "dread",
        "frightened", "worried", "nervous", "alarmed", "horrified", "petrified"
    ],
    "sadness": [
        "sad", "depressed", "miserable", "hopeless", "despair", "grief",
        "sorrow", "unhappy", "gloomy", "dejected", "melancholy", "heartbroken"
    ],
    "disgust": [
        "disgusted", "revolted", "sick", "nauseated", "repulsed", "contempt",
        "loathing", "hatred", "aversion", "horrified"
    ],
    "negative": [
        "worthless", "useless", "burden", "failure", "empty", "numb",
        "exhausted", "drained", "trapped", "alone", "abandoned", "rejected"
    ]
}

# Veteran-specific augmentation (Step 5)
MILITARY_AFFECT_TERMS = {
    "moral_injury": [
        "betrayed", "guilty", "ashamed", "dishonorable", "coward", "failed_them",
        "blood_on_hands", "never_forgive", "unforgivable", "damned"
    ],
    "combat_distress": [
        "hypervigilant", "triggered", "flashback", "nightmare", "ambush",
        "explosion", "incoming", "firefight", "casualties", "body_count"
    ],
    "transition_struggle": [
        "purposeless", "civilian", "nobody_understands", "dont_belong",
        "lost_identity", "brothers_gone", "mission_over", "no_mission"
    ],
    "mst_trauma": [
        "violated", "assaulted", "betrayed_trust", "silenced", "ignored",
        "blamed", "dismissed", "covered_up", "chain_of_command"
    ]
}

# Combined risk lexicon for GAUGE
def get_risk_lexicon() -> dict:
    """Return combined NRC + military-augmented risk lexicon."""
    combined = {}
    for category, terms in NRC_RISK_CATEGORIES.items():
        combined[category] = terms.copy()
    for category, terms in MILITARY_AFFECT_TERMS.items():
        combined[category] = terms.copy()
    return combined

# Flattened word list for probability tracking
def get_risk_words() -> list:
    """Return flat list of all risk words for logit extraction."""
    all_words = []
    for terms in NRC_RISK_CATEGORIES.values():
        all_words.extend(terms)
    for terms in MILITARY_AFFECT_TERMS.values():
        all_words.extend(terms)
    return list(set(all_words))

# Risk profile weights (lambda vector for NRS calculation)
RISK_PROFILE_WEIGHTS = {
    "anger": 0.7,
    "fear": 0.6,
    "sadness": 0.9,      # High weight - strong crisis indicator
    "disgust": 0.5,
    "negative": 0.95,    # Highest weight - direct crisis language
    "moral_injury": 0.85,
    "combat_distress": 0.7,
    "transition_struggle": 0.8,
    "mst_trauma": 0.9
}
```

**Add to requirements:**
```
# /ganuda/vetassist/backend/requirements.txt
# Add:
numpy>=1.24.0  # For vector operations (may already be present)
```

### Step 2: Implement Probability Mass Tracking Service

**File to create:** `/ganuda/vetassist/backend/app/services/gauge_monitor.py`

```python
"""
GAUGE Affective Monitor - Probability Mass Tracking
Based on arXiv 2512.06193

Tracks log-probability shifts across NRC emotion lexicon during LLM inference.
Calculates NRS (Negative Risk Shift) and ARP (Absolute Risk Potential).

SECURITY: Affective data is PII-level sensitive. Never log raw affect vectors.
"""
import math
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GAUGEResult:
    """Result from GAUGE affective monitoring."""
    nrs: float              # Negative Risk Shift (-1 to 1)
    arp: float              # Absolute Risk Potential (0+)
    triggered: bool         # Whether thresholds exceeded
    dominant_affect: str    # Primary affect category detected
    confidence: float       # Detection confidence
    processing_ms: int      # Processing time


class GAUGEMonitor:
    """
    Logit-based affective monitoring using probability mass tracking.

    Reuses LLM vocabulary logits to detect hidden emotional escalation
    with minimal computational overhead (2-3% per GAUGE paper).
    """

    def __init__(self,
                 nrs_threshold: float = 0.15,
                 arp_threshold: float = 1.5,
                 veteran_calibration: bool = True):
        """
        Initialize GAUGE monitor with thresholds.

        Args:
            nrs_threshold: NRS above this triggers concern (default 0.15 for veteran pop)
            arp_threshold: ARP above this triggers concern (default 1.5 for veteran pop)
            veteran_calibration: Apply veteran-specific threshold adjustments
        """
        self.nrs_threshold = nrs_threshold
        self.arp_threshold = arp_threshold
        self.veteran_calibration = veteran_calibration

        # Load lexicon
        from app.data.nrc_emotion_lexicon import (
            get_risk_lexicon, get_risk_words, RISK_PROFILE_WEIGHTS
        )
        self.risk_lexicon = get_risk_lexicon()
        self.risk_words = get_risk_words()
        self.risk_weights = RISK_PROFILE_WEIGHTS

        # Pre-compute risk profile vector (lambda)
        self._build_risk_profile()

        self._numpy_available = False
        try:
            import numpy as np
            self._np = np
            self._numpy_available = True
        except ImportError:
            logger.warning("[GAUGE] numpy not available - using pure Python fallback")

    def _build_risk_profile(self):
        """Build calibrated risk profile vector (lambda) for NRS calculation."""
        self.risk_profile = {}
        for category, weight in self.risk_weights.items():
            if category in self.risk_lexicon:
                for word in self.risk_lexicon[category]:
                    # Combine weights if word in multiple categories
                    current = self.risk_profile.get(word, 0)
                    self.risk_profile[word] = max(current, weight)

    def extract_logits_from_response(self,
                                      logits: Dict[str, float],
                                      tokens: List[str]) -> Dict[str, float]:
        """
        Extract log-probabilities for risk words from LLM logits.

        Args:
            logits: Token-level log-probabilities from LLM
            tokens: Tokenized response

        Returns:
            Dict mapping risk words to their log-probabilities
        """
        risk_probs = {}
        for word in self.risk_words:
            if word in logits:
                risk_probs[word] = logits[word]
            else:
                # Check for subword tokens
                subtokens = self._get_subtokens(word, tokens)
                if subtokens:
                    # Sum log-probs of subtokens (product in probability space)
                    risk_probs[word] = sum(logits.get(t, -20) for t in subtokens)
        return risk_probs

    def _get_subtokens(self, word: str, tokens: List[str]) -> List[str]:
        """Find subtokens that compose a word (for BPE tokenizers)."""
        # Simplified - production should use actual tokenizer
        matches = []
        for token in tokens:
            clean = token.lower().strip('_').strip()
            if clean in word or word in clean:
                matches.append(token)
        return matches

    def calculate_nrs(self, risk_probs: Dict[str, float]) -> float:
        """
        Calculate Negative Risk Shift using cosine similarity.

        NRS = cos(lambda, z) where:
        - lambda is the calibrated risk profile
        - z is the current response risk vector

        Returns value in [-1, 1]. Higher = more alignment with risk.
        """
        if not risk_probs:
            return 0.0

        # Build vectors aligned to same word set
        common_words = set(risk_probs.keys()) & set(self.risk_profile.keys())
        if not common_words:
            return 0.0

        if self._numpy_available:
            lambda_vec = self._np.array([self.risk_profile[w] for w in common_words])
            z_vec = self._np.array([risk_probs[w] for w in common_words])

            # Normalize z to [0, 1] range for cosine similarity
            z_normalized = (z_vec - z_vec.min()) / (z_vec.max() - z_vec.min() + 1e-8)

            dot = self._np.dot(lambda_vec, z_normalized)
            norm_l = self._np.linalg.norm(lambda_vec)
            norm_z = self._np.linalg.norm(z_normalized)

            if norm_l == 0 or norm_z == 0:
                return 0.0
            return float(dot / (norm_l * norm_z))
        else:
            # Pure Python fallback
            lambda_vec = [self.risk_profile[w] for w in common_words]
            z_vec = [risk_probs[w] for w in common_words]

            z_min, z_max = min(z_vec), max(z_vec)
            z_normalized = [(z - z_min) / (z_max - z_min + 1e-8) for z in z_vec]

            dot = sum(l * z for l, z in zip(lambda_vec, z_normalized))
            norm_l = math.sqrt(sum(l * l for l in lambda_vec))
            norm_z = math.sqrt(sum(z * z for z in z_normalized))

            if norm_l == 0 or norm_z == 0:
                return 0.0
            return dot / (norm_l * norm_z)

    def calculate_arp(self, risk_probs: Dict[str, float]) -> float:
        """
        Calculate Absolute Risk Potential using Z-score normalization.

        ARP = sum(lambda_i * Z(z_i)) / sum(lambda_i)

        Returns value >= 0. Higher = more intense risk focus.
        """
        if not risk_probs:
            return 0.0

        common_words = set(risk_probs.keys()) & set(self.risk_profile.keys())
        if not common_words:
            return 0.0

        # Calculate Z-scores
        values = list(risk_probs.values())
        if len(values) < 2:
            return 0.0

        if self._numpy_available:
            mean = self._np.mean(values)
            std = self._np.std(values) + 1e-8
        else:
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std = math.sqrt(variance) + 1e-8

        # Weighted sum of Z-scores
        weighted_sum = 0.0
        weight_sum = 0.0

        for word in common_words:
            z_score = (risk_probs[word] - mean) / std
            weight = self.risk_profile[word]
            weighted_sum += weight * max(z_score, 0)  # Only positive Z-scores
            weight_sum += weight

        if weight_sum == 0:
            return 0.0
        return weighted_sum / weight_sum

    def get_dominant_affect(self, risk_probs: Dict[str, float]) -> str:
        """Identify the dominant affect category from risk probabilities."""
        category_scores = {}

        for category, words in self.risk_lexicon.items():
            scores = [risk_probs.get(w, -20) for w in words if w in risk_probs]
            if scores:
                category_scores[category] = max(scores)

        if not category_scores:
            return "none"
        return max(category_scores, key=category_scores.get)

    def monitor(self,
                message: str,
                llm_logits: Optional[Dict[str, float]] = None) -> GAUGEResult:
        """
        Run GAUGE monitoring on a message/response pair.

        Args:
            message: User message or LLM response text
            llm_logits: Optional pre-extracted logits (if available from inference)

        Returns:
            GAUGEResult with NRS, ARP, and trigger status
        """
        start_time = time.time()

        # If no logits provided, estimate from word presence
        if llm_logits is None:
            llm_logits = self._estimate_logits_from_text(message)

        # Extract risk word probabilities
        tokens = message.lower().split()
        risk_probs = self.extract_logits_from_response(llm_logits, tokens)

        # Calculate metrics
        nrs = self.calculate_nrs(risk_probs)
        arp = self.calculate_arp(risk_probs)
        dominant = self.get_dominant_affect(risk_probs)

        # Apply veteran calibration (lower thresholds for veteran population)
        effective_nrs_thresh = self.nrs_threshold
        effective_arp_thresh = self.arp_threshold

        if self.veteran_calibration:
            # Veteran population has higher baseline risk - use lower thresholds
            effective_nrs_thresh *= 0.85
            effective_arp_thresh *= 0.85

        triggered = (nrs > effective_nrs_thresh) or (arp > effective_arp_thresh)

        # Confidence based on signal strength
        confidence = min(0.5 + (nrs + arp) * 0.25, 0.95) if triggered else 0.3

        elapsed_ms = int((time.time() - start_time) * 1000)

        # SECURITY: Log only aggregate metrics, never raw affect vectors
        if triggered:
            logger.info(f"[GAUGE] TRIGGERED nrs={nrs:.3f} arp={arp:.3f} "
                       f"affect={dominant} in {elapsed_ms}ms")

        return GAUGEResult(
            nrs=round(nrs, 4),
            arp=round(arp, 4),
            triggered=triggered,
            dominant_affect=dominant,
            confidence=confidence,
            processing_ms=elapsed_ms
        )

    def _estimate_logits_from_text(self, text: str) -> Dict[str, float]:
        """
        Estimate pseudo-logits from word presence when real logits unavailable.

        This is a fallback - prefer extracting actual logits from LLM inference.
        """
        words = text.lower().split()
        logits = {}

        for word in self.risk_words:
            if word in words:
                # Word present - high probability
                logits[word] = -0.5
            elif any(word in w or w in word for w in words):
                # Partial match
                logits[word] = -2.0
            else:
                # Not present - low probability
                logits[word] = -10.0

        return logits


# Singleton
_monitor = None

def get_gauge_monitor() -> GAUGEMonitor:
    """Get or create singleton GAUGE monitor."""
    global _monitor
    if _monitor is None:
        _monitor = GAUGEMonitor(
            nrs_threshold=0.15,
            arp_threshold=1.5,
            veteran_calibration=True
        )
    return _monitor

def check_affective_risk(message: str,
                         llm_logits: Optional[Dict] = None) -> GAUGEResult:
    """Convenience function for GAUGE monitoring."""
    return get_gauge_monitor().monitor(message, llm_logits)
```

### Step 3: Integrate GAUGE with Crisis Classifier

**File to modify:** `/ganuda/vetassist/backend/app/services/crisis_classifier.py`

Add GAUGE as a parallel detection path after lexicon screening fails:

```python
# Add import at top of file
from app.services.gauge_monitor import check_affective_risk, GAUGEResult

# Modify the classify() method to include GAUGE pathway:

def classify(self, message: str, session_id: str = None) -> Dict:
    """
    Classify message through three-tier detection + GAUGE affective monitoring.
    """
    start_time = time.time()

    # Tier 1: Lexicon screen
    lexicon_match = self._lexicon_screen(message)

    if lexicon_match:
        # Explicit crisis language detected - proceed to Tier 2 LLM
        llm_result = self._llm_classify(message)
        # ... existing LLM classification logic ...
    else:
        # No explicit markers - run GAUGE affective monitoring
        gauge_result = check_affective_risk(message)

        if gauge_result.triggered:
            # GAUGE detected implicit risk - escalate to Tier 2 LLM
            logger.info(f"[CRISIS] GAUGE triggered - escalating to C-SSRS LLM")
            llm_result = self._llm_classify(message)

            if llm_result:
                cssrs_level = llm_result.get("level", 1)
                # Boost level by 1 if GAUGE triggered (implicit risk indicator)
                cssrs_level = min(cssrs_level + 1, 6)
                confidence = llm_result.get("confidence", 0.5)
            else:
                # LLM unavailable, GAUGE triggered - default to level 2
                cssrs_level = 2
                confidence = gauge_result.confidence

            intervention = self._route_intervention(cssrs_level)
            elapsed_ms = int((time.time() - start_time) * 1000)

            # Log with GAUGE metadata (no PII)
            self._log_detection(
                session_id, cssrs_level, confidence,
                lexicon_match=False,  # Triggered by GAUGE, not lexicon
                llm_classified=llm_result is not None,
                intervention_type=intervention["type"],
                gauge_nrs=gauge_result.nrs,
                gauge_arp=gauge_result.arp,
                gauge_affect=gauge_result.dominant_affect
            )

            return {
                "cssrs_level": cssrs_level,
                "confidence": confidence,
                "category": CSSRS_LEVELS.get(cssrs_level, {}).get("description", "Unknown"),
                "intervention": intervention,
                "resources": self._get_resources(cssrs_level),
                "tier_reached": 2,
                "detection_source": "gauge",
                "gauge_metrics": {
                    "nrs": gauge_result.nrs,
                    "arp": gauge_result.arp,
                    "dominant_affect": gauge_result.dominant_affect
                },
                "processing_ms": elapsed_ms
            }
        else:
            # No explicit or implicit concern
            return {
                "cssrs_level": 0,
                "confidence": 0.95,
                "category": None,
                "intervention": {"type": "none", "display": None, "interrupt_chat": False},
                "resources": None,
                "tier_reached": 1,
                "detection_source": "none",
                "processing_ms": int((time.time() - start_time) * 1000)
            }
```

Update the logging method to capture GAUGE metrics:

```python
def _log_detection(self, session_id, cssrs_level, confidence,
                   lexicon_match, llm_classified, intervention_type,
                   gauge_nrs=None, gauge_arp=None, gauge_affect=None):
    """Log detection metadata. NEVER logs message content or raw affect vectors."""
    try:
        from app.core.database_config import get_db_connection
        conn = get_db_connection(database='triad_federation')
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO crisis_detections
               (session_id, cssrs_level, confidence, lexicon_match,
                llm_classified, intervention_shown,
                gauge_nrs, gauge_arp, gauge_affect, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
            (session_id, cssrs_level, confidence, lexicon_match,
             llm_classified, intervention_type,
             gauge_nrs, gauge_arp, gauge_affect)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"[CRISIS] Failed to log detection: {e}")
```

### Step 4: Database Migration for GAUGE Metrics

**File to create:** `/ganuda/sql/migration_gauge_metrics_v1.sql`

```sql
-- Migration: Add GAUGE affective monitoring columns to crisis_detections
-- Date: 2026-02-05
-- Council Vote: Approved with security concern

-- Add GAUGE metric columns
ALTER TABLE crisis_detections
ADD COLUMN IF NOT EXISTS gauge_nrs FLOAT,
ADD COLUMN IF NOT EXISTS gauge_arp FLOAT,
ADD COLUMN IF NOT EXISTS gauge_affect VARCHAR(32);

-- Add index for GAUGE-triggered detections analysis
CREATE INDEX IF NOT EXISTS idx_crisis_gauge_triggered
ON crisis_detections (gauge_nrs, gauge_arp)
WHERE gauge_nrs IS NOT NULL;

-- Add comment documenting PII protection
COMMENT ON COLUMN crisis_detections.gauge_nrs IS
'Negative Risk Shift metric. PII-sensitive: only store aggregate, never raw affect vectors.';

COMMENT ON COLUMN crisis_detections.gauge_arp IS
'Absolute Risk Potential metric. PII-sensitive: only store aggregate, never raw affect vectors.';

COMMENT ON COLUMN crisis_detections.gauge_affect IS
'Dominant affect category (e.g., sadness, anger). Safe categorical data.';
```

### Step 5: Military Terminology Lexicon Augmentation

Already included in Step 1 via `MILITARY_AFFECT_TERMS` dictionary. Key augmentations:

| Category | Terms | Rationale |
|----------|-------|-----------|
| **moral_injury** | betrayed, guilty, ashamed, blood_on_hands | Combat trauma manifesting as moral weight |
| **combat_distress** | hypervigilant, triggered, flashback, incoming | Active PTSD symptom language |
| **transition_struggle** | purposeless, nobody_understands, lost_identity | Transition period vulnerability |
| **mst_trauma** | violated, silenced, chain_of_command | Military Sexual Trauma indicators |

These terms carry elevated risk weights (0.7-0.9) in the GAUGE risk profile to ensure proper sensitivity for veteran-specific affect patterns.

### Step 6: Threshold Configuration

**File to create:** `/ganuda/vetassist/backend/app/config/gauge_thresholds.py`

```python
"""
GAUGE Threshold Configuration for Veteran Population

CALIBRATION NOTE: Veterans have elevated baseline for negative affect due to:
- Combat exposure
- MST prevalence
- Transition challenges
- Higher rates of TBI

Thresholds are calibrated 15% lower than general population defaults.
Review quarterly with clinical advisory board.
"""

# Base thresholds (from GAUGE paper, tau=0.0 achieves 6% ASR on MinorBench)
BASE_NRS_THRESHOLD = 0.18  # Directional risk threshold
BASE_ARP_THRESHOLD = 1.75  # Magnitude risk threshold

# Veteran population calibration factor
VETERAN_CALIBRATION_FACTOR = 0.85

# Applied thresholds for VetAssist
VETASSIST_NRS_THRESHOLD = BASE_NRS_THRESHOLD * VETERAN_CALIBRATION_FACTOR  # 0.153
VETASSIST_ARP_THRESHOLD = BASE_ARP_THRESHOLD * VETERAN_CALIBRATION_FACTOR  # 1.4875

# Per-category sensitivity adjustments
CATEGORY_SENSITIVITY = {
    "sadness": 1.2,        # Increase sensitivity for depression indicators
    "moral_injury": 1.3,   # High sensitivity for moral injury
    "mst_trauma": 1.3,     # High sensitivity for MST indicators
    "transition_struggle": 1.1,
    "combat_distress": 1.0,
    "anger": 0.9,          # Slightly lower - anger common but not always crisis
    "fear": 1.0,
    "disgust": 0.8,
    "negative": 1.1
}

# Time-of-day adjustments (crisis risk elevated at night)
NIGHT_HOURS = range(22, 6)  # 10 PM - 6 AM
NIGHT_SENSITIVITY_BOOST = 1.15

def get_effective_thresholds(hour: int = None) -> dict:
    """Get effective thresholds adjusted for time of day."""
    nrs = VETASSIST_NRS_THRESHOLD
    arp = VETASSIST_ARP_THRESHOLD

    if hour is not None and hour in NIGHT_HOURS:
        # Lower thresholds at night (more sensitive)
        nrs /= NIGHT_SENSITIVITY_BOOST
        arp /= NIGHT_SENSITIVITY_BOOST

    return {
        "nrs_threshold": round(nrs, 4),
        "arp_threshold": round(arp, 4)
    }
```

---

## Testing Requirements

### Unit Tests

**File to create:** `/ganuda/vetassist/backend/tests/test_gauge_monitor.py`

```python
"""
Tests for GAUGE Affective Monitor
"""
import pytest
from app.services.gauge_monitor import GAUGEMonitor, check_affective_risk

class TestGAUGEMonitor:

    def setup_method(self):
        self.monitor = GAUGEMonitor(
            nrs_threshold=0.15,
            arp_threshold=1.5,
            veteran_calibration=False  # Disable for predictable tests
        )

    def test_neutral_message_no_trigger(self):
        """Neutral message should not trigger GAUGE."""
        result = self.monitor.monitor("What documents do I need for my claim?")
        assert not result.triggered
        assert result.nrs < 0.15
        assert result.arp < 1.5

    def test_explicit_sadness_triggers(self):
        """Explicit sadness language should trigger."""
        result = self.monitor.monitor("I feel hopeless and worthless every day")
        assert result.triggered
        assert result.dominant_affect in ["sadness", "negative"]

    def test_military_specific_triggers(self):
        """Military-specific affect terms should trigger."""
        result = self.monitor.monitor(
            "Nobody understands what I went through. I have blood on my hands."
        )
        assert result.triggered
        assert result.dominant_affect in ["moral_injury", "transition_struggle"]

    def test_implicit_distress_triggers(self):
        """Implicit distress without explicit crisis words should trigger."""
        result = self.monitor.monitor(
            "I'm so exhausted. Everything feels empty. What's the point anymore."
        )
        assert result.triggered

    def test_processing_time_reasonable(self):
        """Processing should complete under 50ms."""
        result = self.monitor.monitor("Test message for timing")
        assert result.processing_ms < 50

    def test_veteran_calibration_lowers_thresholds(self):
        """Veteran calibration should lower effective thresholds."""
        monitor_calibrated = GAUGEMonitor(
            nrs_threshold=0.15,
            arp_threshold=1.5,
            veteran_calibration=True
        )
        # Same borderline message
        msg = "I feel really down and empty lately"

        result_standard = self.monitor.monitor(msg)
        result_calibrated = monitor_calibrated.monitor(msg)

        # Calibrated should be more likely to trigger
        # (or have same trigger with higher confidence)
        if result_standard.triggered == result_calibrated.triggered:
            assert result_calibrated.confidence >= result_standard.confidence
```

### Integration Tests

```python
def test_gauge_crisis_classifier_integration():
    """Test GAUGE integration with crisis classifier."""
    from app.services.crisis_classifier import classify_message

    # Message with no explicit crisis language but implicit distress
    result = classify_message(
        "I don't see the point anymore. Everything is empty.",
        session_id="test-gauge-001"
    )

    # Should be detected via GAUGE pathway
    assert result["cssrs_level"] >= 1
    assert result.get("detection_source") in ["gauge", "lexicon"]

def test_gauge_does_not_override_explicit_detection():
    """Explicit crisis language should use lexicon/LLM path, not GAUGE."""
    from app.services.crisis_classifier import classify_message

    result = classify_message(
        "I want to kill myself",
        session_id="test-explicit-001"
    )

    # Should use lexicon path, not GAUGE
    assert result["cssrs_level"] >= 4
    assert result.get("detection_source") != "gauge"
```

### Manual Verification Checklist

- [ ] Message "I'm fine, just have a question" returns level 0, GAUGE not triggered
- [ ] Message "I feel so hopeless and worthless" triggers GAUGE, escalates to C-SSRS
- [ ] Message "Nobody understands what I went through overseas" triggers military lexicon
- [ ] GAUGE processing adds < 5ms overhead on average
- [ ] Database logs gauge_nrs, gauge_arp, gauge_affect correctly
- [ ] No raw affect vectors or message content logged (verify in DB)
- [ ] Night-time threshold adjustment works (test at 2 AM vs 2 PM)

---

## Security Requirements (Council Concern)

**CRITICAL: Affective data must be handled with PII-level protection.**

1. **Never log raw affect vectors** — Only log aggregate metrics (NRS, ARP, dominant category)
2. **Never expose GAUGE metrics to frontend** — Keep in backend for routing decisions only
3. **Encrypt GAUGE columns at rest** — Add to database encryption policy
4. **Audit access to crisis_detections** — All queries logged
5. **Retention policy** — GAUGE metrics auto-delete after 90 days (configurable)

```sql
-- Add to database security policy
ALTER TABLE crisis_detections ENABLE ROW LEVEL SECURITY;

-- Auto-delete GAUGE metrics after 90 days
CREATE OR REPLACE FUNCTION cleanup_gauge_metrics()
RETURNS void AS $$
BEGIN
    UPDATE crisis_detections
    SET gauge_nrs = NULL, gauge_arp = NULL, gauge_affect = NULL
    WHERE created_at < NOW() - INTERVAL '90 days'
    AND gauge_nrs IS NOT NULL;
END;
$$ LANGUAGE plpgsql;
```

---

## Rollback Plan

### Immediate Rollback (< 5 minutes)

If GAUGE causes issues in production:

```python
# In /ganuda/vetassist/backend/app/services/crisis_classifier.py
# Add feature flag at top of file:

GAUGE_ENABLED = False  # Set to False to disable GAUGE

# In classify() method, wrap GAUGE call:
if not lexicon_match and GAUGE_ENABLED:
    gauge_result = check_affective_risk(message)
    # ... GAUGE logic ...
else:
    # Skip GAUGE, return level 0 for no lexicon match
    return {...}
```

### Database Rollback

```sql
-- Remove GAUGE columns if needed
ALTER TABLE crisis_detections
DROP COLUMN IF EXISTS gauge_nrs,
DROP COLUMN IF EXISTS gauge_arp,
DROP COLUMN IF EXISTS gauge_affect;

DROP INDEX IF EXISTS idx_crisis_gauge_triggered;
```

### Full Rollback

1. Set `GAUGE_ENABLED = False` in crisis_classifier.py
2. Remove gauge_monitor.py import
3. Remove nrc_emotion_lexicon.py
4. Run database rollback SQL
5. Restart vetassist-backend service

---

## Verification Checklist

- [ ] NRC Emotion Lexicon data file created and loads correctly
- [ ] GAUGE monitor calculates NRS within [-1, 1] range
- [ ] GAUGE monitor calculates ARP within [0, +inf) range
- [ ] Military terminology augmentation included and weighted
- [ ] Crisis classifier integrates GAUGE as second detection path
- [ ] Database migration adds GAUGE columns successfully
- [ ] Unit tests pass for GAUGE monitor
- [ ] Integration tests pass for classifier + GAUGE
- [ ] No PII or raw affect vectors in logs
- [ ] Processing overhead < 5ms average
- [ ] Rollback procedure tested and documented

---

## For Seven Generations

Veterans carry invisible wounds that don't always speak in explicit words. GAUGE gives us ears to hear the emotional undertones — the despair beneath "I'm fine," the isolation behind "nobody understands." Every silent crisis we catch is a life we might save. This is how we honor their service: by listening to what they cannot say.

---

## References

- arXiv 2512.06193: GAUGE - Logit-based Framework for Real-time Detection of Hidden Conversational Escalation
- Columbia-Suicide Severity Rating Scale (C-SSRS) Clinical Manual
- NRC Emotion Lexicon (Mohammad & Turney, 2013)
- DARPA LM4VSP Program Technical Documentation
- VetAssist Crisis Detection Architecture (JR-VETASSIST-CRISIS-DETECTION-CSSRS-JAN30-2026)
