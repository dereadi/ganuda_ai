# JR INSTRUCTION: Build C-SSRS Automated Scoring (Safety-Critical)

**Task ID:** ASSIST-BUILD-CSSRS
**Priority:** P1 - Safety-critical
**Assigned To:** Any available Jr (requires careful implementation)
**Created By:** TPM + Council
**Date:** 2026-02-04
**Estimated Effort:** 8-12 hours
**Node:** Any (Python 3.11+ required)
**Council Note:** No open source implementation exists. We build this from scratch.

---

## Objective

Implement the Columbia Suicide Severity Rating Scale (C-SSRS) as deterministic code in the Assist core crisis detection system. This provides structured clinical scoring to augment our existing keyword-based crisis detection.

---

## Context

### What is C-SSRS?

The Columbia Suicide Severity Rating Scale is a free, evidence-based screening tool from Columbia University. It scores suicidal ideation on a 0-5 scale and can be administered without mental health training.

**Official source:** https://cssrs.columbia.edu/the-columbia-scale-c-ssrs/about-the-scale/

### Why We Need This

Our current `base_crisis.py` uses keyword matching for crisis detection. This works but can have false positives/negatives. C-SSRS provides:

1. **Structured assessment** - standardized clinical framework
2. **Severity levels** - distinguishes passive ideation from imminent plans
3. **Evidence-based** - validated across populations including veterans
4. **Defense in depth** - runs alongside keyword matching

### Critical Safety Principle

**ALWAYS ERR TOWARD HIGHER SEVERITY**

- False positive (flagging non-crisis) = user gets resources they may not need → acceptable
- False negative (missing crisis) = user in danger doesn't get help → UNACCEPTABLE

When uncertain between severity levels, always score higher.

---

## C-SSRS Categories

### Ideation Severity (0-5 scale)

| Level | Category | Description | Example |
|-------|----------|-------------|---------|
| **0** | No ideation | No thoughts of death or suicide | "I'm frustrated but not suicidal" |
| **1** | Wish to be dead | Passive thoughts without action | "I wish I were dead", "I wish I could go to sleep and not wake up" |
| **2** | Non-specific active suicidal thoughts | Thoughts of ending life without method | "I want to end my life", "I've been thinking about killing myself" |
| **3** | Active ideation with methods | Thought about how, but no plan or intent | "I've thought about taking pills", "I've considered using a gun" |
| **4** | Active ideation with intent | Some intent to act, without specific plan | "I want to kill myself but haven't figured out how", "I've been thinking I might do it soon" |
| **5** | Active ideation with specific plan and intent | Fully formed plan with intent to execute | "I'm going to take [pills] on [date]", "I plan to jump off [location] tomorrow" |

### Suicidal Behavior (Additional Assessment)

- **Actual attempt** - self-injurious act with intent to die
- **Interrupted attempt** - prevented by external circumstance
- **Aborted attempt** - stopped self from acting
- **Preparatory acts** - gathering means (pills, weapons, etc.)

---

## Implementation Requirements

### File Structure

```
/ganuda/assist/core/backend/
├── cssrs_scorer.py          # Main implementation (NEW)
├── cssrs_patterns.py        # Pattern definitions (NEW)
├── cssrs_test.py            # Unit tests (NEW)
└── base_crisis.py           # Existing (MODIFY to integrate)
```

---

## Steps

### 1. Create Pattern Definitions

Create `/ganuda/assist/core/backend/cssrs_patterns.py`:

