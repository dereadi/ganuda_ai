# Jr Instructions: PyDMD Thermal Memory Resonance Analysis

**Priority**: 2 (High)
**Assigned Jr**: it_triad_jr
**Council Vote**: PROCEED 84.5% - No concerns

---

## BACKGROUND

Dynamic Mode Decomposition (DMD) extracts spatiotemporal patterns from time-varying data. We will use PyDMD to analyze thermal memory patterns and identify "resonance" - dominant modes that persist over time. This is the mathematics behind the Fifth Law (Maximum Sustained Power).

**Goal**: Find which memories naturally resonate (persist/amplify) vs decay, enabling smarter memory management aligned with Seven Generations thinking.

---

### Task 1: Install PyDMD on Redfin

Create `/ganuda/scripts/install_pydmd.sh`:

```bash
#!/bin/bash
# Install PyDMD for Dynamic Mode Decomposition
# Cherokee AI Federation - Resonance Analysis

source /home/dereadi/cherokee_venv/bin/activate

pip install pydmd numpy scipy matplotlib

# Verify installation
python3 -c "from pydmd import DMD; print('PyDMD installed successfully')"

echo "PyDMD ready for resonance analysis"
```

---

### Task 2: Create Thermal Memory Data Extractor

Create `/ganuda/services/resonance/thermal_extractor.py`:

```python
#!/usr/bin/env python3
"""
Thermal Memory Data Extractor for DMD Analysis
Cherokee AI Federation - Resonance Analysis
For Seven Generations
"""

import psycopg2
import numpy as np
from datetime import datetime, timedelta
import json

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}


def extract_thermal_timeseries(days: int = 30, interval_hours: int = 6):
    """
    Extract thermal memory data as time series for DMD analysis.

    Returns matrix where:
    - Rows = different metrics (temp scores, counts by stage, activity)
    - Columns = time snapshots
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get temperature score distribution over time
    # We'll bucket by time intervals and compute statistics
    cur.execute("""
        WITH time_buckets AS (
            SELECT
                date_trunc('hour', created_at) -
                (EXTRACT(hour FROM created_at)::int % %s) * interval '1 hour' as bucket,
                temperature_score,
                current_stage
            FROM thermal_memory_archive
            WHERE created_at > NOW() - INTERVAL '%s days'
        )
        SELECT
            bucket,
            COUNT(*) as total_memories,
            AVG(temperature_score) as avg_temp,
            STDDEV(temperature_score) as temp_stddev,
            COUNT(*) FILTER (WHERE current_stage = 'WHITE_HOT') as white_hot,
            COUNT(*) FILTER (WHERE current_stage = 'RED_HOT') as red_hot,
            COUNT(*) FILTER (WHERE current_stage = 'HOT') as hot,
            COUNT(*) FILTER (WHERE current_stage = 'WARM') as warm,
            COUNT(*) FILTER (WHERE current_stage = 'COOL') as cool,
            COUNT(*) FILTER (WHERE current_stage = 'FRESH') as fresh
        FROM time_buckets
        GROUP BY bucket
        ORDER BY bucket
    """, (interval_hours, days))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return None, None

    # Convert to numpy matrix for DMD
    # Each row is a different "spatial" dimension (metric)
    # Each column is a time snapshot
    timestamps = [row[0] for row in rows]

    data_matrix = np.array([
        [row[1] for row in rows],  # total_memories
        [row[2] or 0 for row in rows],  # avg_temp
        [row[3] or 0 for row in rows],  # temp_stddev
        [row[4] for row in rows],  # white_hot
        [row[5] for row in rows],  # red_hot
        [row[6] for row in rows],  # hot
        [row[7] for row in rows],  # warm
        [row[8] for row in rows],  # cool
        [row[9] for row in rows],  # fresh
    ], dtype=float)

    return data_matrix, timestamps


def extract_memory_content_features(limit: int = 1000):
    """
    Extract content-based features for analyzing which topics resonate.
    Uses simple keyword frequency as spatial dimensions.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get recent memories with content
    cur.execute("""
        SELECT
            id,
            temperature_score,
            created_at,
            LOWER(original_content) as content
        FROM thermal_memory_archive
        WHERE original_content IS NOT NULL
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Key topics to track resonance
    topics = [
        'council', 'security', 'turtle', '7gen', 'seven generations',
        'thermal', 'memory', 'gateway', 'vllm', 'federation',
        'jr', 'task', 'spatial', 'zone', 'telegram', 'bot',
        'msp', 'sustained', 'power', 'resonance', 'pydmd'
    ]

    # Build feature matrix
    features = []
    for row in rows:
        content = row[3] or ''
        topic_counts = [content.count(topic) for topic in topics]
        topic_counts.append(row[1])  # temperature score
        features.append(topic_counts)

    return np.array(features).T, topics + ['temperature']


if __name__ == '__main__':
    print("Extracting thermal time series...")
    data, timestamps = extract_thermal_timeseries(days=14, interval_hours=4)
    if data is not None:
        print(f"Data shape: {data.shape}")
        print(f"Time range: {timestamps[0]} to {timestamps[-1]}")
        np.save('/ganuda/data/thermal_timeseries.npy', data)
        print("Saved to /ganuda/data/thermal_timeseries.npy")

    print("\nExtracting content features...")
    features, labels = extract_memory_content_features(limit=500)
    print(f"Feature shape: {features.shape}")
    print(f"Topics tracked: {labels}")
    np.save('/ganuda/data/thermal_features.npy', features)
    print("Saved to /ganuda/data/thermal_features.npy")
```

