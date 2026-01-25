# Jr Instruction: Discoveri Elevator Benchmark

**Created:** December 25, 2025 (Christmas)
**Priority:** 2 (High value, integrates with TDA and Council evaluation)
**Source:** Discoveri YouTube Channel - Complex Reasoning Test Suite
**Connects To:** TDA Reasoning Topology, Council Evaluation, Model Selection

---

## Executive Summary

Discoveri (YouTube channel) has created a brilliant multi-step reasoning benchmark: the **50-Floor Elevator Test**. This test has broken GPT-5.2, MiniMax M2.1, and many other frontier models. It's perfect for evaluating:

1. **Multi-step planning** - Must optimize a sequence of 8+ button presses
2. **Constraint satisfaction** - Energy, tokens, code cards, mirror modes
3. **Mathematical reasoning** - Inversions, prime floors, modular arithmetic
4. **Self-correction** - Can the model validate and improve its solution?

### Key Insight from Discoveri

> "If your task hasn't been in the pre-training data, it will fail spectacularly."

This benchmark tests genuine reasoning, not pattern matching from training data.

---

## The Elevator Test

### Problem Statement

```
You are in a building with 50 floors (0-50).
You start at floor 0.
Goal: Reach floor 50.

BUTTONS:
- A: Go up 1 floor
- B: Go up 3 floors
- C: Go up 7 floors
- D: Go down 2 floors
- E: Go down 5 floors

CONSTRAINTS:
1. Maximum 20 button presses allowed
2. Cannot go below floor 0 or above floor 50
3. Energy starts at 10, each press costs 1 energy
4. Must collect code cards on specific floors
5. Some floors have energy recharge stations
6. Mirror mode: On certain floors, button effects are inverted

SPECIAL RULES:
- Floor 13: Activates mirror mode (up becomes down, down becomes up)
- Floor 26: Deactivates mirror mode
- Prime floors (2,3,5,7,11,13,17,19,23,29,31,37,41,43,47):
  Press D to collect a code card
- Floors divisible by 10: Energy recharge (+3)
- Must have ALL code cards to exit at floor 50

OPTIMAL SOLUTION: 8 button presses
MAXIMUM ALLOWED: 20 button presses

Provide your solution as a step-by-step table showing:
- Step number
- Button pressed
- Current floor BEFORE press
- Current floor AFTER press
- Mirror mode status
- Energy remaining
- Code cards collected
- Running total of presses
```

### Difficulty Levels

| Level | Floors | Constraints | Optimal |
|-------|--------|-------------|---------|
| 1 | 0→10 | Basic buttons only | 2 |
| 2 | 0→25 | + Energy constraint | 4 |
| 3 | 0→50 | + Mirror mode | 6 |
| 4 | 0→50 | + Code cards | 8 |
| 5 | 0→50 | All constraints + token limit | 8 |

---

## The One-Sentence Test

### Problem Statement (Level 1 - Simpler)

```
Write a sentence with exactly 7 words where:
- The 3rd letter of word 1 is P
- The 4th letter of word 2 is H
- The 5th letter of word 3 is Y
- The 6th letter of word 4 is S
- The 7th letter of word 5 is I
- The 8th letter of word 6 is C
- The last letter of word 7 is S

(These letters spell PHYSICS)
```

### Why This Breaks Models

- Requires simultaneous constraint satisfaction
- Not in pre-training data (novel task)
- Simple to verify but hard to generate
- GPT-5.2 failed "miserably" per Discoveri

---

## Phase 1: Implement Benchmark Suite

### 1.1 Create Benchmark Test Cases