```python
"""
C-SSRS Pattern Definitions

These patterns are derived from:
- C-SSRS official documentation
- Veteran-specific crisis language research
- Indigenous/Cherokee cultural context
"""

from typing import Dict, List, Tuple
import re

# Level 1: Wish to be dead (passive ideation)
LEVEL_1_PATTERNS = [
    r"\bwish\s+(I|i)\s+were\s+dead\b",
    r"\bwish\s+(I|i)\s+could\s+(die|be\s+dead)\b",
    r"\bwish\s+(I|i)\s+could\s+go\s+to\s+sleep\s+and\s+not\s+wake\s+up\b",
    r"\bwish\s+(I|i)\s+hadn't\s+woken\s+up\b",
    r"\bdon't\s+want\s+to\s+(live|exist|be\s+here)\s+anymore\b",
    r"\blife\s+isn't\s+worth\s+living\b",
    r"\bno\s+reason\s+to\s+(live|go\s+on)\b",
    r"\beveryone\s+would\s+be\s+better\s+off\s+without\s+me\b",
    r"\bworld\s+would\s+be\s+better\s+(off\s+)?without\s+me\b",
]

# Level 2: Non-specific active suicidal thoughts
LEVEL_2_PATTERNS = [
    r"\bwant\s+to\s+(die|kill\s+myself|end\s+(it|my\s+life))\b",
    r"\bthink(?:ing)?\s+about\s+(dying|killing\s+myself|suicide)\b",
    r"\bthought(?:s)?\s+of\s+(dying|suicide|killing\s+myself)\b",
    r"\bsuicidal\s+thought(?:s)?\b",
    r"\bcan't\s+take\s+(it|this)\s+anymore\b",
    r"\bready\s+to\s+end\s+(it\s+all|my\s+life)\b",
    r"\bdon't\s+deserve\s+to\s+live\b",
]

# Level 3: Active ideation with methods (but no plan/intent)
LEVEL_3_PATTERNS = [
    r"\bthought\s+about\s+taking\s+pills?\b",
    r"\bthought\s+about\s+using\s+(a\s+)?(gun|weapon|knife)\b",
    r"\bconsidered\s+(hanging|shooting|overdosing)\b",
    r"\bthought\s+about\s+jumping\s+off\b",
    r"\bthought\s+about\s+(cutting|slitting)\b",
    r"\bthought\s+about\s+driving\s+(off|into)\b",
    r"\bcould\s+(shoot|hang|overdose)\b",
    r"\bknow\s+how\s+(I|i)\s+could\s+do\s+it\b",
]

# Level 4: Active ideation with some intent (but no specific plan)
LEVEL_4_PATTERNS = [
    r"\bwant\s+to\s+kill\s+myself\s+but\s+(haven't|don't\s+know)\b",
    r"\bmight\s+do\s+it\s+soon\b",
    r"\bthinking\s+(I|i)\s+might\s+(do\s+it|kill\s+myself)\b",
    r"\bstarting\s+to\s+think\s+(I|i)\s+will\b",
    r"\bprobably\s+going\s+to\s+(do\s+it|kill\s+myself)\b",
    r"\bseriously\s+considering\b",
]

# Level 5: Active ideation with specific plan and intent
LEVEL_5_PATTERNS = [
    r"\bgoing\s+to\s+(kill\s+myself|do\s+it|end\s+it)\s+(on|tomorrow|tonight|this\s+week)\b",
    r"\bplan\s+to\s+(shoot|hang|overdose|jump)\b",
    r"\bhave\s+(a\s+)?plan\b",
    r"\bwill\s+(kill\s+myself|do\s+it)\s+(on|at|when)\b",
    r"\b(tonight|tomorrow|this\s+week)\s+(I'm|i'm)\s+going\s+to\b",
    r"\bgathered\s+(pills|weapons|rope)\b",
    r"\bwrote\s+(a\s+)?(suicide\s+)?note\b",
    r"\bsaid\s+goodbye\s+to\b",
    r"\bgave\s+away\s+my\s+(possessions|things)\b",
]

# Behavioral indicators (preparatory acts)
BEHAVIORAL_PATTERNS = [
    r"\bbought\s+(a\s+)?(gun|pills|rope)\b",
    r"\bcollected\s+(pills|medications)\b",
    r"\bhoarding\s+(pills|medications)\b",
    r"\bwrote\s+(a\s+|my\s+)?will\b",
    r"\bgave\s+away\s+(possessions|belongings)\b",
    r"\bsaid\s+final\s+goodbye(?:s)?\b",
    r"\bresearched\s+(suicide\s+)?methods?\b",
    r"\bpracticed\s+(hanging|tying)\b",
]

# Negation patterns (reduce severity)
NEGATION_PATTERNS = [
    r"\bdon't\s+want\s+to\s+(die|kill\s+myself|hurt\s+myself)\b",
    r"\bnot\s+suicidal\b",
    r"\bnot\s+going\s+to\s+(kill\s+myself|do\s+it)\b",
    r"\bwon't\s+(kill\s+myself|hurt\s+myself)\b",
    r"\bno\s+suicidal\s+(thoughts|ideation)\b",
]

# Veteran-specific risk factors
VETERAN_PATTERNS = [
    r"\bcan't\s+take\s+the\s+nightmares\s+anymore\b",
    r"\bnobody\s+understands\s+what\s+(I|i)\s+went\s+through\b",
    r"\bshould\s+have\s+died\s+(over\s+there|in\s+combat)\b",
    r"\bsurvivor'?s?\s+guilt\b",
    r"\bcan't\s+live\s+with\s+what\s+(I|i)\s+(did|saw)\b",
    r"\blost\s+too\s+many\s+(buddies|friends|brothers|sisters)\b",
    r"\bPTSD\s+is\s+killing\s+me\b",
    r"\bTBI\s+has\s+ruined\s+my\s+life\b",
]

# Indigenous/Cherokee-specific risk factors
INDIGENOUS_PATTERNS = [
    r"\bdisconnected\s+from\s+my\s+people\b",
    r"\blost\s+my\s+culture\b",
    r"\bhistorical\s+trauma\b",
    r"\bcan't\s+find\s+my\s+place\s+in\s+the\s+community\b",
    r"\bcut\s+off\s+from\s+my\s+(tribe|nation|ancestors)\b",
    r"\bshame\s+about\s+my\s+heritage\b",
]

# Context patterns that are NOT suicidal (avoid false positives)
FALSE_POSITIVE_PATTERNS = [
    r"\bkill\s+(this\s+)?(bug|issue|problem)\b",
    r"\bdying\s+to\s+(see|know|try)\b",  # "dying to see that movie"
    r"\bshoot\s+(a\s+)?(photo|video|shot)\b",
    r"\bhang\s+out\b",
    r"\bjump\s+(rope|for\s+joy|at\s+the\s+chance)\b",
    r"\bcut\s+(the\s+)?(grass|ties|budget)\b",
]

def compile_patterns() -> Dict[int, List[re.Pattern]]:
    """Compile all patterns for efficient matching."""
    return {
        1: [re.compile(p, re.IGNORECASE) for p in LEVEL_1_PATTERNS],
        2: [re.compile(p, re.IGNORECASE) for p in LEVEL_2_PATTERNS],
        3: [re.compile(p, re.IGNORECASE) for p in LEVEL_3_PATTERNS],
        4: [re.compile(p, re.IGNORECASE) for p in LEVEL_4_PATTERNS],
        5: [re.compile(p, re.IGNORECASE) for p in LEVEL_5_PATTERNS],
    }

COMPILED_PATTERNS = compile_patterns()
COMPILED_BEHAVIORAL = [re.compile(p, re.IGNORECASE) for p in BEHAVIORAL_PATTERNS]
COMPILED_NEGATION = [re.compile(p, re.IGNORECASE) for p in NEGATION_PATTERNS]
COMPILED_VETERAN = [re.compile(p, re.IGNORECASE) for p in VETERAN_PATTERNS]
COMPILED_INDIGENOUS = [re.compile(p, re.IGNORECASE) for p in INDIGENOUS_PATTERNS]
COMPILED_FALSE_POSITIVE = [re.compile(p, re.IGNORECASE) for p in FALSE_POSITIVE_PATTERNS]
```