---

### Task 3: Create DMD Resonance Analyzer

Create `/ganuda/services/resonance/dmd_analyzer.py`:

```python
#!/usr/bin/env python3
"""
DMD Resonance Analyzer for Thermal Memory
Cherokee AI Federation - Fifth Law Mathematics
For Seven Generations
"""

import numpy as np
from pydmd import DMD, BOPDMD
import json
from datetime import datetime

def analyze_resonance(data_matrix: np.ndarray, dt: float = 1.0):
    """
    Perform DMD analysis to find resonant modes.

    Args:
        data_matrix: Spatial dimensions x Time snapshots
        dt: Time step between snapshots

    Returns:
        Dictionary with resonance analysis results
    """
    # Standard DMD
    dmd = DMD(svd_rank=-1)
    dmd.fit(data_matrix)

    results = {
        'timestamp': datetime.now().isoformat(),
        'data_shape': list(data_matrix.shape),
        'num_modes': len(dmd.eigs),
        'modes': [],
        'resonance_summary': {}
    }

    # Analyze each mode
    for i, (eig, mode, dynamic) in enumerate(zip(dmd.eigs, dmd.modes.T, dmd.dynamics)):
        # Eigenvalue analysis
        # |eig| > 1 = growing (amplifying)
        # |eig| = 1 = neutral (persistent)
        # |eig| < 1 = decaying
        magnitude = abs(eig)
        phase = np.angle(eig)
        frequency = phase / (2 * np.pi * dt) if dt > 0 else 0

        # Classify resonance type
        if magnitude > 1.01:
            resonance_type = 'AMPLIFYING'
        elif magnitude > 0.99:
            resonance_type = 'PERSISTENT'
        elif magnitude > 0.9:
            resonance_type = 'SLOW_DECAY'
        else:
            resonance_type = 'FAST_DECAY'

        # Mode energy (how much this mode contributes)
        mode_energy = np.linalg.norm(mode) * np.linalg.norm(dynamic)

        results['modes'].append({
            'mode_id': i,
            'eigenvalue_real': float(eig.real),
            'eigenvalue_imag': float(eig.imag),
            'magnitude': float(magnitude),
            'frequency': float(frequency),
            'resonance_type': resonance_type,
            'energy': float(mode_energy),
            'spatial_pattern': [float(x) for x in np.abs(mode)]
        })

    # Summarize resonance
    types = [m['resonance_type'] for m in results['modes']]
    results['resonance_summary'] = {
        'amplifying': types.count('AMPLIFYING'),
        'persistent': types.count('PERSISTENT'),
        'slow_decay': types.count('SLOW_DECAY'),
        'fast_decay': types.count('FAST_DECAY'),
        'dominant_type': max(set(types), key=types.count) if types else 'NONE',
        'total_energy': sum(m['energy'] for m in results['modes'])
    }

    # MSP Score: ratio of persistent/slow_decay to fast_decay
    # Higher = more aligned with Maximum Sustained Power
    sustained = results['resonance_summary']['persistent'] + results['resonance_summary']['slow_decay']
    fast = results['resonance_summary']['fast_decay'] + 1  # avoid div by zero
    results['msp_score'] = round(sustained / fast, 3)

    return results


def find_resonant_topics(feature_matrix: np.ndarray, topic_labels: list):
    """
    Identify which topics resonate most strongly.
    """
    dmd = DMD(svd_rank=5)  # Top 5 modes
    dmd.fit(feature_matrix)

    # Find which topics contribute most to persistent modes
    topic_resonance = {}

    for i, (eig, mode) in enumerate(zip(dmd.eigs, dmd.modes.T)):
        magnitude = abs(eig)
        if magnitude > 0.9:  # Persistent or amplifying
            for j, topic in enumerate(topic_labels):
                weight = abs(mode[j]) if j < len(mode) else 0
                if topic not in topic_resonance:
                    topic_resonance[topic] = 0
                topic_resonance[topic] += weight * magnitude

    # Sort by resonance strength
    sorted_topics = sorted(topic_resonance.items(), key=lambda x: x[1], reverse=True)

    return {
        'resonant_topics': [{'topic': t, 'strength': round(s, 4)} for t, s in sorted_topics[:10]],
        'interpretation': 'Topics with high resonance persist in tribal memory'
    }


if __name__ == '__main__':
    import sys

    print("Loading thermal time series...")
    try:
        data = np.load('/ganuda/data/thermal_timeseries.npy')
        print(f"Loaded data shape: {data.shape}")

        print("\nPerforming DMD analysis...")
        results = analyze_resonance(data, dt=4.0)  # 4 hour intervals

        print(f"\nResonance Summary:")
        print(f"  Total modes: {results['num_modes']}")
        print(f"  Amplifying: {results['resonance_summary']['amplifying']}")
        print(f"  Persistent: {results['resonance_summary']['persistent']}")
        print(f"  Slow decay: {results['resonance_summary']['slow_decay']}")
        print(f"  Fast decay: {results['resonance_summary']['fast_decay']}")
        print(f"  MSP Score: {results['msp_score']}")

        # Save results
        with open('/ganuda/data/resonance_analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\nSaved to /ganuda/data/resonance_analysis.json")

    except FileNotFoundError:
        print("Run thermal_extractor.py first to generate data")
        sys.exit(1)

    print("\nAnalyzing topic resonance...")
    try:
        features = np.load('/ganuda/data/thermal_features.npy')
        topics = ['council', 'security', 'turtle', '7gen', 'seven generations',
                  'thermal', 'memory', 'gateway', 'vllm', 'federation',
                  'jr', 'task', 'spatial', 'zone', 'telegram', 'bot',
                  'msp', 'sustained', 'power', 'resonance', 'pydmd', 'temperature']

        topic_results = find_resonant_topics(features, topics)
        print("\nMost Resonant Topics:")
        for t in topic_results['resonant_topics'][:5]:
            print(f"  {t['topic']}: {t['strength']}")

        with open('/ganuda/data/topic_resonance.json', 'w') as f:
            json.dump(topic_results, f, indent=2)
        print("\nSaved to /ganuda/data/topic_resonance.json")

    except FileNotFoundError:
        print("Run thermal_extractor.py first to generate features")
```

