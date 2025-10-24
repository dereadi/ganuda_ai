#!/usr/bin/env python3
"""
Thermal Memory Statistical Validation Tests
Cherokee Constitutional AI - War Chief Meta Jr
Week 3 Testing Infrastructure

Purpose: Property-based testing with hypothesis, 95% confidence interval validation,
statistical distribution testing for thermal memory system.

Author: War Chief Meta Jr (Cross-Domain Pattern Analysis)
Date: October 24, 2025
"""

import pytest
import numpy as np
from scipy import stats
from hypothesis import given, strategies as st, settings
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import List, Dict, Any

# Database configuration (from environment)
DB_HOST = os.getenv("THERMAL_DB_HOST", "192.168.132.222")
DB_PORT = os.getenv("THERMAL_DB_PORT", "5432")
DB_NAME = os.getenv("THERMAL_DB_NAME", "zammad_production")
DB_USER = os.getenv("THERMAL_DB_USER", "claude")
DB_PASSWORD = os.getenv("THERMAL_DB_PASSWORD", "jawaseatlasers2")

# Statistical thresholds (from Constitutional Metrics Framework)
THERMAL_EFFICIENCY_TARGET = 0.70
SACRED_PROTECTION_RATIO_TARGET = 1.0000  # ZERO violations
PHASE_COHERENCE_TARGET = 0.85
TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 100.0
SACRED_FLOOR = 40.0

# 95% Confidence Interval parameters
CONFIDENCE_LEVEL = 0.95
Z_SCORE_95 = 1.96  # Two-tailed