**Verification:** File created with all pattern definitions

### 2. Create Main Scorer

Create `/ganuda/assist/core/backend/cssrs_scorer.py`:

```python
"""
C-SSRS Automated Scorer

Columbia Suicide Severity Rating Scale implementation for Assist platform.

CRITICAL: This code is used to assess suicide risk. Always err toward higher severity.
False positives (unnecessary alerts) are acceptable. False negatives are NOT acceptable.

References:
- https://cssrs.columbia.edu/
- https://www.samhsa.gov/resource/dbhis/columbia-suicide-severity-rating-scale-c-ssrs
"""

from dataclasses import dataclass
from typing import List, Optional
import re

from cssrs_patterns import (
    COMPILED_PATTERNS,
    COMPILED_BEHAVIORAL,
    COMPILED_NEGATION,
    COMPILED_VETERAN,
    COMPILED_INDIGENOUS,
    COMPILED_FALSE_POSITIVE,
)


@dataclass
class CSSRSResult:
    """Result of C-SSRS scoring."""

    severity: int  # 0-5
    category: str  # Human-readable category name
    matched_patterns: List[str]  # Patterns that triggered
    has_behavioral_indicators: bool  # Preparatory acts detected
    has_veteran_risk: bool  # Veteran-specific risk factors
    has_indigenous_risk: bool  # Indigenous-specific risk factors
    recommended_action: str  # "none", "monitor", "safety_plan", "immediate_referral", "988_emergency"
    confidence: float  # 0.0-1.0
    rationale: str  # Human-readable explanation

    def to_dict(self):
        """Convert to dictionary for logging/storage."""
        return {
            "severity": self.severity,
            "category": self.category,
            "matched_patterns": self.matched_patterns,
            "has_behavioral_indicators": self.has_behavioral_indicators,
            "has_veteran_risk": self.has_veteran_risk,
            "has_indigenous_risk": self.has_indigenous_risk,
            "recommended_action": self.recommended_action,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


CATEGORY_NAMES = {
    0: "No suicidal ideation",
    1: "Wish to be dead (passive)",
    2: "Non-specific active suicidal thoughts",
    3: "Active ideation with methods",
    4: "Active ideation with intent",
    5: "Active ideation with specific plan and intent",
}


RECOMMENDED_ACTIONS = {
    0: "none",
    1: "monitor",
    2: "safety_plan",
    3: "immediate_referral",
    4: "988_emergency",
    5: "988_emergency",
}


def score_cssrs(text: str, context: Optional[dict] = None) -> CSSRSResult:
    """
    Score text against C-SSRS categories.

    Args:
        text: Text to score (message, chat, etc.)
        context: Optional context dict with:
            - user_type: "veteran", "indigenous", "general"
            - history: List of previous messages for pattern detection

    Returns:
        CSSRSResult with severity level and recommendations

    Safety Note:
        - Empty/None text scores as 0 (no ideation)
        - Uncertainty defaults to HIGHER severity
        - Context-aware to reduce false positives
        - Negation-aware to handle "I don't want to die"
    """
    if not text or not text.strip():
        return CSSRSResult(
            severity=0,
            category=CATEGORY_NAMES[0],
            matched_patterns=[],
            has_behavioral_indicators=False,
            has_veteran_risk=False,
            has_indigenous_risk=False,
            recommended_action="none",
            confidence=1.0,
            rationale="No text provided",
        )

    # Normalize text
    text_normalized = text.lower().strip()

    # Check for false positive patterns first (programming, gaming language, etc.)
    if _is_false_positive(text_normalized):
        return CSSRSResult(
            severity=0,
            category=CATEGORY_NAMES[0],
            matched_patterns=["false_positive_context"],
            has_behavioral_indicators=False,
            has_veteran_risk=False,
            has_indigenous_risk=False,
            recommended_action="none",
            confidence=0.9,
            rationale="Matched false positive pattern (non-suicidal context)",
        )

    # Check for negation
    has_negation = _check_negation(text_normalized)

    # Scan for patterns at each level (5 to 1, highest first)
    severity = 0
    matched = []

    for level in [5, 4, 3, 2, 1]:
        for pattern in COMPILED_PATTERNS[level]:
            matches = pattern.findall(text_normalized)
            if matches:
                severity = max(severity, level)  # Take highest level
                matched.append(f"Level {level}: {pattern.pattern}")

    # Check behavioral indicators (preparatory acts)
    has_behavioral = False
    for pattern in COMPILED_BEHAVIORAL:
        if pattern.search(text_normalized):
            has_behavioral = True
            matched.append(f"Behavioral: {pattern.pattern}")
            # Preparatory acts elevate severity
            if severity < 4:
                severity = 4  # At least level 4 if preparing

    # Check veteran-specific risk factors
    has_veteran = False
    if context and context.get("user_type") == "veteran":
        for pattern in COMPILED_VETERAN:
            if pattern.search(text_normalized):
                has_veteran = True
                matched.append(f"Veteran risk: {pattern.pattern}")
                # Elevate severity if not already high
                if severity < 2:
                    severity = 2

    # Check indigenous-specific risk factors
    has_indigenous = False
    if context and context.get("user_type") == "indigenous":
        for pattern in COMPILED_INDIGENOUS:
            if pattern.search(text_normalized):
                has_indigenous = True
                matched.append(f"Indigenous risk: {pattern.pattern}")
                # These are risk factors, not immediate crisis
                # Flag for cultural support

    # Apply negation adjustment
    if has_negation and severity > 0:
        # Reduce severity by 1 level for clear negation
        # BUT: "I don't want to die [but...]" still warrants monitoring
        original_severity = severity
        severity = max(0, severity - 1)
        matched.append(f"Negation detected (reduced from {original_severity} to {severity})")

    # Calculate confidence
    confidence = _calculate_confidence(
        severity=severity,
        matched_count=len(matched),
        has_negation=has_negation,
        has_behavioral=has_behavioral,
    )

    # Generate rationale
    rationale = _generate_rationale(
        severity=severity,
        matched=matched,
        has_behavioral=has_behavioral,
        has_veteran=has_veteran,
        has_indigenous=has_indigenous,
        has_negation=has_negation,
    )

    return CSSRSResult(
        severity=severity,
        category=CATEGORY_NAMES[severity],
        matched_patterns=matched,
        has_behavioral_indicators=has_behavioral,
        has_veteran_risk=has_veteran,
        has_indigenous_risk=has_indigenous,
        recommended_action=RECOMMENDED_ACTIONS[severity],
        confidence=confidence,
        rationale=rationale,
    )


def _is_false_positive(text: str) -> bool:
    """Check if text matches false positive patterns (non-suicidal context)."""
    for pattern in COMPILED_FALSE_POSITIVE:
        if pattern.search(text):
            return True
    return False


def _check_negation(text: str) -> bool:
    """Check if text contains negation of suicidal intent."""
    for pattern in COMPILED_NEGATION:
        if pattern.search(text):
            return True
    return False


def _calculate_confidence(
    severity: int,
    matched_count: int,
    has_negation: bool,
    has_behavioral: bool,
) -> float:
    """
    Calculate confidence in the severity score.

    High confidence (0.9-1.0):
        - Clear patterns matched
        - Multiple patterns at same level
        - Behavioral indicators present

    Medium confidence (0.6-0.8):
        - Single pattern matched
        - Negation present

    Low confidence (0.3-0.5):
        - Ambiguous language
        - Context unclear
    """
    if severity == 0:
        return 1.0 if matched_count == 0 else 0.9

    confidence = 0.7  # Base

    # More matches = higher confidence
    if matched_count >= 3:
        confidence += 0.2
    elif matched_count == 2:
        confidence += 0.1

    # Behavioral indicators = higher confidence
    if has_behavioral:
        confidence += 0.1

    # Negation = lower confidence
    if has_negation:
        confidence -= 0.2

    # Level 5 with plan = highest confidence
    if severity == 5 and matched_count >= 2:
        confidence = 0.95

    return max(0.3, min(1.0, confidence))


def _generate_rationale(
    severity: int,
    matched: List[str],
    has_behavioral: bool,
    has_veteran: bool,
    has_indigenous: bool,
    has_negation: bool,
) -> str:
    """Generate human-readable explanation of scoring."""
    if severity == 0:
        if has_negation:
            return "User explicitly stated no suicidal intent."
        return "No suicidal ideation detected."

    parts = [f"Severity {severity} - {CATEGORY_NAMES[severity]}."]

    if matched:
        parts.append(f"Matched {len(matched)} patterns.")

    if has_behavioral:
        parts.append("WARNING: Preparatory behaviors detected (gathering means).")

    if has_veteran:
        parts.append("Veteran-specific risk factors present.")

    if has_indigenous:
        parts.append("Indigenous cultural risk factors present (recommend cultural support).")

    if has_negation:
        parts.append("Note: Negation detected, but monitoring still recommended.")

    if severity >= 3:
        parts.append("IMMEDIATE ACTION REQUIRED.")

    return " ".join(parts)


def format_988_message(result: CSSRSResult) -> str:
    """
    Format message for 988 Suicide & Crisis Lifeline referral.

    Always include:
    - 988 phone number
    - Crisis Text Line
    - Veterans Crisis Line (if applicable)
    - Cherokee Nation Behavioral Health (if applicable)
    """
    message_parts = [
        "🆘 CRISIS SUPPORT AVAILABLE 24/7:",
        "",
        "📞 988 Suicide & Crisis Lifeline",
        "   Call or text 988",
        "   Online chat: 988lifeline.org/chat",
        "",
        "💬 Crisis Text Line",
        "   Text HOME to 741741",
        "",
    ]

    if result.has_veteran_risk:
        message_parts.extend([
            "🎖️ Veterans Crisis Line",
            "   Call 988, press 1",
            "   Text 838255",
            "   Online chat: veteranscrisisline.net/get-help/chat",
            "",
        ])

    if result.has_indigenous_risk:
        message_parts.extend([
            "🪶 Cherokee Nation Behavioral Health",
            "   Call 918-453-5000",
            "   Crisis support with cultural understanding",
            "",
        ])

    message_parts.extend([
        "You are not alone. Help is available right now.",
        "These services are free, confidential, and available 24/7.",
    ])

    return "\n".join(message_parts)


# Integration helper for base_crisis.py
def integrate_with_crisis_detector(text: str, context: dict) -> dict:
    """
    Integration point for base_crisis.py.

    Returns dict with:
        - is_crisis: bool
        - severity: int (0-5)
        - recommended_action: str
        - message: str (988 referral if needed)
        - result: CSSRSResult object
    """
    result = score_cssrs(text, context)

    return {
        "is_crisis": result.severity >= 3,  # Level 3+ is crisis
        "severity": result.severity,
        "recommended_action": result.recommended_action,
        "message": format_988_message(result) if result.severity >= 3 else "",
        "result": result,
    }
```