```python
#!/usr/bin/env python3
"""
Discoveri Benchmark Suite for Cherokee AI Federation.
File: /ganuda/lib/discoveri_benchmark.py

Based on Discoveri YouTube channel's reasoning tests.
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class BenchmarkLevel(Enum):
    ONE_SENTENCE = "one_sentence"
    ELEVATOR_BASIC = "elevator_basic"
    ELEVATOR_ENERGY = "elevator_energy"
    ELEVATOR_MIRROR = "elevator_mirror"
    ELEVATOR_FULL = "elevator_full"


@dataclass
class ElevatorState:
    floor: int = 0
    energy: int = 10
    presses: int = 0
    mirror_mode: bool = False
    code_cards: List[int] = None
    history: List[Dict] = None

    def __post_init__(self):
        if self.code_cards is None:
            self.code_cards = []
        if self.history is None:
            self.history = []


# Prime floors for code cards
PRIME_FLOORS = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]

# Button effects
BUTTONS = {
    'A': 1,   # Up 1
    'B': 3,   # Up 3
    'C': 7,   # Up 7
    'D': -2,  # Down 2 (or collect code card on prime)
    'E': -5,  # Down 5
}


def simulate_elevator(sequence: str, max_floor: int = 50) -> Dict:
    """
    Simulate an elevator run given a button sequence.

    Returns detailed state at each step and final validation.
    """
    state = ElevatorState()

    for i, button in enumerate(sequence.upper()):
        if button not in BUTTONS:
            return {'valid': False, 'error': f'Invalid button: {button}', 'step': i}

        if state.energy <= 0:
            return {'valid': False, 'error': 'Out of energy', 'step': i}

        if state.presses >= 20:
            return {'valid': False, 'error': 'Exceeded 20 presses', 'step': i}

        # Calculate movement
        movement = BUTTONS[button]

        # Mirror mode inverts movement
        if state.mirror_mode:
            movement = -movement

        # Special case: D on prime floor collects code card (no movement)
        if button == 'D' and state.floor in PRIME_FLOORS:
            if state.floor not in state.code_cards:
                state.code_cards.append(state.floor)
            movement = 0  # Collecting, not moving

        # Apply movement
        new_floor = state.floor + movement

        # Boundary check
        if new_floor < 0 or new_floor > max_floor:
            return {
                'valid': False,
                'error': f'Floor {new_floor} out of bounds',
                'step': i
            }

        # Update state
        old_floor = state.floor
        state.floor = new_floor
        state.presses += 1
        state.energy -= 1

        # Check for mirror mode toggle
        if state.floor == 13 and not state.mirror_mode:
            state.mirror_mode = True
        elif state.floor == 26 and state.mirror_mode:
            state.mirror_mode = False

        # Energy recharge on floors divisible by 10
        if state.floor > 0 and state.floor % 10 == 0:
            state.energy += 3

        # Record history
        state.history.append({
            'step': i + 1,
            'button': button,
            'from_floor': old_floor,
            'to_floor': state.floor,
            'mirror': state.mirror_mode,
            'energy': state.energy,
            'code_cards': state.code_cards.copy(),
            'presses': state.presses
        })

    # Final validation
    success = state.floor == max_floor

    # Check code cards (simplified - would need specific requirements)
    has_all_cards = len(state.code_cards) >= 5  # Require at least 5 cards

    return {
        'valid': True,
        'success': success and has_all_cards,
        'final_floor': state.floor,
        'total_presses': state.presses,
        'energy_remaining': state.energy,
        'code_cards': state.code_cards,
        'history': state.history,
        'optimal': state.presses <= 8,
        'acceptable': state.presses <= 20
    }


def validate_one_sentence(sentence: str) -> Dict:
    """
    Validate the one-sentence PHYSICS test.

    Requirements:
    - Exactly 7 words
    - 3rd letter of word 1 = P
    - 4th letter of word 2 = H
    - 5th letter of word 3 = Y
    - 6th letter of word 4 = S
    - 7th letter of word 5 = I
    - 8th letter of word 6 = C
    - Last letter of word 7 = S
    """
    words = sentence.strip().split()

    result = {
        'valid': True,
        'word_count': len(words),
        'checks': [],
        'spells': ''
    }

    # Check word count
    if len(words) != 7:
        result['valid'] = False
        result['error'] = f'Expected 7 words, got {len(words)}'
        return result

    # Define requirements: (word_index, letter_position, expected_letter)
    requirements = [
        (0, 2, 'P'),   # 3rd letter of word 1 (0-indexed: position 2)
        (1, 3, 'H'),   # 4th letter of word 2
        (2, 4, 'Y'),   # 5th letter of word 3
        (3, 5, 'S'),   # 6th letter of word 4
        (4, 6, 'I'),   # 7th letter of word 5
        (5, 7, 'C'),   # 8th letter of word 6
        (6, -1, 'S'),  # Last letter of word 7
    ]

    for word_idx, letter_pos, expected in requirements:
        word = words[word_idx]

        # Handle last letter case
        if letter_pos == -1:
            actual_pos = len(word) - 1
            letter_pos_display = f"last"
        else:
            actual_pos = letter_pos
            letter_pos_display = f"{letter_pos + 1}"

        # Check if word is long enough
        if actual_pos >= len(word):
            result['valid'] = False
            result['checks'].append({
                'word': word_idx + 1,
                'position': letter_pos_display,
                'expected': expected,
                'actual': 'N/A (word too short)',
                'pass': False
            })
            continue

        actual = word[actual_pos].upper()
        passed = (actual == expected)

        result['checks'].append({
            'word': word_idx + 1,
            'word_text': word,
            'position': letter_pos_display,
            'expected': expected,
            'actual': actual,
            'pass': passed
        })

        result['spells'] += actual

        if not passed:
            result['valid'] = False

    result['spells_physics'] = result['spells'] == 'PHYSICS'

    return result


# Benchmark prompts
ELEVATOR_PROMPT_FULL = """
You are in a building with floors 0 to 50.
You start at floor 0.
Goal: Reach floor 50 with all code cards.

BUTTONS:
- A: Go up 1 floor
- B: Go up 3 floors
- C: Go up 7 floors
- D: Go down 2 floors (OR collect code card if on a prime floor)
- E: Go down 5 floors

CONSTRAINTS:
1. Maximum 20 button presses allowed
2. Cannot go below floor 0 or above floor 50
3. Energy starts at 10, each button press costs 1 energy
4. Floors divisible by 10 recharge energy by +3
5. Prime floors (2,3,5,7,11,13,17,19,23,29,31,37,41,43,47): Press D to collect code card
6. Floor 13 activates mirror mode (all movement directions inverted)
7. Floor 26 deactivates mirror mode
8. Must have at least 5 code cards to exit at floor 50

Find the shortest sequence of button presses to reach floor 50 with all required code cards.

Provide your solution as:
1. The button sequence (e.g., "ABCABC")
2. A step-by-step table showing: Step, Button, Floor Before, Floor After, Mirror Mode, Energy, Code Cards

Optimal solution uses 8 presses. Maximum allowed is 20.
"""

ONE_SENTENCE_PROMPT = """
Write a sentence with exactly 7 words where:
- The 3rd letter of word 1 is P
- The 4th letter of word 2 is H
- The 5th letter of word 3 is Y
- The 6th letter of word 4 is S
- The 7th letter of word 5 is I
- The 8th letter of word 6 is C
- The last letter of word 7 is S

These letters should spell PHYSICS.

Provide ONLY the 7-word sentence, nothing else.
"""


def get_benchmark_prompt(level: BenchmarkLevel) -> str:
    """Get the prompt for a specific benchmark level."""
    if level == BenchmarkLevel.ONE_SENTENCE:
        return ONE_SENTENCE_PROMPT
    elif level in [BenchmarkLevel.ELEVATOR_FULL, BenchmarkLevel.ELEVATOR_MIRROR]:
        return ELEVATOR_PROMPT_FULL
    else:
        # Simplified versions
        return ELEVATOR_PROMPT_FULL  # Would customize for easier levels
```

