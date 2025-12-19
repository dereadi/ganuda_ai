# Jr Build Instructions: Metacognition Module

## Priority: HIGH - Differentiating Feature

---

## Overview

**Metacognition**: The ability to think about thinking. The "shadow level" above Bloom's Taxonomy pyramid.

This module adds self-awareness to Cherokee AI - the ability for the system to:
1. Observe its own reasoning processes
2. Detect cognitive biases and emotional triggers
3. Calibrate uncertainty (know what it doesn't know)
4. Reflect on past decisions to improve future ones

---

## Theoretical Foundation

### Bloom's Taxonomy + Metacognition

| Level | Bloom's Name | Cherokee Current | With Metacognition |
|-------|--------------|------------------|-------------------|
| 1 | Remember | vLLM inference | Same |
| 2 | Understand | Response generation | Same |
| 3 | Apply | Task completion | Same |
| 4 | Analyze | 7-Specialist Council | Council observes its own analysis patterns |
| 5 | Evaluate | Peace Chief synthesis | Peace Chief questions its own judgments |
| 6 | Create | Novel connections | System recognizes when creating vs. recombining |
| **7** | **Metacognition** | **Not implemented** | **Self-monitoring layer** |

### Key Insight from Research

> "The highest level of thinking is this: To be able to hold your mind in your hands, examine it with honesty, reshape it with intention."

Cherokee AI should be able to do this programmatically.

---

## Architecture

### Component 1: Reasoning Tracer

Captures the "inner monologue" during inference.

```python
class ReasoningTracer:
    """
    Traces reasoning steps during Council deliberation
    """

    def __init__(self):
        self.trace = []
        self.biases_detected = []
        self.uncertainty_points = []

    def log_step(self, specialist: str, thought: str, confidence: float):
        """Log a reasoning step"""
        self.trace.append({
            'timestamp': datetime.now().isoformat(),
            'specialist': specialist,
            'thought': thought,
            'confidence': confidence,
            'step_number': len(self.trace) + 1
        })

    def detect_bias(self, bias_type: str, evidence: str):
        """Flag potential cognitive bias"""
        self.biases_detected.append({
            'type': bias_type,
            'evidence': evidence,
            'timestamp': datetime.now().isoformat()
        })

    def mark_uncertainty(self, topic: str, reason: str):
        """Mark areas of uncertainty"""
        self.uncertainty_points.append({
            'topic': topic,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })

    def get_metacognitive_summary(self) -> dict:
        """Summarize the reasoning process"""
        return {
            'total_steps': len(self.trace),
            'biases_flagged': len(self.biases_detected),
            'uncertainty_areas': len(self.uncertainty_points),
            'dominant_specialist': self._most_active_specialist(),
            'confidence_trajectory': self._confidence_over_time(),
            'self_assessment': self._generate_self_assessment()
        }
```

### Component 2: Bias Detector

Identifies common cognitive biases in reasoning.

```python
class BiasDetector:
    """
    Detects cognitive biases in Council reasoning
    """

    BIAS_PATTERNS = {
        'confirmation_bias': {
            'signals': ['confirms what we expected', 'as predicted', 'this supports'],
            'description': 'Favoring information that confirms existing beliefs'
        },
        'anchoring_bias': {
            'signals': ['starting from', 'based on initial', 'adjusting from'],
            'description': 'Over-relying on first piece of information'
        },
        'availability_heuristic': {
            'signals': ['recently saw', 'common example', 'typical case'],
            'description': 'Overweighting easily recalled information'
        },
        'groupthink': {
            'signals': ['all specialists agree', 'unanimous', 'no concerns'],
            'description': 'Excessive consensus without critical evaluation'
        },
        'sunk_cost': {
            'signals': ['already invested', 'come this far', 'can\'t abandon now'],
            'description': 'Continuing due to past investment'
        },
        'recency_bias': {
            'signals': ['just happened', 'most recent', 'latest'],
            'description': 'Overweighting recent events'
        }
    }

    def analyze_response(self, response_text: str, specialist_votes: list) -> list:
        """Analyze response for potential biases"""
        detected = []

        for bias_name, pattern in self.BIAS_PATTERNS.items():
            for signal in pattern['signals']:
                if signal.lower() in response_text.lower():
                    detected.append({
                        'bias': bias_name,
                        'description': pattern['description'],
                        'trigger': signal,
                        'severity': self._assess_severity(bias_name, response_text)
                    })

        # Check for groupthink specifically
        if self._check_groupthink(specialist_votes):
            detected.append({
                'bias': 'groupthink',
                'description': 'All specialists unanimous - may lack critical evaluation',
                'trigger': 'unanimous_vote',
                'severity': 'medium'
            })

        return detected

    def _check_groupthink(self, votes: list) -> bool:
        """Check if all specialists gave same recommendation"""
        if not votes:
            return False
        recommendations = [v.get('recommendation') for v in votes]
        return len(set(recommendations)) == 1 and len(recommendations) >= 5
```

### Component 3: Uncertainty Calibrator

Helps the system know what it doesn't know.

```python
class UncertaintyCalibrator:
    """
    Calibrates confidence levels and identifies knowledge gaps
    """

    def __init__(self):
        self.historical_accuracy = {}  # topic -> accuracy rate

    def calibrate_confidence(self,
                            raw_confidence: float,
                            topic: str,
                            specialist_agreement: float) -> dict:
        """
        Adjust confidence based on historical accuracy and agreement
        """
        # Get historical accuracy for this topic
        historical = self.historical_accuracy.get(topic, 0.7)  # default 70%

        # Calculate calibrated confidence
        calibrated = (raw_confidence * 0.4 +
                     historical * 0.3 +
                     specialist_agreement * 0.3)

        # Determine confidence level
        if calibrated > 0.85:
            level = 'high'
            caveat = None
        elif calibrated > 0.6:
            level = 'medium'
            caveat = 'Some uncertainty exists'
        else:
            level = 'low'
            caveat = 'Significant uncertainty - recommend verification'

        return {
            'raw_confidence': raw_confidence,
            'calibrated_confidence': calibrated,
            'level': level,
            'caveat': caveat,
            'factors': {
                'historical_accuracy': historical,
                'specialist_agreement': specialist_agreement
            }
        }

    def identify_knowledge_gaps(self, query: str, response: str) -> list:
        """
        Identify what the system doesn't know
        """
        gaps = []

        # Signals of uncertainty in response
        uncertainty_phrases = [
            'I\'m not sure', 'may be', 'possibly', 'uncertain',
            'don\'t have information', 'unable to determine',
            'would need more', 'depends on'
        ]

        for phrase in uncertainty_phrases:
            if phrase.lower() in response.lower():
                gaps.append({
                    'signal': phrase,
                    'context': self._extract_context(response, phrase)
                })

        return gaps
```

### Component 4: Reflection Engine

Enables learning from past decisions.

```python
class ReflectionEngine:
    """
    Enables the system to reflect on and learn from past decisions
    """

    def __init__(self, db_config: dict):
        self.db_config = db_config

    def store_decision(self, decision: dict):
        """Store decision in thermal memory for later reflection"""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO decision_reflections
            (decision_hash, query, response, confidence, biases_detected,
             uncertainty_areas, specialist_votes, outcome, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            decision['hash'],
            decision['query'],
            decision['response'],
            decision['confidence'],
            json.dumps(decision.get('biases', [])),
            json.dumps(decision.get('uncertainties', [])),
            json.dumps(decision.get('votes', [])),
            None  # Outcome filled in later
        ))

        conn.commit()
        cur.close()
        conn.close()

    def record_outcome(self, decision_hash: str, outcome: str, success: bool):
        """Record the actual outcome of a decision"""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        cur.execute("""
            UPDATE decision_reflections
            SET outcome = %s, outcome_success = %s, outcome_recorded_at = NOW()
            WHERE decision_hash = %s
        """, (outcome, success, decision_hash))

        conn.commit()
        cur.close()
        conn.close()

    def generate_reflection(self, topic: str = None, days: int = 30) -> dict:
        """
        Generate metacognitive reflection on past decisions

        Returns insights like:
        - Topics where confidence was miscalibrated
        - Biases that led to poor outcomes
        - Patterns in successful vs unsuccessful decisions
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get decisions with outcomes
        cur.execute("""
            SELECT * FROM decision_reflections
            WHERE outcome IS NOT NULL
            AND created_at > NOW() - INTERVAL '%s days'
            ORDER BY created_at DESC
        """, (days,))

        decisions = cur.fetchall()
        cur.close()
        conn.close()

        # Analyze patterns
        reflection = {
            'period_days': days,
            'total_decisions': len(decisions),
            'success_rate': self._calc_success_rate(decisions),
            'confidence_calibration': self._analyze_calibration(decisions),
            'bias_impact': self._analyze_bias_impact(decisions),
            'lessons_learned': self._extract_lessons(decisions),
            'recommendations': self._generate_recommendations(decisions)
        }

        return reflection
```

---

## Database Schema

```sql
-- Decision reflections table
CREATE TABLE decision_reflections (
    id SERIAL PRIMARY KEY,
    decision_hash VARCHAR(64) UNIQUE,
    query TEXT,
    response TEXT,
    confidence FLOAT,
    biases_detected JSONB,
    uncertainty_areas JSONB,
    specialist_votes JSONB,
    reasoning_trace JSONB,
    outcome TEXT,
    outcome_success BOOLEAN,
    outcome_recorded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bias patterns learned
CREATE TABLE learned_bias_patterns (
    id SERIAL PRIMARY KEY,
    bias_type VARCHAR(100),
    topic VARCHAR(200),
    frequency INTEGER DEFAULT 1,
    led_to_error_count INTEGER DEFAULT 0,
    last_seen TIMESTAMP,
    notes TEXT
);

-- Uncertainty calibration history
CREATE TABLE calibration_history (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(200),
    predicted_confidence FLOAT,
    actual_accuracy FLOAT,
    sample_size INTEGER,
    calibration_error FLOAT,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reflections_topic ON decision_reflections USING gin (to_tsvector('english', query));
CREATE INDEX idx_reflections_outcome ON decision_reflections (outcome_success);
CREATE INDEX idx_reflections_date ON decision_reflections (created_at DESC);
```

---

## Integration with Council

### Modified Council Vote Flow

```python
async def council_vote_with_metacognition(question: str, context: str = None):
    """
    Enhanced council vote with metacognitive monitoring
    """
    # Initialize metacognition components
    tracer = ReasoningTracer()
    bias_detector = BiasDetector()
    uncertainty_calibrator = UncertaintyCalibrator()

    # Get specialist votes (existing flow)
    votes = await gather_specialist_votes(question, context)

    # Trace each vote
    for vote in votes:
        tracer.log_step(
            specialist=vote['specialist'],
            thought=vote['reasoning'],
            confidence=vote['confidence']
        )

    # Synthesize response (existing flow)
    synthesis = peace_chief_synthesize(votes)

    # Metacognitive analysis
    biases = bias_detector.analyze_response(synthesis['response'], votes)
    for bias in biases:
        tracer.detect_bias(bias['bias'], bias['evidence'])

    # Calibrate confidence
    calibration = uncertainty_calibrator.calibrate_confidence(
        raw_confidence=synthesis['confidence'],
        topic=extract_topic(question),
        specialist_agreement=calc_agreement(votes)
    )

    # Identify knowledge gaps
    gaps = uncertainty_calibrator.identify_knowledge_gaps(question, synthesis['response'])
    for gap in gaps:
        tracer.mark_uncertainty(gap['signal'], gap['context'])

    # Get metacognitive summary
    meta_summary = tracer.get_metacognitive_summary()

    # Enhanced response
    return {
        **synthesis,
        'confidence': calibration['calibrated_confidence'],
        'confidence_level': calibration['level'],
        'caveat': calibration['caveat'],
        'metacognition': {
            'biases_detected': biases,
            'uncertainty_areas': gaps,
            'reasoning_steps': len(tracer.trace),
            'self_assessment': meta_summary['self_assessment']
        }
    }
```

---

## API Endpoints

### `/v1/council/vote` (Enhanced)

Response now includes metacognition section:

```json
{
  "question": "Should we deploy to production?",
  "recommendation": "PROCEED",
  "confidence": 0.82,
  "confidence_level": "medium",
  "caveat": "Some uncertainty exists",
  "response": "Yes, proceed with deployment...",
  "metacognition": {
    "biases_detected": [
      {
        "bias": "groupthink",
        "description": "All specialists unanimous - may lack critical evaluation",
        "severity": "low"
      }
    ],
    "uncertainty_areas": [
      {
        "signal": "depends on",
        "context": "...depends on load testing results..."
      }
    ],
    "reasoning_steps": 7,
    "self_assessment": "High agreement among specialists but limited data on load patterns"
  }
}
```

### `/v1/metacognition/reflect` (New)

Get system self-reflection:

```json
POST /v1/metacognition/reflect
{
  "topic": "security",
  "days": 30
}

Response:
{
  "period_days": 30,
  "total_decisions": 47,
  "success_rate": 0.89,
  "confidence_calibration": {
    "average_predicted": 0.82,
    "average_actual": 0.89,
    "calibration_error": 0.07,
    "assessment": "Slightly underconfident"
  },
  "bias_impact": {
    "most_common": "confirmation_bias",
    "most_harmful": "anchoring_bias",
    "improvement_areas": ["Consider more alternative viewpoints"]
  },
  "lessons_learned": [
    "Security decisions benefit from Crawdad's skepticism",
    "Performance predictions often underestimate real-world load"
  ],
  "recommendations": [
    "Increase weight of Crawdad's security concerns",
    "Add load testing data to context for deployment decisions"
  ]
}
```

### `/v1/metacognition/calibrate` (New)

Check confidence calibration:

```json
GET /v1/metacognition/calibrate?topic=deployment

Response:
{
  "topic": "deployment",
  "historical_accuracy": 0.91,
  "sample_size": 23,
  "confidence_adjustment": "+0.05",
  "recommendation": "Current confidence levels are well-calibrated for this topic"
}
```

---

## Cherokee Cultural Integration

### Two Wolves Principle Applied

The metacognition module embodies the Two Wolves teaching:

| Wolf | Role in Metacognition |
|------|----------------------|
| **Good Wolf** (Feed) | Honest self-assessment, learning from mistakes |
| **Bad Wolf** (Acknowledge) | Detecting biases, recognizing limitations |

The system feeds the good wolf by learning and improving. It acknowledges the bad wolf by being honest about biases and uncertainties.

### Seven Generations Principle

Every metacognitive reflection asks: "Will this pattern of thinking serve us for seven generations?"

```python
def seven_gen_assessment(decision_pattern: dict) -> str:
    """
    Assess if a reasoning pattern is sustainable for 175 years
    """
    concerns = []

    # Check for short-term thinking
    if decision_pattern.get('time_horizon', 0) < 365:
        concerns.append("Short time horizon - consider longer-term impacts")

    # Check for bias patterns
    if decision_pattern.get('recurring_biases'):
        concerns.append("Recurring biases may compound over generations")

    # Check for learning
    if not decision_pattern.get('learns_from_errors'):
        concerns.append("Pattern doesn't incorporate learning - will repeat mistakes")

    if not concerns:
        return "This reasoning pattern is sustainable for seven generations"
    else:
        return f"7-Gen concerns: {'; '.join(concerns)}"
```

---

## Success Criteria

1. **Bias Detection**: System flags at least 3 types of cognitive bias
2. **Confidence Calibration**: Predicted vs actual accuracy within 10%
3. **Self-Reflection**: Can generate meaningful insights from past decisions
4. **Integration**: Metacognition data appears in Council responses
5. **Learning**: System improves accuracy over time based on reflections

---

## Implementation Phases

### Phase 1: Reasoning Tracer
- Log all Council reasoning steps
- Store in thermal memory
- Basic API to query traces

### Phase 2: Bias Detection
- Implement pattern matching for 6 bias types
- Flag biases in Council responses
- Track bias frequency

### Phase 3: Uncertainty Calibration
- Track historical accuracy by topic
- Adjust confidence levels
- Identify knowledge gaps

### Phase 4: Reflection Engine
- Store decisions with outcomes
- Generate periodic reflections
- Extract lessons learned

### Phase 5: Integration
- Add metacognition to `/v1/council/vote`
- New `/v1/metacognition/*` endpoints
- Dashboard visualization in SAG

---

## Why This Matters

> "Most people don't even realize there are higher levels of thinking that you can ascend."

Cherokee AI will be one of the first AI systems that:
1. **Knows what it doesn't know**
2. **Detects its own biases**
3. **Learns from its mistakes**
4. **Can explain its reasoning process**
5. **Questions its own conclusions**

This is the differentiator. Not just intelligence, but **wisdom**.

---

*For Seven Generations*