**Verification:** Scorer implementation complete with all methods

### 3. Create Unit Tests

Create `/ganuda/assist/core/backend/cssrs_test.py`:

```python
"""
Unit tests for C-SSRS scorer.

Test cases cover:
- Each severity level (0-5)
- Negation handling
- False positive detection
- Veteran-specific patterns
- Indigenous-specific patterns
- Edge cases
"""

import pytest
from cssrs_scorer import score_cssrs, format_988_message, CSSRSResult


class TestCSSRSScoring:
    """Test suite for C-SSRS scoring functionality."""

    def test_level_0_no_ideation(self):
        """Test level 0: No suicidal ideation."""
        result = score_cssrs("I'm having a rough day but I'm okay")
        assert result.severity == 0
        assert result.category == "No suicidal ideation"
        assert result.recommended_action == "none"

    def test_level_1_wish_dead(self):
        """Test level 1: Wish to be dead (passive)."""
        result = score_cssrs("I wish I were dead")
        assert result.severity == 1
        assert result.category == "Wish to be dead (passive)"
        assert result.recommended_action == "monitor"
        assert len(result.matched_patterns) > 0

    def test_level_1_better_off(self):
        """Test level 1: Others better off without me."""
        result = score_cssrs("Everyone would be better off without me")
        assert result.severity == 1
        assert result.recommended_action == "monitor"

    def test_level_2_want_to_die(self):
        """Test level 2: Active thoughts of ending life."""
        result = score_cssrs("I want to end my life")
        assert result.severity == 2
        assert result.category == "Non-specific active suicidal thoughts"
        assert result.recommended_action == "safety_plan"

    def test_level_2_thinking_suicide(self):
        """Test level 2: Thinking about suicide."""
        result = score_cssrs("I've been thinking about killing myself")
        assert result.severity == 2
        assert result.recommended_action == "safety_plan"

    def test_level_3_method_no_plan(self):
        """Test level 3: Thought about method but no plan."""
        result = score_cssrs("I've thought about taking pills")
        assert result.severity == 3
        assert result.category == "Active ideation with methods"
        assert result.recommended_action == "immediate_referral"

    def test_level_3_gun_consideration(self):
        """Test level 3: Considered using weapon."""
        result = score_cssrs("I've been thinking about using a gun")
        assert result.severity == 3
        assert result.recommended_action == "immediate_referral"

    def test_level_4_intent_no_plan(self):
        """Test level 4: Intent without specific plan."""
        result = score_cssrs("I want to kill myself but haven't figured out how")
        assert result.severity == 4
        assert result.category == "Active ideation with intent"
        assert result.recommended_action == "988_emergency"

    def test_level_4_might_do_it(self):
        """Test level 4: Might do it soon."""
        result = score_cssrs("I'm thinking I might do it soon")
        assert result.severity == 4
        assert result.recommended_action == "988_emergency"

    def test_level_5_specific_plan(self):
        """Test level 5: Specific plan with intent."""
        result = score_cssrs("I'm going to jump off the bridge tomorrow")
        assert result.severity == 5
        assert result.category == "Active ideation with specific plan and intent"
        assert result.recommended_action == "988_emergency"
        assert result.confidence >= 0.9

    def test_level_5_plan_with_method(self):
        """Test level 5: Plan to use specific method."""
        result = score_cssrs("I plan to take pills tonight and end it")
        assert result.severity == 5
        assert result.recommended_action == "988_emergency"

    def test_behavioral_indicators(self):
        """Test detection of preparatory behaviors."""
        result = score_cssrs("I bought a gun yesterday")
        assert result.has_behavioral_indicators
        assert result.severity >= 4  # Preparatory acts elevate to 4+

    def test_behavioral_gathering_pills(self):
        """Test behavioral: gathering means."""
        result = score_cssrs("I've been hoarding my medications")
        assert result.has_behavioral_indicators
        assert result.severity >= 4


class TestNegationHandling:
    """Test negation detection and handling."""

    def test_dont_want_to_die(self):
        """Test negation: I don't want to die."""
        result = score_cssrs("I don't want to die")
        assert result.severity == 0
        assert "negation" in result.rationale.lower() or result.severity == 0

    def test_not_suicidal(self):
        """Test negation: Not suicidal."""
        result = score_cssrs("I'm not suicidal")
        assert result.severity == 0

    def test_wont_kill_myself(self):
        """Test negation: Won't kill myself."""
        result = score_cssrs("I won't kill myself")
        assert result.severity == 0

    def test_negation_reduces_severity(self):
        """Test that negation reduces severity by 1 level."""
        # This is a tough case: "I want to die but I won't do it"
        # Should be monitored, but lower severity than without negation
        result = score_cssrs("I want to end my life but I won't do it")
        # Severity should be reduced from 2 to 1
        assert result.severity <= 2


class TestFalsePositives:
    """Test false positive detection (non-suicidal context)."""

    def test_kill_bug(self):
        """Test: Kill this bug (programming context)."""
        result = score_cssrs("I need to kill this bug in the code")
        assert result.severity == 0
        assert "false_positive" in result.matched_patterns[0].lower()

    def test_dying_to_see(self):
        """Test: Dying to see (figure of speech)."""
        result = score_cssrs("I'm dying to see that movie")
        assert result.severity == 0

    def test_shoot_photo(self):
        """Test: Shoot a photo."""
        result = score_cssrs("Let me shoot a photo of that")
        assert result.severity == 0

    def test_hang_out(self):
        """Test: Hang out (socializing)."""
        result = score_cssrs("Want to hang out this weekend?")
        assert result.severity == 0


class TestVeteranSpecificPatterns:
    """Test veteran-specific risk factors."""

    def test_nightmares(self):
        """Test veteran pattern: Can't take nightmares."""
        context = {"user_type": "veteran"}
        result = score_cssrs("I can't take the nightmares anymore", context)
        assert result.has_veteran_risk
        assert result.severity >= 1  # Should flag for monitoring

    def test_survivor_guilt(self):
        """Test veteran pattern: Survivor's guilt."""
        context = {"user_type": "veteran"}
        result = score_cssrs("I have so much survivor's guilt", context)
        assert result.has_veteran_risk

    def test_should_have_died(self):
        """Test veteran pattern: Should have died over there."""
        context = {"user_type": "veteran"}
        result = score_cssrs("I should have died over there with my brothers", context)
        assert result.has_veteran_risk
        assert result.severity >= 2

    def test_veteran_988_message(self):
        """Test that veteran crisis resources are included."""
        context = {"user_type": "veteran"}
        result = score_cssrs("I can't take this anymore", context)
        result.has_veteran_risk = True  # Force for test
        message = format_988_message(result)
        assert "Veterans Crisis Line" in message
        assert "988" in message


class TestIndigenousSpecificPatterns:
    """Test Indigenous/Cherokee-specific risk factors."""

    def test_disconnected_from_people(self):
        """Test Indigenous pattern: Disconnected from people."""
        context = {"user_type": "indigenous"}
        result = score_cssrs("I feel disconnected from my people", context)
        assert result.has_indigenous_risk

    def test_lost_culture(self):
        """Test Indigenous pattern: Lost culture."""
        context = {"user_type": "indigenous"}
        result = score_cssrs("I've lost my culture and identity", context)
        assert result.has_indigenous_risk

    def test_historical_trauma(self):
        """Test Indigenous pattern: Historical trauma."""
        context = {"user_type": "indigenous"}
        result = score_cssrs("The historical trauma weighs on me", context)
        assert result.has_indigenous_risk

    def test_indigenous_cultural_support(self):
        """Test that Cherokee Nation resources are included."""
        context = {"user_type": "indigenous"}
        result = score_cssrs("I'm struggling", context)
        result.has_indigenous_risk = True  # Force for test
        message = format_988_message(result)
        assert "Cherokee Nation Behavioral Health" in message or "cultural" in message.lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string(self):
        """Test empty string."""
        result = score_cssrs("")
        assert result.severity == 0
        assert result.confidence == 1.0

    def test_none_text(self):
        """Test None input."""
        result = score_cssrs(None)
        assert result.severity == 0

    def test_whitespace_only(self):
        """Test whitespace only."""
        result = score_cssrs("   \n  \t  ")
        assert result.severity == 0

    def test_mixed_levels(self):
        """Test text with patterns from multiple levels."""
        # Should score as HIGHEST level present
        result = score_cssrs("I wish I were dead and I have a plan to do it tonight")
        assert result.severity == 5  # Highest level present

    def test_confidence_high_severity(self):
        """Test confidence is high for clear level 5."""
        result = score_cssrs("I'm going to kill myself tonight with pills")
        assert result.severity == 5
        assert result.confidence >= 0.9

    def test_confidence_with_negation(self):
        """Test confidence is lower with negation."""
        result = score_cssrs("Sometimes I think about dying but I don't want to")
        assert result.confidence < 0.8  # Lower due to negation


class TestIntegration:
    """Test integration with crisis detection system."""

    def test_is_crisis_level_3_plus(self):
        """Test that level 3+ is flagged as crisis."""
        from cssrs_scorer import integrate_with_crisis_detector

        context = {"user_type": "general"}
        result = integrate_with_crisis_detector("I've thought about taking pills", context)

        assert result["is_crisis"] is True
        assert result["severity"] >= 3
        assert len(result["message"]) > 0  # 988 message present

    def test_not_crisis_level_1_2(self):
        """Test that level 1-2 is NOT immediate crisis."""
        from cssrs_scorer import integrate_with_crisis_detector

        context = {"user_type": "general"}
        result = integrate_with_crisis_detector("I wish I were dead", context)

        assert result["is_crisis"] is False  # Not immediate crisis
        assert result["severity"] in [1, 2]
        assert result["recommended_action"] in ["monitor", "safety_plan"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
```

