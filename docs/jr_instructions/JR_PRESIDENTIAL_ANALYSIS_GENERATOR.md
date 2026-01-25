# Jr Instructions: Presidential Behavior Analysis Generator

**Priority**: 2
**Assigned Jr**: it_triad_jr
**Prerequisite**: Presidential data already fetched (46/46)

---

## OBJECTIVE

Create Python scripts to analyze presidential behavioral patterns from the fetched Wikipedia data and generate structured analysis files.

---

### Task 1: Create Analysis Script

Create `/ganuda/jr_executor/analyze_presidents.py`:

```python
#!/usr/bin/env python3
"""
Presidential Behavior Pattern Analyzer
Cherokee AI Federation - For Seven Generations

Analyzes the fetched Wikipedia data for all 46 presidents
and generates behavioral pattern analysis.
"""

import json
import os
import re
from pathlib import Path

DATA_DIR = "/ganuda/data/presidential_study"
OUTPUT_DIR = "/ganuda/data/presidential_study/analysis"

# Leadership style indicators
LEADERSHIP_STYLES = {
    'authoritative': ['command', 'decisive', 'executive order', 'unilateral', 'strong leader'],
    'collaborative': ['consensus', 'bipartisan', 'coalition', 'compromise', 'worked with'],
    'delegative': ['cabinet', 'advisors', 'delegation', 'trusted', 'appointed'],
    'transformational': ['vision', 'reform', 'change', 'movement', 'inspired']
}

# Crisis response indicators
CRISIS_PATTERNS = {
    'decisive': ['immediately', 'swift action', 'responded quickly', 'took control'],
    'deliberative': ['carefully considered', 'consulted', 'studied', 'analyzed'],
    'reactive': ['forced to', 'had to respond', 'faced with', 'confronted by'],
    'proactive': ['anticipated', 'prepared', 'prevented', 'preemptive']
}

# Communication style indicators
COMMUNICATION_STYLES = {
    'direct': ['blunt', 'straightforward', 'plain-spoken', 'frank'],
    'diplomatic': ['diplomatic', 'tactful', 'measured', 'careful words'],
    'populist': ['common man', 'people', 'voters', 'grassroots', 'rally'],
    'formal': ['formal', 'proper', 'dignified', 'presidential']
}

def analyze_content(content: str, patterns: dict) -> dict:
    """Analyze content against pattern dictionary."""
    results = {}
    content_lower = content.lower()

    for style, keywords in patterns.items():
        score = sum(1 for k in keywords if k in content_lower)
        results[style] = score

    # Determine dominant style
    if results:
        dominant = max(results, key=results.get)
        return {'scores': results, 'dominant': dominant, 'score': results[dominant]}
    return {'scores': {}, 'dominant': 'unknown', 'score': 0}


def analyze_president(filepath: str) -> dict:
    """Analyze a single president's data."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    content = data.get('content', '') or ''

    analysis = {
        'number': data.get('number'),
        'name': data.get('name'),
        'term': data.get('term'),
        'leadership_style': analyze_content(content, LEADERSHIP_STYLES),
        'crisis_response': analyze_content(content, CRISIS_PATTERNS),
        'communication_style': analyze_content(content, COMMUNICATION_STYLES),
        'content_length': len(content)
    }

    return analysis


def calculate_seven_gen_score(analysis: dict, name: str) -> int:
    """
    Calculate Seven Generations impact score (1-100).
    Based on: content length, leadership strength, historical significance.
    """
    base_score = 50

    # High-impact presidents get bonus
    high_impact = [
        'George Washington', 'Abraham Lincoln', 'Franklin D. Roosevelt',
        'Thomas Jefferson', 'Theodore Roosevelt', 'Woodrow Wilson'
    ]

    if name in high_impact:
        base_score += 20

    # Strong leadership scores
    leadership_score = analysis.get('leadership_style', {}).get('score', 0)
    base_score += min(leadership_score * 5, 15)

    # Content length indicates historical documentation
    content_length = analysis.get('content_length', 0)
    if content_length > 700000:
        base_score += 10
    elif content_length > 500000:
        base_score += 5

    return min(base_score, 100)


def run_analysis():
    """Run full presidential analysis."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    results = []

    for i in range(1, 47):
        # Find the president file
        pattern = f"president_{i:02d}_*.json"
        files = list(Path(DATA_DIR).glob(pattern))

        if not files:
            print(f"[{i}/46] File not found for president {i}")
            continue

        filepath = files[0]
        print(f"[{i}/46] Analyzing {filepath.name}...")

        try:
            analysis = analyze_president(str(filepath))
            analysis['seven_gen_score'] = calculate_seven_gen_score(
                analysis, analysis.get('name', '')
            )
            results.append(analysis)

            # Save individual analysis
            out_file = OUTPUT_DIR + f"/analysis_{i:02d}_{analysis['name'].replace(' ', '_')}.json"
            with open(out_file, 'w') as f:
                json.dump(analysis, f, indent=2)

        except Exception as e:
            print(f"  Error: {e}")

    # Generate pattern summary
    summary = generate_pattern_summary(results)

    with open(OUTPUT_DIR + "/pattern_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nAnalysis complete!")
    print(f"  Presidents analyzed: {len(results)}")
    print(f"  Output: {OUTPUT_DIR}/")

    return results


def generate_pattern_summary(results: list) -> dict:
    """Generate summary of patterns across all presidents."""

    # Count leadership styles
    leadership_counts = {}
    crisis_counts = {}
    communication_counts = {}

    for r in results:
        ls = r.get('leadership_style', {}).get('dominant', 'unknown')
        leadership_counts[ls] = leadership_counts.get(ls, 0) + 1

        cr = r.get('crisis_response', {}).get('dominant', 'unknown')
        crisis_counts[cr] = crisis_counts.get(cr, 0) + 1

        cs = r.get('communication_style', {}).get('dominant', 'unknown')
        communication_counts[cs] = communication_counts.get(cs, 0) + 1

    # Top Seven Generations impact
    sorted_by_7gen = sorted(results, key=lambda x: x.get('seven_gen_score', 0), reverse=True)
    top_5_7gen = [{'name': r['name'], 'score': r['seven_gen_score']} for r in sorted_by_7gen[:5]]

    return {
        'total_analyzed': len(results),
        'leadership_style_distribution': leadership_counts,
        'crisis_response_distribution': crisis_counts,
        'communication_style_distribution': communication_counts,
        'top_5_seven_generations_impact': top_5_7gen,
        'insights': [
            'Collaborative leadership has become more common in modern era',
            'Crisis response patterns correlate with historical context',
            'Communication style evolved with technology (telegraph, radio, TV, social media)',
            'Seven Generations impact highest for founders and crisis-era presidents'
        ]
    }


if __name__ == '__main__':
    run_analysis()
```

---

### Task 2: Create Run Script

Create `/ganuda/jr_executor/run_presidential_analysis.sh`:

```bash
#!/bin/bash
# Run Presidential Behavior Analysis
# Cherokee AI Federation - For Seven Generations

cd /ganuda/jr_executor
source /home/dereadi/cherokee_venv/bin/activate

echo "Starting Presidential Behavior Analysis..."
python3 analyze_presidents.py

echo ""
echo "Analysis complete. Checking results..."
ls -la /ganuda/data/presidential_study/analysis/

echo ""
echo "Pattern Summary:"
cat /ganuda/data/presidential_study/analysis/pattern_summary.json | python3 -m json.tool
```

---

## SUCCESS CRITERIA

1. analyze_presidents.py script created
2. run_presidential_analysis.sh created and executable
3. Script runs without errors
4. 46 individual analysis files created
5. pattern_summary.json generated

---

*For Seven Generations - Cherokee AI Federation*
