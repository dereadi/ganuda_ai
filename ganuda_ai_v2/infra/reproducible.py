#!/usr/bin/env python3
"""
Reproducible Methods - Meta Jr
Cherokee Constitutional AI - Auto-Emit Manifest Decorator
Purpose: Automatically log dataset/code hashes, seeds, sample sizes for reproducibility
"""

import hashlib
import json
import inspect
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from functools import wraps
from typing import Any, Callable
import os


def _hash_dataframe(df: pd.DataFrame) -> str:
    """Calculate SHA256 hash of pandas DataFrame"""
    # Convert DataFrame to bytes for hashing
    df_bytes = pd.util.hash_pandas_object(df).values.tobytes()
    return hashlib.sha256(df_bytes).hexdigest()


def _hash_array(arr: np.ndarray) -> str:
    """Calculate SHA256 hash of numpy array"""
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _hash_code(func: Callable) -> str:
    """Calculate SHA256 hash of function source code"""
    try:
        source_code = inspect.getsource(func)
        return hashlib.sha256(source_code.encode()).hexdigest()
    except:
        # If source unavailable, hash function name
        return hashlib.sha256(func.__name__.encode()).hexdigest()


def _get_node_name() -> str:
    """Determine current node name from hostname"""
    import socket
    hostname = socket.gethostname().lower()

    if 'redfin' in hostname:
        return 'redfin'
    elif 'bluefin' in hostname:
        return 'bluefin'
    elif 'sasass' in hostname:
        return 'sasass2'
    else:
        return hostname


def emit_manifest(manifest_dir: str = './manifests', seed: int = 42):
    """
    Decorator that auto-emits reproducibility manifest for analysis functions.

    Usage:
        @emit_manifest(manifest_dir='./week2_manifests', seed=42)
        def my_analysis(df: pd.DataFrame) -> float:
            return df['temperature'].mean()

    Manifest includes:
        - dataset_hash: SHA256 of input DataFrame/array
        - code_hash: SHA256 of function source code
        - seed: Random seed used
        - n: Sample size (number of rows)
        - timestamp: UTC timestamp
        - node: Current node name (redfin/bluefin/sasass2)
        - executor: Function name
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Extract dataset from first argument (assume DataFrame or array)
            dataset = args[0] if args else None

            # Calculate dataset hash and sample size
            if isinstance(dataset, pd.DataFrame):
                dataset_hash = _hash_dataframe(dataset)
                n = len(dataset)
            elif isinstance(dataset, np.ndarray):
                dataset_hash = _hash_array(dataset)
                n = len(dataset)
            else:
                dataset_hash = 'unknown'
                n = 0

            # Calculate code hash
            code_hash = _hash_code(func)

            # Build manifest
            manifest = {
                'dataset_hash': f'sha256:{dataset_hash}',
                'code_hash': f'sha256:{code_hash}',
                'seed': seed,
                'n': n,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'node': _get_node_name(),
                'executor': func.__name__,
                'function_file': inspect.getfile(func)
            }

            # Save manifest to JSON file
            os.makedirs(manifest_dir, exist_ok=True)
            manifest_file = Path(manifest_dir) / f'{func.__name__}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'

            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)

            print(f"📋 Manifest emitted: {manifest_file}")
            print(f"   Dataset: {dataset_hash[:16]}... (n={n})")
            print(f"   Code: {code_hash[:16]}...")
            print(f"   Seed: {seed}, Node: {manifest['node']}")

            # Execute original function
            result = func(*args, **kwargs)

            return result

        return wrapper
    return decorator


# Example usage:
if __name__ == '__main__':
    # Example analysis function with auto-manifest
    @emit_manifest(manifest_dir='./example_manifests', seed=42)
    def calculate_r_squared(df: pd.DataFrame) -> float:
        """Example analysis with reproducibility tracking"""
        np.random.seed(42)
        X = df[['phase_coherence', 'access_count']].values
        y = df['temperature_score'].values

        # Simple R² calculation
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(X, y)
        r2 = model.score(X, y)

        return r2

    # Generate example data
    df = pd.DataFrame({
        'phase_coherence': np.random.rand(90),
        'access_count': np.random.randint(0, 100, 90),
        'temperature_score': np.random.rand(90) * 100
    })

    # Run analysis - manifest auto-emitted
    r2 = calculate_r_squared(df)
    print(f"\nR² = {r2:.4f}")
    print("\n✅ Reproducibility manifest automatically logged!")