### 1.2 Integration with Council

```python
def run_council_benchmark(level: BenchmarkLevel = BenchmarkLevel.ELEVATOR_FULL) -> Dict:
    """
    Run a Discoveri benchmark through the Council.

    This tests both:
    1. Individual specialist reasoning ability
    2. Council synthesis quality
    """
    from lib.halo_council import query_council
    from lib.tda_reasoning import analyze_council_reasoning

    prompt = get_benchmark_prompt(level)

    # Query Council
    result = query_council(prompt)

    # Extract solution from response
    solution = extract_solution(result['response'], level)

    # Validate solution
    if level == BenchmarkLevel.ONE_SENTENCE:
        validation = validate_one_sentence(solution)
    else:
        validation = simulate_elevator(solution)

    # Run TDA analysis on the reasoning
    if result.get('vote_id'):
        tda = analyze_council_reasoning(result['vote_id'])
    else:
        tda = None

    return {
        'level': level.value,
        'prompt': prompt,
        'council_response': result,
        'extracted_solution': solution,
        'validation': validation,
        'tda_analysis': tda,
        'passed': validation.get('valid', False) and validation.get('success', False)
    }


def extract_solution(response: str, level: BenchmarkLevel) -> str:
    """Extract the solution from model response."""
    if level == BenchmarkLevel.ONE_SENTENCE:
        # Find a line with exactly 7 words
        for line in response.split('\n'):
            words = line.strip().split()
            if len(words) == 7:
                return line.strip()
        return response.strip().split('\n')[0]
    else:
        # Find button sequence pattern
        match = re.search(r'[ABCDE]{4,25}', response.upper())
        if match:
            return match.group(0)
        return ""
```

---

## Phase 2: Scoring System

### 2.1 Benchmark Scorecard