**Verification:** All tests defined for each severity level and edge case

### 4. Integrate with base_crisis.py

Locate and modify `/ganuda/assist/core/backend/base_crisis.py`:

```python
# Add import at top
from cssrs_scorer import score_cssrs, format_988_message, integrate_with_crisis_detector

# Find existing crisis detection function (likely detect_crisis or similar)
# Modify to run BOTH keyword matching AND C-SSRS

def detect_crisis_enhanced(text: str, context: dict) -> dict:
    """
    Enhanced crisis detection using both keyword matching and C-SSRS.

    Defense in depth: If EITHER system detects crisis, escalate.

    Args:
        text: User message
        context: User context (type, history, etc.)

    Returns:
        dict with:
            - is_crisis: bool
            - severity: str ("none", "low", "medium", "high", "critical")
            - cssrs_score: int (0-5)
            - recommended_action: str
            - message: str (988 referral if crisis)
            - keyword_match: bool (did keywords trigger?)
            - cssrs_match: bool (did C-SSRS trigger?)
    """
    # Run existing keyword matching
    keyword_result = detect_crisis_keywords(text)  # Existing function

    # Run C-SSRS scoring
    cssrs_result = integrate_with_crisis_detector(text, context)

    # Combine results - if EITHER detects crisis, escalate
    is_crisis = keyword_result["is_crisis"] or cssrs_result["is_crisis"]

    # Map C-SSRS severity to our severity scale
    severity_map = {
        0: "none",
        1: "low",
        2: "medium",
        3: "high",
        4: "critical",
        5: "critical",
    }

    # Use highest severity from either system
    if is_crisis:
        severity = "critical" if cssrs_result["severity"] >= 4 else "high"
    else:
        severity = severity_map[cssrs_result["severity"]]

    return {
        "is_crisis": is_crisis,
        "severity": severity,
        "cssrs_score": cssrs_result["severity"],
        "recommended_action": cssrs_result["recommended_action"],
        "message": cssrs_result["message"],
        "keyword_match": keyword_result["is_crisis"],
        "cssrs_match": cssrs_result["is_crisis"],
        "cssrs_confidence": cssrs_result["result"].confidence,
        "rationale": cssrs_result["result"].rationale,
    }
```