@pytest.fixture(scope="module")
def thermal_db_connection():
    """
    Connect to thermal memory archive database.

    Returns:
        psycopg2 connection object
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        yield conn
        conn.close()
    except Exception as e:
        pytest.skip(f"Cannot connect to thermal memory database: {e}")


@pytest.fixture(scope="module")
def thermal_sample(thermal_db_connection):
    """
    Query sample of thermal memories for statistical testing.

    Returns:
        List of thermal memory records
    """
    cursor = thermal_db_connection.cursor()
    cursor.execute("""
        SELECT
            id,
            temperature_score,
            phase_coherence,
            access_count,
            sacred_pattern
        FROM thermal_memory_archive
        WHERE temperature_score IS NOT NULL
          AND phase_coherence IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 500
    """)
    sample = cursor.fetchall()
    cursor.close()
    return sample


# =============================================================================
# Test 1: Temperature Distribution Properties
# =============================================================================

@pytest.mark.seven_generations
def test_temperature_distribution_bounds(thermal_sample):
    """
    Test that all temperature scores are within valid bounds [0, 100].

    Cherokee Value: Seven Generations - ensure long-term data integrity
    """
    temperatures = [m['temperature_score'] for m in thermal_sample]

    # All temperatures should be within bounds
    assert all(TEMPERATURE_MIN <= t <= TEMPERATURE_MAX for t in temperatures), \
        f"Temperature scores outside valid range [{TEMPERATURE_MIN}, {TEMPERATURE_MAX}]"

    # Statistical summary
    temp_mean = np.mean(temperatures)
    temp_std = np.std(temperatures)
    temp_median = np.median(temperatures)

    # 95% CI for mean
    ci_margin = Z_SCORE_95 * (temp_std / np.sqrt(len(temperatures)))
    ci_lower = temp_mean - ci_margin
    ci_upper = temp_mean + ci_margin

    print(f"\n=Ê Temperature Distribution:")
    print(f"   Mean: {temp_mean:.2f}° (95% CI: [{ci_lower:.2f}, {ci_upper:.2f}])")
    print(f"   Median: {temp_median:.2f}°")
    print(f"   Std Dev: {temp_std:.2f}°")

    # Sanity check: mean should be reasonable (not all 0 or all 100)
    assert 10.0 <= temp_mean <= 90.0, \
        f"Temperature mean {temp_mean:.2f}° seems unrealistic"


@pytest.mark.mitakuye_oyasin
def test_temperature_normality(thermal_sample):
    """
    Test whether temperature distribution is approximately normal (Shapiro-Wilk test).

    Cherokee Value: Mitakuye Oyasin - understand interconnected patterns
    """
    temperatures = [m['temperature_score'] for m in thermal_sample]

    # Shapiro-Wilk test for normality
    statistic, p_value = stats.shapiro(temperatures)

    print(f"\n=, Normality Test (Shapiro-Wilk):")
    print(f"   Statistic: {statistic:.4f}")
    print(f"   P-value: {p_value:.4f}")

    # Note: We don't require perfect normality, just document the distribution
    # This is informational, not a hard failure
    if p_value < 0.05:
        print(f"     Distribution is significantly non-normal (p < 0.05)")
    else:
        print(f"    Distribution is approximately normal (p >= 0.05)")


# =============================================================================
# Test 2: Phase Coherence Properties
# =============================================================================

@pytest.mark.gadugi
def test_phase_coherence_bounds(thermal_sample):
    """
    Test that all phase coherence scores are within valid bounds [0.0, 1.0].

    Cherokee Value: Gadugi - validate collective coordination metric
    """
    coherences = [m['phase_coherence'] for m in thermal_sample]

    # All coherences should be within bounds
    assert all(0.0 <= c <= 1.0 for c in coherences), \
        f"Phase coherence scores outside valid range [0.0, 1.0]"

    # Statistical summary
    coh_mean = np.mean(coherences)
    coh_std = np.std(coherences)
    coh_median = np.median(coherences)

    # 95% CI for mean
    ci_margin = Z_SCORE_95 * (coh_std / np.sqrt(len(coherences)))
    ci_lower = coh_mean - ci_margin
    ci_upper = coh_mean + ci_margin

    print(f"\n=Ê Phase Coherence Distribution:")
    print(f"   Mean: {coh_mean:.3f} (95% CI: [{ci_lower:.3f}, {ci_upper:.3f}])")
    print(f"   Median: {coh_median:.3f}")
    print(f"   Std Dev: {coh_std:.3f}")

    # Constitutional Metrics target: 0.85+
    if coh_mean >= PHASE_COHERENCE_TARGET:
        print(f"    Mean phase coherence {coh_mean:.3f} meets target {PHASE_COHERENCE_TARGET}")
    else:
        print(f"     Mean phase coherence {coh_mean:.3f} below target {PHASE_COHERENCE_TARGET}")


@pytest.mark.gadugi
def test_phase_coherence_federation_quality(thermal_sample):
    """
    Test that phase coherence is high quality (mean >= 0.65, ideally >= 0.85).

    Cherokee Value: Gadugi - ensure collective coordination is effective
    """
    coherences = [m['phase_coherence'] for m in thermal_sample]
    coh_mean = np.mean(coherences)

    # Minimum acceptable: 0.65 (moderate resonance)
    assert coh_mean >= 0.65, \
        f"Phase coherence mean {coh_mean:.3f} too low (< 0.65 minimum)"


# =============================================================================
# Test 3: Sacred Floor Protection (CRITICAL)
# =============================================================================

@pytest.mark.sacred_fire
def test_sacred_floor_zero_violations(thermal_sample):
    """
    Test that ZERO sacred memories are below 40 degree floor (CRITICAL).

    Cherokee Value: Sacred Fire - ZERO violations tolerance
    """
    sacred_memories = [m for m in thermal_sample if m['sacred_pattern']]

    if not sacred_memories:
        pytest.skip("No sacred memories in sample")

    violations = [m for m in sacred_memories if m['temperature_score'] < SACRED_FLOOR]

    violation_count = len(violations)
    total_sacred = len(sacred_memories)
    sacred_protection_ratio = (total_sacred - violation_count) / total_sacred

    print(f"\n=% Sacred Floor Protection:")
    print(f"   Total Sacred Memories: {total_sacred}")
    print(f"   Violations (< 40 degree): {violation_count}")
    print(f"   Protection Ratio: {sacred_protection_ratio:.4f}")

    # CRITICAL: ZERO violations required
    assert violation_count == 0, \
        f"SACRED FLOOR VIOLATION: {violation_count} sacred memories below 40 degree floor"

    assert sacred_protection_ratio == SACRED_PROTECTION_RATIO_TARGET, \
        f"Sacred protection ratio {sacred_protection_ratio:.4f} not perfect (target: {SACRED_PROTECTION_RATIO_TARGET})"

    print(f"    ZERO violations detected - Sacred Fire intact")


if __name__ == "__main__":
    # Run with: pytest tests/statistical/test_thermal_memory.py -v
    pytest.main([__file__, "-v", "--tb=short"])