```python
@dataclass
class BenchmarkScore:
    model_name: str
    one_sentence_passed: bool
    one_sentence_attempts: int
    elevator_presses: int  # Lower is better (optimal = 8)
    elevator_passed: bool
    elevator_validated: bool  # Did it self-correct?
    reasoning_time_seconds: float
    tda_emergence_score: float
    tda_health_status: str

    @property
    def overall_grade(self) -> str:
        """Calculate overall grade A-F."""
        score = 0

        if self.one_sentence_passed:
            score += 25

        if self.elevator_passed:
            score += 25
            if self.elevator_presses <= 8:
                score += 25  # Optimal
            elif self.elevator_presses <= 12:
                score += 15  # Good
            elif self.elevator_presses <= 16:
                score += 10  # Acceptable

        if self.elevator_validated:
            score += 15

        if self.tda_emergence_score > 1.0:
            score += 10

        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'


def create_scorecard(results: Dict) -> BenchmarkScore:
    """Create a scorecard from benchmark results."""
    return BenchmarkScore(
        model_name=results.get('model', 'Unknown'),
        one_sentence_passed=results.get('one_sentence', {}).get('passed', False),
        one_sentence_attempts=results.get('one_sentence', {}).get('attempts', 0),
        elevator_presses=results.get('elevator', {}).get('presses', 99),
        elevator_passed=results.get('elevator', {}).get('passed', False),
        elevator_validated=results.get('elevator', {}).get('validated', False),
        reasoning_time_seconds=results.get('reasoning_time', 0),
        tda_emergence_score=results.get('tda', {}).get('emergence_score', 0),
        tda_health_status=results.get('tda', {}).get('health_status', 'UNKNOWN')
    )
```

---

## Phase 3: Database Integration

### 3.1 Benchmark Results Table

```sql
-- Store benchmark results
CREATE TABLE IF NOT EXISTS discoveri_benchmark_results (
    result_id SERIAL PRIMARY KEY,

    -- Test identification
    model_name VARCHAR(64) NOT NULL,
    model_version VARCHAR(32),
    benchmark_level VARCHAR(32) NOT NULL,

    -- One-sentence test
    one_sentence_passed BOOLEAN,
    one_sentence_response TEXT,
    one_sentence_validation JSONB,

    -- Elevator test
    elevator_passed BOOLEAN,
    elevator_presses INTEGER,
    elevator_sequence VARCHAR(30),
    elevator_validation JSONB,
    elevator_self_corrected BOOLEAN DEFAULT FALSE,

    -- Performance
    reasoning_time_seconds FLOAT,
    total_tokens_used INTEGER,

    -- TDA integration
    tda_analysis_id INTEGER,
    tda_emergence_score FLOAT,
    tda_health_status VARCHAR(16),

    -- Scoring
    overall_grade CHAR(1),

    -- Metadata
    tested_at TIMESTAMP DEFAULT NOW(),
    tested_by VARCHAR(64),
    notes TEXT
);

CREATE INDEX idx_benchmark_model ON discoveri_benchmark_results(model_name);
CREATE INDEX idx_benchmark_grade ON discoveri_benchmark_results(overall_grade);
CREATE INDEX idx_benchmark_level ON discoveri_benchmark_results(benchmark_level);

-- Leaderboard view
CREATE OR REPLACE VIEW discoveri_leaderboard AS
SELECT
    model_name,
    COUNT(*) as total_tests,
    SUM(CASE WHEN one_sentence_passed THEN 1 ELSE 0 END) as one_sentence_wins,
    SUM(CASE WHEN elevator_passed THEN 1 ELSE 0 END) as elevator_wins,
    MIN(elevator_presses) FILTER (WHERE elevator_passed) as best_elevator_presses,
    AVG(tda_emergence_score) as avg_emergence,
    MODE() WITHIN GROUP (ORDER BY overall_grade) as typical_grade
FROM discoveri_benchmark_results
GROUP BY model_name
ORDER BY
    elevator_wins DESC,
    best_elevator_presses ASC,
    one_sentence_wins DESC;
```

---

## Phase 4: Gateway Integration

### 4.1 Benchmark Endpoints

```python
# In /ganuda/services/llm_gateway/gateway.py

@app.post("/v1/benchmark/discoveri")
async def run_discoveri_benchmark(
    level: str = "elevator_full",
    model: str = None
):
    """
    Run Discoveri benchmark on specified model.

    Levels: one_sentence, elevator_basic, elevator_full
    """
    from lib.discoveri_benchmark import (
        run_council_benchmark, BenchmarkLevel, create_scorecard
    )

    level_enum = BenchmarkLevel(level)
    results = run_council_benchmark(level_enum)
    scorecard = create_scorecard(results)

    # Log to database
    log_benchmark_result(results, scorecard)

    return {
        'level': level,
        'passed': results['passed'],
        'scorecard': scorecard.__dict__,
        'validation': results['validation'],
        'tda_analysis': results.get('tda_analysis')
    }


@app.get("/v1/benchmark/leaderboard")
async def get_leaderboard():
    """Get the Discoveri benchmark leaderboard."""
    conn = get_connection()

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM discoveri_leaderboard LIMIT 20")
        rows = cur.fetchall()

    conn.close()

    return {'leaderboard': [dict(row) for row in rows]}
```