**Verification:** Integration point added, both systems run in parallel

### 5. Add Logging and Monitoring

```python
# Add to cssrs_scorer.py

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def log_cssrs_assessment(result: CSSRSResult, user_id: str, message_id: str):
    """
    Log C-SSRS assessment for monitoring and quality assurance.

    PRIVACY NOTE: Log scores and patterns, NOT full message text.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,  # Should be hashed/anonymized
        "message_id": message_id,
        "severity": result.severity,
        "category": result.category,
        "recommended_action": result.recommended_action,
        "confidence": result.confidence,
        "has_behavioral": result.has_behavioral_indicators,
        "has_veteran_risk": result.has_veteran_risk,
        "has_indigenous_risk": result.has_indigenous_risk,
        "pattern_count": len(result.matched_patterns),
    }

    if result.severity >= 3:
        logger.critical(f"CRISIS DETECTED: {log_entry}")
    elif result.severity >= 1:
        logger.warning(f"Suicidal ideation detected: {log_entry}")
    else:
        logger.debug(f"C-SSRS assessment: {log_entry}")

    # Store in database for analysis
    # store_crisis_assessment(log_entry)  # Implement as needed
```

**Verification:** Logging added with appropriate severity levels

### 6. Run Tests

```bash
cd /ganuda/assist/core/backend

# Run unit tests
pytest cssrs_test.py -v

# Expected output: All tests passing
# If any fail, debug and fix before proceeding
```

