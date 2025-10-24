# Cherokee Constitutional AI - Pytest Configuration
# Week 3 Testing Infrastructure
# Created: October 24, 2025

import pytest
import sys
from pathlib import Path

# Add desktop_assistant to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'desktop_assistant'))


@pytest.fixture
def mock_guardian():
    """Mock Guardian instance for testing.

    Returns:
        Guardian instance with in-memory SQLite cache
    """
    try:
        from guardian_api_bridge import Guardian
        guardian = Guardian()
        guardian.initialize_cache(db_path=":memory:")
        return guardian
    except ImportError:
        pytest.skip("Guardian module not available")


@pytest.fixture
def mock_cache():
    """Mock EncryptedCache instance for testing.

    Returns:
        EncryptedCache instance with in-memory database
    """
    try:
        from cache.encrypted_cache import EncryptedCache
        cache = EncryptedCache(db_path=":memory:")
        return cache
    except ImportError:
        pytest.skip("EncryptedCache module not available")


@pytest.fixture
def sample_thermal_metrics():
    """Sample thermal memory metrics for testing.

    Returns:
        Dictionary with sample temperature, phase coherence, access count, sacred pattern
    """
    return {
        "temperature_score": 85.0,
        "phase_coherence": 0.92,
        "access_count": 3,
        "sacred_pattern": True
    }


@pytest.fixture
def sample_provenance_data():
    """Sample provenance log data for testing.

    Returns:
        Dictionary with sample provenance metadata
    """
    return {
        "entry_id": "test_entry_001",
        "user_id": "test_user",
        "operation": "READ",
        "data_type": "medical",
        "guardian_decision": "ALLOWED",
        "protection_level": "PRIVATE",
        "consent_token": "consent_abc123",
        "biometric_flag": False
    }


@pytest.fixture
def sacred_memory_violation():
    """Sample sacred memory below 40 degree floor for testing.

    Returns:
        Dictionary with sacred memory violation data
    """
    return {
        "entry_id": "sacred_001",
        "temperature_score": 35.0,  # Below 40 degree sacred floor
        "phase_coherence": 0.88,
        "sacred_pattern": True,
        "violation_severity": "CRITICAL"
    }


# Cherokee Values Integration
def pytest_configure(config):
    """Configure pytest with Cherokee Constitutional AI markers."""
    config.addinivalue_line(
        "markers", "gadugi: Test validates working together (Gadugi principle)"
    )
    config.addinivalue_line(
        "markers", "seven_generations: Test ensures long-term quality"
    )
    config.addinivalue_line(
        "markers", "mitakuye_oyasin: Test validates interconnection (All Our Relations)"
    )
    config.addinivalue_line(
        "markers", "sacred_fire: Test protects sacred memory (40 degree floor)"
    )


# Test collection hook
def pytest_collection_modifyitems(config, items):
    """Modify test collection to prioritize sacred floor tests."""
    sacred_tests = []
    other_tests = []

    for item in items:
        if "sacred" in item.nodeid.lower():
            sacred_tests.append(item)
        else:
            other_tests.append(item)

    # Run sacred floor tests first (critical protection)
    items[:] = sacred_tests + other_tests