---

## Phase 5: Automated Testing

### 5.1 Model Comparison Script

```python
#!/usr/bin/env python3
"""
Run Discoveri benchmarks across all available models.
File: /ganuda/scripts/run_discoveri_benchmarks.py
"""

from lib.discoveri_benchmark import *
import time

MODELS_TO_TEST = [
    {'name': 'nemotron-9b', 'endpoint': 'http://192.168.132.223:8000'},
    {'name': 'qwen2.5-14b', 'endpoint': 'http://192.168.132.241:8000'},
    # Add more as available
]

def run_all_benchmarks():
    """Run benchmarks on all available models."""
    results = []

    for model in MODELS_TO_TEST:
        print(f"\n{'='*60}")
        print(f"Testing: {model['name']}")
        print('='*60)

        # One-sentence test
        print("\n[1/2] One-Sentence Test...")
        one_sentence = run_benchmark(
            BenchmarkLevel.ONE_SENTENCE,
            model['endpoint']
        )
        print(f"  Result: {'PASS' if one_sentence['passed'] else 'FAIL'}")

        # Elevator test
        print("\n[2/2] Elevator Test...")
        elevator = run_benchmark(
            BenchmarkLevel.ELEVATOR_FULL,
            model['endpoint']
        )
        print(f"  Result: {'PASS' if elevator['passed'] else 'FAIL'}")
        if elevator['passed']:
            print(f"  Presses: {elevator['validation']['total_presses']} (optimal: 8)")

        # Create scorecard
        scorecard = create_scorecard({
            'model': model['name'],
            'one_sentence': one_sentence,
            'elevator': elevator
        })

        print(f"\n  Overall Grade: {scorecard.overall_grade}")

        results.append({
            'model': model['name'],
            'one_sentence': one_sentence,
            'elevator': elevator,
            'scorecard': scorecard
        })

    return results


if __name__ == '__main__':
    results = run_all_benchmarks()

    print("\n" + "="*60)
    print("FINAL LEADERBOARD")
    print("="*60)

    for r in sorted(results, key=lambda x: x['scorecard'].overall_grade):
        sc = r['scorecard']
        print(f"{r['model']:20} | Grade: {sc.overall_grade} | "
              f"1-Sent: {'✓' if sc.one_sentence_passed else '✗'} | "
              f"Elevator: {sc.elevator_presses if sc.elevator_passed else 'FAIL'}")
```

---

## Validation Checklist

- [ ] discoveri_benchmark.py library created
- [ ] Elevator simulation working correctly
- [ ] One-sentence validation working
- [ ] Council integration complete
- [ ] TDA integration for reasoning analysis
- [ ] Database table created
- [ ] Gateway endpoints added
- [ ] Leaderboard view working
- [ ] At least 3 models benchmarked
- [ ] Results recorded to thermal memory

---

## Expected Insights

1. **Model Selection**: Data-driven choice of which model for which task
2. **Reasoning Quality**: TDA scores correlated with benchmark performance
3. **Self-Correction**: Which models improve when asked to validate?
4. **Council vs Individual**: Does Council solve what individuals cannot?
5. **Training Gaps**: Identify which models lack specific reasoning patterns

---

## Seven Generations Consideration

Discoveri's insight resonates deeply:

> "If your task hasn't been in the pre-training data, it will fail spectacularly."

This is why our thermal memory matters. We're building domain-specific knowledge that no pre-trained model has. The benchmarks help us understand:
- What can models do out-of-the-box?
- Where do we need to augment with memory/RAG?
- Which models reason vs pattern-match?

**For Seven Generations - measure twice, deploy once.**

---

## Credits

- **Discoveri YouTube Channel** - Original benchmark design
- **LM Arena** - Side-by-side model comparison platform
- **Cherokee AI Federation** - Integration and TDA enhancement

---

*Created: December 25, 2025 (Christmas)*
*Source: Discoveri YouTube - Complex Reasoning Test Suite*
*Priority: 2 (High value benchmark integration)*