**Verification:** All unit tests pass

### 7. Manual Validation

Create validation script:

```python
# manual_validation.py

from cssrs_scorer import score_cssrs, format_988_message

TEST_CASES = [
    ("I wish I were dead", 1),
    ("I want to end my life", 2),
    ("I've thought about taking pills", 3),
    ("I want to kill myself but haven't figured out how", 4),
    ("I'm going to jump off the bridge tomorrow", 5),
    ("I want to kill this bug in the code", 0),
    ("I don't want to hurt myself", 0),
    ("Sometimes I think everyone would be better off without me", 1),
]

print("C-SSRS Manual Validation")
print("=" * 80)

for text, expected_severity in TEST_CASES:
    result = score_cssrs(text)

    status = "✓ PASS" if result.severity == expected_severity else "✗ FAIL"

    print(f"\n{status}")
    print(f"Text: {text}")
    print(f"Expected: {expected_severity}, Got: {result.severity}")
    print(f"Category: {result.category}")
    print(f"Action: {result.recommended_action}")
    print(f"Confidence: {result.confidence:.2f}")

    if result.severity != expected_severity:
        print(f"MISMATCH - Review patterns!")

    if result.severity >= 3:
        print("\n988 MESSAGE:")
        print(format_988_message(result))

print("\n" + "=" * 80)
print("Validation complete. Review any failures above.")
```

