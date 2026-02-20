#!/usr/bin/env python3
"""
DMD Resonance Analyzer for Thermal Memory
Cherokee AI Federation - Fifth Law Mathematics
For Seven Generations
"""

import numpy as np
from pydmd import DMD
import json
from datetime import datetime

def analyze_resonance(data_matrix: np.ndarray, dt: float = 1.0):
    """
    Perform DMD analysis to find resonant modes.
    """
    # Remove rows with zero variance (all same values)
    row_stds = np.std(data_matrix, axis=1)
    valid_rows = row_stds > 1e-10
    filtered_data = data_matrix[valid_rows]
    
    if filtered_data.shape[0] < 2:
        return {'error': 'Not enough varying data for DMD analysis'}
    
    # Normalize data to avoid numerical issues
    row_means = np.mean(filtered_data, axis=1, keepdims=True)
    row_stds = np.std(filtered_data, axis=1, keepdims=True)
    row_stds[row_stds < 1e-10] = 1  # Avoid division by zero
    normalized_data = (filtered_data - row_means) / row_stds

    # DMD with truncated SVD for stability
    dmd = DMD(svd_rank=min(5, normalized_data.shape[0] - 1))
    dmd.fit(normalized_data)

    results = {
        'timestamp': datetime.now().isoformat(),
        'data_shape': list(data_matrix.shape),
        'filtered_shape': list(filtered_data.shape),
        'num_modes': len(dmd.eigs),
        'modes': [],
        'resonance_summary': {}
    }

    # Analyze each mode
    for i, eig in enumerate(dmd.eigs):
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

        results['modes'].append({
            'mode_id': i,
            'eigenvalue_real': float(eig.real),
            'eigenvalue_imag': float(eig.imag),
            'magnitude': float(magnitude),
            'frequency': float(frequency),
            'resonance_type': resonance_type
        })

    # Summarize resonance
    types = [m['resonance_type'] for m in results['modes']]
    results['resonance_summary'] = {
        'amplifying': types.count('AMPLIFYING'),
        'persistent': types.count('PERSISTENT'),
        'slow_decay': types.count('SLOW_DECAY'),
        'fast_decay': types.count('FAST_DECAY'),
        'dominant_type': max(set(types), key=types.count) if types else 'NONE'
    }

    # MSP Score: ratio of persistent/slow_decay to fast_decay
    sustained = results['resonance_summary']['persistent'] + results['resonance_summary']['slow_decay']
    fast = results['resonance_summary']['fast_decay'] + 1  # avoid div by zero
    results['msp_score'] = round(sustained / fast, 3)

    return results


if __name__ == '__main__':
    print("Loading thermal time series...")
    try:
        data = np.load('/ganuda/data/thermal_timeseries.npy')
        print(f"Loaded data shape: {data.shape}")

        print("\nPerforming DMD analysis...")
        results = analyze_resonance(data, dt=1.0)  # 1 hour intervals

        if 'error' in results:
            print(f"Error: {results['error']}")
        else:
            print(f"\nResonance Summary:")
            print(f"  Total modes: {results['num_modes']}")
            print(f"  Amplifying: {results['resonance_summary']['amplifying']}")
            print(f"  Persistent: {results['resonance_summary']['persistent']}")
            print(f"  Slow decay: {results['resonance_summary']['slow_decay']}")
            print(f"  Fast decay: {results['resonance_summary']['fast_decay']}")
            print(f"  MSP Score: {results['msp_score']}")
            print(f"  Dominant: {results['resonance_summary']['dominant_type']}")

            with open('/ganuda/data/resonance_analysis.json', 'w') as f:
                json.dump(results, f, indent=2)
            print("\nSaved to /ganuda/data/resonance_analysis.json")

    except FileNotFoundError:
        print("Run thermal_extractor.py first to generate data")
