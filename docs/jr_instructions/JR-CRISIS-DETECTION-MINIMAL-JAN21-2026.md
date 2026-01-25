# JR Instruction: Crisis Detection - Core Model Only
## Task ID: CRISIS-MINI-001
## Priority: P1 (Veteran Safety)

---

## Objective

Create minimal crisis detection model file. This is Part 1 of a larger upgrade.

---

## Implementation

Create `/ganuda/vetassist/backend/app/ml/crisis_detector.py`:

```python
#!/usr/bin/env python3
"""
Crisis Detection for VetAssist
Cherokee AI Federation - Veteran Safety Critical

Uses keyword matching with severity scoring.
Future: Upgrade to RoBERTa when context allows.
"""

import re
from typing import Dict, Tuple, List

# Crisis indicators with severity weights
CRISIS_PATTERNS = {
    'high': [
        r'\b(suicid|kill myself|end it all|want to die|better off dead)\b',
        r'\b(gun to my head|pull the trigger|overdose|hanging)\b',
        r'\b(no reason to live|cant go on|final goodbye)\b',
    ],
    'medium': [
        r'\b(hopeless|worthless|burden to everyone)\b',
        r'\b(cant take it anymore|giving up|no way out)\b',
        r'\b(self.harm|cutting myself|hurt myself)\b',
    ],
    'low': [
        r'\b(depressed|anxious|cant sleep|nightmares)\b',
        r'\b(flashbacks|ptsd|trauma|panic)\b',
        r'\b(isolated|alone|no one understands)\b',
    ]
}

CRISIS_RESOURCES = {
    'veterans_crisis_line': '988 (Press 1)',
    'crisis_text': 'Text 838255',
    'chat': 'https://www.veteranscrisisline.net/get-help/chat',
}


class CrisisDetector:
    """Detect crisis signals in veteran messages."""

    def __init__(self):
        self.compiled_patterns = {
            level: [re.compile(p, re.IGNORECASE) for p in patterns]
            for level, patterns in CRISIS_PATTERNS.items()
        }

    def analyze(self, text: str) -> Dict:
        """
        Analyze text for crisis indicators.

        Returns:
            {
                'is_crisis': bool,
                'severity': 'high'|'medium'|'low'|'none',
                'confidence': float,
                'matches': list,
                'resources': dict (if crisis detected)
            }
        """
        text_lower = text.lower()
        matches = []
        max_severity = 'none'
        severity_order = ['none', 'low', 'medium', 'high']

        for level, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    matches.append({'level': level, 'pattern': pattern.pattern})
                    if severity_order.index(level) > severity_order.index(max_severity):
                        max_severity = level

        is_crisis = max_severity in ('high', 'medium')
        confidence = min(0.5 + (len(matches) * 0.1), 0.95)

        result = {
            'is_crisis': is_crisis,
            'severity': max_severity,
            'confidence': confidence,
            'matches': matches[:5],  # Limit for privacy
        }

        if is_crisis:
            result['resources'] = CRISIS_RESOURCES
            result['message'] = self._get_response_message(max_severity)

        return result

    def _get_response_message(self, severity: str) -> str:
        if severity == 'high':
            return (
                "I'm concerned about what you've shared. "
                "Please reach out to the Veterans Crisis Line: 988 (Press 1). "
                "You matter, and help is available 24/7."
            )
        return (
            "I hear that you're going through a difficult time. "
            "The Veterans Crisis Line is available if you need support: 988 (Press 1)."
        )


# Singleton instance
_detector = None

def get_detector() -> CrisisDetector:
    global _detector
    if _detector is None:
        _detector = CrisisDetector()
    return _detector

def check_crisis(text: str) -> Dict:
    """Convenience function for crisis check."""
    return get_detector().analyze(text)
```

---

## Verification

```bash
# Test the module
cd /ganuda/vetassist/backend
python3 -c "
from app.ml.crisis_detector import check_crisis
print(check_crisis('I feel hopeless and want to give up'))
print(check_crisis('Having a good day today'))
"
```

---

*Cherokee AI Federation - Veteran Safety First*
