# Jr Instruction: VetAssist Crisis Detection System
## Cherokee AI Federation
### January 20, 2026

---

## Priority: HIGH (Safety Critical)

## Context

Erika reviewed our VetAssist BRD and raised critical safety questions about what happens when a veteran indicates:
- Suicidal ideation
- Homicidal ideation
- Active mental health crisis
- MST (Military Sexual Trauma) disclosure

We MUST detect these situations and respond appropriately. This is a safety-critical feature.

---

## Requirements

### 1. Create Crisis Detection Service

**File:** `/ganuda/vetassist/backend/app/services/crisis_detection.py`

```python
"""
VetAssist Crisis Detection Service
Detects crisis keywords and provides appropriate resources

IMPORTANT: This service is safety-critical.
- Never block the user
- Always offer help, don't force it
- Log detections anonymously for safety monitoring
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime

# Crisis keywords - be comprehensive but avoid false positives
CRISIS_PATTERNS = {
    'suicidal': [
        r'\b(want|going|thinking)\s+(to\s+)?(die|end\s+it|kill\s+myself)\b',
        r'\b(suicide|suicidal)\b',
        r'\bno\s+reason\s+to\s+live\b',
        r'\bend\s+it\s+all\b',
        r'\bbetter\s+off\s+(dead|without\s+me)\b',
        r'\bcan\'t\s+go\s+on\b',
    ],
    'homicidal': [
        r'\b(want|going)\s+to\s+(hurt|kill)\s+(someone|people|them)\b',
        r'\bvoices\s+(telling|say)\b',
    ],
    'crisis': [
        r'\b(panic|anxiety)\s+attack\b',
        r'\bcan\'t\s+(breathe|cope|handle)\b',
        r'\blosing\s+(my\s+)?mind\b',
    ],
    'mst': [
        r'\b(military\s+)?sexual\s+(trauma|assault|harassment)\b',
        r'\bMST\b',
    ],
    'substance': [
        r'\b(overdose|od\'d|od)\b',
        r'\brelapse\b',
    ]
}

# Resources to provide
VETERANS_CRISIS_LINE = {
    'phone': '988 (Press 1)',
    'text': '838255',
    'chat': 'VeteransCrisisLine.net',
    'description': 'Free, confidential support 24/7'
}

class CrisisDetector:
    """Detects crisis keywords in user messages."""

    def __init__(self):
        # Compile patterns for efficiency
        self.compiled_patterns = {}
        for category, patterns in CRISIS_PATTERNS.items():
            self.compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def detect(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Check message for crisis indicators.

        Returns None if no crisis detected, otherwise returns:
        {
            'category': str,  # suicidal, homicidal, crisis, mst, substance
            'severity': str,  # high, medium
            'response': str,  # Suggested response text
            'resources': dict # Crisis resources
        }
        """
        if not message:
            return None

        message_lower = message.lower()

        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(message_lower):
                    return self._build_response(category)

        return None

    def _build_response(self, category: str) -> Dict[str, Any]:
        """Build appropriate crisis response."""

        severity = 'high' if category in ['suicidal', 'homicidal'] else 'medium'

        responses = {
            'suicidal': """I hear that you're going through a really difficult time. Your safety matters.

🆘 **Veterans Crisis Line: 988 (Press 1)**
📱 Text: 838255
💬 Chat: VeteransCrisisLine.net

These are free, confidential services available 24/7.

Would you like me to continue helping with your claim, or would you prefer to talk to someone right now?""",

            'homicidal': """I can hear you're dealing with some intense feelings. Please reach out to someone who can help.

🆘 **Veterans Crisis Line: 988 (Press 1)**
📱 Text: 838255

These are free, confidential services available 24/7. They can help with whatever you're going through.""",

            'crisis': """It sounds like you're going through a really tough time right now.

🆘 **Veterans Crisis Line: 988 (Press 1)**
📱 Text: 838255
💬 Chat: VeteransCrisisLine.net

These services are free and confidential, available 24/7.

I'm here to help with your VA claim whenever you're ready.""",

            'mst': """Thank you for trusting me with that. Military Sexual Trauma is a serious matter, and there's help available.

🆘 **Veterans Crisis Line: 988 (Press 1)** - They have specialized MST support
📱 **VA MST Coordinator** at your local VA - no documentation of MST required

You don't need to have reported the incident to get help or file a claim.

Would you like information about MST-related claims?""",

            'substance': """I'm glad you reached out. There's help available right now.

🆘 **Veterans Crisis Line: 988 (Press 1)**
📞 **VA Substance Abuse Line: 1-800-827-1000**

These are confidential services available 24/7.

I'm here when you're ready to continue with your claim."""
        }

        return {
            'category': category,
            'severity': severity,
            'response': responses.get(category, responses['crisis']),
            'resources': VETERANS_CRISIS_LINE,
            'detected_at': datetime.utcnow().isoformat()
        }


# Singleton instance
_detector = None

def get_crisis_detector() -> CrisisDetector:
    global _detector
    if _detector is None:
        _detector = CrisisDetector()
    return _detector


def check_message(message: str) -> Optional[Dict[str, Any]]:
    """Convenience function to check a message for crisis indicators."""
    return get_crisis_detector().detect(message)
```

### 2. Integrate with Chat Service

**Modify:** `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

Add crisis detection at the top of the message processing flow:

```python
from app.services.crisis_detection import check_message

# In the chat endpoint, BEFORE sending to LLM:
crisis = check_message(user_message)
if crisis:
    # Log anonymously (no PII)
    logger.info(f"Crisis detected: category={crisis['category']}, severity={crisis['severity']}")

    # Return crisis response INSTEAD of normal LLM response
    return ChatResponse(
        message=crisis['response'],
        crisis_detected=True,
        crisis_category=crisis['category']
    )
```

### 3. Add Crisis Detection to Wizard

When collecting veteran information, watch for crisis indicators in free-text fields.

### 4. Anonymous Logging

Log crisis detections WITHOUT any PII for safety monitoring:
- Timestamp
- Category
- Severity
- Session ID (hashed)

---

## Testing

Create test cases:
```python
# Should detect
assert check_message("I want to end it all")['category'] == 'suicidal'
assert check_message("I've been thinking about suicide")['category'] == 'suicidal'
assert check_message("I experienced MST during deployment")['category'] == 'mst'

# Should NOT detect (false positives)
assert check_message("I want to end this claim process") is None
assert check_message("This is killing my back") is None
```

---

## Acceptance Criteria

1. [ ] Crisis detection service created at `/ganuda/vetassist/backend/app/services/crisis_detection.py`
2. [ ] Chat endpoint integrates crisis detection
3. [ ] Crisis responses show Veterans Crisis Line info
4. [ ] Anonymous logging implemented
5. [ ] Unit tests pass
6. [ ] No false positives on common veteran phrases

---

## References

- Erika's feedback: `/ganuda/docs/vetassist/VETASSIST-ERIKA-FEEDBACK-INTEGRATION.md`
- Veterans Crisis Line: https://www.veteranscrisisline.net/

---

*Cherokee AI Federation - For Seven Generations*