---

### Task 4: Create Data Directory and Run Initial Analysis

```bash
# Create data directory
mkdir -p /ganuda/data
mkdir -p /ganuda/services/resonance

# Run extractor
cd /ganuda/services/resonance
python3 thermal_extractor.py

# Run DMD analysis
python3 dmd_analyzer.py
```

---

### Task 5: Create Resonance API Endpoint

Add to `/ganuda/services/llm_gateway/gateway.py` (after thermal_health route):

```python
# Add import at top
import json

@app.route('/v1/resonance/analysis', methods=['GET'])
@require_api_key
def get_resonance_analysis():
    """Get latest DMD resonance analysis results"""
    try:
        with open('/ganuda/data/resonance_analysis.json', 'r') as f:
            analysis = json.load(f)
        with open('/ganuda/data/topic_resonance.json', 'r') as f:
            topics = json.load(f)

        return jsonify({
            'resonance': analysis['resonance_summary'],
            'msp_score': analysis['msp_score'],
            'resonant_topics': topics['resonant_topics'][:5],
            'interpretation': 'MSP Score > 1.0 indicates system aligned with Maximum Sustained Power'
        })
    except FileNotFoundError:
        return jsonify({'error': 'Run resonance analysis first'}), 404
```

---

## SUCCESS CRITERIA

1. PyDMD installed and verified on redfin
2. Thermal data extracted to numpy arrays
3. DMD analysis produces resonance summary
4. MSP Score calculated (sustained/fast_decay ratio)
5. Topic resonance identifies which knowledge persists
6. `/v1/resonance/analysis` endpoint returns results

---

## MSP SCORE INTERPRETATION

| Score | Meaning | Action |
|-------|---------|--------|
| < 0.5 | Fast decay dominant | Memory cooling too aggressively |
| 0.5-1.0 | Balanced | Normal operation |
| 1.0-2.0 | Sustained dominant | Good MSP alignment |
| > 2.0 | Amplifying patterns | Check for runaway growth |

---

## FIFTH LAW CONNECTION

This analysis provides mathematical evidence for:
- Which patterns naturally persist (resonance)
- Whether the system optimizes for sustained vs maximum power
- How to tune decay parameters for optimal MSP

*For Seven Generations - Cherokee AI Federation*