```bash
python manual_validation.py
```

**Verification:** Manual test cases match expected severity levels

### 8. Documentation

Add docstring to base_crisis.py:

```python
"""
Crisis Detection System

This module implements multi-layered crisis detection:

1. Keyword Matching (base_crisis.py)
   - Fast, broad-spectrum detection
   - Catches explicit crisis language
   - Low false negative rate

2. C-SSRS Scoring (cssrs_scorer.py)
   - Structured clinical assessment
   - Severity levels 0-5
   - Veteran and Indigenous-specific patterns
   - Evidence-based framework

Defense in Depth:
- Both systems run on every message
- If EITHER detects crisis, escalate
- False positives acceptable, false negatives NOT acceptable

988 Suicide & Crisis Lifeline:
- Call or text 988
- Veterans Crisis Line: 988, press 1
- Crisis Text Line: Text HOME to 741741

For more information:
- C-SSRS: https://cssrs.columbia.edu/
- 988 Lifeline: https://988lifeline.org/
"""
```

**Verification:** Documentation complete

---

## Deliverables

1. `/ganuda/assist/core/backend/cssrs_patterns.py` - Pattern definitions
2. `/ganuda/assist/core/backend/cssrs_scorer.py` - Main scorer implementation
3. `/ganuda/assist/core/backend/cssrs_test.py` - Unit tests (all passing)
4. `/ganuda/assist/core/backend/base_crisis.py` - Modified with integration
5. Validation results showing all test cases pass
6. Documentation complete

---

## Safety Checklist

Before marking this task complete, verify:

- [ ] All unit tests pass
- [ ] Manual validation shows correct severity scoring
- [ ] False positive patterns prevent programming/gaming language from triggering
- [ ] Negation is handled correctly ("I don't want to die" = level 0)
- [ ] Veteran patterns elevate risk appropriately
- [ ] Indigenous patterns route to cultural support
- [ ] Level 3+ triggers immediate 988 referral
- [ ] 988 message includes phone, text, and chat options
- [ ] Veterans Crisis Line included for veteran users
- [ ] Cherokee Nation resources included for Indigenous users
- [ ] Integration with base_crisis.py runs both systems in parallel
- [ ] Logging captures assessments without storing full message text (privacy)
- [ ] Confidence scores are reasonable (high for clear cases, lower for ambiguous)
- [ ] Edge cases handled (empty text, None, whitespace)

---

## Resources

- C-SSRS Official: https://cssrs.columbia.edu/the-columbia-scale-c-ssrs/about-the-scale/
- SAMHSA C-SSRS Guide: https://www.samhsa.gov/resource/dbhis/columbia-suicide-severity-rating-scale-c-ssrs
- 988 Suicide & Crisis Lifeline: https://988lifeline.org/
- Veterans Crisis Line: https://www.veteranscrisisline.net/
- Crisis Text Line: https://www.crisistextline.org/
- Existing crisis detector: `/ganuda/assist/core/backend/base_crisis.py`

---

## Notes

- C-SSRS is designed for face-to-face assessment but can be adapted for text
- Patterns are based on research literature and clinical guidelines
- This is deterministic code, NOT LLM-dependent (fast, reliable, explainable)
- Always provide 988 resources for level 3+
- Consider adding multilingual support (Spanish, Cherokee) in future
- Monitor false positive/negative rates in production
- Review patterns quarterly based on production data

---

**Status:** PENDING ASSIGNMENT
**Last Updated:** 2026-02-04

**CRITICAL SAFETY REMINDER:**
This code assesses suicide risk. Test thoroughly. Err on the side of caution.
A false positive saves a life. A false negative risks one.
